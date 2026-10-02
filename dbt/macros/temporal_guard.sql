{% macro trusted_customer(c) -%}
{{ c }}.last_updated < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
{%- endmacro %}

{% macro trusted_product(p) -%}
{{ p }}.last_updated < cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)
and {{ p }}.opening_date <= (
  cast('{{ env_var("BANK_CLOCK") }}' as timestamptz)-interval 6 hour-interval 1 microsecond
)::date
{%- endmacro %}

{% macro trusted_transaction(t, p) -%}
{{ t }}.customer_id={{ p }}.customer_id
and {{ t }}.transaction_date::date >= {{ p }}.opening_date
and {{ t }}.process_date >= {{ p }}.opening_date
and {{ t }}.process_date=({{ t }}.transaction_date-interval 6 hour)::date
{%- endmacro %}
