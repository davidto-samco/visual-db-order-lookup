# Feature Specification: Engineering Module - Work Order Hierarchy Viewer

**Feature ID**: 003-engineering-work-order-hierarchy
**Created**: 2025-01-14
**Status**: Planning
**Owner**: Engineering/Spare Parts Department

## Overview

Add an Engineering module to the Visual Database Order Lookup application that provides hierarchical viewing of work order structures. The module enables users to search for work orders by BASE_ID and view detailed manufacturing information in an expandable/collapsible tree format.

### Context

The legacy VISUAL Enterprise Manufacturing Window displays work orders with their complete BOM hierarchy, operations, requirements, labor, and material transactions. When the Manufacturing Window became unavailable, engineering and spare parts staff lost the ability to quickly look up historical work order details needed for:
- Analyzing past production runs
- Understanding as-built configurations
- Researching material usage and labor hours
- Investigating work order history for customer quotes

This module provides read-only access to historical work order data (1985-present) in a hierarchical tree view matching the original Manufacturing Window layout.

### Relationship to Legacy System

In VISUAL Enterprise, the Manufacturing Window module provides comprehensive work order management including BOM editing, routing changes, and production scheduling. This Engineering module replaces ONLY the **work order lookup and viewing** functionality:

**In Scope:**
- Search work orders by BASE_ID (shows all lots/subs with that base)
- Display work order header information
- View hierarchical structure:
  - Operations (routing steps)
  - Requirements (materials per operation)
  - Part details (component information)
  - Labor tickets (labor transactions)
  - Inventory transactions (material issues/returns)
  - WIP balance (work-in-progress costs)
- Expand/collapse tree nodes for navigation
- Export work order details to CSV

**Out of Scope:**
- Creating or editing work orders (read-only per Constitution III)
- Modifying BOMs or routing
- Production scheduling
- Shop floor control
- Work order status changes
- Material requisitioning
- Integration with current production system

## Requirements

### Functional Requirements

**FR-1: Work Order Search**
- Search by BASE_ID (partial match, case-insensitive)
- Display list of matching work orders showing:
  - Work Order/Engineering Master ID (BASE_ID with LOT_ID/SUB_ID)
  - Date Created
  - Status (Open/Closed)
  - Part Description (manufactured part)
- List sorted by date created descending (most recent first)
- Maximum 1000 results displayed with pagination

**FR-2: Work Order Selection**
- Single-click selects work order from list
- Display hierarchical tree view in detail pane
- Tree shows work order structure with expand/collapse controls

**FR-3: Hierarchical Display Structure**

The work order tree displays 7 different node types arranged in 4 hierarchy levels:

**Level 1 - Work Order Header**
- Format: `[C] BASE_ID/LOT_ID` or `[C] BASE_ID-SUB_ID/LOT_ID`
- Shows: Part ID, Description, Quantity, Status, Dates
- Always displayed (cannot collapse)

**Level 2 - Operations (routing steps)**
- Node: `[OPERATION SEQ] - OPERATION_DESCRIPTION`
- Collapsible/Expandable
- Shows: Sequence, Department, Setup hours, Run hours, Status

**Level 3 - Requirements (materials for operation)**
- Node: `Part ID - Part Description - Qty`
- Nested under operation
- Shows: Part number, Description, Quantity per, Fixed qty, Scrap %
- Links to Part master information

**Level 4 - Part Details**
- Shows: Part type, Unit of measure, Cost information
- Read from PART table

**Level 2 (alternate) - Labor Tickets**
- Node: `[LABOR] Employee - Date - Hours`
- Collapsible/Expandable
- Shows: Employee ID, Operation, Date, Hours, Rate

**Level 2 (alternate) - Inventory Transactions**
- Node: `[MATERIAL] Part ID - Type - Qty - Date`
- Collapsible/Expandable
- Shows: Transaction type (Issue/Return), Part, Quantity, Date, Location

**Level 2 (alternate) - WIP Balance**
- Node: `[WIP] Cost Category - Amount`
- Collapsible/Expandable
- Shows: Material cost, Labor cost, Burden cost, Total

**Level 3 (special case) - Sub Work Orders**
- Node: Appears under Requirements when `SUBORD_WO_BASE_ID`, `SUBORD_WO_LOT_ID`, `SUBORD_WO_SUB_ID` are populated
- Represents child work order assembly steps
- Displays child work order identifier with expandable tree
- Shows: Child work order dates (SCHED_START_DATE, SCHED_FINISH_DATE)
- Quantity comes from child work order's DESIRED_QTY field
- Notes retrieved from REQUIREMENT_BINARY.bits column (cast from image type)

**FR-4: Tree Interaction**
- Click `[+]` icon to expand node
- Click `[-]` icon to collapse node
- Keyboard: Arrow keys for navigation, Space/Enter to toggle
- Double-click node to expand/collapse
- Expand All / Collapse All buttons at top of tree

**FR-5: Visual Indicators**
- `[C]` prefix for work order header (Closed status)
- Black bars indicate selected/highlighted nodes (as shown in screenshots)
- Indentation shows hierarchy depth
- Icons distinguish node types (operation, material, labor, WIP)

**FR-6: Export Functionality**
- Export button saves current work order structure to CSV
- Flattened format with hierarchy indicated by indentation level
- File naming: `workorder_{BASE_ID}_{LOT_ID}_{TIMESTAMP}.csv`

### Non-Functional Requirements

**NFR-1: Performance**
- Work order search MUST complete within 5 seconds
- Tree rendering MUST complete within 2 seconds for 500 nodes
- Expand/collapse operations MUST feel instant (<100ms)
- Total load time (search + render) MUST not exceed 10 seconds

**NFR-2: Database Access**
- Read-only access to Visual database (Constitutional requirement)
- Query tables: WORK_ORDER, OPERATION, REQUIREMENT, PART, LABOR_TICKET, INVENTORY_TRANS, WIP_BALANCE, WORKORDER_BINARY, REQUIREMENT_BINARY
- Use WITH (NOLOCK) hint for all queries
- Parameterized queries to prevent SQL injection

**NFR-3: UI Consistency**
- Match existing Inventory and Sales module layout
- Use same PyQt6 widgets and styling
- Maintain left sidebar navigation pattern
- Follow existing pagination and export patterns

**NFR-4: Tree Control Performance**
- Lazy loading: Only load child nodes when expanded
- Virtual scrolling for large trees (>1000 nodes)
- Progressive rendering for responsive UI

## Database Schema Reference

### Primary Tables

**WORK_ORDER** (Header information)
- `BASE_ID` (varchar 30, PK) - Base work order identifier
- `LOT_ID` (varchar 30, PK) - Lot identifier
- `SUB_ID` (varchar 30, PK) - Sub identifier
- `PART_ID` (varchar 30) - Manufactured part
- `TYPE` (char 1) - M=Manufacturing, W=Work Order
- `STATUS` (varchar 10) - Open/Closed
- `START_DATE`, `COMPLETE_DATE` - Production dates
- `ORDER_QTY` (decimal) - Quantity to produce

**OPERATION** (Routing steps)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK to WORK_ORDER)
- `SEQUENCE` (smallint) - Operation sequence number
- `OPERATION_ID` (varchar 30) - Operation identifier
- `DESCRIPTION` (varchar 255) - Operation description
- `DEPARTMENT_ID` (varchar 30) - Department
- `SETUP_HRS` (decimal) - Setup hours
- `RUN_HRS` (decimal) - Run hours per unit

**REQUIREMENT** (BOM materials per operation)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK)
- `OPERATION_SEQ_NO` (smallint, FK to OPERATION.SEQUENCE)
- `PART_ID` (varchar 30) - Required component
- `QTY_PER` (decimal) - Quantity per assembly
- `FIXED_QTY` (decimal) - Fixed quantity
- `SCRAP_PERCENT` (decimal) - Scrap percentage

**PART** (Component details)
- `ID` (varchar 30, PK) - Part number
- `DESCRIPTION` (varchar 255) - Part description
- `TYPE` (varchar 10) - Part type (Purchased, Manufactured, etc.)
- `UNIT_OF_MEASURE` (varchar 10)
- `UNIT_MATERIAL_COST`, `UNIT_LABOR_COST`, `UNIT_BURDEN_COST` (decimal)

**LABOR_TICKET** (Labor transactions)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK)
- `OPERATION_SEQ` (smallint)
- `EMPLOYEE_ID` (varchar 30)
- `LABOR_DATE` (datetime)
- `SETUP_HRS` (decimal)
- `RUN_HRS` (decimal)
- `LABOR_RATE` (decimal)

**INVENTORY_TRANS** (Material transactions)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK)
- `PART_ID` (varchar 30)
- `TRANS_TYPE` (varchar 10) - Issue, Return, Scrap
- `QUANTITY` (decimal)
- `TRANS_DATE` (datetime)
- `LOCATION_ID` (varchar 30)

**WIP_BALANCE** (Work-in-progress costs)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK)
- `MATERIAL_COST` (decimal)
- `LABOR_COST` (decimal)
- `BURDEN_COST` (decimal)
- `TOTAL_COST` (decimal)

**WORKORDER_BINARY** (Work order notes)
- `WORKORDER_BASE_ID` (varchar 30, FK to WORK_ORDER.BASE_ID)
- `WORKORDER_LOT_ID` (varchar 30, FK to WORK_ORDER.LOT_ID)
- `bits` (image) - Work order notes stored as binary data
- **Note**: Requires two-step cast to retrieve text: `CAST(CAST(bits AS VARBINARY(MAX)) AS VARCHAR(MAX))`

**REQUIREMENT_BINARY** (Requirement notes)
- `WORKORDER_BASE_ID`, `WORKORDER_LOT_ID`, `WORKORDER_SUB_ID` (FK to WORK_ORDER)
- `OPERATION_SEQ_NO` (smallint, FK to OPERATION.SEQUENCE)
- `PART_ID` (varchar 30, FK to REQUIREMENT.PART_ID)
- `bits` (image) - Requirement notes stored as binary data
- **Note**: Requires two-step cast to retrieve text: `CAST(CAST(bits AS VARBINARY(MAX)) AS VARCHAR(MAX))`

### Query Patterns

**Note**: Sample queries shown below. Complete implementation includes 8 query functions (search, header, operations, requirements, labor, inventory, WIP, hierarchy) - see `visual_order_lookup/database/queries/work_order_queries.py` for full set.

**Work Order Search:**
```sql
SELECT BASE_ID, LOT_ID, SUB_ID, PART_ID, TYPE, STATUS, START_DATE
FROM WORK_ORDER WITH (NOLOCK)
WHERE BASE_ID LIKE ?
ORDER BY START_DATE DESC
```

**Work Order Header:**
```sql
SELECT wo.*, p.DESCRIPTION AS part_description
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = ? AND wo.LOT_ID = ? AND wo.SUB_ID = ?
```

**Operations (Level 2):**
```sql
SELECT SEQUENCE, OPERATION_ID, DESCRIPTION, DEPARTMENT_ID, SETUP_HRS, RUN_HRS
FROM OPERATION WITH (NOLOCK)
WHERE WORKORDER_BASE_ID = ? AND WORKORDER_LOT_ID = ? AND WORKORDER_SUB_ID = ?
ORDER BY SEQUENCE
```

**Requirements (Level 3 - lazy load per operation):**
```sql
SELECT r.PART_ID, p.DESCRIPTION, r.QTY_PER, r.FIXED_QTY, r.SCRAP_PERCENT
FROM REQUIREMENT r WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON r.PART_ID = p.ID
WHERE r.WORKORDER_BASE_ID = ?
  AND r.WORKORDER_LOT_ID = ?
  AND r.WORKORDER_SUB_ID = ?
  AND r.OPERATION_SEQ_NO = ?
ORDER BY r.PART_ID
```

## Implementation Scope

### In Scope
- Create Engineering module UI (left sidebar entry)
- Implement BASE_ID search with work order list
- Build hierarchical tree view widget (PyQt6 QTreeWidget)
- Create data models for WorkOrder, Operation, Requirement, Labor, InventoryTransaction, WIPBalance
- Implement lazy loading for tree nodes
- Add expand/collapse all functionality
- Implement CSV export for work order structure
- Add keyboard navigation for tree

### Out of Scope
- Editing work order data (read-only per Constitution)
- Creating new work orders
- Graphical BOM editor
- Production scheduling integration
- Real-time work order status updates
- Shop floor data entry
- Material requisition generation
- Cost rollup calculations (display only)

## Success Criteria

1. Engineering module accessible from left sidebar
2. BASE_ID search returns matching work orders within 5 seconds
3. Work order hierarchical tree displays correctly with all 7 node types across 4 hierarchy levels
4. Expand/collapse operations work smoothly (<100ms response)
5. Tree supports keyboard navigation (arrows, space, enter)
6. Export generates CSV with correct hierarchy indentation
7. Performance: 500-node tree renders in <2 seconds
8. No database write operations (Constitutional compliance)
9. UI matches existing Inventory/Sales module styling

## Acceptance Tests

### Test 1: Work Order Search
- **Given**: Engineering module open
- **When**: User enters "8113" in BASE_ID search
- **Then**:
  - List displays all work orders starting with "8113" (e.g., 8113/26, 8113-1/26, 8113-2/26)
  - Each row shows BASE_ID, Date Created, Status, Part Description
  - Results sorted by date descending

### Test 2: Hierarchical Tree Display
- **Given**: User selects work order "8113/26"
- **When**: Tree view loads
- **Then**:
  - Header node shows: `[C] 8113/26` with part info
  - Child nodes visible: Operations, Labor, Materials, WIP
  - All nodes initially collapsed except header

### Test 3: Expand Operations
- **Given**: Tree loaded for work order "8113/26"
- **When**: User clicks `[+]` on Operations node
- **Then**:
  - Node expands showing operation list (10, 20, 30, etc.)
  - Each operation shows: Seq # - Description
  - Expand icon changes to `[-]`

### Test 4: Expand Requirements (Lazy Load)
- **Given**: Operations expanded showing sequence 10
- **When**: User expands operation 10
- **Then**:
  - Database query executes for requirements of operation 10
  - Child nodes display showing parts with quantities
  - Example: "M28803 - TOP BEARING COVER - Qty: 1.0000"

### Test 5: Keyboard Navigation
- **Given**: Tree with expanded operations
- **When**: User presses Down arrow
- **Then**: Selection moves to next node
- **When**: User presses Space
- **Then**: Selected node expands/collapses

### Test 6: Expand All / Collapse All
- **Given**: Tree partially expanded
- **When**: User clicks "Expand All" button
- **Then**: All nodes expand (operations, requirements, labor, materials, WIP)
- **When**: User clicks "Collapse All" button
- **Then**: All nodes collapse except header

### Test 7: CSV Export
- **Given**: Work order tree fully expanded
- **When**: User clicks "Export to CSV"
- **Then**:
  - File dialog prompts for save location
  - CSV file generated with hierarchy indicated by indentation
  - Filename: `workorder_8113_26_20250114.csv`

### Test 8: Performance
- **Given**: Work order with 500 requirements across 50 operations
- **When**: User expands all nodes
- **Then**: Tree renders within 2 seconds
- **When**: User collapses a node
- **Then**: Response feels instant (<100ms)

## Dependencies

- Existing application infrastructure (database connection, PyQt6)
- Visual database tables: WORK_ORDER, OPERATION, REQUIREMENT, PART, LABOR_TICKET, INVENTORY_TRANS, WIP_BALANCE (primary), WORKORDER_BINARY, REQUIREMENT_BINARY (binary notes)
- PyQt6 QTreeWidget for hierarchical display
- CSV export functionality (similar to existing modules)

## Risks & Mitigation

**Risk**: Large work orders (1000+ nodes) may cause UI lag
- **Mitigation**: Implement lazy loading (only load expanded nodes) + virtual scrolling + pagination for top-level results

**Risk**: Complex joins across 7 tables may slow queries
- **Mitigation**: Separate queries per level (lazy load), use database indexes on FK columns, implement 5-second timeout

**Risk**: Tree control may not match VISUAL Enterprise visual appearance exactly
- **Mitigation**: Use screenshots as reference, prioritize functional equivalence over pixel-perfect match

**Risk**: Users may confuse read-only view with Manufacturing Window edit capabilities
- **Mitigation**: Clear labeling ("Engineering Lookup - Read Only"), no edit controls visible, documentation

## Open Questions

None - all technical details resolved through screenshots and database analysis.

## Notes

- Screenshots show VISUAL Enterprise Manufacturing Window displaying work order 8113/26
- Collapsed view (manugacturing.png) shows high-level structure
- Expanded view (manugacturing-expand.png) shows detailed operations and requirements
- Black bars indicate selection/focus state
- `[C]` prefix indicates Closed status
- Hierarchy depth shown through indentation (approximately 20px per level)
- BASE_ID search list (base_workorder.png) shows standard list view with columns
- Tree control performance critical for user experience - lazy loading essential

## Terminology

- **BASE_ID**: Primary work order identifier (e.g., "8113")
- **LOT_ID**: Lot/batch identifier for the work order (e.g., "26")
- **SUB_ID**: Sub-identifier for work order variants (default: "0")
- **Work Order Composite Key**: (BASE_ID, LOT_ID, SUB_ID) - uniquely identifies a work order
- **Operation**: Routing step/manufacturing operation within a work order (e.g., sequence 10, 20, 30)
- **Requirement**: Material/component needed for an operation (BOM line item)
- **Sub Work Order**: Child work order referenced by REQUIREMENT.SUBORD_WO_* fields
- **Labor Ticket**: Time entry record for work performed on an operation
- **Inventory Transaction**: Material issue/return record for a work order
- **WIP Balance**: Work-in-progress cost accumulation (material + labor + burden)
- **Lazy Loading**: Loading child tree nodes only when expanded (performance optimization)
- **WORKORDER_BINARY**: Table containing work order notes in image-type `bits` column
- **REQUIREMENT_BINARY**: Table containing requirement notes in image-type `bits` column
