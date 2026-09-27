select t.*, r.fraud_score from {{ ref('matcher_ledger') }} t
join {{ source('silver','transactions') }} r using(transaction_id)
where t.transaction_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 120 day
and t.transaction_date < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
