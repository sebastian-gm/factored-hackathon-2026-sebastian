select count(*) as failures from (
  select date,source_currency,target_currency from {{ ref('fx_rates') }}
  group by 1,2,3 having count(*)>1
) duplicates having count(*)>0
