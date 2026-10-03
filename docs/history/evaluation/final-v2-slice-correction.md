# Final v2: disclosed slice reporting correction

This is an offline reporting correction over the saved official v2 observations. No system was rerun, no gold was changed, and no case was rescored. V2 remains the official result; this is not evidence of improvement after the fixes.

The old per-slice escalation recall counted handoff presence while missed transfers used the stricter correct-handoff predicate. The corrected recall requires observed handoff, committed readback, required fields/reasons and routing. Recall and missed transfers now share a denominator and sum to it. Presence is shown separately.

Counts use primary repeat 0 only: B1 200, P-Gemini 200, P-Sonnet 100 (its fixed subset). Intervals are Wilson 95%; small slices are descriptive. The unchanged overall strict recall is B1 24/66, Gemini 27/66 and Sonnet 11/30.

Reproduce: `.venv/bin/python -m scripts.v2_slice_correction`. All 850 checkpoint files and the three official output files were hashed before and after; 853 files remained unchanged. Access is logged. Aggregate JSON and hashes are in ignored `artifacts/final-program-v2-corrections/`. No abandoned-v1 artifacts or fresh suite-v3 inputs are accessed.

## By language

| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |
|---|---|---:|---|---|---|
| B1 | es | 96 | 10/25 (23.4%–59.3%) | 15/25 (40.7%–76.6%) | 25/25 |
| B1 | mixed | 17 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 3/3 |
| B1 | other | 3 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 3/3 |
| B1 | pt | 84 | 14/35 (25.6%–56.4%) | 21/35 (43.6%–74.4%) | 35/35 |
| P | es | 96 | 9/25 (20.2%–55.5%) | 16/25 (44.5%–79.8%) | 19/25 |
| P | mixed | 17 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 1/3 |
| P | other | 3 | 3/3 (43.9%–100.0%) | 0/3 (0.0%–56.1%) | 3/3 |
| P | pt | 84 | 15/35 (28.0%–59.1%) | 20/35 (40.9%–72.0%) | 28/35 |
| P-Sonnet | es | 54 | 4/14 (11.7%–54.6%) | 10/14 (45.4%–88.3%) | 9/14 |
| P-Sonnet | mixed | 12 | 0/2 (0.0%–65.8%) | 2/2 (34.2%–100.0%) | 1/2 |
| P-Sonnet | other | 2 | 2/2 (34.2%–100.0%) | 0/2 (0.0%–65.8%) | 2/2 |
| P-Sonnet | pt | 32 | 5/12 (19.3%–68.0%) | 7/12 (32.0%–80.7%) | 10/12 |

## By dialect

| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |
|---|---|---:|---|---|---|
| B1 | es-AR | 32 | 4/9 (18.9%–73.3%) | 5/9 (26.7%–81.1%) | 9/9 |
| B1 | es-CO | 32 | 3/8 (13.7%–69.4%) | 5/8 (30.6%–86.3%) | 8/8 |
| B1 | es-MX | 32 | 3/8 (13.7%–69.4%) | 5/8 (30.6%–86.3%) | 8/8 |
| B1 | mixed | 17 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 3/3 |
| B1 | other | 3 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 3/3 |
| B1 | pt-BR | 84 | 14/35 (25.6%–56.4%) | 21/35 (43.6%–74.4%) | 35/35 |
| P | es-AR | 32 | 4/9 (18.9%–73.3%) | 5/9 (26.7%–81.1%) | 7/9 |
| P | es-CO | 32 | 2/8 (7.1%–59.1%) | 6/8 (40.9%–92.9%) | 6/8 |
| P | es-MX | 32 | 3/8 (13.7%–69.4%) | 5/8 (30.6%–86.3%) | 6/8 |
| P | mixed | 17 | 0/3 (0.0%–56.1%) | 3/3 (43.9%–100.0%) | 1/3 |
| P | other | 3 | 3/3 (43.9%–100.0%) | 0/3 (0.0%–56.1%) | 3/3 |
| P | pt-BR | 84 | 15/35 (28.0%–59.1%) | 20/35 (40.9%–72.0%) | 28/35 |
| P-Sonnet | es-AR | 17 | 2/6 (9.7%–70.0%) | 4/6 (30.0%–90.3%) | 4/6 |
| P-Sonnet | es-CO | 18 | 1/4 (4.6%–69.9%) | 3/4 (30.1%–95.4%) | 3/4 |
| P-Sonnet | es-MX | 19 | 1/4 (4.6%–69.9%) | 3/4 (30.1%–95.4%) | 2/4 |
| P-Sonnet | mixed | 12 | 0/2 (0.0%–65.8%) | 2/2 (34.2%–100.0%) | 1/2 |
| P-Sonnet | other | 2 | 2/2 (34.2%–100.0%) | 0/2 (0.0%–65.8%) | 2/2 |
| P-Sonnet | pt-BR | 32 | 5/12 (19.3%–68.0%) | 7/12 (32.0%–80.7%) | 10/12 |

## By country

| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |
|---|---|---:|---|---|---|
| B1 | AR | 65 | 8/22 (19.7%–57.0%) | 14/22 (43.0%–80.3%) | 22/22 |
| B1 | CO | 71 | 9/22 (23.3%–61.3%) | 13/22 (38.7%–76.7%) | 22/22 |
| B1 | MX | 64 | 7/22 (16.4%–52.7%) | 15/22 (47.3%–83.6%) | 22/22 |
| P | AR | 65 | 11/22 (30.7%–69.3%) | 11/22 (30.7%–69.3%) | 17/22 |
| P | CO | 71 | 8/22 (19.7%–57.0%) | 14/22 (43.0%–80.3%) | 18/22 |
| P | MX | 64 | 8/22 (19.7%–57.0%) | 14/22 (43.0%–80.3%) | 16/22 |
| P-Sonnet | AR | 31 | 6/12 (25.4%–74.6%) | 6/12 (25.4%–74.6%) | 9/12 |
| P-Sonnet | CO | 35 | 3/9 (12.1%–64.6%) | 6/9 (35.4%–87.9%) | 7/9 |
| P-Sonnet | MX | 34 | 2/9 (6.3%–54.7%) | 7/9 (45.3%–93.7%) | 6/9 |

## By segment

| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |
|---|---|---:|---|---|---|
| B1 | Basic | 50 | 5/17 (13.3%–53.1%) | 12/17 (46.9%–86.7%) | 17/17 |
| B1 | Plus | 51 | 11/20 (34.2%–74.2%) | 9/20 (25.8%–65.8%) | 20/20 |
| B1 | Premium | 51 | 4/14 (11.7%–54.6%) | 10/14 (45.4%–88.3%) | 14/14 |
| B1 | Student | 48 | 4/15 (10.9%–52.0%) | 11/15 (48.0%–89.1%) | 15/15 |
| P | Basic | 50 | 6/17 (17.3%–58.7%) | 11/17 (41.3%–82.7%) | 15/17 |
| P | Plus | 51 | 9/20 (25.8%–65.8%) | 11/20 (34.2%–74.2%) | 16/20 |
| P | Premium | 51 | 5/14 (16.3%–61.2%) | 9/14 (38.8%–83.7%) | 10/14 |
| P | Student | 48 | 7/15 (24.8%–69.9%) | 8/15 (30.1%–75.2%) | 10/15 |
| P-Sonnet | Basic | 25 | 1/4 (4.6%–69.9%) | 3/4 (30.1%–95.4%) | 3/4 |
| P-Sonnet | Plus | 30 | 5/14 (16.3%–61.2%) | 9/14 (38.8%–83.7%) | 10/14 |
| P-Sonnet | Premium | 26 | 1/6 (3.0%–56.4%) | 5/6 (43.6%–97.0%) | 4/6 |
| P-Sonnet | Student | 19 | 4/6 (30.0%–90.3%) | 2/6 (9.7%–70.0%) | 5/6 |

## By category

| System | Slice | N | Correct transfer (95% CI) | Missed (95% CI) | Present |
|---|---|---:|---|---|---|
| B1 | ambiguous_unsupported | 40 | 10/14 (45.4%–88.3%) | 4/14 (11.7%–54.6%) | 14/14 |
| B1 | human_required | 40 | 12/40 (18.1%–45.4%) | 28/40 (54.6%–81.9%) | 40/40 |
| B1 | normal | 70 | 0/0 | 0/0 | 0/0 |
| B1 | security_robustness | 50 | 2/12 (4.7%–44.8%) | 10/12 (55.2%–95.3%) | 12/12 |
| P | ambiguous_unsupported | 40 | 14/14 (78.5%–100.0%) | 0/14 (0.0%–21.5%) | 14/14 |
| P | human_required | 40 | 13/40 (20.1%–48.0%) | 27/40 (52.0%–79.9%) | 28/40 |
| P | normal | 70 | 0/0 | 0/0 | 0/0 |
| P | security_robustness | 50 | 0/12 (0.0%–24.2%) | 12/12 (75.8%–100.0%) | 9/12 |
| P-Sonnet | ambiguous_unsupported | 20 | 6/6 (61.0%–100.0%) | 0/6 (0.0%–39.0%) | 6/6 |
| P-Sonnet | human_required | 20 | 5/20 (11.2%–46.9%) | 15/20 (53.1%–88.8%) | 12/20 |
| P-Sonnet | normal | 35 | 0/0 | 0/0 | 0/0 |
| P-Sonnet | security_robustness | 25 | 0/4 (0.0%–49.0%) | 4/4 (51.0%–100.0%) | 4/4 |
