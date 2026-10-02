-- Source-equivalent row sets and correct nullable flags; anomalous rows stay visible.
with customer_gap as (
  (select customer_id from {{ ref('customers') }}
   except all select customer_id from {{ source('silver','customers') }})
  union all
  (select customer_id from {{ source('silver','customers') }}
   except all select customer_id from {{ ref('customers') }})
), product_gap as (
  (select product_id from {{ ref('products') }}
   except all select product_id from {{ source('silver','products') }})
  union all
  (select product_id from {{ source('silver','products') }}
   except all select product_id from {{ ref('products') }})
), expected_transactions as (
  select transaction_id from {{ source('silver','transactions') }}
  where transaction_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 120 day
    and transaction_date < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
), transaction_gap as (
  (select transaction_id from {{ ref('transactions') }} except all select * from expected_transactions)
  union all
  (select * from expected_transactions except all select transaction_id from {{ ref('transactions') }})
)
select 'customers' as relation_name, count(*) as failures from customer_gap having count(*)>0
union all select 'products', count(*) from product_gap having count(*)>0
union all select 'transactions', count(*) from transaction_gap having count(*)>0
union all
select 'temporal_quality_reason', count(*)
from {{ ref('transactions') }} t join {{ source('silver','products') }} p using(product_id)
join {{ source('silver','customers') }} c on t.customer_id=c.customer_id
where t.temporal_quality_reason is distinct from {{ temporal_quality_reason('t', 'p', 'c') }}
having count(*)>0
