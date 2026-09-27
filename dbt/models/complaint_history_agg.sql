select c.customer_id, count(q.complaint_id)::BIGINT as complaint_count_90d,
c._dataset_version, 'aggregate:customers+complaints'::VARCHAR as _source_file,
c._dataset_version as _source_sha256, max(c._ingested_at) as _ingested_at, c._pipeline_version
from {{ ref('customers') }} c left join {{ source('silver','complaints') }} q
on c.customer_id=q.customer_id
and q.creation_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 90 day
and q.creation_date < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
group by c.customer_id,c._dataset_version,c._pipeline_version
