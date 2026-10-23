-- What percentage of delivered parcels met the promised calendar-day deadline?
SELECT Service_Type, COUNT(*) AS delivered,
 SUM(CASE WHEN Actual_Delivery_Date<=Expected_Delivery_Date THEN 1 ELSE 0 END) AS on_time,
 SUM(CASE WHEN Actual_Delivery_Date>Expected_Delivery_Date THEN 1 ELSE 0 END) AS late,
 ROUND(100.0*SUM(CASE WHEN Actual_Delivery_Date<=Expected_Delivery_Date THEN 1 ELSE 0 END)/COUNT(*),2) AS sla_pct,
 ROUND(AVG(CASE WHEN Actual_Delivery_Date>Expected_Delivery_Date THEN JULIANDAY(Actual_Delivery_Date)-JULIANDAY(Expected_Delivery_Date) END),2) AS mean_days_late
FROM shipments WHERE Delivery_Status='Delivered' GROUP BY Service_Type ORDER BY sla_pct;

-- Which region/service pairs require investigation?
SELECT Destination_Region, Service_Type, COUNT(*) AS delivered,
 SUM(CASE WHEN Actual_Delivery_Date>Expected_Delivery_Date THEN 1 ELSE 0 END) AS breaches
FROM shipments WHERE Delivery_Status='Delivered'
GROUP BY Destination_Region,Service_Type HAVING delivered>=50 ORDER BY breaches DESC;
