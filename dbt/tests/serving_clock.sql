select count(*) as failures from {{ ref('transactions') }}
where transaction_date<cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 120 day
   or transaction_date>=cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
having count(*)>0
