PRAGMA foreign_keys=ON;
DROP TABLE IF EXISTS delivery_events;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS sla_rules;
DROP TABLE IF EXISTS couriers;
DROP TABLE IF EXISTS hubs;

CREATE TABLE hubs (
 Hub_ID TEXT PRIMARY KEY, Hub_Name TEXT NOT NULL, Region TEXT NOT NULL,
 Province TEXT NOT NULL, City TEXT NOT NULL, Latitude REAL NOT NULL CHECK (Latitude BETWEEN 4 AND 22),
 Longitude REAL NOT NULL CHECK (Longitude BETWEEN 116 AND 127), Hub_Type TEXT NOT NULL
);
CREATE TABLE couriers (
 Courier_ID TEXT PRIMARY KEY, Courier_Name TEXT NOT NULL, Courier_Type TEXT NOT NULL,
 Assigned_Region TEXT NOT NULL, Employment_Status TEXT NOT NULL,
 Vehicle_Type TEXT NOT NULL CHECK (Vehicle_Type IN ('Motorcycle','Van','Light Truck','Delivery Truck')),
 Start_Date TEXT NOT NULL
);
CREATE TABLE sla_rules (
 SLA_ID TEXT PRIMARY KEY, Service_Type TEXT NOT NULL CHECK(Service_Type IN ('Same Day','Express','Standard','Economy')),
 Origin_Region TEXT NOT NULL, Destination_Region TEXT NOT NULL, SLA_Days INTEGER NOT NULL CHECK(SLA_Days >= 0),
 UNIQUE (Service_Type, Origin_Region, Destination_Region)
);
CREATE TABLE shipments (
 Shipment_ID TEXT PRIMARY KEY, Order_ID TEXT NOT NULL UNIQUE, Customer_ID TEXT NOT NULL,
 Courier_ID TEXT NOT NULL REFERENCES couriers(Courier_ID),
 Origin_Hub_ID TEXT NOT NULL REFERENCES hubs(Hub_ID),
 Destination_Region TEXT NOT NULL, Destination_Province TEXT NOT NULL, Destination_City TEXT NOT NULL,
 Destination_Latitude REAL NOT NULL CHECK (Destination_Latitude BETWEEN 4 AND 22),
 Destination_Longitude REAL NOT NULL CHECK (Destination_Longitude BETWEEN 116 AND 127),
 Shipment_Date TEXT NOT NULL, Dispatch_Date TEXT NOT NULL, Expected_Delivery_Date TEXT NOT NULL,
 Actual_Delivery_Date TEXT,
 Delivery_Status TEXT NOT NULL CHECK (Delivery_Status IN ('Delivered','Failed','Returned','In Transit','Cancelled')),
 Delivery_Attempts INTEGER NOT NULL CHECK (Delivery_Attempts >= 0), Failure_Reason TEXT,
 Package_Weight_KG REAL NOT NULL CHECK(Package_Weight_KG > 0),
 Shipping_Cost_PHP REAL NOT NULL CHECK(Shipping_Cost_PHP >= 0),
 Delivery_Fee_PHP REAL NOT NULL CHECK(Delivery_Fee_PHP >= 0),
 Service_Type TEXT NOT NULL, Distance_KM REAL NOT NULL CHECK(Distance_KM >= 0),
 SLA_ID TEXT NOT NULL REFERENCES sla_rules(SLA_ID),
 CHECK(Shipment_Date <= Dispatch_Date),
 CHECK(Dispatch_Date <= Expected_Delivery_Date),
 CHECK(Actual_Delivery_Date IS NULL OR Actual_Delivery_Date >= Dispatch_Date),
 CHECK((Delivery_Status='Delivered' AND Actual_Delivery_Date IS NOT NULL) OR
       (Delivery_Status<>'Delivered' AND Actual_Delivery_Date IS NULL))
);
CREATE TABLE delivery_events (
 Event_ID TEXT PRIMARY KEY, Shipment_ID TEXT NOT NULL REFERENCES shipments(Shipment_ID),
 Event_DateTime TEXT NOT NULL, Event_Type TEXT NOT NULL,
 Hub_ID TEXT REFERENCES hubs(Hub_ID), Event_Description TEXT NOT NULL
);
