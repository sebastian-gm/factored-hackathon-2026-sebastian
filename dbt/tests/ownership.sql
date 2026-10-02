select count(*) as failures from {{ ref('transaction_facts') }} t
left join {{ source('silver','products') }} p on t.product_id=p.product_id
where p.product_id is null or t.customer_id<>p.customer_id
having count(*)>0
