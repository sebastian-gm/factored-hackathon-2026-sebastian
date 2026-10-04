"use client";

export type EvidenceRow = {
  label: string;
  value: number;
  detail: string;
  variant?: "p" | "b1";
};

/** Labels are real text; SVG supplies only the proportional, zero-based marks.
 * The same values remain readable without color, SVG, hover or a legend. */
export function EvidenceChart({
  title,
  rows,
  axisLabel,
  tick,
  max = 1,
  sort = true,
}: {
  title: string;
  rows: EvidenceRow[];
  axisLabel: string;
  tick: (value: number) => string;
  max?: number;
  sort?: boolean;
}) {
  const ordered = sort ? [...rows].sort((a, b) => b.value - a.value) : rows;
  const axisTick = (value: number) => tick(value).replaceAll("\u00a0", " ");
  return (
    <figure
      className="evidence-chart"
      data-zero-based="true"
      data-axis-max={max}
    >
      <figcaption>{title}</figcaption>
      <div className="evidence-bars">
        {ordered.map((row) => (
          <div className={`evidence-row ${row.variant ?? "p"}`} key={row.label}>
            <div className="evidence-label">
              <span>{row.label}</span>
              <strong>{row.detail}</strong>
            </div>
            <svg
              viewBox="0 0 100 12"
              preserveAspectRatio="none"
              aria-hidden="true"
            >
              <line x1="0" x2="0" y1="0" y2="12" className="evidence-origin" />
              <rect
                x="0"
                y="1"
                width={(100 * row.value) / max}
                height="10"
                data-value={row.value}
              />
            </svg>
          </div>
        ))}
      </div>
      <div className="evidence-axis" aria-hidden="true">
        <span>{axisTick(0)}</span>
        <span>{axisTick(max / 2)}</span>
        <span>{axisTick(max)}</span>
      </div>
      <p className="evidence-units">{axisLabel}</p>
    </figure>
  );
}
