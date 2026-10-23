-- Business question: how many parcels were resolved, delivered or failed?
-- Success denominator = Delivered + Failed + Returned (excludes in transit/cancelled).
SELECT COUNT(*) AS all_shipments,
 SUM(CASE WHEN Delivery_Status='Delivered' THEN 1 ELSE 0 END) AS delivered,
 SUM(CASE WHEN Delivery_Status IN ('Delivered','Failed','Returned') THEN 1 ELSE 0 END) AS eligible_resolved,
 ROUND(100.0*SUM(CASE WHEN Delivery_Status='Delivered' THEN 1 ELSE 0 END)/NULLIF(SUM(CASE WHEN Delivery_Status IN ('Delivered','Failed','Returned') THEN 1 ELSE 0 END),0),2) AS success_pct,
 ROUND(AVG(CASE WHEN Delivery_Status='Delivered' THEN JULIANDAY(Actual_Delivery_Date)-JULIANDAY(Dispatch_Date) END),2) AS avg_delivery_days
FROM shipments;

-- How did shipment volume trend by month?
SELECT STRFTIME('%Y-%m',Shipment_Date) AS month, COUNT(*) AS shipments,
 SUM(CASE WHEN Delivery_Status='Delivered' THEN 1 ELSE 0 END) AS delivered
FROM shipments GROUP BY month ORDER BY month;
