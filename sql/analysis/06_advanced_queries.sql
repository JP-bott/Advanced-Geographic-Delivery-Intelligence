-- CTE and LAG: month-over-month shipment growth by region.
WITH monthly AS (
 SELECT Destination_Region AS region,STRFTIME('%Y-%m',Shipment_Date) AS month,COUNT(*) AS n
 FROM shipments GROUP BY region,month
), changes AS (
 SELECT region,month,n,LAG(n) OVER(PARTITION BY region ORDER BY month) AS previous
 FROM monthly
)
SELECT region,month,n,previous,ROUND(100.0*(n-previous)/NULLIF(previous,0),1) AS mom_pct
FROM changes ORDER BY region,month;

-- ROW_NUMBER and RANK: busiest and most expensive hub-to-region corridors.
WITH corridors AS (
 SELECT h.Region AS origin,s.Destination_Region AS destination,COUNT(*) AS volume,
 ROUND(AVG(s.Shipping_Cost_PHP),2) AS cost
 FROM shipments s JOIN hubs h ON s.Origin_Hub_ID=h.Hub_ID
 GROUP BY h.Region,s.Destination_Region
)
SELECT origin,destination,volume,cost,
 ROW_NUMBER() OVER(PARTITION BY origin ORDER BY volume DESC,destination) AS by_volume,
 RANK() OVER(ORDER BY cost DESC) AS cost_rank
FROM corridors ORDER BY origin,by_volume;

-- Conditional aggregation and JOIN: courier outcomes by vehicle.
SELECT c.Vehicle_Type,COUNT(*) AS assigned,
 SUM(CASE WHEN s.Delivery_Status='Delivered' THEN 1 ELSE 0 END) AS delivered,
 SUM(CASE WHEN s.Delivery_Status='Failed' THEN 1 ELSE 0 END) AS failed,
 SUM(CASE WHEN s.Delivery_Status='Returned' THEN 1 ELSE 0 END) AS returned
FROM shipments s JOIN couriers c ON s.Courier_ID=c.Courier_ID
GROUP BY c.Vehicle_Type ORDER BY assigned DESC;
