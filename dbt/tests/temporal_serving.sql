-- Serving facts only: historical transaction_facts/matcher_ledger retain warnings.
select 'customers' as relation_name, count(*) as failures
from {{ ref('customers') }} g join {{ source('silver','customers') }} c using(customer_id)
where not ({{ trusted_customer('c') }}) having count(*)>0
union all
select 'products', count(*)
from {{ ref('products') }} g join {{ source('silver','products') }} p using(product_id)
join {{ source('silver','customers') }} c on p.customer_id=c.customer_id
where not ({{ trusted_customer('c') }} and {{ trusted_product('p') }}) having count(*)>0
union all
select 'transactions', count(*)
from {{ ref('transactions') }} t join {{ source('silver','products') }} p using(product_id)
join {{ source('silver','customers') }} c on t.customer_id=c.customer_id
where not ({{ trusted_customer('c') }} and {{ trusted_product('p') }} and {{ trusted_transaction('t', 'p') }})
having count(*)>0
