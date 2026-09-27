select * from {{ source('silver','analysis_aggregates') }}
