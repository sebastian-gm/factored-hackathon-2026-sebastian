select date, source_currency, target_currency, exchange_rate, _dataset_version, _source_file, _source_sha256, _ingested_at, _pipeline_version from {{ source('silver', 'daily_exchange_rates') }}
