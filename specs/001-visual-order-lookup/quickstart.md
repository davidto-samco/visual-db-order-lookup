# Visual Database Multi-Module Application - Quick Start Guide

**Version**: 1.0
**Date**: 2025-11-07
**Application**: Visual Database Order Lookup (Multi-Module Edition)

---

## Overview

The Visual Database Multi-Module Application provides read-only access to legacy Visual manufacturing data through three specialized modules:

1. **Sales Module** - Customer order lookup and acknowledgement display
2. **Inventory Module** - Part information, where-used, and purchase history
3. **Engineering Module** - Job-based Bill of Materials (BOM) exploration

All modules connect to the Visual SQL Server database over the WLAN. All operations are read-only - no data can be modified or deleted.

---

## Application Layout

```
┌────────────────────────────────────────────────────────┐
│  Visual Database Multi-Module Application              │
├────────────┬───────────────────────────────────────────┤
│            │                                           │
│ Sales      │        Active Module Content              │
│ (Active)   │                                           │
│            │        [Search controls]                  │
│ Inventory  │        [Results table/tree]               │
│            │        [Detail view]                      │
│ Engineering│                                           │
│            │                                           │
└────────────┴───────────────────────────────────────────┘
   200px              Remaining Width
```

**Navigation Panel** (left):
- 200px fixed width
- Three module buttons with icons
- Active module highlighted with blue background

**Module Container** (right):
- Displays content for selected module
- Each module has dedicated search controls and results display
- Switching modules preserves state (searches, selections, scroll positions)

---

## Getting Started

### 1. Launch Application

- Double-click `visual_order_lookup.exe` (or run `python main.py` from source)
- Application opens to **Sales Module** by default
- Status bar shows database connection status

### 2. Module Navigation

**To switch modules**:
1. Click module name in left navigation panel
2. Active module changes instantly
3. Previous module's state is preserved (you can return to same search results)

**Module Selection Indicators**:
- Dark blue background on active module
- Blue vertical accent bar on left edge
- White text for active module name

---

## Sales Module Quick Start

**Purpose**: Look up customer orders by job number, customer name, or date range. View order acknowledgement reports.

### Search by Job Number

1. Select **Sales** module (default on startup)
2. Locate **"Job Number"** search box (top search panel)
3. Enter job number (examples: `4049`, `8113`, `4327B`)
4. Press **Enter** or click **Search**
5. If found, order details display immediately in the detail pane
6. If not found, error message displays: "Order [job] not found"

**Example**: Search for job `4049` to see THE TRANE COMPANY order from 2000.

### Search by Customer Name

1. Select **Sales** module
2. Locate **"Customer Name"** search box
3. Enter customer name or partial name (examples: `TRANE`, `ARCADIA`)
4. Press **Enter** or click **Search**
5. Matching orders display in the order list (top pane)
6. Click an order in the list to view details

**Example**: Search for `TRANE` to see all Trane Company orders.

### Filter by Date Range

1. Select **Sales** module
2. Locate **Date Range Filter** panel (top of module)
3. Enter **Start Date** and/or **End Date** (format: MM/DD/YYYY)
   - Start Date only: Shows orders from that date forward
   - End Date only: Shows orders up to that date
   - Both dates: Shows orders between dates (inclusive)
4. Click **Apply Filter**
5. Orders matching date range display in order list

**Example**: Enter Start Date `01/01/2000` and End Date `12/31/2000` to see all 2000 orders.

**Clear Date Filter**:
- Click **Clear** button to reset date range
- Default view loads (100 most recent orders)

### View Order Details

**Order Acknowledgement Display** (right detail pane):
- **Customer Information**: Name, ship-to address, bill-to address
- **Order Header**: Order date, PO reference, contact information, promise date
- **Line Items Table**: Part descriptions, quantities, prices, totals
- **Order Total**: Currency-formatted total amount

**Print/Export Order**:
- Click **Print** button to generate PDF order acknowledgement
- Click **Export** to save as HTML file

---

## Inventory Module Quick Start

**Purpose**: Look up parts by part number. View part information, where the part has been used, and purchase history.

### Search for a Part

1. Select **Inventory** module from left navigation panel
2. Locate **"Part Number"** search box (top of module)
3. Enter part number (examples: `F0195`, `PF004`, `PP001`)
4. Press **Enter** or click **Search**
5. If found, part information displays in tabbed interface
6. If not found, message displays: "Part [number] not found"

**Example**: Search for part `F0195` to see "SLW 1/2" part details.

**Part Number Format**:
- Part numbers are case-insensitive (`f0195` same as `F0195`)
- Whitespace is automatically trimmed
- Typical length: 4-10 characters
- Common prefixes: `P` (purchased), `M` (manufactured), `F`/`R` (fabricated/raw)

### View Part Information

**Part Info Tab** (default tab, displays automatically after search):

**Part Master Data**:
- Part Number
- Description
- Extended Description (if available)
- Unit of Measure (EA, IN, FT, etc.)
- Material Code (e.g., 4140, 304SS)
- Drawing Number and Revision
- Weight and Weight Unit

**Cost Information**:
- Unit Material Cost
- Unit Labor Cost
- Unit Burden Cost
- Total Unit Cost (sum of material + labor + burden)
- Unit Price (selling price)

**Inventory Status**:
- Quantity On Hand (color-coded: red if <10, green if adequate)
- Quantity Available (available for issue)
- Quantity On Order (from vendors)
- Quantity In Demand (allocated to orders)

**Vendor Information**:
- Preferred Vendor Name
- Vendor ID

**Part Classification**:
- Purchased Part (Y/N)
- Fabricated Part (Y/N)
- Stocked Part (Y/N)

### View Where-Used

**Where Used Tab** (second tab):

1. After searching for a part, click **"Where Used"** tab
2. Table displays all usage records for this part
3. Columns:
   - Transaction Date (when part was used)
   - Job Number
   - Customer Order ID
   - Work Order (format: BASE_ID/LOT_ID)
   - Customer Name (or "Internal/Stock" for non-customer work)
   - Quantity (amount used)
   - Location (warehouse/location where part was issued)

**Interpreting Where-Used Results**:
- Each row represents one transaction where the part was issued/consumed
- Results sorted by most recent transaction first
- Empty fields show "N/A" (some transactions lack customer order references)

**Example**: Part `F0195` shows 900+ usage records across many jobs and customers.

### View Purchase History

**Purchase History Tab** (third tab):

1. After searching for a part, click **"Purchase History"** tab
2. Table displays all purchase orders for this part
3. Columns:
   - Order Date (PO date)
   - PO Number
   - Line (PO line number)
   - Vendor Name
   - Vendor Part # (vendor's part number, if different)
   - Quantity (ordered quantity)
   - Unit Price (cost per unit)
   - Line Total (total for PO line)
   - Received Date (when order was received)

**Results Limit**: Shows up to 100 most recent purchase orders (configurable in settings).

**Example**: Part `F0195` shows 995 purchase orders, primarily from vendor KARRIC.

### Print/Export Part Information

- Click **Print** button to generate PDF report with all three sections (Part Info, Where Used, Purchase History)
- Click **Export** to save as HTML file

---

## Engineering Module Quick Start

**Purpose**: Explore job-based Bill of Materials (BOM) hierarchies. View assemblies and components in hierarchical tree structure.

### Load a Job BOM

1. Select **Engineering** module from left navigation panel
2. Locate **"Job Number"** search box (top of module)
3. Enter job number (examples: `8113`, `8059`)
4. **Optional**: Check **"Use lazy loading (for large jobs)"** if job has 500+ work orders
   - Lazy loading: Loads assemblies first, then expands parts on demand (faster startup)
   - Full load: Loads entire BOM upfront (may take 5-10 seconds for large jobs)
5. Click **Load BOM**
6. BOM tree displays in hierarchical structure

**Example**:
- Job `8113`: Large job with 702 work orders, 15 assemblies (use lazy loading)
- Job `8059`: Small job with 33 work orders, 4 assemblies (full load is fine)

### Navigate the BOM Tree

**Tree Structure**:
```
Job 8113
├── Assembly 01 (collapsed)
├── Assembly 26 (expanded)
│   ├── Part M1234 - Manufactured part
│   ├── Part P5678 - Purchased part
│   └── Part M9999 - Another part
└── Assembly 41 (collapsed)
```

**Color Coding** (matches Visual conventions):
- **Blue text**: Assemblies (fabricated with sub-components)
- **Black text**: Manufactured parts (fabricated, no sub-components)
- **Red text**: Purchased parts (vendor-supplied)
- **Gray text**: Other/unknown parts

**Tree Columns**:
1. **Base/Lot ID**: Job number + assembly identifier (e.g., `8113/26`)
2. **Description**: Part or assembly description
3. **Drawing Number**: Drawing/blueprint reference
4. **Quantity**: Desired quantity for this component
5. **Material**: Material specification code

### Expand/Collapse Assemblies

**To expand an assembly**:
1. Click the arrow icon next to assembly name
2. If using lazy loading, parts load from database (100-300ms)
3. Parts display as children under assembly

**To collapse an assembly**:
1. Click the arrow icon again
2. Parts remain in memory (instant re-expand)

**Expand All/Collapse All**:
- Right-click on tree → **Expand All** (loads all assemblies if lazy loading enabled)
- Right-click on tree → **Collapse All** (collapses all assemblies)

### Search Within BOM

1. Locate **"Search"** box above tree (or press Ctrl+F)
2. Enter search term (part number, description keyword, drawing number)
3. Tree filters to show only matching items
4. Clear search box to show full tree again

**Example**: Search for `bearing` to find all bearings in the BOM.

### Export BOM

- Click **Export** button to save BOM hierarchy as HTML file
- Click **Print** to generate PDF report
- Export includes all assemblies and parts with color coding

---

## Tips & Tricks

### General

- **State Preservation**: Switching modules preserves your searches and results. You can load 100 orders in Sales, switch to Inventory to look up a part, then return to Sales and see the same 100 orders.

- **Database Connection**: If database connection is lost, error message displays. Check WLAN connection and retry.

- **Query Timeouts**: All queries have 30-second timeout. If a query times out, error message suggests narrowing search or using lazy loading for large datasets.

### Test Data

Use these known records to test each module:

**Sales Module**:
- Job `4049` - THE TRANE COMPANY, $1,751,000 order from 2000
- Job `8113` - ARCADIA order with large BOM
- Job `4327B` - Example of job with letter suffix
- Customer search: `TRANE` - Returns multiple orders

**Inventory Module**:
- Part `F0195` - "SLW 1/2", 995 purchase orders, vendor KARRIC
- Part `PF004` - "1/4 - 20 x 3/4\" BOLT GRADE", has where-used and purchase history
- Part `PP001` - "ISYS MODULE CLIP", used in 3 customer orders

**Engineering Module**:
- Job `8113` - Large BOM: 702 work orders, 15 assemblies
  - Assembly `26` - Roll former assembly with 330+ parts (great for lazy loading test)
  - Assembly `41` - Hydraulics assembly
- Job `8059` - Small BOM: 33 work orders, 4 assemblies (quick full load)

### Keyboard Shortcuts

- **Ctrl+F**: Focus search box in active module
- **Enter**: Execute search (when search box has focus)
- **Ctrl+P**: Print current view
- **Ctrl+E**: Export current view
- **Esc**: Clear search or close dialog

### Performance

- **Date Range Filters**: Narrower date ranges return results faster (fewer database rows)
- **Customer Name Search**: Partial names (e.g., `TRA`) may return many results; be specific
- **BOM Loading**: Use lazy loading for jobs with >100 work orders to avoid 5-10 second startup delays
- **Where-Used Queries**: May take 1-2 seconds for parts used in 500+ transactions

---

## Troubleshooting

### Connection Errors

**Problem**: "Could not connect to Visual database. Please check network connection."

**Solutions**:
1. Verify you are on the WLAN (not guest Wi-Fi)
2. Ping the SQL Server from Command Prompt: `ping [server_address]`
3. Check `.env` file has correct server, database, username, password
4. Contact IT if firewall or VPN issues

### Timeout Errors

**Problem**: "Query timed out after 30 seconds."

**Solutions**:
1. For BOM queries: Enable lazy loading for large jobs
2. For date range queries: Narrow date range (search smaller time periods)
3. For customer searches: Use more specific name (fewer results)
4. If persistent, contact IT to check database performance

### No Results Found

**Problem**: "No results found for [search term]."

**Possible Causes**:
- **Sales**: Job number doesn't exist, customer name misspelled, date range has no orders
- **Inventory**: Part number doesn't exist, typo in part number (check O vs 0)
- **Engineering**: Job number doesn't exist, job has no work orders

**Solutions**:
1. Double-check spelling and format
2. Try partial search (for customer names)
3. Check test data examples above to verify database connection is working

### Slow Performance

**Problem**: Application feels slow or unresponsive.

**Solutions**:
1. For large BOM loads: Use lazy loading
2. Close and reopen application to reset connection
3. Check network speed (run speed test)
4. Contact IT if database server is slow

### Display Issues

**Problem**: Text too small, window too large, colors incorrect.

**Solutions**:
1. Text size: Adjust Windows display scaling (Settings → Display)
2. Window size: Resize window and position is remembered
3. Colors: Check monitor color calibration

---

## Additional Resources

### Database Schema

See `specs/001-visual-order-lookup/research.md` for complete database schema documentation including:
- Table names and columns
- Join relationships
- Sample queries

### Data Model

See `specs/001-visual-order-lookup/data-model.md` for entity definitions:
- OrderSummary, OrderHeader, Customer, OrderLineItem
- Part, WhereUsed, PurchaseHistory
- BOMNode, Job

### API Contracts

See `specs/001-visual-order-lookup/contracts/` for service method documentation:
- `part_service.yaml` - Part lookup, where-used, purchase history methods
- `bom_service.yaml` - BOM hierarchy methods
- `module_architecture.md` - Architecture overview

---

## Support

For technical issues, feature requests, or questions:

1. **Application Logs**: Check `logs/` folder for error details
2. **Database Issues**: Contact IT database team
3. **Application Bugs**: Report to development team with:
   - Steps to reproduce
   - Error message (if any)
   - Module and search query used
   - Screenshot (if helpful)

---

**Last Updated**: 2025-11-07
**Application Version**: 1.0
**Documentation Version**: 1.0
