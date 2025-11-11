# Implementation Plan: Visual Database Multi-Module Application Expansion

**Branch**: `001-visual-order-lookup` | **Date**: 2025-11-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-visual-order-lookup/spec.md`

**Note**: This plan expands the existing Sales - Customer Order Entry module to include Inventory - Part Maintenance and Engineering - Manufacturing Window modules based on user requirements from visual-transcript.md and visual-spare-parts-guide.md.

## Summary

Expand the existing Visual database order lookup application from a single-purpose tool (Sales - Customer Order Entry) to a comprehensive three-module system that replicates the core functionality used by Spare Parts staff: **Sales (Customer Order Entry)**, **Inventory (Part Maintenance)**, and **Engineering (Manufacturing Window)**. The application will feature a left-hand navigation panel allowing users to switch between modules, with each module providing specialized lookup and search capabilities against the legacy Visual database.

**Current State**: Application implements Sales - Customer Order Entry with job number search, customer name search, date filtering, and order acknowledgement display.

**Target State**: Multi-module application with:
- Left navigation panel for module selection
- Sales module (existing functionality preserved)
- Inventory module for part number lookups with "Where Used" and "Purchase History" views
- Engineering module for job-based BOM exploration with hierarchical part listings

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyQt6 (GUI framework), pyodbc (SQL Server connectivity), python-dotenv (configuration), Jinja2 (report templates)
**Storage**: SQL Server Visual database (read-only access via WLAN)
**Testing**: pytest, unit tests for services and database queries
**Target Platform**: Windows 10/11 workstations on WLAN
**Project Type**: Single desktop application
**Performance Goals**: <10s per query, <15s total operation including UI rendering
**Constraints**: Read-only database access, <100MB memory footprint, 30s query timeout
**Scale/Scope**: 3 modules, 40+ years historical data, 3-5 concurrent users on separate workstations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle Compliance

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Local-First Architecture** | ✅ PASS | All three modules run locally; no cloud dependencies |
| **II. Reliable Database Connection** | ✅ PASS | Existing connection handling applies to all modules |
| **III. Read-Only Database Access (NON-NEGOTIABLE)** | ✅ PASS | All queries remain SELECT-only across all modules |
| **IV. Dual Search Capability (NON-NEGOTIABLE)** | ✅ PASS | Each module provides appropriate search methods: Sales (job/customer/date), Inventory (part number), Engineering (job number) |
| **V. Report Template System** | ✅ PASS | Templates extend to part info displays and BOM hierarchies |
| **VI. Minimal UI with Error Visibility** | ✅ PASS | Left navigation panel maintains simplicity; each module has focused UI |

### Legacy System Context Compliance

| Requirement | Status | Notes |
|------------|--------|-------|
| **Replacement Focus** | ✅ PASS | Matches three areas from transcript: Customer Order Entry (Sales), Part Maintenance (Inventory), Manufacturing Window (Engineering) |
| **Out of Scope Items** | ✅ PASS | Not replicating: Order Entry (write operations), Purchasing (out of scope), Production Management, Quality Management, or Integration with AX/D365 |
| **Data Preservation** | ✅ PASS | All historical data remains in Visual database; no migration |

**GATE RESULT**: ✅ **PASSED** - All principles satisfied; expansion aligns with constitution

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-order-lookup/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - database schema research
├── data-model.md        # Phase 1 output - entity definitions for all modules
├── quickstart.md        # Phase 1 output - user guide for three modules
├── contracts/           # Phase 1 output - API contracts for service methods
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
visual_order_lookup/
├── ui/
│   ├── __init__.py
│   ├── main_window.py           # MODIFIED: Add left navigation panel and module switching
│   ├── navigation_panel.py      # NEW: Left-hand module navigation (Sales/Inventory/Engineering)
│   ├── search_panel.py          # EXISTING: Reused for Sales module
│   ├── order_list_view.py       # EXISTING: Reused for Sales module
│   ├── order_detail_view.py     # EXISTING: Reused for Sales module
│   ├── dialogs.py               # EXISTING: Reused for all modules
│   ├── inventory_module.py      # NEW: Inventory module UI container
│   ├── part_search_panel.py     # NEW: Part number search controls
│   ├── part_detail_view.py      # NEW: Part info, Where Used, Purchase History display
│   ├── engineering_module.py    # NEW: Engineering module UI container
│   ├── job_search_panel.py      # NEW: Job number search for BOM
│   └── bom_tree_view.py         # NEW: Hierarchical BOM display with expandable tree
│
├── services/
│   ├── __init__.py
│   ├── order_service.py         # EXISTING: Sales module service
│   ├── part_service.py          # NEW: Inventory module service (part lookups)
│   └── bom_service.py           # NEW: Engineering module service (BOM hierarchies)
│
├── database/
│   ├── __init__.py
│   ├── connection.py            # EXISTING: Shared database connection
│   ├── models.py                # MODIFIED: Add Part, WhereUsed, PurchaseHistory, BOMNode entities
│   └── queries.py               # MODIFIED: Add queries for Inventory and Engineering modules
│
├── utils/
│   ├── __init__.py
│   ├── config.py                # EXISTING: Configuration management
│   └── formatters.py            # MODIFIED: Add formatters for part info and BOM displays
│
├── resources/
│   ├── styles/
│   │   └── visual_legacy.qss    # MODIFIED: Add styles for navigation panel and new modules
│   └── templates/
│       ├── order_template.html  # EXISTING: Sales module template
│       ├── part_template.html   # NEW: Part info display template
│       └── bom_template.html    # NEW: BOM hierarchy display template
│
└── main.py                      # EXISTING: Entry point (no changes needed)

tests/
├── unit/
│   ├── test_order_service.py    # EXISTING
│   ├── test_part_service.py     # NEW: Part lookup tests
│   └── test_bom_service.py      # NEW: BOM hierarchy tests
│
└── integration/
    ├── test_sales_integration.py      # EXISTING
    ├── test_inventory_integration.py  # NEW: End-to-end part lookup tests
    └── test_engineering_integration.py # NEW: End-to-end BOM tests
```

**Structure Decision**: Single project structure maintained. New modules added as horizontal extensions with dedicated UI, service, and test files. Existing database connection and configuration infrastructure reused across all modules.

## Complexity Tracking

> **No Constitution violations** - all complexity justified by business requirements from transcript analysis.

| Feature | Complexity | Justification |
|---------|-----------|---------------|
| Three modules | Moderate | Matches three distinct areas used by Spare Parts staff (from transcript: Sales, Inventory, Engineering) |
| Left navigation panel | Low | Standard UI pattern for multi-module applications; improves usability over separate applications |
| BOM tree hierarchy | Moderate | Essential for Manufacturing Window replication; matches Visual's hierarchical part display |
| Where Used queries | Moderate | Critical for part lookup workflows (from transcript: verifying part usage on specific jobs) |

---

## Phase 0: Outline & Research

### Research Tasks

#### RT-001: Visual Database Schema - Inventory Tables
**Goal**: Identify tables and columns for Part Maintenance module (part masters, where used, purchase history)

**Questions to Answer**:
- Which table stores part master data (part number, description, etc.)?
- How to query "Where Used" - which tables link parts to jobs/orders?
- Which tables store purchase history (vendor, PO number, purchase date)?
- What are the join conditions between part tables and order/job tables?

**Expected Outcome**: Document table names, key columns, and sample queries for:
- Part master lookup by part number (exact and partial match)
- Where Used query (all jobs/orders using a specific part)
- Purchase History query (all purchases of a specific part)

#### RT-002: Visual Database Schema - Engineering/BOM Tables
**Goal**: Identify tables and structure for Manufacturing Window module (job BOM hierarchies)

**Questions to Answer**:
- Which tables store work order structures (WORK_ORDER confirmed; what are columns)?
- How are parent-child relationships represented in BOM hierarchy?
- Which columns identify base ID, lot ID, part descriptions, and drawing numbers?
- What distinguishes white lines (assemblies), black lines (parts), and red lines (purchased parts)?
- How to query all components for a specific job in hierarchical order?

**Expected Outcome**: Document table schema for:
- Work order base structure (job → subassemblies)
- Part/assembly relationships (parent-child hierarchy)
- Part metadata (drawing numbers, descriptions, material specifications)
- Sample hierarchical query returning tree structure

#### RT-003: UI/UX Patterns for Multi-Module Applications
**Goal**: Research best practices for desktop application module navigation

**Questions to Answer**:
- What are standard PyQt6 patterns for left navigation panels?
- How to implement module switching without destroying/recreating widgets (performance)?
- What visual indicators work best for active module selection?
- How to preserve module state when switching (e.g., search results in Sales while viewing Inventory)?

**Expected Outcome**: Design decision for:
- Navigation panel implementation (QListWidget, QTreeWidget, or custom buttons)
- Module switching mechanism (QStackedWidget recommended)
- State preservation strategy (keep all module widgets in memory vs. recreate on demand)

#### RT-004: BOM Tree Display Patterns
**Goal**: Research PyQt6 approaches for hierarchical tree displays with large datasets

**Questions to Answer**:
- QTreeWidget vs. QTreeView with custom model - which is more appropriate?
- How to handle lazy loading for large BOMs (8113 job took a while per transcript)?
- How to color-code tree items (white/black/red lines per Visual conventions)?
- What are performance implications of loading 500+ part trees at once?

**Expected Outcome**: Design decision for:
- Tree widget selection
- Lazy loading strategy for large jobs
- Color coding mechanism
- Performance optimizations

#### RT-005: Part Number Search Strategies
**Goal**: Determine optimal search strategies for part number lookups

**Questions to Answer**:
- Do part numbers follow consistent format (e.g., "PO649" from transcript)?
- Should search support wildcards (e.g., "PO*" to find all PO parts)?
- What is average result count for part searches (performance implications)?
- Are there common user errors in part number entry (e.g., O vs 0)?

**Expected Outcome**: Search implementation strategy:
- Exact match vs. partial match vs. wildcard support
- Query optimization approach
- User input validation rules

### Research Consolidation

All findings from RT-001 through RT-005 will be documented in `research.md` with the following format:

```markdown
## Decision: [Technology/Approach Chosen]

**Rationale**: [Why this choice best meets requirements]

**Alternatives Considered**:
- Alternative A: [Reason for rejection]
- Alternative B: [Reason for rejection]

**Implementation Notes**: [Key details for Phase 1 design]
```

**Output**: research.md with all database schema details, UI/UX decisions, and implementation strategies

---

## Phase 1: Design & Contracts

**Prerequisites:** `research.md` complete with all database schema research

### Design Artifacts

#### D-001: Data Model Extensions
**File**: `data-model.md`

**Required Entity Definitions**:

1. **Part** (from Inventory module)
   - Fields: part_id, part_number, description, unit_of_measure, last_cost, material_spec
   - Validation: part_number required, non-empty
   - Relationships: has many WhereUsed records, has many PurchaseHistory records

2. **WhereUsed** (from Inventory module)
   - Fields: part_number, job_number, order_id, quantity, usage_date, line_number
   - Relationships: belongs to Part, belongs to Order
   - Query pattern: Get all WhereUsed for a given part_number

3. **PurchaseHistory** (from Inventory module)
   - Fields: part_number, po_number, vendor_name, quantity, unit_cost, purchase_date
   - Relationships: belongs to Part
   - Query pattern: Get all PurchaseHistory for a given part_number, ordered by purchase_date DESC

4. **BOMNode** (from Engineering module)
   - Fields: job_number, base_id, lot_id, parent_id, node_type (assembly/part/purchased), description, drawing_number, quantity, material_spec
   - Relationships: belongs to Job, has many children (self-referential)
   - Hierarchy: Uses parent_id to build tree structure
   - Display rules: node_type determines color (assembly=white, part=black, purchased=red)

5. **Job** (from Engineering module)
   - Fields: job_number, customer_id, description, start_date
   - Relationships: has many BOMNode records (root nodes where parent_id is NULL)

**Existing Entities** (preserved):
- Order (Customer Order)
- OrderSummary
- OrderLineItem
- Customer
- DateRangeFilter

#### D-002: Service Contracts
**File**: `contracts/part_service.yaml`

```yaml
PartService:
  search_by_part_number:
    input:
      part_number: string (required)
    output: Part | null
    errors:
      - ConnectionError: Database connection failed
      - TimeoutError: Query exceeded 30s

  get_where_used:
    input:
      part_number: string (required)
    output: List[WhereUsed]
    errors:
      - ConnectionError: Database connection failed
      - TimeoutError: Query exceeded 30s

  get_purchase_history:
    input:
      part_number: string (required)
      limit: int (optional, default 100)
    output: List[PurchaseHistory]
    errors:
      - ConnectionError: Database connection failed
      - TimeoutError: Query exceeded 30s
```

**File**: `contracts/bom_service.yaml`

```yaml
BOMService:
  get_bom_hierarchy:
    input:
      job_number: string (required)
    output: List[BOMNode] (tree structure with parent-child relationships)
    errors:
      - ConnectionError: Database connection failed
      - TimeoutError: Query exceeded 30s
      - JobNotFoundError: No BOM found for job_number

  get_bom_subtree:
    input:
      job_number: string (required)
      base_id: string (required)
    output: List[BOMNode] (subtree for specific subassembly)
    errors:
      - ConnectionError: Database connection failed
      - TimeoutError: Query exceeded 30s
```

#### D-003: Module Architecture
**File**: `contracts/module_architecture.md`

```markdown
## Module Architecture

### Navigation System
- **NavigationPanel** (QWidget): Left-hand panel with three module buttons
  - Sales button (default selected)
  - Inventory button
  - Engineering button
  - Visual indicator for active module

### Module Containers
- **SalesModule** (QWidget): Wraps existing DateRangePanel + SearchPanel + OrderListView + OrderDetailView
- **InventoryModule** (QWidget): Contains PartSearchPanel + PartDetailView (Where Used / Purchase History tabs)
- **Engineering Module** (QWidget): Contains JobSearchPanel + BOMTreeView

### State Management
- **Module Switching**: Use QStackedWidget to switch between module containers
- **State Preservation**: All three modules remain in memory; switching modules preserves search results and UI state
- **Database Connection**: Single DatabaseConnection instance shared across all modules

### Service Layer
- **OrderService** (existing): Handles Sales module queries
- **PartService** (new): Handles Inventory module queries
- **BOMService** (new): Handles Engineering module queries
- All services use the same DatabaseConnection instance
- All services follow DatabaseWorker pattern for async execution
```

#### D-004: UI Templates
**File**: `resources/templates/part_template.html` (Jinja2 template)

```html
<!-- Part Information Display Template -->
<div class="part-info">
  <h2>Part Information</h2>
  <table>
    <tr><th>Part Number:</th><td>{{ part_number }}</td></tr>
    <tr><th>Description:</th><td>{{ description }}</td></tr>
    <tr><th>Unit of Measure:</th><td>{{ unit_of_measure }}</td></tr>
    <tr><th>Last Cost:</th><td>{{ last_cost | currency }}</td></tr>
    <tr><th>Material:</th><td>{{ material_spec | default('N/A') }}</td></tr>
  </table>
</div>

<div class="where-used">
  <h3>Where Used</h3>
  <table>
    <thead>
      <tr><th>Job Number</th><th>Order ID</th><th>Quantity</th><th>Usage Date</th></tr>
    </thead>
    <tbody>
      {% for usage in where_used %}
      <tr>
        <td>{{ usage.job_number }}</td>
        <td>{{ usage.order_id }}</td>
        <td>{{ usage.quantity }}</td>
        <td>{{ usage.usage_date | date }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
```

**File**: `resources/templates/bom_template.html` (Jinja2 template for print/export)

```html
<!-- BOM Hierarchy Display Template -->
<div class="bom-hierarchy">
  <h2>Bill of Materials - Job {{ job_number }}</h2>
  <div class="bom-tree">
    {% for node in bom_nodes %}
    <div class="bom-node {{ node.node_type }}" style="margin-left: {{ node.depth * 20 }}px;">
      <span class="base-lot">{{ node.base_id }}/{{ node.lot_id }}</span>
      <span class="description">{{ node.description }}</span>
      {% if node.drawing_number %}
      <span class="drawing">Dwg: {{ node.drawing_number }}</span>
      {% endif %}
    </div>
    {% endfor %}
  </div>
</div>
```

#### D-005: Agent Context Update
After completing all Phase 1 artifacts, run:

```powershell
.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude
```

This updates `CLAUDE.md` with new technologies and module information:
- Part lookup services
- BOM hierarchy services
- Multi-module navigation pattern
- Three-module architecture

**Output**: Updated `CLAUDE.md` with all Phase 1 context

---

## Phase 2: Re-evaluate Constitution Check

*Performed after Phase 1 design artifacts complete*

### Post-Design Validation

| Principle | Re-check Status | Notes |
|-----------|----------------|-------|
| **I. Local-First Architecture** | ✅ PASS | Design maintains local execution; no cloud dependencies introduced |
| **II. Reliable Database Connection** | ✅ PASS | Shared DatabaseConnection; error handling consistent across modules |
| **III. Read-Only Database Access** | ✅ PASS | All queries remain SELECT-only; no write operations in any module |
| **IV. Dual Search Capability** | ✅ PASS | Each module has appropriate search: Sales (job/customer/date), Inventory (part), Engineering (job) |
| **V. Report Template System** | ✅ PASS | Templates created for part info and BOM displays |
| **VI. Minimal UI with Error Visibility** | ✅ PASS | Navigation panel adds 200px width; UI remains focused and simple |

### Performance Validation

| Requirement | Design Impact | Mitigation |
|-------------|---------------|------------|
| **<10s query execution** | BOM queries may be slow for large jobs (per transcript: 8113 "takes a while") | Implement lazy loading; show loading indicator; consider query optimization in research phase |
| **<15s total operation** | Module switching should be instant (no DB operations) | Use QStackedWidget; keep all modules in memory |
| **<100MB memory** | Three modules + state preservation may increase memory | Monitor in testing; consider lazy widget creation if needed |

**GATE RESULT**: ✅ **PASSED** - Design maintains all constitution principles; performance concerns identified and mitigated

---

## Implementation Sequence (for /speckit.tasks)

*This section outlines the recommended task generation strategy for `/speckit.tasks` command*

### Milestone 1: Navigation Infrastructure (3-5 tasks)
1. Create NavigationPanel widget with three module buttons
2. Modify MainWindow to use QStackedWidget for module switching
3. Create empty module container widgets (SalesModule, InventoryModule, EngineeringModule)
4. Integrate existing Sales functionality into SalesModule container
5. Test module switching and state preservation

### Milestone 2: Inventory Module (8-12 tasks)
1. Research and document Inventory tables schema (RT-001)
2. Define Part, WhereUsed, PurchaseHistory data models
3. Create database queries for part lookup, where used, purchase history
4. Implement PartService with three methods (search, get_where_used, get_purchase_history)
5. Create PartSearchPanel UI widget
6. Create PartDetailView UI widget with tabs (Info, Where Used, Purchase History)
7. Integrate PartService with InventoryModule container
8. Create part_template.html Jinja2 template
9. Write unit tests for PartService
10. Write integration tests for Inventory module

### Milestone 3: Engineering Module (10-15 tasks)
1. Research and document Engineering/BOM tables schema (RT-002)
2. Research BOM tree display patterns (RT-004)
3. Define BOMNode and Job data models
4. Create database queries for BOM hierarchy (recursive or hierarchical query)
5. Implement BOMService with get_bom_hierarchy method
6. Create JobSearchPanel UI widget
7. Create BOMTreeView UI widget with color coding (white/black/red)
8. Implement lazy loading for large BOM trees
9. Integrate BOMService with EngineeringModule container
10. Create bom_template.html Jinja2 template
11. Write unit tests for BOMService
12. Write integration tests for Engineering module
13. Performance testing for large jobs (8113 from transcript)

### Milestone 4: Polish & Documentation (3-5 tasks)
1. Update visual_legacy.qss with navigation panel styles
2. Create quickstart.md user guide for all three modules
3. Update README.md with module descriptions
4. End-to-end testing across all three modules
5. Performance validation (<15s operations, <100MB memory)

---

## Notes for Implementation (/speckit.implement)

### Key Implementation Guidelines

1. **Reuse Existing Patterns**: OrderService provides the template for PartService and BOMService (async DatabaseWorker, error handling, timeout management)

2. **Shared Infrastructure**: All modules share:
   - DatabaseConnection instance
   - ErrorHandler dialogs
   - LoadingDialog widget
   - Configuration from .env file

3. **Module Independence**: Each module should be independently testable and deployable; no cross-module dependencies

4. **Performance Monitoring**: Large BOM queries (8113, 8059 from transcript) require special attention:
   - Implement query timeout handling
   - Show progress indicators for slow queries
   - Consider lazy loading for tree expansion

5. **User Workflows** (from transcript):
   - **Sales**: Customer calls with job number → search by job → view order acknowledgement
   - **Inventory**: Customer provides part number → search part → view where used → identify jobs where part was used
   - **Engineering**: Customer knows job but not part → search job → expand BOM tree → identify specific component (e.g., "bearing cover on roll former")

6. **Color Coding** (from transcript lines 229-256):
   - White lines = assemblies (main drawings)
   - Black lines = manufactured parts (Ms with drawing numbers)
   - Red lines = purchased parts (P parts)

7. **Base/Lot ID Format**: Maintain existing {ORDER_ID}/{LOT_ID} format from Sales module; apply same logic to Engineering module BOM display

---

## Success Criteria

### Technical Success Criteria

- ✅ All three modules accessible via left navigation panel
- ✅ Sales module preserves existing functionality (order search, date filter, order acknowledgement)
- ✅ Inventory module supports part number search with Where Used and Purchase History displays
- ✅ Engineering module supports job number search with hierarchical BOM tree display
- ✅ All queries complete within 15 seconds or show timeout error
- ✅ Module switching is instant (<500ms)
- ✅ Application memory usage stays below 100MB during normal operation
- ✅ All database operations remain read-only (no write queries)

### User Experience Success Criteria

- ✅ Staff can switch between modules without losing search results or state
- ✅ Part lookups show clear "Where Used" lists (transcript: "we can go in and see everywhere this part was used")
- ✅ BOM trees display with appropriate color coding (white/black/red per Visual conventions)
- ✅ Large BOM loads (job 8113) show progress indicators and complete within 30 seconds
- ✅ Error messages remain clear and actionable across all modules
- ✅ UI remains simple and focused (no feature bloat)

### Validation Methods

1. **Manual Testing with Known Data**:
   - Test Sales module with jobs 4049, 8113, 4327B (from transcript and test files)
   - Test Inventory module with part PO649 (from transcript line 76)
   - Test Engineering module with jobs 8113, 8059 (from transcript lines 172-175)

2. **Performance Testing**:
   - Measure query execution times for 100 random parts (Inventory)
   - Measure BOM load times for 10 large jobs (Engineering)
   - Measure memory footprint with all three modules in use simultaneously

3. **User Acceptance Testing**:
   - Pam, Cindy, or Efron validate that each module matches Visual functionality
   - Verify workflows from transcript can be completed in new application

---

**End of Implementation Plan**

**Next Steps**:
1. Run `/speckit.plan` Phase 0 to generate `research.md` (database schema research)
2. Complete Phase 1 to generate `data-model.md`, `contracts/`, and `quickstart.md`
3. Run `/speckit.tasks` to generate `tasks.md` with actionable implementation tasks
4. Execute implementation via `/speckit.implement`
