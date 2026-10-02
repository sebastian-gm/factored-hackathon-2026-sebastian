select customer_id, country, segment, customer_status, _dataset_version, _source_file, _source_sha256, _ingested_at, _pipeline_version
from {{ source('silver', 'customers') }} c where {{ trusted_customer('c') }}
