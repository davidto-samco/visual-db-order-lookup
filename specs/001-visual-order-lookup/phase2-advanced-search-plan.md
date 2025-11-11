# Implementation Plan: Visual Database Order Lookup with Advanced Search

**Branch**: `001-visual-order-lookup` | **Date**: 2025-11-06 | **Spec**: [spec.md](./spec.md)

**Feature Extension**: Adding Query-by-Example advanced search capabilities from VISUAL Enterprise 6.3.8.014

## Summary

Extending the existing Visual Database Order Lookup application to include **Advanced Search (Query-by-Example)** functionality from VISUAL Enterprise's Sales module. The current application provides basic search by job number and customer name. This extension adds a comprehensive filtering dialog allowing users to search by multiple criteria simultaneously: Order ID, Customer ID, Customer Name, Order Status, Salesrep ID, Total Amount range, Currency, Bill-To Name, and multiple date fields (Last Order Date, Open Date, Desired Ship Date, Create Date).

**Technical Approach**: Implement a modal dialog (QDialog) with dynamic query builder that generates parameterized SQL WHERE clauses from user-selected filter criteria. Maintain read-only database access while providing VISUAL Enterprise's "Query by Example" pattern familiar to existing users.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyQt6 6.6.0 (GUI framework), pyodbc 5.0.1 (SQL Server connectivity), Jinja2 3.1.2 (templates), python-dotenv 1.0.0 (configuration)
**Storage**: SQL Server (SAMCO database on 10.10.10.142:1433) - READ ONLY access
**Testing**: pytest 7.4.3, pytest-qt 4.2.0, pytest-mock 3.12.0
**Target Platform**: Windows 10/11 desktop
**Project Type**: Single desktop application (PyQt6)
**Performance Goals**:
- Advanced search query execution: <15 seconds (same as existing search)
- Filter dialog display: <500ms
- Query result rendering: <1 second for up to 1000 results
**Constraints**:
- Read-only database access (no INSERT/UPDATE/DELETE)
- WLAN-only connectivity
- Memory footprint: <100MB
- Single-threaded execution acceptable
**Scale/Scope**:
- 40+ years of historical order data (1985-present)
- Estimated 100,000+ orders in database
- Max 1000 search results displayed at once
- 3-5 concurrent users (Pam, Cindy, Efron)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-evaluated after Phase 1 design.*

### Compliance Validation

✅ **Principle I - Local-First Architecture**
- Advanced search dialog runs locally in PyQt6
- No cloud services or external dependencies
- All filtering logic happens client-side before query generation

✅ **Principle II - Reliable Database Connection**
- Reuses existing DatabaseConnection class
- Same retry logic and timeout handling
- No changes to connection management

✅ **Principle III - Read-Only Database Access (NON-NEGOTIABLE)**
- Advanced search generates SELECT queries only
- All filters applied via WHERE clauses (parameterized)
- No write operations introduced

✅ **Principle IV - Dual Search Capability (NON-NEGOTIABLE)**
- **EXTENDS** existing search modes (preserves job number and customer name search)
- Adds "Advanced Search" as third search mode
- Maintains <15 second response time requirement

✅ **Principle V - Report Template System**
- Uses existing order acknowledgement template
- No changes to report generation logic
- Search results display in existing OrderListView

✅ **Principle VI - Minimal UI with Error Visibility**
- Advanced search dialog follows existing UI patterns
- Clear validation messages for invalid filter combinations
- Loading states and timeout handling consistent with current implementation

### Scope Boundary Check

✅ **Within Constitutional Scope**:
- Extends "Customer Order Lookup" functionality (Replacement Focus)
- Provides additional search/filter capabilities for historical orders
- Maintains read-only access pattern
- No write operations or order modification

✅ **Does NOT Violate OUT OF SCOPE**:
- Not replicating Part Maintenance
- Not replicating Manufacturing Window
- Not replicating Production Management
- Not creating/modifying orders (Order Entry)
- Not integrating with AX/D365

**Rationale for Extension**: Advanced search is a natural enhancement to order lookup capability. VISUAL Enterprise users are familiar with "Query by Example" pattern. Adding this improves search precision without violating read-only constraint or expanding into out-of-scope modules.

### Gate Status: ✅ PASS

All constitutional principles satisfied. Extension aligns with "targeted replacement of Customer Order Lookup functionality" scope.

## Project Structure

### Documentation (this feature)

```text
specs/001-visual-order-lookup/
├── plan.md              # This file (updated)
├── spec.md              # Feature spec (will be updated with advanced search user stories)
├── research.md          # Exists (will add query builder patterns research)
├── research-gui-redesign.md  # Exists (UI patterns)
├── data-model.md        # Exists (will add AdvancedSearchFilter entity)
├── quickstart.md        # Exists (will add advanced search test scenarios)
├── contracts/           # Exists (will add advanced-search-filters.sql)
│   └── database-schema.sql
├── checklists/          # Exists
│   └── requirements.md
└── tasks.md             # Exists (will be updated via /speckit.tasks)
```

### Source Code (repository root)

```text
visual-order-lookup/
├── visual_order_lookup/
│   ├── main.py                 # Application entry point
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py     # Main application window
│   │   ├── order_list_view.py # Order table display
│   │   ├── order_detail_view.py # Order acknowledgement
│   │   ├── search_panel.py    # Search controls (WILL EXTEND)
│   │   ├── advanced_search_dialog.py  # NEW - Advanced search dialog
│   │   └── dialogs.py         # Error dialogs
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # Database connection
│   │   ├── models.py          # Data models (WILL ADD AdvancedSearchFilter)
│   │   └── queries.py         # SQL queries (WILL ADD advanced_search())
│   ├── services/
│   │   ├── __init__.py
│   │   ├── order_service.py   # Business logic (WILL ADD advanced search method)
│   │   └── report_service.py  # Report generation
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── config.py          # Configuration
│   │   ├── formatters.py      # Date/currency formatting
│   │   └── query_builder.py   # NEW - Dynamic SQL WHERE clause builder
│   ├── templates/
│   │   └── order_acknowledgement.html
│   └── resources/             # Icons, styles
├── tests/
│   ├── unit/
│   │   ├── test_query_builder.py  # NEW - Query builder tests
│   │   ├── test_order_service.py  # WILL ADD advanced search tests
│   │   └── ...
│   ├── integration/
│   │   └── test_advanced_search_integration.py  # NEW
│   └── fixtures/
├── .env                        # Configuration (not in Git)
├── .env.example                # Template
├── requirements.txt            # Dependencies
├── requirements-dev.txt        # Dev dependencies
├── pytest.ini                  # Test configuration
├── pyproject.toml              # Project metadata
└── README.md                   # Usage documentation (WILL UPDATE)
```

**Structure Decision**: Single project structure maintained. Advanced search extends existing `ui/search_panel.py` with new dialog component. Query builder utility added as separate module for testability.

## Complexity Tracking

**No constitutional violations requiring justification.**

All complexity added serves core order lookup functionality:
- Advanced search improves search precision (reduces time to find orders)
- Query-by-Example pattern familiar to VISUAL Enterprise users (reduces training)
- Dynamic query builder maintains parameterized queries (security requirement)
- Modal dialog pattern consistent with existing error dialogs (UI consistency)

---

## Phase 0: Research & Technology Decisions

### 0.1 Dynamic SQL Query Building Pattern

**Decision**: Implement `QueryBuilder` utility class with fluent API for safe WHERE clause generation

**Rationale**:
- Prevents SQL injection via parameterized queries
- Allows conditional inclusion of filters (only add WHERE clauses for non-empty fields)
- Testable independently of UI and database
- Supports complex conditions (ranges, LIKE, IN clauses)

**Alternatives Considered**:
- SQLAlchemy query builder: Too heavyweight for simple SELECT queries, adds dependency
- String concatenation: Unsafe, prone to SQL injection
- ORM (SQLAlchemy Core): Overkill for read-only queries, adds complexity

**Implementation Approach**:
```python
class QueryBuilder:
    def __init__(self, base_query: str):
        self.base_query = base_query
        self.where_clauses = []
        self.parameters = []

    def add_equals(self, column: str, value: Any) -> 'QueryBuilder':
        if value is not None and value != "":
            self.where_clauses.append(f"{column} = ?")
            self.parameters.append(value)
        return self

    def add_like(self, column: str, value: str) -> 'QueryBuilder':
        if value:
            self.where_clauses.append(f"{column} LIKE ?")
            self.parameters.append(f"%{value}%")
        return self

    def add_range(self, column: str, min_val: Any, max_val: Any) -> 'QueryBuilder':
        if min_val is not None:
            self.where_clauses.append(f"{column} >= ?")
            self.parameters.append(min_val)
        if max_val is not None:
            self.where_clauses.append(f"{column} <= ?")
            self.parameters.append(max_val)
        return self

    def build(self) -> Tuple[str, List[Any]]:
        if not self.where_clauses:
            return self.base_query, []
        where_clause = " AND ".join(self.where_clauses)
        full_query = f"{self.base_query} WHERE {where_clause}"
        return full_query, self.parameters
```

### 0.2 Advanced Search Dialog Design

**Decision**: Use QDialog modal with QFormLayout for filter fields

**Rationale**:
- Modal dialog focuses user on search criteria before executing query
- QFormLayout provides clean label-field pairs
- Consistent with existing dialogs.py error dialogs
- Easy to add/remove filter fields as needed

**Alternatives Considered**:
- Dockable widget: Too permanent, clutters main window
- Expanding sidebar: Complex interaction, not PyQt6 standard
- Inline filters in main window: No space in current layout

**UI Layout**:
```
┌─────────────────────────────────────┐
│ Advanced Search                  [X]│
├─────────────────────────────────────┤
│ Order ID:         [_______________] │
│ Customer ID:      [_______________] │
│ Customer Name:    [_______________] │
│ Status:           [▼Closed        ] │
│ Salesrep ID:      [_______________] │
│ Total Amount:                       │
│   Min: [_______]  Max: [_______]   │
│ Currency:         [▼USD           ] │
│ Bill To Name:     [_______________] │
│ Last Order Date:                    │
│   From: [📅____]  To: [📅____]     │
│ Create Date:                        │
│   From: [📅____]  To: [📅____]     │
│                                     │
│ [Clear All] [Cancel] [Search]      │
└─────────────────────────────────────┘
```

### 0.3 Filter Field Validation

**Decision**: Client-side validation before query execution

**Rationale**:
- Prevents invalid queries from reaching database
- Immediate user feedback
- Reduces database load from malformed queries

**Validation Rules**:
- Date ranges: Start date <= End date
- Amount ranges: Min amount <= Max amount
- Required fields: None (all filters optional)
- Max combined filters: 10 (prevent overly complex queries)

### 0.4 Search Result Handling

**Decision**: Reuse existing `OrderListView` for displaying advanced search results

**Rationale**:
- Consistent user experience
- No duplicate code
- Existing sorting/selection logic works
- Same performance characteristics (handles 1000+ rows)

**Integration**: Advanced search populates same `OrderSummary` list as existing searches

---

## Phase 1: Design Artifacts

### 1.1 Data Model Extensions

**File**: `specs/001-visual-order-lookup/data-model.md` (to be updated)

**New Entity**: `AdvancedSearchFilter`

```python
@dataclass
class AdvancedSearchFilter:
    """Represents user-selected filters for advanced search."""
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None  # e.g., "Closed", "Open"
    salesrep_id: Optional[str] = None
    total_amount_min: Optional[Decimal] = None
    total_amount_max: Optional[Decimal] = None
    currency_id: Optional[str] = None
    bill_to_name: Optional[str] = None
    last_order_date_from: Optional[date] = None
    last_order_date_to: Optional[date] = None
    create_date_from: Optional[date] = None
    create_date_to: Optional[date] = None

    def is_empty(self) -> bool:
        """Returns True if no filters are set."""
        return all(getattr(self, field.name) is None
                   for field in fields(self))

    def validate(self) -> Tuple[bool, str]:
        """Validates filter combinations. Returns (is_valid, error_message)."""
        if self.total_amount_min and self.total_amount_max:
            if self.total_amount_min > self.total_amount_max:
                return False, "Minimum amount cannot exceed maximum amount"

        if self.last_order_date_from and self.last_order_date_to:
            if self.last_order_date_from > self.last_order_date_to:
                return False, "Start date cannot be after end date"

        if self.create_date_from and self.create_date_to:
            if self.create_date_from > self.create_date_to:
                return False, "Create start date cannot be after create end date"

        return True, ""
```

### 1.2 Database Contracts

**File**: `specs/001-visual-order-lookup/contracts/advanced-search-query.sql` (to be created)

```sql
-- Advanced Search Query Template
-- Dynamically built WHERE clause based on user-selected filters

SELECT
    co.ID AS order_id,
    co.ORDER_DATE AS order_date,
    co.CUSTOMER_PO_REF AS customer_po_ref,
    co.TOTAL_AMT_ORDERED AS total_amount,
    co.CURRENCY_ID AS currency_id,
    co.STATUS AS status,
    co.SALESREP_ID AS sales_rep,
    co.LAST_SHIPPED_DATE AS last_order_date,
    co.CREATE_DATE AS create_date,
    c.ID AS customer_id,
    c.NAME AS customer_name,
    c.BILL_TO_NAME AS bill_to_name
FROM CUSTOMER_ORDER co WITH (NOLOCK)
INNER JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
WHERE 1=1
    -- Dynamic conditions added by QueryBuilder:
    -- AND co.ID = ?                              -- if order_id filter set
    -- AND c.ID = ?                               -- if customer_id filter set
    -- AND c.NAME LIKE ?                          -- if customer_name filter set
    -- AND co.STATUS = ?                          -- if status filter set
    -- AND co.SALESREP_ID = ?                     -- if salesrep_id filter set
    -- AND co.TOTAL_AMT_ORDERED >= ?              -- if total_amount_min set
    -- AND co.TOTAL_AMT_ORDERED <= ?              -- if total_amount_max set
    -- AND co.CURRENCY_ID = ?                     -- if currency_id filter set
    -- AND c.BILL_TO_NAME LIKE ?                  -- if bill_to_name filter set
    -- AND co.LAST_SHIPPED_DATE >= ?              -- if last_order_date_from set
    -- AND co.LAST_SHIPPED_DATE <= ?              -- if last_order_date_to set
    -- AND co.CREATE_DATE >= ?                    -- if create_date_from set
    -- AND co.CREATE_DATE <= ?                    -- if create_date_to set
ORDER BY co.ORDER_DATE DESC
OFFSET 0 ROWS
FETCH NEXT 1000 ROWS ONLY;  -- Limit results to prevent performance issues
```

### 1.3 UI Component Specifications

**File**: `visual_order_lookup/ui/advanced_search_dialog.py` (to be created)

**Class**: `AdvancedSearchDialog(QDialog)`

**Public Methods**:
- `__init__(parent)`: Initialize dialog with empty filters
- `get_filters() -> AdvancedSearchFilter`: Return user-selected filters
- `clear_filters()`: Reset all filter fields to empty
- `exec_() -> int`: Show modal dialog, return QDialog.Accepted or QDialog.Rejected

**Signals**:
- `search_requested(AdvancedSearchFilter)`: Emitted when Search button clicked

**Validation**:
- Real-time validation on field changes (highlight invalid fields in red)
- Disable Search button if validation fails
- Show validation error message below invalid field

### 1.4 Service Layer Extensions

**File**: `visual_order_lookup/services/order_service.py` (to be updated)

**New Method**: `advanced_search(filter: AdvancedSearchFilter) -> List[OrderSummary]`

**Responsibilities**:
1. Validate filter using `filter.validate()`
2. Check if filter is empty using `filter.is_empty()` → return error
3. Use QueryBuilder to generate SQL and parameters
4. Execute parameterized query via DatabaseConnection
5. Convert rows to `OrderSummary` DTOs
6. Return list (max 1000 results)

**Error Handling**:
- Invalid filter → raise ValueError with validation message
- Database timeout → raise TimeoutError
- Connection failure → raise ConnectionError
- No results → return empty list (not an error)

### 1.5 Quickstart Test Scenarios

**File**: `specs/001-visual-order-lookup/quickstart.md` (to be updated)

**New Test Scenario**: Advanced Search

```markdown
## Advanced Search Test Scenario

### Prerequisites
- Application running and connected to database
- Main window displayed with order list

### Test Steps

1. **Open Advanced Search Dialog**
   - Click "Advanced Search" button (or menu item)
   - Verify modal dialog appears with all filter fields empty
   - Verify Search button is enabled (no filters required)

2. **Single Filter Search**
   - Enter Customer Name: "TRANE"
   - Click Search
   - Verify results list shows only orders for customers containing "TRANE"
   - Verify results load within 15 seconds

3. **Multiple Filter Search**
   - Click "Advanced Search" again
   - Enter Customer Name: "TRANE"
   - Set Status: "Closed"
   - Set Last Order Date From: "01/01/2000"
   - Set Last Order Date To: "12/31/2010"
   - Click Search
   - Verify results show only closed TRANE orders from 2000-2010
   - Verify results load within 15 seconds

4. **Amount Range Search**
   - Click "Advanced Search"
   - Set Total Amount Min: "500000"
   - Set Total Amount Max: "2000000"
   - Click Search
   - Verify all results have total amount between $500K and $2M
   - Verify results sorted by date descending

5. **Validation Test**
   - Click "Advanced Search"
   - Set Last Order Date From: "01/01/2020"
   - Set Last Order Date To: "01/01/2010"
   - Verify error message appears: "Start date cannot be after end date"
   - Verify Search button is disabled
   - Clear filters
   - Verify Search button is re-enabled

6. **Empty Results**
   - Click "Advanced Search"
   - Enter Order ID: "99999999" (non-existent)
   - Click Search
   - Verify message displays: "No orders found matching search criteria"
   - Verify suggestion to try different filters

7. **Clear Filters**
   - Click "Advanced Search"
   - Fill in several filter fields
   - Click "Clear All" button
   - Verify all fields reset to empty
   - Click Cancel
   - Verify returns to main window (no search executed)

### Expected Results
- All advanced searches complete within 15 seconds
- Validation prevents invalid filter combinations
- Results display in existing order list view
- Clicking any result opens order acknowledgement (existing behavior)
```

---

## Phase 2: Implementation Tracking

Implementation will be tracked via `/speckit.tasks` command after this plan is complete.

**Estimated Task Phases**:
1. **Phase A**: QueryBuilder utility implementation and unit tests
2. **Phase B**: AdvancedSearchFilter data model and validation
3. **Phase C**: Advanced search SQL query in queries.py
4. **Phase D**: OrderService.advanced_search() method
5. **Phase E**: AdvancedSearchDialog UI component
6. **Phase F**: Integration with main window and search panel
7. **Phase G**: Integration testing and error handling
8. **Phase H**: Documentation updates (README, quickstart)

**Parallel Opportunities**:
- Phase A and Phase B can be developed in parallel (different modules)
- Phase C and Phase D can be developed in parallel (query writing + service method)
- Phase E can start after Phase B (UI needs data model)

---

## Summary & Next Steps

This plan extends the Visual Database Order Lookup application with **Advanced Search (Query-by-Example)** functionality from VISUAL Enterprise 6.3.8.014, while maintaining all constitutional requirements:

✅ Read-only database access (SELECT queries only)
✅ Local-first architecture (PyQt6 modal dialog)
✅ <15 second search response time
✅ Minimal UI with clear error messages
✅ Within scope of "Customer Order Lookup" replacement

**Generated Artifacts**:
- `plan.md`: This document ✅
- `research.md`: Will be updated with query builder patterns
- `data-model.md`: Will add AdvancedSearchFilter entity
- `contracts/advanced-search-query.sql`: Will create SQL template
- `quickstart.md`: Will add advanced search test scenarios

**Next Command**: Run `/speckit.tasks` to generate implementation task list

**Branch**: `001-visual-order-lookup` (extends existing feature)
**Estimated Effort**: 2-3 days development + 1 day testing
