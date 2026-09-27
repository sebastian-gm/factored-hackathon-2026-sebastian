select count(*) as failures from information_schema.columns
where table_schema='gold' and column_name in ('affected_product_id','description','resolution','is_fraud')
having count(*)>0
