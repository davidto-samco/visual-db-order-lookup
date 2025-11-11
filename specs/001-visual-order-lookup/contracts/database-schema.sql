-- =====================================================
-- VISUAL DATABASE SCHEMA DOCUMENTATION
-- =====================================================
--
-- Purpose: Document the existing Visual SQL Server database schema
--          for read-only access by the Order Lookup application
--
-- Database: SAMCO
-- Server: 10.10.10.142:1433
--
-- IMPORTANT: This application does NOT modify the database schema.
--            All queries are read-only (SELECT only).
--
-- Last Updated: 2025-11-04
-- =====================================================

-- =====================================================
-- TABLE: CUSTOMER_ORDER
-- =====================================================
-- Stores customer order header information
--
-- Primary Key: ID
-- Referenced by: CUST_ORDER_LINE (CUST_ORDER_ID)
-- =====================================================

-- Note: Exact schema inferred from context files.
-- Actual schema should be verified against Visual database.

CREATE TABLE CUSTOMER_ORDER (
    -- Primary identification
    ID VARCHAR(15) NOT NULL PRIMARY KEY,  -- Order/Job number (e.g., "4049")

    -- Order dates
    ORDER_DATE DATETIME NOT NULL,         -- Date order was placed
    PROMISE_DATE DATETIME NULL,           -- Promised delivery date
    DESIRED_SHIP_DATE DATETIME NULL,      -- Customer requested ship date
    LAST_SHIPPED_DATE DATETIME NULL,      -- Date last shipment occurred

    -- Customer references
    CUSTOMER_ID VARCHAR(15) NOT NULL,     -- Foreign key to CUSTOMER.ID
    CUSTOMER_PO_REF VARCHAR(50) NULL,     -- Customer's PO reference number

    -- Contact information
    CONTACT_FIRST_NAME VARCHAR(50) NULL,  -- Contact person first name
    CONTACT_LAST_NAME VARCHAR(50) NULL,   -- Contact person last name
    CONTACT_PHONE VARCHAR(20) NULL,       -- Contact phone number
    CONTACT_FAX VARCHAR(20) NULL,         -- Contact fax number
    CONTACT_EMAIL VARCHAR(100) NULL,      -- Contact email address
    CONTACT_MOBILE VARCHAR(20) NULL,      -- Contact mobile number

    -- Financial information
    TOTAL_AMT_ORDERED DECIMAL(18,2) NOT NULL DEFAULT 0.00,  -- Total order amount
    TOTAL_AMT_SHIPPED DECIMAL(18,2) NULL DEFAULT 0.00,      -- Total shipped amount
    CURRENCY_ID VARCHAR(3) NOT NULL DEFAULT 'USD',          -- Currency code

    -- Payment terms
    TERMS_NET_TYPE VARCHAR(20) NULL,      -- Net payment type
    TERMS_NET_DAYS INT NULL,              -- Net payment days
    TERMS_DISC_PERCENT DECIMAL(5,2) NULL, -- Discount percentage
    TERMS_DESCRIPTION VARCHAR(200) NULL,  -- Payment terms description

    -- Shipping information
    SHIP_VIA VARCHAR(50) NULL,            -- Shipping method
    FREE_ON_BOARD VARCHAR(50) NULL,       -- FOB point
    FREIGHT_TERMS VARCHAR(50) NULL,       -- Freight terms

    -- Order status and tracking
    STATUS VARCHAR(20) NULL,              -- Order status
    REVISION_ID VARCHAR(10) NULL,         -- Revision number
    SALESREP_ID VARCHAR(15) NULL,         -- Sales representative
    SALES_TAX_GROUP_ID VARCHAR(15) NULL,  -- Sales tax group

    -- Indexes for performance
    CONSTRAINT FK_CUSTOMER_ORDER_CUSTOMER FOREIGN KEY (CUSTOMER_ID)
        REFERENCES CUSTOMER(ID)
);

-- Performance indexes
CREATE INDEX IX_CUSTOMER_ORDER_ORDER_DATE ON CUSTOMER_ORDER(ORDER_DATE DESC);
CREATE INDEX IX_CUSTOMER_ORDER_CUSTOMER_ID ON CUSTOMER_ORDER(CUSTOMER_ID);
CREATE INDEX IX_CUSTOMER_ORDER_STATUS ON CUSTOMER_ORDER(STATUS);


-- =====================================================
-- TABLE: CUSTOMER
-- =====================================================
-- Stores customer information including addresses
--
-- Primary Key: ID
-- Referenced by: CUSTOMER_ORDER (CUSTOMER_ID)
-- =====================================================

CREATE TABLE CUSTOMER (
    -- Primary identification
    ID VARCHAR(15) NOT NULL PRIMARY KEY,  -- Customer identifier
    NAME VARCHAR(100) NOT NULL,           -- Customer company name

    -- Primary/Ship-To address
    ADDR_1 VARCHAR(100) NULL,             -- Address line 1
    ADDR_2 VARCHAR(100) NULL,             -- Address line 2
    CITY VARCHAR(50) NULL,                -- City
    STATE VARCHAR(20) NULL,               -- State/Province
    ZIPCODE VARCHAR(20) NULL,             -- Postal code
    COUNTRY VARCHAR(50) NULL,             -- Country

    -- Bill-To address
    BILL_TO_NAME VARCHAR(100) NULL,       -- Billing name
    BILL_TO_ADDR_1 VARCHAR(100) NULL,     -- Billing address line 1
    BILL_TO_ADDR_2 VARCHAR(100) NULL,     -- Billing address line 2
    BILL_TO_ADDR_3 VARCHAR(100) NULL,     -- Billing address line 3
    BILL_TO_CITY VARCHAR(50) NULL,        -- Billing city
    BILL_TO_STATE VARCHAR(20) NULL,       -- Billing state
    BILL_TO_ZIPCODE VARCHAR(20) NULL,     -- Billing postal code
    BILL_TO_COUNTRY VARCHAR(50) NULL,     -- Billing country

    -- Additional customer information (not used in current app)
    PHONE VARCHAR(20) NULL,               -- Primary phone
    FAX VARCHAR(20) NULL,                 -- Fax number
    EMAIL VARCHAR(100) NULL,              -- Email address

    -- Customer status
    ACTIVE BIT DEFAULT 1,                 -- Active status

    -- Performance indexes
    -- None needed for current use case (lookups by ID only)
);

-- Index for customer name search (case-insensitive partial match)
CREATE INDEX IX_CUSTOMER_NAME ON CUSTOMER(NAME);


-- =====================================================
-- TABLE: CUST_ORDER_LINE
-- =====================================================
-- Stores individual line items within customer orders
--
-- Primary Key: (CUST_ORDER_ID, LINE_NO)
-- Referenced by: None
-- =====================================================

CREATE TABLE CUST_ORDER_LINE (
    -- Composite primary key
    CUST_ORDER_ID VARCHAR(15) NOT NULL,   -- Foreign key to CUSTOMER_ORDER.ID
    LINE_NO INT NOT NULL,                 -- Line item number (sequence)

    -- Part information
    PART_ID VARCHAR(50) NULL,             -- Part identifier
    CUSTOMER_PART_ID VARCHAR(50) NULL,    -- Customer's part number

    -- Quantity and pricing
    ORDER_QTY DECIMAL(18,4) NOT NULL DEFAULT 0.0000,  -- Ordered quantity
    UNIT_PRICE DECIMAL(18,2) NOT NULL DEFAULT 0.00,   -- Price per unit
    TOTAL_AMT_ORDERED DECIMAL(18,2) NOT NULL DEFAULT 0.00,  -- Line total

    -- Description and reference
    MISC_REFERENCE VARCHAR(500) NULL,     -- Line item description

    -- Line-specific dates
    PROMISE_DATE DATETIME NULL,           -- Line-specific promise date

    -- Line status
    LINE_STATUS VARCHAR(20) NULL,         -- Status of this line item

    -- Unit of measure
    SELLING_UM VARCHAR(10) NULL,          -- Selling unit of measure

    -- Primary key constraint
    CONSTRAINT PK_CUST_ORDER_LINE PRIMARY KEY (CUST_ORDER_ID, LINE_NO),

    -- Foreign key constraint
    CONSTRAINT FK_CUST_ORDER_LINE_ORDER FOREIGN KEY (CUST_ORDER_ID)
        REFERENCES CUSTOMER_ORDER(ID)
);

-- Performance index for retrieving all lines for an order
CREATE INDEX IX_CUST_ORDER_LINE_ORDER_ID ON CUST_ORDER_LINE(CUST_ORDER_ID, LINE_NO);


-- =====================================================
-- QUERY CONTRACTS
-- =====================================================
-- These queries define the "API" for the application.
-- All application database access goes through these queries.
-- =====================================================

-- -----------------------------------------------------
-- QUERY: Get Recent Orders (Default List - FR-001)
-- -----------------------------------------------------
-- Purpose: Load 100 most recent orders for initial display
-- Parameters: @Limit (default 100)
-- Returns: OrderSummary DTOs
-- Performance: <5 seconds (indexed on ORDER_DATE DESC)

-- Example Query:
SELECT TOP (@Limit)
    co.ID AS job_number,
    c.NAME AS customer_name,
    co.ORDER_DATE AS order_date,
    co.TOTAL_AMT_ORDERED AS total_amount
FROM CUSTOMER_ORDER co WITH (NOLOCK)
INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
ORDER BY co.ORDER_DATE DESC;

-- Example: @Limit = 100


-- -----------------------------------------------------
-- QUERY: Filter Orders by Date Range (FR-010, FR-011)
-- -----------------------------------------------------
-- Purpose: Filter orders by start date, end date, or both
-- Parameters: @StartDate (nullable), @EndDate (nullable)
-- Returns: OrderSummary DTOs (max 1000 - FR-013)
-- Performance: <10 seconds (indexed on ORDER_DATE)

-- Example Query:
SELECT TOP (1000)
    co.ID AS job_number,
    c.NAME AS customer_name,
    co.ORDER_DATE AS order_date,
    co.TOTAL_AMT_ORDERED AS total_amount
FROM CUSTOMER_ORDER co WITH (NOLOCK)
INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE
    (@StartDate IS NULL OR co.ORDER_DATE >= @StartDate)
    AND (@EndDate IS NULL OR co.ORDER_DATE <= @EndDate)
ORDER BY co.ORDER_DATE DESC;

-- Example: @StartDate = '2000-01-01', @EndDate = '2000-12-31'


-- -----------------------------------------------------
-- QUERY: Search by Job Number (FR-015)
-- -----------------------------------------------------
-- Purpose: Find specific order by exact job number match
-- Parameters: @JobNumber (required)
-- Returns: Single OrderHeader DTO with Customer and LineItems
-- Performance: <5 seconds (indexed on PRIMARY KEY)

-- Example Query (Step 1: Get Order Header and Customer):
SELECT
    co.ID AS order_id,
    co.ORDER_DATE AS order_date,
    co.CUSTOMER_PO_REF AS customer_po_ref,
    co.CONTACT_FIRST_NAME AS contact_first_name,
    co.CONTACT_LAST_NAME AS contact_last_name,
    co.CONTACT_PHONE AS contact_phone,
    co.CONTACT_FAX AS contact_fax,
    co.PROMISE_DATE AS promise_date,
    co.TOTAL_AMT_ORDERED AS total_amount,
    co.CURRENCY_ID AS currency_id,
    co.TERMS_DESCRIPTION AS terms_description,

    -- Customer fields
    c.ID AS customer_id,
    c.NAME AS customer_name,
    c.ADDR_1 AS address_1,
    c.ADDR_2 AS address_2,
    c.CITY AS city,
    c.STATE AS state,
    c.ZIPCODE AS zip_code,
    c.COUNTRY AS country,
    c.BILL_TO_NAME AS bill_to_name,
    c.BILL_TO_ADDR_1 AS bill_to_address_1,
    c.BILL_TO_ADDR_2 AS bill_to_address_2,
    c.BILL_TO_ADDR_3 AS bill_to_address_3,
    c.BILL_TO_CITY AS bill_to_city,
    c.BILL_TO_STATE AS bill_to_state,
    c.BILL_TO_ZIPCODE AS bill_to_zip_code,
    c.BILL_TO_COUNTRY AS bill_to_country

FROM CUSTOMER_ORDER co WITH (NOLOCK)
INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE co.ID = @JobNumber;

-- Example Query (Step 2: Get Line Items):
SELECT
    LINE_NO AS line_number,
    CUST_ORDER_ID AS order_id,
    PART_ID AS part_id,
    ORDER_QTY AS quantity,
    UNIT_PRICE AS unit_price,
    TOTAL_AMT_ORDERED AS line_total,
    MISC_REFERENCE AS description,
    PROMISE_DATE AS promise_date
FROM CUST_ORDER_LINE WITH (NOLOCK)
WHERE CUST_ORDER_ID = @JobNumber
ORDER BY LINE_NO;

-- Example: @JobNumber = '4049'


-- -----------------------------------------------------
-- QUERY: Search by Customer Name (FR-016)
-- -----------------------------------------------------
-- Purpose: Find orders by partial, case-insensitive customer name
-- Parameters: @CustomerName (required, partial match)
-- Returns: OrderSummary DTOs (max 100 results)
-- Performance: <10 seconds (indexed on CUSTOMER.NAME)

-- Example Query:
SELECT TOP (100)
    co.ID AS job_number,
    c.NAME AS customer_name,
    co.ORDER_DATE AS order_date,
    co.TOTAL_AMT_ORDERED AS total_amount
FROM CUSTOMER_ORDER co WITH (NOLOCK)
INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE c.NAME LIKE '%' + @CustomerName + '%'
ORDER BY co.ORDER_DATE DESC;

-- Example: @CustomerName = 'TRANE'
-- Matches: "THE TRANE COMPANY", "TRANE RESIDENTIAL", etc.


-- -----------------------------------------------------
-- QUERY: Get Order Details (FR-021)
-- -----------------------------------------------------
-- Purpose: Load complete order details for acknowledgement display
-- Parameters: @OrderId (required)
-- Returns: OrderHeader DTO with Customer and LineItems
-- Performance: <5 seconds
-- Note: Same as "Search by Job Number" above


-- =====================================================
-- DATA VALIDATION NOTES
-- =====================================================

-- Missing/NULL Data Handling (FR-024):
-- - All nullable fields should be handled in Python with COALESCE or "N/A"
-- - Application displays "N/A" for NULL values in UI
-- - Example: COALESCE(CONTACT_PHONE, 'N/A') AS contact_phone

-- Date Format (FR-026):
-- - All dates stored as DATETIME in database
-- - Application formats as MM/DD/YYYY for display
-- - Python: order_date.strftime("%m/%d/%Y")

-- Currency Format (FR-025):
-- - All amounts stored as DECIMAL(18,2)
-- - Application formats with $ symbol and thousand separators
-- - Python: f"${amount:,.2f}"

-- Parameterized Queries (Security - Constitution):
-- - ALL queries MUST use parameterized statements via pyodbc
-- - NEVER construct SQL with string concatenation
-- - Example: cursor.execute("SELECT * FROM CUSTOMER_ORDER WHERE ID = ?", (job_number,))


-- =====================================================
-- PERFORMANCE OPTIMIZATION NOTES
-- =====================================================

-- Query Timeout (Constitution):
-- - All queries have 30-second timeout
-- - pyodbc: cursor.execute(...); cursor.timeout = 30

-- WITH (NOLOCK) Hints:
-- - Read-only access allows NOLOCK for better performance
-- - Prevents read locks on Visual database
-- - Acceptable for historical data queries

-- TOP Clauses:
-- - All list queries use TOP to limit results
-- - Default: 100 (order list), Max: 1000 (date filter)
-- - Prevents excessive memory usage

-- Index Usage:
-- - ORDER_DATE DESC index for recent orders query
-- - CUSTOMER.NAME index for customer search
-- - Primary key indexes for exact lookups


-- =====================================================
-- TESTING QUERIES
-- =====================================================
-- Use these queries to verify database connectivity
-- and test data retrieval during development

-- Test 1: Check connection
SELECT 1 AS test;

-- Test 2: Count total orders
SELECT COUNT(*) AS total_orders FROM CUSTOMER_ORDER;

-- Test 3: Get earliest and latest order dates
SELECT
    MIN(ORDER_DATE) AS earliest_order,
    MAX(ORDER_DATE) AS latest_order
FROM CUSTOMER_ORDER;

-- Test 4: Verify order 4049 exists (from context)
SELECT
    co.ID,
    c.NAME,
    co.ORDER_DATE,
    co.TOTAL_AMT_ORDERED,
    COUNT(col.LINE_NO) AS line_count
FROM CUSTOMER_ORDER co
INNER JOIN CUSTOMER c ON co.CUSTOMER_ID = c.ID
LEFT JOIN CUST_ORDER_LINE col ON co.ID = col.CUST_ORDER_ID
WHERE co.ID = '4049'
GROUP BY co.ID, c.NAME, co.ORDER_DATE, co.TOTAL_AMT_ORDERED;

-- Expected result:
-- ID    NAME                  ORDER_DATE   TOTAL_AMT_ORDERED  line_count
-- 4049  THE TRANE COMPANY     2000-12-20   1751000.00         17


-- =====================================================
-- END OF SCHEMA DOCUMENTATION
-- =====================================================
