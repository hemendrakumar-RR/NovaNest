# NovaNest Power BI — MySQL Data Source & Enterprise Refresh Configuration Guide

---

## 1. Overview & Architecture

This runbook documents the configuration, security boundaries, and scheduled refresh architecture for connecting **NovaNest Power BI** (`powerbi/NovaNest.pbix`) directly to the canonical **MySQL 8.0** relational database (`novanest_db`).

```
+--------------------+        +-----------------------------+        +--------------------------+
|  MySQL 8.0 Engine  |  --->  |  Power Query M Data Engine  |  --->  |  Power BI Tabular Model  |
|   (novanest_db)    |        | (Direct Query / Import ETL) |        |    (Star Schema VertiPaq)|
+--------------------+        +-----------------------------+        +--------------------------+
          ^                                                                        |
          |                                                                        v
+--------------------+                                               +--------------------------+
| On-Premises Data   | <---------------- Scheduled Refresh Clock --- | Power BI Service Cloud   |
| Gateway (Personal  |                                               |  (Standard Workspace)    |
| / Enterprise Mode) |                                               +--------------------------+
+--------------------+
```

---

## 2. Canonical Source Mapping & `orders` vs `orders_table` Resolution

### Historical Discrepancy
- In the MySQL storage engine, the physical base table is named `orders_table`.
- In CSV extracts, analytical models, and Power BI dashboards, the business entity is named `orders`.

### Certified Architectural Resolution
A permanent SQL view `orders` was provisioned in `novanest_db` with SQL SECURITY DEFINER:
```sql
CREATE VIEW `orders` AS 
SELECT 
    `order_id`,
    `customer_id`,
    `restaurant_id`,
    `item_id`,
    `rider_id`,
    `order_datetime`,
    `quantity`,
    `order_amount`,
    `discount_amount`,
    `delivery_fee`,
    `final_amount`,
    `order_status`
FROM `orders_table`;
```

In Power Query, all fact references query `orders` directly:
```powerquery
let
    Source = MySQL.Database("db:3306", "novanest_db", [ReturnSingleDatabase=true]),
    orders_View = Source{[Schema="novanest_db", Item="orders"]}[Data]
in
    orders_View
```
This guarantees identical column structures, row counts (49,971), and field names across MySQL, FastAPI, React, Streamlit, and Power BI.

---

## 3. Power Query M Data Ingestion Scripts

### 3.1 Primary MySQL Ingestion Pattern (Parameterized)
To avoid hardcoding credentials in PBIX files, connections utilize Power Query Parameters (`ServerName`, `DatabaseName`):

```powerquery
// 1. Parameter: ServerName
"localhost:3306" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

// 2. Parameter: DatabaseName
"novanest_db" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]

// 3. Fact_Orders Query
let
    Source = MySQL.Database(ServerName, DatabaseName, [ReturnSingleDatabase=true]),
    novanest_orders = Source{[Schema=DatabaseName, Item="orders"]}[Data],
    #"Changed Types" = Table.TransformColumnTypes(novanest_orders,{
        {"order_id", type text},
        {"customer_id", type text},
        {"restaurant_id", type text},
        {"item_id", type text},
        {"rider_id", type text},
        {"order_datetime", type datetime},
        {"quantity", Int64.Type},
        {"order_amount", Currency.Type},
        {"discount_amount", Currency.Type},
        {"delivery_fee", Currency.Type},
        {"final_amount", Currency.Type},
        {"order_status", type text}
    })
in
    #"Changed Types"
```

### 3.2 Offline CSV Fallback Pattern
For development environments where MySQL is unreachable on the host network:
```powerquery
let
    Source = Csv.Document(File.Contents("c:\Users\madha\OneDrive\Documents\NovaNest-main\datasets\cleaned\orders.csv"), [Delimiter=",", Columns=12, Encoding=65001, QuoteStyle=QuoteStyle.None]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Type" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"order_id", type text}, {"customer_id", type text}, {"restaurant_id", type text},
        {"item_id", type text}, {"rider_id", type text}, {"order_datetime", type datetime},
        {"quantity", Int64.Type}, {"order_amount", Currency.Type}, {"discount_amount", Currency.Type},
        {"delivery_fee", Currency.Type}, {"final_amount", Currency.Type}, {"order_status", type text}
    })
in
    #"Changed Type"
```

---

## 4. On-Premises Data Gateway Configuration

To enable automated scheduled refresh in the Power BI Service:

1. **Install Gateway**: Download and install the *Microsoft On-Premises Data Gateway (Standard Mode)* on the Windows host machine hosting MySQL or Docker.
2. **Cluster Registration**:
   - Gateway Cluster Name: `NovaNest-Analytics-Gateway`
   - Recovery Key: Stored in enterprise password manager.
3. **Data Source Configuration in Power BI Service**:
   - Connection Type: `MySQL`
   - Server: `127.0.0.1:3306` (or `db:3306` inside Docker bridge network)
   - Database: `novanest_db`
   - Authentication Method: `Database`
   - Username: `novanest_app`
   - Password: `[CONFIGURED_IN_SECRETS_VAULT]`
   - Privacy Level: `Organizational`
4. **Scheduled Refresh Plan**:
   - Frequency: Daily at `04:00 AM IST` and `04:00 PM IST`.
   - Send refresh failure notifications to: `operations-telemetry@novanest.internal`.

---

## 5. Data Freshness & Telemetry Badges

To provide executive users with complete transparency regarding data recency:

1. **DAX Freshness Measure**:
```dax
[Data Last Refreshed] = 
"Data Refreshed: " & FORMAT(NOW(), "yyyy-mm-dd hh:mm") & " IST | Engine: MySQL 8.0.46"
```
2. **Visual Implementation**:
   - Displayed as a glassmorphic subtle subtitle card in the top-right header of Page 1 (Executive Command Dashboard) and Page 2 (Financial Intelligence).
3. **Refresh Failure Handling**:
   - In the event of a gateway or network timeout (>120s), Power BI automatically alerts administrators and maintains the last successfully cached VertiPaq tabular snapshot.
   - Zero visual disruption or data loss for reporting consumers.
