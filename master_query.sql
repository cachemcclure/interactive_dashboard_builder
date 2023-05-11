select fs2.order_number
    , trunc(fs2.created_at) as created_at
    , pp.title as product_title
    , pp.vendor as brand
    , pp.partner_id as partner 
    , pp.product_category
    , pp.product_type
    , pp.product_subtype
    , fs2.customer_id
    , fs2.tax
    , fs2.revenue
    , fs2.total_discount
    , fs2.quantity
    , sd.shipping_method as order_type
    , sd2.storefront_name
    , fs2.order_status
    , dg2.state_province_abbreviation as province
from reporting.fact_sales fs2 
inner join reporting.product pp on fs2.product_id = pp.product_id 
left join reporting.dim_geography_active dg on dg.geo_key = fs2.bill_geo_key 
left join reporting.dim_geography_active dg2 on dg2.geo_key = fs2.ship_geo_key 
left join reporting.shipping_definitions sd on sd.id = fs2.shipping_definition_id 
left join reporting.storefront_details sd2 on 'mb-'||sd2.id = fs2.storefront_id
;