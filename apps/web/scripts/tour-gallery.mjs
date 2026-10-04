import { readdirSync, writeFileSync, chmodSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
const directory = fileURLToPath(
  new URL("../../../artifacts/ux-audit/go-live/", import.meta.url),
);
function walk(root) {
  return readdirSync(root, { withFileTypes: true }).flatMap((item) => {
    const file = path.join(root, item.name);
    return item.isDirectory()
      ? walk(file)
      : item.name.endsWith(".png")
        ? [file]
        : [];
  });
}
const escape = (value) =>
  value.replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
const files = walk(directory).sort();
for (const file of files) chmodSync(file, 0o600);
writeFileSync(
  path.join(directory, "index.html"),
  `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Private Aclara judge gallery</title><style>body{font:16px system-ui;margin:24px;background:#f5f5f2;color:#202f32}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:24px}figure{margin:0}img{width:100%;max-height:650px;object-fit:contain;object-position:top;background:white}a{color:#1b6654}figcaption{padding:12px;overflow-wrap:anywhere}</style><h1>Private judge tour</h1><p>Local mock evidence is under demo. Live evidence is added after judge access opens. Credentials are masked; live customer facts are also masked. Select an image for full size.</p><main>${files
    .map((file) => {
      const relative = path.relative(directory, file);
      return `<figure><a href="${escape(relative)}"><img loading="lazy" src="${escape(relative)}" alt="${escape(relative)}"></a><figcaption>${escape(relative)}</figcaption></figure>`;
    })
    .join("")}</main></html>`,
  { mode: 0o600 },
);
process.stdout.write(
  JSON.stringify({
    screenshots: files.length,
    gallery: "artifacts/ux-audit/go-live/index.html",
  }) + "\n",
);
