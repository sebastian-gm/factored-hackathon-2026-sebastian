select p.product_id, p.customer_id, p.product_type, p.currency, p.product_status, p.opening_date,
p._dataset_version, p._source_file, p._source_sha256, p._ingested_at, p._pipeline_version
from {{ source('silver', 'products') }} p join {{ source('silver', 'customers') }} c using(customer_id)
where {{ trusted_customer('c') }} and {{ trusted_product('p') }}
