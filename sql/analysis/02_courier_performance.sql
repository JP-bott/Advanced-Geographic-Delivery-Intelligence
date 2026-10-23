-- Who delivers most reliably, after excluding couriers with fewer than 75 delivered parcels?
SELECT c.Courier_ID,c.Courier_Name,c.Assigned_Region,c.Vehicle_Type,
 COUNT(*) AS assigned,
 SUM(CASE WHEN s.Delivery_Status='Delivered' THEN 1 ELSE 0 END) AS delivered,
 ROUND(100.0*SUM(CASE WHEN s.Delivery_Status='Delivered' THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN s.Delivery_Status IN ('Delivered','Failed','Returned') THEN 1 ELSE 0 END),0),2) AS success_pct,
 ROUND(100.0*SUM(CASE WHEN s.Delivery_Status='Delivered' AND s.Actual_Delivery_Date<=s.Expected_Delivery_Date THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN s.Delivery_Status='Delivered' THEN 1 ELSE 0 END),0),2) AS on_time_pct,
 ROUND(AVG(CASE WHEN s.Delivery_Status='Delivered' THEN JULIANDAY(s.Actual_Delivery_Date)-JULIANDAY(s.Dispatch_Date) END),2) AS mean_delivery_days
FROM shipments s JOIN couriers c ON c.Courier_ID=s.Courier_ID
GROUP BY c.Courier_ID HAVING delivered>=75 ORDER BY on_time_pct DESC,delivered DESC;
