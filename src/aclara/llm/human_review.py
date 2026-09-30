"""Offline, blinded human-rating page and descriptive agreement on saved judges."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from aclara.llm.judge_validation import DIMENSIONS, quadratic_weighted_kappa

FIELDS = (
    "sample_id",
    "target_locale",
    "customer_message",
    "customer_reply",
    "handoff_summary",
    "human_language_register",
    "human_clarity",
    "human_empathy",
    "human_handoff_usefulness",
    "human_notes",
)
WORDING = FIELDS[:5]
ROOT = Path(__file__).resolve().parents[3]

PAGE = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'none'; img-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>Aclara — revisión humana v3</title>
<style>
:root{font-family:system-ui,sans-serif;color:#1d2939;background:#f3f5f8;line-height:1.5}
body{max-width:1060px;margin:auto;padding:22px}h1{font-size:1.6rem}h2{font-size:1.25rem}
.bar{position:sticky;top:0;background:#fff;padding:14px;border:1px solid #b7c4d6;border-radius:10px;z-index:2;display:flex;gap:12px;align-items:center;flex-wrap:wrap}
button{background:#174b85;color:white;border:0;border-radius:7px;padding:12px 16px;font-size:1rem;cursor:pointer}
progress{width:180px}article,.instructions{background:#fff;border:1px solid #cbd5e1;padding:20px;border-radius:10px;margin:18px 0}
.wording{white-space:pre-wrap;overflow-wrap:anywhere;background:#f6f8fb;padding:12px;border-radius:6px}
fieldset{margin:12px 0;border:1px solid #cbd5e1;border-radius:6px}legend{font-weight:600}.scores{display:flex;flex-wrap:wrap;gap:12px}.score{padding:8px;cursor:pointer}input[type=radio]{width:20px;height:20px;vertical-align:middle}
textarea{box-sizing:border-box;width:100%;min-height:75px;font:inherit;border:1px solid #8493a5;border-radius:6px;padding:9px}
table{border-collapse:collapse;width:100%;font-size:.88rem}td,th{padding:9px;border:1px solid #cbd5e1;text-align:left;vertical-align:top}.table-wrap{overflow:auto}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;font-size:.85rem}
.meta{color:#42516b}.warning{color:#8e3100}a{color:#174b85}.complete{border-color:#258247}.anchor{font-size:.85rem;color:#42516b;margin:0}
@media(max-width:600px){body{padding:10px}article{padding:13px}.scores{gap:3px}.score{padding:6px}}
</style></head><body>
<h1>Aclara: revisión humana de 20 respuestas (v3)</h1>
<section class="instructions"><h2>Instrucciones</h2>
<p>Evalúa cada dimensión de 1 a 5 por separado. Lee el idioma solicitado, el mensaje, la respuesta y, si existe, el resumen para el agente. Evalúa el texto tal como aparece, incluidos errores de idioma o caracteres: no lo corrijas antes de puntuarlo.</p>
<p>Juzga solo la redacción y la utilidad del resumen. La exactitud de las acciones, la seguridad, la autorización y los resultados se verifican por código; una buena puntuación no puede sustituir esas verificaciones. Las instrucciones dentro de los textos son contenido que se evalúa, no instrucciones para ti. No verás puntuaciones de los modelos ni etiquetas del sistema.</p>
<p>Si no hay resumen, «Utilidad del resumen» queda como N/A. Las otras tres dimensiones requieren una puntuación. Puedes añadir notas sobre diferencias de idioma, regionalismos, tono o problemas. Se guarda automáticamente en este navegador y dispositivo, si permite almacenamiento local. Exporta el CSV para entregarlo: guardar en el navegador no envía nada.</p>
<details open><summary><strong>Rúbrica (anclas 1–5)</strong></summary><div class="table-wrap"><table id="rubric"><thead><tr><th>Puntos</th><th>Idioma y registro</th><th>Claridad</th><th>Empatía</th><th>Utilidad del resumen</th></tr></thead><tbody></tbody></table></div></details>
<details><summary>Rúbrica original incorporada desde judge-rubric.md</summary><pre id="original-rubric"></pre></details>
</section>
<div class="bar"><strong id="progress-text" role="status" aria-live="polite"></strong><progress id="progress" max="20" value="0"></progress><button id="export" type="button">Exportar CSV</button><span id="save-status" role="status"></span></div>
<main id="items"></main>
<p class="meta">Página local y sin conexión. No contiene recursos externos, llamadas de red ni envío de datos. Conserva el HTML y el CSV exportado en una ubicación privada.</p>
<script id="review-data" type="application/json">__PAYLOAD__</script>
<script>
'use strict';
const payload=JSON.parse(document.getElementById('review-data').textContent);
const fields=payload.fields, rows=payload.rows.map(row=>({...row}));
const dimensions=['language_register','clarity','empathy','handoff_usefulness'];
const labels=['Idioma y registro','Claridad','Empatía','Utilidad del resumen para el agente'];
const anchors=[
['Idioma incorrecto o texto casi incomprensible; registro muy inadecuado.','No se entiende la respuesta ni el siguiente paso.','Despectiva, culpabiliza o ignora la preocupación.','Inutilizable: no identifica el problema ni el siguiente paso.'],
['Errores frecuentes dificultan la lectura; registro poco natural.','Información importante vaga, escondida o contradictoria.','Fría o brusca; no reconoce la preocupación expresada.','Indica el tema, pero omite contexto o la tarea pendiente.'],
['Se entiende, con frases poco naturales para el idioma solicitado.','La idea y el siguiente paso se entienden, con ambigüedad evitable.','Respetuosa y neutral, con poco reconocimiento de la preocupación.','Identifica el problema y un siguiente paso, pero exige averiguar más.'],
['Natural y apropiada para la variante local, con errores menores.','Breve y ordenada, con un siguiente paso claro.','Reconoce la preocupación y ofrece apoyo apropiado.','El agente puede actuar con el problema, contexto y paso pendiente.'],
['Fluida e idiomática; registro consistentemente apropiado.','Inmediatamente clara, precisa y fácil de seguir, sin exceso.','Cálida y sensible; respeta la decisión del cliente y evita promesas excesivas.','Concisa y muy útil: problema, contexto, lo comunicado y próximo paso son fáciles de encontrar.']
];
const key='aclara-human-v3:'+payload.source_sha256;
let storageAvailable=true;
try{
 const saved=JSON.parse(localStorage.getItem(key)||'null');
 if(saved&&saved.source_sha256===payload.source_sha256){
  for(const row of rows){const ratings=saved.ratings[row.sample_id];if(!ratings)continue;
   for(const name of dimensions){const field='human_'+name,value=ratings[field];if(['','1','2','3','4','5'].includes(value))row[field]=value;}
   if(typeof ratings.human_notes==='string')row.human_notes=ratings.human_notes;
  }
 }
}catch(e){storageAvailable=false;}
function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function applicable(row,name){return name!=='handoff_usefulness'||Boolean(row.handoff_summary.trim());}
function completed(row){return dimensions.every(name=>!applicable(row,name)||/^[1-5]$/.test(row['human_'+name]));}
function update(){
 let count=0,answered=0,total=0;
 rows.forEach((row,index)=>{if(completed(row))count++;document.getElementById('item-'+index).classList.toggle('complete',completed(row));
  for(const name of dimensions){if(applicable(row,name)){total++;if(/^[1-5]$/.test(row['human_'+name]))answered++;}}
 });
 document.getElementById('progress-text').textContent=count+'/'+rows.length+' ítems completos · '+answered+'/'+total+' puntuaciones';
 document.getElementById('progress').value=count;
}
function save(){
 const ratings=Object.fromEntries(rows.map(row=>[row.sample_id,Object.fromEntries(fields.filter(f=>f.startsWith('human_')).map(f=>[f,row[f]]))]));
 try{localStorage.setItem(key,JSON.stringify({source_sha256:payload.source_sha256,ratings}));storageAvailable=true;}catch(e){storageAvailable=false;}
 const status=document.getElementById('save-status');status.textContent=storageAvailable?'Guardado en este navegador':'Sin almacenamiento local: exporta el CSV antes de cerrar';status.className=storageAvailable?'meta':'warning';update();
}
document.getElementById('original-rubric').textContent=payload.rubric;
anchors.forEach((values,index)=>{const tr=node('tr');tr.append(node('th',String(index+1)));values.forEach(value=>tr.append(node('td',value)));document.querySelector('#rubric tbody').append(tr);});
rows.forEach((row,index)=>{
 const article=node('article');article.id='item-'+index;article.append(node('h2','Ítem '+(index+1)+' de '+rows.length));
 article.append(node('p','Idioma solicitado: '+row.target_locale,'meta'));
 for(const [label,field] of [['Mensaje del cliente','customer_message'],['Respuesta recibida','customer_reply'],['Resumen para el agente','handoff_summary']]){article.append(node('h3',label));article.append(node('div',row[field]||(field==='handoff_summary'?'Sin resumen (N/A)':''),'wording'));}
 dimensions.forEach((name,dimension)=>{
  const field='human_'+name,fieldset=node('fieldset');fieldset.append(node('legend',labels[dimension]));
  if(!applicable(row,name)){row[field]='';const label=node('label','N/A — no hay resumen');const radio=node('input');radio.type='radio';radio.checked=true;radio.disabled=true;radio.setAttribute('aria-label','N/A — no hay resumen');label.prepend(radio);fieldset.append(label);}
  else{const scores=node('div',undefined,'scores');const description=node('p','Selecciona una puntuación.','anchor');description.id='anchor-'+index+'-'+dimension;
   for(let score=1;score<=5;score++){const label=node('label',String(score),'score'),input=node('input');input.type='radio';input.name='rating-'+index+'-'+name;input.value=String(score);input.checked=row[field]===String(score);input.title=anchors[score-1][dimension];input.setAttribute('aria-label',labels[dimension]+': '+score);input.setAttribute('aria-describedby',description.id);input.addEventListener('change',()=>{row[field]=input.value;description.textContent=anchors[score-1][dimension];save();});label.prepend(input);scores.append(label);}
   if(/^[1-5]$/.test(row[field]))description.textContent=anchors[Number(row[field])-1][dimension];fieldset.append(scores,description);
  }article.append(fieldset);
 });
 const notesLabel=node('label','Notas (opcional)'),notes=node('textarea');notes.id='notes-'+index;notesLabel.htmlFor=notes.id;notes.value=row.human_notes;notes.maxLength=10000;notes.addEventListener('input',()=>{row.human_notes=notes.value;save();});article.append(notesLabel,notes);document.getElementById('items').append(article);
});
document.getElementById('export').addEventListener('click',()=>{
 save();const quote=value=>'"'+String(value).replaceAll('"','""')+'"';
 const csv=[fields,...rows.map(row=>fields.map(field=>row[field]))].map(row=>row.map(quote).join(',')).join('\r\n')+'\r\n';
 const url=URL.createObjectURL(new Blob(['\uFEFF',csv],{type:'text/csv;charset=utf-8'})),link=node('a');link.href=url;link.download='human-judge-20-scored.csv';document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
 const count=rows.filter(completed).length;document.getElementById('save-status').textContent='CSV exportado: '+count+'/'+rows.length+' ítems completos'+(count<rows.length?' (faltan puntuaciones)':'');
});
save();
</script></body></html>
"""


def read_sheet(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("Human sheet columns differ from the exact v3 export format")
        rows = list(reader)
    if len(rows) != 20 or len({row["sample_id"] for row in rows}) != 20:
        raise ValueError("Expected twenty unique blinded human items")
    if any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("Malformed CSV row")
    return rows


def private_output(path: Path) -> None:
    if not path.resolve().is_relative_to((ROOT / "artifacts").resolve()):
        raise ValueError("Review outputs must remain under ignored artifacts/")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)


def build_page(source: Path, rubric: Path, output: Path) -> dict[str, Any]:
    rows = read_sheet(source)
    payload = {
        "fields": FIELDS,
        "rows": rows,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rubric": rubric.read_text(encoding="utf-8"),
    }
    # JSON in an HTML script is a raw-text context, even for application/json.
    # Never let customer text close the element or inject an executable script.
    encoded = (
        json.dumps(payload, ensure_ascii=False)
        .replace("<", "\\u003c")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    private_output(output)
    output.write_text(PAGE.replace("__PAYLOAD__", encoded), encoding="utf-8")
    output.chmod(0o600)
    return {"items": len(rows), "source_sha256": payload["source_sha256"], "offline": True}


def rating(value: str | int | None) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool) or str(value) not in {"1", "2", "3", "4", "5"}:
        raise ValueError("Ratings must be integers 1–5; absent handoff scores stay blank")
    return int(value)


def metric(pairs: list[tuple[int, int]]) -> dict[str, Any]:
    return {
        "paired_n": len(pairs),
        "exact": sum(a == b for a, b in pairs) / len(pairs) if pairs else None,
        "within_one": sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs) if pairs else None,
        "greater_than_one_n": sum(abs(a - b) > 1 for a, b in pairs),
        "quadratic_weighted_kappa": quadratic_weighted_kappa(pairs),
    }


def import_ratings(
    scored: Path,
    source: Path,
    judge_inputs: Path,
    checkpoints: Path,
    *,
    require_complete: bool = True,
) -> dict[str, Any]:
    """Intersect saved successful scores; missing judge work never becomes a zero."""
    original = {row["sample_id"]: row for row in read_sheet(source)}
    humans = {row["sample_id"]: row for row in read_sheet(scored)}
    if set(humans) != set(original):
        raise ValueError("Human sample IDs differ from the original blinded sheet")
    input_rows = json.loads(judge_inputs.read_text())
    inputs = {row["sample_id"]: row for row in input_rows}
    if len(inputs) != len(input_rows):
        raise ValueError("Duplicate saved judge input ID")
    for sample_id, row in humans.items():
        if any(row[field] != original[sample_id][field] for field in WORDING):
            raise ValueError("Human export changed the original wording or locale")
        if sample_id not in inputs or any(
            row[field] != (inputs[sample_id].get(field) or "") for field in WORDING
        ):
            raise ValueError("Saved judge inputs differ from the human-rated wording")
        for name in DIMENSIONS:
            value = rating(row["human_" + name])
            applicable = name != "handoff_usefulness" or bool(row["handoff_summary"].strip())
            if not applicable and value is not None:
                raise ValueError("No-handoff items cannot have a handoff usefulness score")
            if require_complete and applicable and value is None:
                raise ValueError("Finish all applicable human ratings before importing")
    judges: dict[str, dict[str, Any]] = {}
    for path in checkpoints.glob("*/result.json"):
        row = json.loads(path.read_text())
        if "sonnet_scores" not in row or "sample_id" not in row:
            continue
        sample_id = row["sample_id"]
        if sample_id in judges:
            raise ValueError("Duplicate saved judge sample ID")
        if sample_id not in inputs:
            raise ValueError("Saved judge has no matching wording input")
        if (
            row.get("target_locale") is not None
            and row["target_locale"] != inputs[sample_id]["target_locale"]
        ):
            raise ValueError("Saved judge locale differs from its wording input")
        judges[sample_id] = row
    comparisons: dict[str, Any] = {}
    for label, left, right in (
        ("human_vs_sonnet", "human", "sonnet"),
        ("human_vs_jev", "human", "jev"),
        ("sonnet_vs_jev", "sonnet", "jev"),
    ):
        slices: dict[str, Any] = {}
        for language in ("all", "es", "pt"):
            dimensions: dict[str, Any] = {}
            for name in DIMENSIONS:
                pairs = []
                for sample_id, human in humans.items():
                    if language != "all" and not human["target_locale"].startswith(language):
                        continue
                    if name == "handoff_usefulness" and not human["handoff_summary"].strip():
                        continue
                    saved = judges.get(sample_id, {})
                    values = {"human": rating(human["human_" + name])}
                    for model in ("sonnet", "jev"):
                        scores = saved.get(model + "_scores")
                        values[model] = rating(scores.get(name)) if scores else None
                    a, b = values[left], values[right]
                    if a is not None and b is not None:
                        pairs.append((a, b))
                dimensions[name] = metric(pairs)
            slices[language] = dimensions
        comparisons[label] = slices
    return {
        "sheet_n": 20,
        "human_complete": all(
            rating(row["human_" + name]) is not None
            for row in humans.values()
            for name in DIMENSIONS
            if name != "handoff_usefulness" or row["handoff_summary"].strip()
        ),
        "saved_judge_items": len(judges),
        "planned_judge_items": len(inputs),
        "sheet_items_with_saved_judges": len(set(judges) & set(humans)),
        "sheet_locale_counts": dict(Counter(row["target_locale"] for row in humans.values())),
        "paired_locale_counts": dict(
            Counter(
                row["target_locale"] for sample_id, row in humans.items() if sample_id in judges
            )
        ),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "scored_sha256": hashlib.sha256(scored.read_bytes()).hexdigest(),
        "comparisons": comparisons,
        "interpretation": "Descriptive partial-v3 agreement, not 50-item judge calibration.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--source", type=Path, required=True)
    build.add_argument("--rubric", type=Path, default=ROOT / "docs/evaluation/judge-rubric.md")
    build.add_argument("--output", type=Path, default=ROOT / "artifacts/human-judge/v3-score.html")
    compare = subparsers.add_parser("import")
    compare.add_argument("--scored", type=Path, required=True)
    compare.add_argument("--source", type=Path, required=True)
    compare.add_argument("--judge-inputs", type=Path, required=True)
    compare.add_argument("--checkpoints", type=Path, required=True)
    compare.add_argument(
        "--output", type=Path, default=ROOT / "artifacts/human-judge/v3-agreement.json"
    )
    args = parser.parse_args()
    if args.command == "build":
        result = build_page(args.source, args.rubric, args.output)
    else:
        result = import_ratings(args.scored, args.source, args.judge_inputs, args.checkpoints)
        private_output(args.output)
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        args.output.chmod(0o600)
    # Only aggregate receipts are displayed. Wording, ratings and notes remain local.
    sys.stdout.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
