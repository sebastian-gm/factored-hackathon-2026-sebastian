# Production readiness

This local prototype is not ready for real customer data or real banking actions. Before production it needs:

- a real identity provider, private networking, and reviewed access policies;
- a core banking integration and a scheduled, monitored data pipeline;
- model-risk governance and regulatory review for each country;
- human review of Portuguese and load behavior at scale;
- backup, disaster recovery, and on-call ownership;
- durable operational storage, retention enforcement, and incident procedures.

The same controlled workflow could later support fee disputes, card replacement, or payment-status questions after separate policy and safety review.
