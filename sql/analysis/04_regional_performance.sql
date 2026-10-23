-- Which destination regions have the highest burden of failed or late deliveries?
SELECT Destination_Region,COUNT(*) AS shipments,
 SUM(CASE WHEN Delivery_Status='Failed' THEN 1 ELSE 0 END) AS failed,
 SUM(CASE WHEN Delivery_Status='Delivered' AND Actual_Delivery_Date>Expected_Delivery_Date THEN 1 ELSE 0 END) AS late,
 ROUND(AVG(CASE WHEN Delivery_Status='Delivered' THEN JULIANDAY(Actual_Delivery_Date)-JULIANDAY(Dispatch_Date) END),2) AS avg_delivery_days,
 ROUND(AVG(Shipping_Cost_PHP),2) AS mean_shipping_php
FROM shipments GROUP BY Destination_Region ORDER BY shipments DESC;

-- Which city centers receive the highest shipment volume?
SELECT Destination_Province,Destination_City,COUNT(*) AS shipment_count
FROM shipments GROUP BY Destination_Province,Destination_City ORDER BY shipment_count DESC LIMIT 15;
