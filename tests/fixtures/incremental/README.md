# Incremental fixture (team-generated)

These fictional rows were authored from the schema, not copied from organizer data.
`day1` contains three transaction partitions plus the required dimensions and analytic inputs.
`day2` overlays a new day, an older late arrival, a restated amount and an extra column.
`bad` adds a duplicate primary key and a negative amount. The failed run quarantines invalid
rows and preserves the last good gold pointer. Removing `bad` permits the corrected snapshot.
The test also covers object removal, a clock-only rebuild, no-op reruns and a missing column.
The complaint deliberately points at another fixture customer's product to verify exclusion.
