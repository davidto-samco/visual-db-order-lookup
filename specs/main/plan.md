# Implementation Plan: Engineering Module - Work Order Hierarchy Viewer

**Branch**: `main` | **Date**: 2025-01-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/main/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Add an Engineering module providing hierarchical tree view of work order structures from Visual database. Users search by BASE_ID to view operations, requirements, labor tickets, material transactions, and WIP costs in an expandable/collapsible format matching the legacy VISUAL Enterprise Manufacturing Window. Read-only access for historical work order lookup (1985-present) needed by Engineering and Spare Parts departments.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PyQt6 (GUI framework), pyodbc (SQL Server connectivity), python-dotenv (configuration)
**Storage**: Visual SQL Server database (read-only access via WLAN)
**Testing**: pytest with fixtures for database mocking, integration tests for tree control
**Target Platform**: Windows 10/11 desktop application
**Project Type**: Single project (desktop GUI application)
**Performance Goals**:
- Work order search: <5 seconds
- Tree rendering (500 nodes): <2 seconds
- Expand/collapse: <100ms (instant feel)
- Total operation time: <10 seconds

**Constraints**:
- Read-only database access (Constitution Principle III requirement)
- No write operations to Visual database
- Lazy loading required for large trees (1000+ nodes)
- Memory footprint: <100MB for normal operation
- WLAN-only network access

**Scale/Scope**:
- Historical work orders: 40+ years (1985-present)
- Expected tree size: 50-500 nodes per work order
- Concurrent users: 5-10 (Spare Parts staff)
- Query tables: 7 core tables (WORK_ORDER, OPERATION, REQUIREMENT, PART, LABOR_TICKET, INVENTORY_TRANS, WIP_BALANCE)
- Note: Binary note tables (WORKORDER_BINARY, REQUIREMENT_BINARY) deferred to future scope

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle III: Read-Only Database Access ✅ **PASS**
- **Requirement**: No write operations (INSERT, UPDATE, DELETE, DDL)
- **Compliance**: All queries use SELECT with WITH (NOLOCK) hint (no INSERT, UPDATE, DELETE)
- **Evidence**: Feature spec explicitly states "read-only work order lookup", no edit functionality

### Principle II: Reliable Database Connection ✅ **PASS**
- **Requirement**: Graceful handling of network failures
- **Compliance**: Existing database connection infrastructure handles errors, 5-second query timeout
- **Evidence**: Reuses proven connection handling from Sales and Inventory modules

### Principle VI: Minimal UI with Error Visibility ✅ **PASS**
- **Requirement**: Simple, focused UI with visible errors
- **Compliance**: Tree view follows existing module patterns, loading states shown, errors displayed to user
- **Evidence**: Uses PyQt6 QTreeWidget (standard control), matches Inventory module styling

### Principle IV: Dual Search Capability ✅ **PASS** (adapted)
- **Requirement**: Multiple search modes for customer service
- **Compliance**: BASE_ID search with partial match, list view shows multiple results
- **Evidence**: Engineering module extends search capability to work orders (aligned with customer service needs)

### Principle V: Report Template System ✅ **PASS** (adapted)
- **Requirement**: Structured data display
- **Compliance**: Hierarchical tree structure provides organized display format, CSV export available
- **Evidence**: Tree view template defines 7 levels, consistent presentation

### Legacy System Context ✅ **PASS**
- **Requirement**: Only replace specific VISUAL Enterprise functionality, not entire system
- **Compliance**: Replaces Manufacturing Window **lookup only**, explicitly excludes editing, scheduling, shop floor control
- **Evidence**: Feature spec clearly defines "Out of Scope" (work order creation, BOM editing, production management)

### Performance Standards ✅ **PASS**
- **Requirement**: <15 seconds total operation time
- **Compliance**: 5s search + 2s render + 100ms interactions = <10s total
- **Evidence**: Lazy loading ensures responsive UI even for large work orders

### **Overall Status**: ✅ **ALL CONSTITUTION PRINCIPLES SATISFIED**

**Justification**: This feature aligns with all Constitution principles by extending read-only lookup capability to engineering staff (similar to existing Sales/Inventory modules). No write operations (Principle III), no scope creep into Manufacturing Window editing territory (Legacy System Context), maintains simple UI pattern (Principle VI).

## Project Structure

### Documentation (this feature)

```text
specs/main/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file (/speckit.plan command output - IN PROGRESS)
├── research.md          # Phase 0 output (/speckit.plan command - pending)
├── data-model.md        # Phase 1 output (/speckit.plan command - pending)
├── quickstart.md        # Phase 1 output (/speckit.plan command - pending)
├── contracts/           # Phase 1 output (/speckit.plan command - pending)
│   ├── work_order_queries.sql
│   └── engineering_service.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
visual_order_lookup/
├── database/
│   ├── connection.py         # Existing - database connection management
│   ├── models.py             # Existing + NEW: WorkOrder, Operation, Requirement, LaborTicket, InventoryTransaction, WIPBalance
│   ├── part_queries.py       # Existing - part/BOM queries
│   └── work_order_queries.py # NEW - Engineering module queries
│
├── services/
│   ├── part_service.py       # Existing - part business logic
│   └── work_order_service.py # NEW - work order business logic
│
├── ui/
│   ├── main_window.py        # Existing - modify to add Engineering module
│   ├── inventory_module.py   # Existing - Inventory tab
│   ├── sales_module.py       # Existing - Sales tab
│   ├── engineering_module.py # NEW - Engineering tab (tree view)
│   ├── work_order_tree.py    # NEW - Custom tree widget for hierarchical display
│   └── search_panel.py       # Existing - shared search controls
│
└── utils/
    ├── config.py             # Existing - configuration loading
    └── logging.py            # Existing - application logging

tests/
├── unit/
│   ├── test_work_order_models.py    # NEW - model validation
│   ├── test_work_order_service.py   # NEW - service logic tests
│   └── test_work_order_queries.py   # NEW - query tests
│
├── integration/
│   ├── test_engineering_module.py   # NEW - UI integration tests
│   └── test_tree_performance.py     # NEW - lazy loading and performance
│
└── fixtures/
    └── work_order_samples.json      # NEW - test data for work orders
```

**Structure Decision**: Single project (desktop application) following existing visual_order_lookup module pattern. Engineering module integrates as third tab alongside Sales and Inventory, reusing database connection, models, and UI infrastructure. New files isolated to work order functionality (queries, service, UI) to minimize impact on existing modules.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations - Constitution Check passed all gates.
