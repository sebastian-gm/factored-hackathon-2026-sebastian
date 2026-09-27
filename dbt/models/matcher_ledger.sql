select t.*,
case when t.currency='USD' then t.amount else t.amount*f.exchange_rate end::DOUBLE as amount_usd_recomputed,
case when t.currency='USD' then t.process_date else f.date end::DATE as fx_date,
coalesce(t.currency<>'USD' and f.date<t.process_date,false)::BOOLEAN as fx_nearest_prior,
(t.transaction_country<>t.customer_country)::BOOLEAN as foreign_transaction
from {{ ref('transaction_facts') }} t
asof left join (select * from {{ ref('fx_rates') }} where target_currency='USD') f
on t.currency=f.source_currency and t.process_date>=f.date
