# Feature Specification: Visual Database Order Lookup Application

**Feature Branch**: `001-visual-order-lookup`
**Created**: 2025-11-04
**Updated**: 2025-11-04
**Status**: Draft
**Input**: User description: "Building local application to replace deprecated Visual database software for order lookup"
**Update**: Added default order list display on startup and date range filtering capability

## Overview

The Spare Parts department needs a replacement application to access historical order data from the legacy Visual database. The current Visual software is deprecated and incompatible with the new version of the Visual database. Staff members (Pam, Cindy, Efron) use this system regularly to look up customer orders from 1985 onwards, helping customers identify parts, job numbers, and historical purchase information.

The application provides immediate access to recent orders upon startup and allows staff to filter by date ranges, search by job number or customer name, and view complete order acknowledgements with all historical details.

### Business Context

Customers frequently contact Spare Parts requesting information about machines purchased years or decades ago. They may not remember exact job numbers or part numbers, only knowing the customer name or approximate purchase date ("we bought it around 1995"). The Visual database contains critical historical data spanning 40+ years that is not available in the current AX/D365 system. By displaying recent orders immediately and providing date range filtering, the application helps staff quickly narrow down possibilities while talking to customers.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Recent Orders on Startup (Priority: P1)

As a Spare Parts representative, when I open the application, I want to immediately see a list of recent orders (most recent first) so I can quickly browse and identify orders without needing to search first. This helps me when customers call without specific information, or when I want to check what recent orders exist.

**Why this priority**: Many customer inquiries are about recent orders, and seeing the order list immediately saves time. Staff can browse the list while talking to customers who are describing their order by approximate date or customer name.

**Independent Test**: Can be fully tested by launching the application and verifying that a list of orders appears automatically, showing the 100 most recent orders with job number, customer name, order date, and total amount, sorted by date descending.

**Acceptance Scenarios**:

1. **Given** the application starts and connects to the database, **When** the main screen loads, **Then** the system displays a list of the 100 most recent orders sorted by order date (newest first), showing columns: job number, customer name, order date, and total amount
2. **Given** the order list is displayed, **When** I scroll through the list, **Then** I can see all 100 orders without performance degradation
3. **Given** the order list is displayed, **When** I click on any order in the list, **Then** the system displays the complete order acknowledgement for that order

---

### User Story 2 - Filter Orders by Date Range (Priority: P1)

As a Spare Parts representative, when a customer tells me they purchased a machine "around 1995" or "between 2000 and 2005", I need to filter the order list by date range to narrow down the possibilities and help identify their specific order.

**Why this priority**: Date ranges are one of the most common pieces of information customers provide when they don't remember job numbers. This is essential for narrowing down orders from customers with multiple purchases over the years.

**Independent Test**: Can be fully tested by setting a date range (e.g., "01/01/2000" to "12/31/2000") and verifying that only orders within that range appear in the list, including order 4049 dated "12/20/2000".

**Acceptance Scenarios**:

1. **Given** the order list is displayed, **When** I enter a start date "01/01/2000" and end date "12/31/2000" and click "Filter", **Then** the system displays only orders with order dates between those dates, maintaining the job number, customer name, order date, and total amount columns
2. **Given** I have filtered by date range, **When** I clear the date filters, **Then** the system returns to showing the default 100 most recent orders
3. **Given** I enter only a start date "01/01/1995" with no end date, **When** I click "Filter", **Then** the system displays all orders from January 1, 1995 to present
4. **Given** I enter only an end date "12/31/2000" with no start date, **When** I click "Filter", **Then** the system displays all orders from the earliest order in the database up to December 31, 2000

---

### User Story 3 - Find Order by Job Number (Priority: P1)

As a Spare Parts representative, I receive a customer inquiry with a specific job number (e.g., "8113"). I need to quickly retrieve the complete order information including all line items, subprojects, customer details, and pricing to help the customer identify the parts they need.

**Why this priority**: This is the most common lookup scenario. Customers with job numbers stamped on their machines need fast, reliable access to what was included in that specific order.

**Independent Test**: Can be fully tested by entering a known job number (e.g., "4049") and verifying that the complete order acknowledgement report displays with customer details, line items, and pricing within 10 seconds.

**Acceptance Scenarios**:

1. **Given** the application is connected to the Visual database on WLAN, **When** I enter job number "4049" and click search, **Then** the system displays the complete order acknowledgement showing customer "THE TRANE COMPANY", order date "12/20/2000", total amount "$1,751,000.00", and all 18 line items with their descriptions
2. **Given** I have searched for job number "8113", **When** the order details are displayed, **Then** I can see all subprojects (26, 41, etc.) with their descriptions and part listings
3. **Given** I search for a non-existent job number "9999999", **When** the search completes, **Then** the system displays a clear message "No order found for job number 9999999" with suggestions to try searching by customer name

---

### User Story 4 - Find Orders by Customer Name (Priority: P1)

As a Spare Parts representative, I receive a call from a customer who knows their company name (e.g., "Bailey" or "Arcadia") but doesn't have a job number. I need to search by customer name and see a list of all orders for that customer, so I can help them identify which specific job/machine they're asking about.

**Why this priority**: Customers often don't have job numbers readily available. This is essential for identifying the correct order when customers only know their company name or reference a project by location/year.

**Independent Test**: Can be fully tested by searching for "TRANE" and verifying that all orders for Trane appear in the results list, showing order numbers, dates, and total amounts. Clicking any result opens the full order acknowledgement.

**Acceptance Scenarios**:

1. **Given** the application is connected to the database, **When** I enter "TRANE" in the customer name search field, **Then** the system displays a list of all orders for customers containing "TRANE" including job numbers, order dates, and order amounts
2. **Given** search results display multiple orders for "Arcadia", **When** I select job number "7558" from the list, **Then** the system displays the complete order acknowledgement for that specific job
3. **Given** I search for customer name "XYZ Company", **When** no matching customers are found, **Then** the system displays "No customers found matching 'XYZ Company'" with a suggestion to check spelling or try partial name

---

### User Story 5 - Display Complete Order Acknowledgement Report (Priority: P1)

As a Spare Parts representative, once I've found the correct order, I need to view a formatted order acknowledgement that matches the Visual printout format, showing customer information, billing/shipping addresses, line items with quantities and prices, and project descriptions - so I can provide accurate information to the customer or print/save it for their records.

**Why this priority**: The order acknowledgement report is the primary deliverable. It must contain all necessary information in a familiar, readable format that staff are accustomed to.

**Independent Test**: Can be fully tested by retrieving order "4049" and verifying the displayed report matches the expected format with all sections: header with customer name, order date, contact info, bill-to and ship-to addresses, line items table with quantities/prices, and total amount.

**Acceptance Scenarios**:

1. **Given** I have retrieved order "4049", **When** the order acknowledgement displays, **Then** I see customer name "THE TRANE COMPANY", contact "BEN HUDGENS", phone "903-581-3038", order date "12/20/2000", payment terms "Due after receipt", bill-to address in El Paso TX, ship-to address in Tyler TX, and 17 line items with base/lot IDs and descriptions
2. **Given** the order acknowledgement is displayed, **When** I scroll to the line items section, **Then** each line shows quantity, base/lot ID (e.g., "4049/01"), description (e.g., "UNCOILER - 10,000 LB"), unit price, and line total, with a grand total at the bottom
3. **Given** an order has missing or null data fields (e.g., no sales rep, blank quote ID), **When** the acknowledgement displays, **Then** those fields show "N/A" instead of blank spaces or error messages

---

### User Story 6 - Handle Network Connection Issues (Priority: P2)

As a Spare Parts representative working on the WLAN network, I may experience intermittent connectivity. When the connection to the Visual database is lost or times out, I need clear error messages that tell me what's wrong and what to do, rather than seeing cryptic error codes or the application crashing.

**Why this priority**: WLAN reliability can vary, and connection issues are the most likely failure scenario. Clear error handling prevents user frustration and support calls.

**Independent Test**: Can be fully tested by disconnecting from WLAN, attempting a search, and verifying that a user-friendly error message appears (e.g., "Cannot connect to Visual database. Please check your network connection and try again.") without application crash.

**Acceptance Scenarios**:

1. **Given** the application starts but cannot connect to the Visual database, **When** the application loads, **Then** a clear message displays "Unable to connect to Visual database on [server name]. Check that you are connected to the WLAN network and try again."
2. **Given** I am searching for an order and the network connection drops mid-query, **When** the timeout occurs (after 30 seconds), **Then** the system displays "Search timed out. Please check your network connection and try again." and returns to the search screen
3. **Given** the database connection is lost, **When** I click a "Retry Connection" button, **Then** the system attempts to reconnect and shows either success or the same error message if still unable to connect

---

### User Story 7 - Print or Export Order Acknowledgement (Priority: P3)

As a Spare Parts representative, after finding an order, I may need to print the order acknowledgement or save it as a PDF to email to the customer for their records.

**Why this priority**: While viewing on screen is primary, occasionally customers request written documentation. This is nice-to-have but not critical for initial deployment.

**Independent Test**: Can be fully tested by retrieving any order, clicking "Print" or "Save as PDF", and verifying that the output matches the screen format with all details intact.

**Acceptance Scenarios**:

1. **Given** I have an order acknowledgement displayed, **When** I click the "Print" button, **Then** the system sends the formatted report to my default printer
2. **Given** I have an order acknowledgement displayed, **When** I click "Save as PDF", **Then** the system prompts me to choose a save location and creates a PDF file with the complete order details
3. **Given** the PDF is saved, **When** I open the PDF file, **Then** it matches the on-screen display with all customer info, line items, and formatting preserved

---

### Edge Cases

- What happens when the application starts and there are no orders in the database? System should display an empty list with message "No orders found in database."
- What happens when the default order list is loading and takes longer than expected? System should show a loading indicator with message "Loading recent orders..."
- What happens when a user enters an invalid date format in the date range filter (e.g., "abc" or "13/32/2000")? System should show validation error "Please enter a valid date in MM/DD/YYYY format."
- What happens when a user enters a start date that is after the end date? System should show validation error "Start date must be before end date."
- What happens when a date range filter returns zero orders? System should display "No orders found for the selected date range" with option to clear filters.
- What happens when a date range filter returns thousands of orders (e.g., all orders from 1985-2025)? System should limit display to first 1000 results with message "Showing first 1000 results. Narrow your date range for more specific results."
- What happens when a customer gives a slightly wrong job number (e.g., "7555" instead of "7558")? System should show "not found" with suggestion to try browsing the order list or search by customer name.
- What happens when searching for a very common customer name like "Smith" that returns hundreds of results? System should limit display to first 100 results with message "Showing first 100 results. Use date range filter to narrow results."
- What happens when an order has unusual characters in description fields or foreign address characters? System should display them correctly without encoding errors or crashes.
- What happens if a user starts a search, then starts another search before the first completes? System should cancel the first search and process only the most recent request.
- What happens when database contains orders with null/missing critical fields like customer name or order date? System should display "Unknown" or "N/A" rather than showing blank or throwing errors.
- What happens if two users search for the same order simultaneously? Each should see the correct results independently (read-only access prevents conflicts).
- What happens when the application is used on a slow network connection? Queries should still complete within the 15-second maximum, or timeout with clear message.

## Requirements *(mandatory)*

### Functional Requirements

#### Order List Display

- **FR-001**: System MUST display a list of the 100 most recent orders automatically on application startup, sorted by order date descending (newest first)
- **FR-002**: For each order in the list, system MUST display: job number, customer name, order date, and total amount
- **FR-003**: System MUST load and display the default order list within 10 seconds of application startup (database query execution only, not including initial connection establishment)
- **FR-004**: Users MUST be able to click on any order in the list to view the full order acknowledgement
- **FR-005**: System MUST show a loading indicator while the order list is being retrieved from the database

#### Date Range Filtering

- **FR-006**: System MUST provide date range filter controls with start date and end date input fields
- **FR-007**: System MUST accept dates in MM/DD/YYYY format for date range filters
- **FR-008**: System MUST validate that start date is before or equal to end date
- **FR-009**: System MUST display validation errors for invalid date formats or invalid date ranges
- **FR-010**: System MUST filter the order list to show only orders with order dates within the specified range (inclusive) when both dates are provided
- **FR-011**: System MUST support filtering with only start date (shows all orders from that date forward) or only end date (shows all orders up to that date)
- **FR-012**: System MUST provide a "Clear Filters" option to reset to the default 100 most recent orders
- **FR-013**: System MUST limit date range filter results to 1000 orders maximum, with a message if more results exist
- **FR-014**: System MUST complete date range filtering within 10 seconds

#### Search Capabilities

- **FR-015**: System MUST allow users to search for orders by exact job number (order ID)
- **FR-016**: System MUST allow users to search for orders by customer name using partial, case-insensitive matching
- **FR-017**: System MUST display search results within 10 seconds for job number searches (database query execution only)
- **FR-018**: System MUST display search results within 10 seconds for customer name searches (database query execution only)
- **FR-019**: System MUST show a list of matching orders when customer name search returns multiple results, displaying job number, customer name, order date, and total amount for each
- **FR-020**: Users MUST be able to select an order from the search results list to view the full order acknowledgement

#### Order Display Requirements

- **FR-021**: System MUST display a complete order acknowledgement report containing: customer name, order ID, order date, customer PO reference, contact name and phone, payment terms, bill-to address, ship-to address, and all order line items
- **FR-022**: For each order line item, system MUST display: quantity, base/lot ID, description, unit price, and line total
- **FR-023**: System MUST display the order total amount at the bottom of the line items
- **FR-024**: System MUST show "N/A" for any missing or null data fields rather than blank spaces or error text
- **FR-025**: System MUST format currency amounts with appropriate symbols (e.g., "$1,751,000.00")
- **FR-026**: System MUST format dates in readable format (e.g., "12/20/2000")

#### Database Connectivity Requirements

- **FR-027**: System MUST connect to the Visual database over WLAN using secure connection credentials
- **FR-028**: System MUST validate database connection on application startup
- **FR-029**: System MUST use read-only database access (no write operations permitted)
- **FR-030**: System MUST use parameterized queries to prevent SQL injection
- **FR-031**: System MUST timeout database queries after 30 seconds maximum
- **FR-032**: System MUST maintain a single database connection (no connection pooling)

#### Error Handling Requirements

- **FR-033**: System MUST display clear, user-friendly error messages for all failure scenarios
- **FR-034**: System MUST show "No order found" message when search returns zero results, with suggestion to try alternative search method
- **FR-035**: System MUST show "Unable to connect to database" message when connection fails, with instructions to check WLAN connection
- **FR-036**: System MUST show "Search timed out" message when query exceeds 30-second timeout, with option to retry
- **FR-037**: System MUST not display technical error details (stack traces, SQL errors) to end users
- **FR-038**: System MUST log errors to a local log file for troubleshooting by IT support

#### Configuration Requirements

- **FR-039**: System MUST load database connection settings from a configuration file or environment variables
- **FR-040**: System MUST NOT store database passwords in plain text
- **FR-041**: System MUST load the order acknowledgement report template from a configurable template file
- **FR-042**: Users with appropriate permissions MUST be able to modify the report template without changing application code

#### Performance Requirements

- **FR-043**: System MUST complete database connection within 10 seconds of application startup
- **FR-044**: System MUST complete date range filtering within 10 seconds (total operation time including query execution)
- **FR-045**: System MUST complete job number searches within 10 seconds (total operation time including network latency and query execution)
- **FR-046**: System MUST complete customer name searches within 10 seconds (total operation time including network latency and query execution)
- **FR-047**: System MUST render the order acknowledgement report within 1 second after data is retrieved
- **FR-048**: System MUST operate with less than 100MB of memory usage during normal operation

#### Print and Export Requirements

- **FR-049**: System MUST provide a "Print" button on the order acknowledgement view that sends the formatted report to the user's default printer
- **FR-050**: System MUST provide a "Save as PDF" button on the order acknowledgement view that prompts the user for a save location and creates a PDF file
- **FR-051**: System MUST preserve all order details (customer information, line items, formatting, Base/Lot IDs) when printing
- **FR-052**: System MUST preserve all order details (customer information, line items, formatting, Base/Lot IDs) when saving to PDF
- **FR-053**: System MUST ensure PDF output matches the on-screen display format

### Key Entities *(include if feature involves data)*

- **Order List**: A collection of order summary records displayed on the main screen, showing job number, customer name, order date, and total amount for each order. Can be the default 100 most recent orders, date-filtered orders, or search results.
- **Date Range Filter**: User-specified start and end dates used to filter the order list to show only orders within that date range. Either or both dates may be provided.
- **Customer Order**: Represents a complete sales order with header information including order ID (job number), customer ID, order date, customer PO reference, contact information, payment terms, ship via, freight terms, total amounts, status, currency, and revision information
- **Customer**: Represents a customer entity with customer ID, name, primary address (street, city, state, zip, country), bill-to address, and ship-to address
- **Order Line Item**: Represents individual line items within an order, including line number, part ID, customer part ID, order quantity, unit price, line total, description (misc reference), promise date, and line status
- **Base/Lot ID**: A formatted identifier combining order ID and lot number (e.g., "4049/00", "4049/01") that uniquely identifies components within a project. Retrieved by joining WORK_ORDER to INVENTORY_TRANS table, where INVENTORY_TRANS links WORKORDER_BASE_ID + WORKORDER_LOT_ID to CUST_ORDER_LINE_NO, providing the authoritative mapping between line items and lot numbers. The query filters by exact CUST_ORDER_ID match to exclude LOT_IDs from order revisions (e.g., order "4049 R3" would be excluded when retrieving order "4049"). When no mapping is available from INVENTORY_TRANS, the system uses a fallback format of {ORDER_ID}/{LINE_NO:02d}.
- **Report Template**: Configuration defining which database fields to extract and how to format the order acknowledgement display

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Application displays the default list of 100 recent orders within 15 seconds of startup (including 5s max connection + 10s max query execution)
- **SC-002**: Spare Parts staff can browse the order list and identify an order within 20 seconds of application startup
- **SC-003**: Staff can filter orders by date range and see filtered results within 15 seconds total
- **SC-004**: Spare Parts staff can retrieve order information by job number in under 15 seconds total (including max 5s overhead + 10s max query execution)
- **SC-005**: Spare Parts staff can search by customer name and find the correct order in under 30 seconds including reviewing results and selecting the right order
- **SC-006**: 100% of orders in the Visual database are retrievable and display correctly formatted order acknowledgements
- **SC-007**: System successfully handles network disconnections and timeouts with clear error messages, preventing application crashes
- **SC-008**: 95% of user searches return results on the first attempt without requiring troubleshooting or IT support
- **SC-009**: Zero database write operations occur during normal application usage (verified through audit logs)
- **SC-010**: Staff report satisfaction with the default order list view and date filtering features, noting improved efficiency compared to always requiring manual searches

## Assumptions *(mandatory)*

1. **Database Schema Stability**: The Visual database schema (CUSTOMER_ORDER, CUSTOMER, CUST_ORDER_LINE tables) will not change during development or deployment
2. **Network Infrastructure**: WLAN network infrastructure is stable and provides adequate bandwidth for database queries (assuming <1MB per query response)
3. **User Training**: Current staff (Pam, Cindy, Efron) are familiar with job numbers, customer names, and the legacy Visual interface, requiring minimal training on new application
4. **Read-Only Access**: Application only needs read-only database access - no requirement to modify historical orders
5. **Windows Environment**: Primary deployment target is Windows workstations used by Spare Parts staff
6. **Single User Sessions**: Only one user per workstation will use the application at a time (no concurrent user sessions on same machine)
7. **Database Availability**: Visual database server is accessible on WLAN during business hours (8am-5pm)
8. **Data Completeness**: Historical order data in Visual database is complete enough for customer inquiries (some null fields acceptable)
9. **No Real-Time Updates**: Order data is historical and static - no need for real-time synchronization or updates
10. **English Language Only**: All UI text and error messages will be in English (customer data may contain various languages)
11. **Recent Orders Preference**: Showing the 100 most recent orders by default is sufficient for most common use cases, as many customer inquiries are about recent orders or staff can use date filtering for older orders
12. **Date Format Standard**: MM/DD/YYYY date format is acceptable for the primary user base in North America

## Dependencies *(mandatory)*

1. **Visual Database Access**: Requires credentials and network access to the Visual database server on WLAN
2. **Database Schema Documentation**: Requires complete schema documentation for CUSTOMER_ORDER, CUSTOMER, and CUST_ORDER_LINE tables with field definitions
3. **Sample Data**: Requires access to sample/test orders (like 4049, 8113) for development and testing
4. **Connection String**: Requires properly formatted connection string for Visual database (SQL Server or compatible)
5. **Network Configuration**: Requires WLAN network configuration that allows database server connectivity
6. **IT Support**: Requires IT support to configure initial database credentials and test connectivity
7. **Report Template Definition**: Requires business stakeholders to confirm all required fields for order acknowledgement report

## Out of Scope *(mandatory)*

1. **Historical Data Migration**: Not migrating data from Visual database to AX/D365 - data remains in Visual database
2. **Order Creation/Editing**: Not creating or modifying orders - read-only access only
3. **Part Maintenance Lookups**: Not replacing the Visual "Part Maintenance" functionality for looking up part usage history (may be future phase)
4. **Manufacturing Window BOM**: Not replacing the Visual "Manufacturing Window" functionality for viewing bill of materials hierarchies (may be future phase)
5. **Purchase Order Lookups**: Not replacing Visual purchasing functionality
6. **Multi-User Collaboration**: Not supporting features like shared notes, user comments, or collaborative workflows
7. **Advanced Reporting**: Not generating custom reports, analytics, or data exports beyond the standard order acknowledgement
8. **Mobile Access**: Not providing mobile app or responsive web interface - desktop only
9. **Integration with AX/D365**: Not integrating with current AX/D365 system - standalone application
10. **Database Maintenance**: Not providing tools to backup, restore, or maintain the Visual database
11. **User Authentication/Authorization**: Not implementing user login system - assumes Windows authentication or single-user access
12. **Audit Trails**: Not tracking who views which orders or when (beyond basic error logging)

## Open Questions

*No open questions at this time. The transcript, order acknowledgement example, and SQL queries provide sufficient detail for all requirements.*
