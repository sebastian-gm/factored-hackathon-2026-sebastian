"""Render actual dbt manifest dependencies; no paths or row data in the figure."""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import dotenv_values


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    values = dotenv_values(root / ".env")
    lake = Path(os.environ.get("LAKE_DIR") or values.get("LAKE_DIR") or root / "lake")
    marker = json.loads((lake / "_meta/current.json").read_text())
    manifest = json.loads((Path(marker["database"]).parent / "dbt/manifest.json").read_text())
    os.environ.setdefault("MPLCONFIGDIR", str(root / "artifacts/matplotlib"))
    import matplotlib

    matplotlib.use("Agg")
    import networkx as nx
    from matplotlib import pyplot as plt

    graph = nx.DiGraph()
    labels = {}
    for identifier, node in {**manifest["sources"], **manifest["nodes"]}.items():
        if node["resource_type"] not in {"source", "model"}:
            continue
        graph.add_node(identifier)
        labels[identifier] = ("silver." if node["resource_type"] == "source" else "gold.") + node[
            "name"
        ]
        for dependency in node.get("depends_on", {}).get("nodes", []):
            if dependency.startswith(("source.", "model.")):
                graph.add_edge(dependency, identifier)
    generations = list(nx.topological_generations(graph))
    positions = {
        node: (level, -index + len(nodes) / 2)
        for level, nodes in enumerate(generations)
        for index, node in enumerate(sorted(nodes))
    }
    fig, ax = plt.subplots(figsize=(19, 10), layout="constrained")
    nx.draw_networkx(
        graph,
        pos=positions,
        labels=labels,
        ax=ax,
        node_size=1200,
        node_color="#d6e9f2",
        edge_color="#6b7d87",
        font_size=8,
        arrowsize=12,
    )
    ax.set_title("Aclara: dependencies from the verified dbt manifest")
    ax.axis("off")
    out = root / "docs/data/dbt-lineage.svg"
    fig.savefig(out)
    out.write_text("\n".join(line.rstrip() for line in out.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
