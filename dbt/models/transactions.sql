select t.*, r.fraud_score, {{ temporal_quality_reason('t', 'p', 'c') }} as temporal_quality_reason
from {{ ref('matcher_ledger') }} t
join {{ source('silver','transactions') }} r using(transaction_id)
join {{ source('silver','products') }} p on t.product_id=p.product_id
join {{ source('silver','customers') }} c on t.customer_id=c.customer_id
where t.transaction_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 120 day
and t.transaction_date < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
