-- Which service categories consume the largest modeled shipping budget?
SELECT Service_Type,COUNT(*) AS shipments,ROUND(SUM(Shipping_Cost_PHP),2) AS total_cost_php,
 ROUND(AVG(Shipping_Cost_PHP),2) AS avg_cost_php
FROM shipments GROUP BY Service_Type ORDER BY total_cost_php DESC;

-- Does modeled cost rise with straight-line distance bands?
SELECT CASE WHEN Distance_KM<50 THEN '<50 km' WHEN Distance_KM<200 THEN '50-199 km'
 WHEN Distance_KM<500 THEN '200-499 km' ELSE '500+ km' END AS geodesic_band,
 COUNT(*) AS shipments,ROUND(AVG(Shipping_Cost_PHP),2) AS avg_cost_php,
 ROUND(AVG(Package_Weight_KG),2) AS avg_weight_kg
FROM shipments GROUP BY geodesic_band ORDER BY avg_cost_php;

-- Which hub-to-destination region pairs have the highest average shipping cost?
SELECT h.Hub_Name,s.Destination_Region,COUNT(*) AS shipments,
 ROUND(AVG(s.Shipping_Cost_PHP),2) AS avg_cost_php
FROM shipments s JOIN hubs h ON s.Origin_Hub_ID=h.Hub_ID
GROUP BY h.Hub_ID,s.Destination_Region HAVING shipments>=25 ORDER BY avg_cost_php DESC LIMIT 15;
