{% macro temporal_quality_reason(t, p, c) -%}
-- One primary reason in contract order; no serving row is removed by a flag.
case
  when {{ t }}.transaction_date::date < {{ p }}.opening_date
    or {{ t }}.process_date < {{ p }}.opening_date then 'before_product_open'
  when {{ t }}.transaction_date >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
    then 'after_bank_clock'
  when {{ p }}.last_updated >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
    then 'product_updated_after_clock'
  when {{ c }}.last_updated >= cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
    then 'customer_updated_after_clock'
  else null::varchar
end
{%- endmacro %}
