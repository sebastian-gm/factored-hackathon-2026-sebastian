# Frozen matcher result review

This review reuses the one-time v1 predictions; there is no refitting or additional test inference.

## Selection and uncertainty

LightGBM was selected on validation before opening test. Test logistic regression has lower mean cost and better calibration, while LightGBM makes fewer wrong proposals. The held-out result does not change thresholds or the selected artifact. A future independent workload should revisit this trade-off.

| Model | Cost difference vs rules | Customer-clustered 95% interval |
|---|---:|---|
| logistic | -0.2217 | [-0.27330867489318195, -0.16777418521920653] |
| lightgbm | -0.1480 | [-0.19208010109397175, -0.10385692018958553] |

The lower-is-better cost combines explicitly chosen synthetic error costs; this interval is not a guarantee of production safety.

## Slice review

| Model | Slice | Group | n | Top-1 | Cost |
|---|---|---|---:|---:|---:|
| lightgbm | by_country | AR | 612 | 0.9578 | 0.4379 |
| lightgbm | by_country | CO | 909 | 0.9513 | 0.4939 |
| lightgbm | by_country | MX | 1479 | 0.9503 | 0.4719 |
| lightgbm | by_segment | Basic | 1797 | 0.9540 | 0.4686 |
| lightgbm | by_segment | Plus | 729 | 0.9468 | 0.4540 |
| lightgbm | by_segment | Premium | 306 | 0.9621 | 0.5163 |
| lightgbm | by_segment | Student | 168 | 0.9371 | 0.5000 |
| logistic | by_country | AR | 612 | 0.9693 | 0.3284 |
| logistic | by_country | CO | 909 | 0.9718 | 0.4037 |
| logistic | by_country | MX | 1479 | 0.9647 | 0.4233 |
| logistic | by_segment | Basic | 1797 | 0.9691 | 0.4124 |
| logistic | by_segment | Plus | 729 | 0.9645 | 0.3731 |
| logistic | by_segment | Premium | 306 | 0.9697 | 0.3922 |
| logistic | by_segment | Student | 168 | 0.9650 | 0.3631 |
| rules | by_country | AR | 612 | 0.8541 | 0.6062 |
| rules | by_country | CO | 909 | 0.8656 | 0.6744 |
| rules | by_country | MX | 1479 | 0.8710 | 0.5916 |
| rules | by_segment | Basic | 1797 | 0.8641 | 0.5982 |
| rules | by_segment | Plus | 729 | 0.8694 | 0.5981 |
| rules | by_segment | Premium | 306 | 0.8788 | 0.6993 |
| rules | by_segment | Student | 168 | 0.8462 | 0.7976 |

These groups describe source customer attributes, not language performance. Candidate-set size, query family and source composition can differ by group; gaps are observational. Protected attributes never enter the feature vector.

## Known synthetic artifacts

As-of clocks are zero to ten days after the target business date. This makes recency predictive by construction and can overstate improvement on a real workload. Customers without a target transaction are not sampled, so the target-sampled candidate distribution is larger than the all-customer serving distribution. No-match donor/fabrication and held-out stress profiles can shift confidence; LightGBM’s NONE precision and ECE warrant particular caution.

## Human validation plan

Sebastian has 40 private Spanish cards from customers excluded from every synthetic benchmark split. Recollections are blank and human validation is pending. Portuguese recollections will be labeled model-generated and cross-checked by a second model vendor, after the relevant model access/cost approval. No Portuguese performance or human labeling agreement is claimed.
