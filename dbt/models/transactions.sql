select t.*, r.fraud_score from {{ ref('matcher_ledger') }} t
join {{ source('silver','transactions') }} r using(transaction_id)
join {{ ref('products') }} p on t.product_id=p.product_id and t.customer_id=p.customer_id
join {{ ref('customers') }} c on t.customer_id=c.customer_id
where t.transaction_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 120 day
and t.transaction_date < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
and {{ trusted_transaction('t', 'p') }}
