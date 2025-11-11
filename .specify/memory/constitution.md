<!--
SYNC IMPACT REPORT
==================
Version Change: 1.0.0 → 1.1.0
Bump Rationale: MINOR - Added new principle (Legacy System Context) defining the original system being replaced and scope boundaries
Modified Principles: None
Added Sections:
  - Section 0 (prepended): Legacy System Context - defines VISUAL Enterprise v6.3.8.014 as the deprecated system
  - Clarified Data & Security Requirements to emphasize read-only database access pattern
Removed Sections: None
Templates Requiring Updates:
  ✅ .specify/memory/constitution.md - Updated
  ⚠ .specify/templates/spec-template.md - Should reference VISUAL Enterprise context in overview
  ⚠ .specify/templates/plan-template.md - Constitution check should validate legacy replacement scope
  ⚠ README.md - Already mentions Visual database, no changes needed
Follow-up TODOs:
  - Consider documenting additional VISUAL Enterprise modules that are explicitly OUT OF SCOPE (Part Maintenance, Manufacturing Window BOM, etc.)
  - Update spec template to include "Legacy System Replacement" section for similar projects
-->

# Visual Database Order Lookup Constitution

## Version & Governance

**Version**: 1.1.0
**Ratified**: 2025-11-04
**Last Amended**: 2025-11-06

**Amendment Procedure**: Constitution changes require explicit justification and version increment following semantic versioning (MAJOR for breaking changes to principles, MINOR for new principles/sections, PATCH for clarifications). All amendments must update dependent templates and documentation.

## Legacy System Context

### Replacement Scope

This application is a **targeted replacement** for specific functionality from **VISUAL Enterprise by Lilly Software version 6.3.8.014**, which has become deprecated and incompatible with current database infrastructure.

**Original System**: VISUAL Enterprise v6.3.8.014
- Windows-based ERP/MES/MRP system for manufacturing operations
- Comprehensive suite including: Order Management, Part Maintenance, Manufacturing Window (BOM), Production Planning, Inventory Control, Quality Management, Purchasing
- Developed by Lilly Software Associates (acquired by Infor Global Solutions)
- First manufacturing software with graphical user interface (launched 1991)

**Replacement Focus**: This application replaces ONLY the **Customer Order Lookup** functionality:
- Browse and search customer orders from historical database (1985-present)
- View customer order acknowledgements with line items
- Access ship-to and bill-to addresses
- Search by job number (exact match) or customer name (partial match)
- Filter orders by date range
- Display base/lot IDs for manufactured items

**Explicitly OUT OF SCOPE** (retained in VISUAL or migrated to AX/D365):
- Part Maintenance: Part masters, BOMs, inventory item management
- Manufacturing Window: Bill of materials hierarchies and production routing
- Production Management: Work orders, shop floor control, scheduling
- Purchasing: Vendor management, purchase orders
- Order Entry: Creating or modifying orders (read-only access only)
- Quality Management: QC processes and inspections
- Integration capabilities: Data exchange with current AX/D365 system

**Rationale**: The Spare Parts department requires access to 40+ years of historical customer order data stored in the Visual SQL Server database for customer service inquiries. The deprecated VISUAL Enterprise client cannot connect to the current database infrastructure. Rather than migrate historical data (complex and risky) or replace the entire ERP suite (massive scope), this targeted application provides essential order lookup capability with modern technology while preserving all historical data in place.

## Core Principles

### I. Local-First Architecture

The application MUST run entirely on the local machine without external dependencies beyond the Visual database connection. No cloud services, no internet requirements except WLAN for database access. All processing happens locally.

**Rationale**: Desktop deployment simplifies IT support, eliminates external service dependencies, and ensures Spare Parts staff can access orders without web browser or internet connectivity concerns.

### II. Reliable Database Connection

Database connectivity MUST be robust and handle network failures gracefully:
- Connection validation before queries
- Clear error messages for connection failures
- Automatic retry logic with timeout limits
- Connection pooling disabled for simplicity (single connection per application instance)
- Support for Visual database specific connection strings (SQL Server ODBC)

**Rationale**: The Visual database is a critical legacy system accessed over WLAN. Network interruptions are possible, and users must receive clear, actionable error messages rather than cryptic database exceptions.

### III. Read-Only Database Access (NON-NEGOTIABLE)

The application MUST maintain read-only access to the Visual database at all times:
- All queries use SELECT statements only (no INSERT, UPDATE, DELETE, or DDL)
- Parameterized queries prevent SQL injection
- No database schema modifications permitted
- No write operations to any table
- Connection uses read-only user credentials or enforced through application logic

**Rationale**: The Visual database contains authoritative historical manufacturing data spanning 40+ years. Any write operations risk data corruption in a system still used by other applications. Read-only access ensures safety while providing full lookup capability.

### IV. Dual Search Capability (NON-NEGOTIABLE)

The application MUST support multiple search modes:
- Search by customer name (partial match, case-insensitive)
- Search by job number (exact match)
- Filter by date range (start date, end date, or both)
- Browse recent orders on startup (100 most recent by default)

All search operations MUST return results within 15 seconds total or display timeout message.

**Rationale**: Customers contact Spare Parts with varying levels of information. Some remember job numbers exactly; others know only the company name or approximate purchase date ("around 1995"). Multiple search modes accommodate real-world customer service scenarios.

### V. Report Template System

All order information display MUST use a predefined report template:
- Template defines which database fields to extract
- Template specifies display format and order
- Template MUST be configurable without code changes (Jinja2 or equivalent)
- Missing data fields display as "N/A" not empty/null
- Report includes: customer info, ship-to/bill-to addresses, line items with base/lot IDs, totals

**Rationale**: Customer order acknowledgements follow a standard format familiar to staff and customers. Templating separates data retrieval from presentation, allowing business users to adjust formatting without code changes.

### VI. Minimal UI with Error Visibility

User interface MUST be simple and focused:
- Order list view with search/filter controls
- Order detail view with formatted acknowledgement
- All errors visible to user with actionable messages (never silent failures)
- Loading states clearly indicated
- Status bar showing connection state

**Rationale**: Spare Parts staff need efficient access to order data during phone calls with customers. Complex UI adds training burden and slows lookups. Visible error states enable staff to communicate issues to IT or explain delays to customers.

## Data & Security Requirements

### Data Handling
- **Read-only access**: No write operations to Visual database (see Principle III)
- **Parameterized queries**: All SQL uses prepared statements to prevent injection
- **No local caching**: Order data displayed only, not persisted locally
- **No sensitive logging**: Customer names, addresses, and order details excluded from log files
- **Error logging**: Database connection errors, query timeouts, and application crashes logged without customer data

**Rationale**: The Visual database contains sensitive customer information (company names, addresses, order amounts). Read-only access protects data integrity. Avoiding local caching prevents data synchronization issues and reduces security surface area.

### Network Security
- **WLAN connection only**: No external network access required or permitted
- **Secure credential storage**: Database credentials stored in environment variables or encrypted config (never plaintext in code)
- **Connection timeout**: Maximum 30 seconds for queries
- **No password transmission**: Connection string uses Windows authentication or encrypted SQL Server authentication

**Rationale**: WLAN-only access limits exposure. Environment variable storage follows secure configuration management practices and allows credential rotation without code deployment.

## Performance Standards

### Response Times
- **Database connection**: Maximum 10 seconds
- **Search query execution**: Maximum 5 seconds
- **Report generation**: Maximum 1 second
- **Total user wait time**: Maximum 15 seconds for any operation

**Rationale**: Staff use this application during live customer phone calls. Response times exceeding 15 seconds force customers to wait or require callbacks, degrading service quality.

### Resource Constraints
- **Memory footprint**: Under 100MB for normal operation (1000 orders displayed)
- **No background processes**: Application does not spawn background services
- **Single-threaded execution**: Acceptable for single-user desktop application
- **Graceful degradation**: Slow networks result in timeout messages, not crashes

**Rationale**: Desktop deployment on shared workstations requires lightweight resource usage. Single-threaded execution simplifies development while meeting performance needs for single-user operation.

## Quality Requirements

### Testing Gates
- **Database connection handling**: Must test with mock/disconnected scenarios
- **Both search modes**: Must test with valid and invalid inputs
- **Report template rendering**: Must test with complete and incomplete data (missing fields show "N/A")
- **Error messages**: Must be user-friendly and actionable (no stack traces to users)

**Rationale**: Network failures and incomplete data are expected conditions. Testing ensures graceful handling rather than crashes, maintaining professional user experience.

### Deployment Simplicity
- **Single executable or simple installation**: PyInstaller bundle or Python + requirements.txt
- **Configuration via single file**: .env file or equivalent for connection string
- **No database schema changes**: Works with existing Visual database as-is
- **Windows environment**: Primary target platform (Windows 10/11)

**Rationale**: IT department has limited bandwidth for application support. Simple deployment reduces support burden. No schema changes eliminate risk to production database and approval overhead.

## Compliance & Review

### Constitution Compliance Validation

All development MUST verify:
1. **Does it maintain read-only database access?** (Principle III)
2. **Does it work on WLAN with network interruptions?** (Principle II)
3. **Can users understand error messages and take action?** (Principle VI)
4. **Does it stay within scope of order lookup?** (Legacy System Context)
5. **Are response times under 15 seconds?** (Performance Standards)

### Scope Boundary Enforcement

Any feature request MUST be rejected if it:
- Writes to the Visual database (violates Principle III)
- Attempts to replicate Part Maintenance, Manufacturing Window, or other VISUAL Enterprise modules explicitly out of scope
- Requires cloud services or internet connectivity beyond WLAN database access
- Adds complexity that doesn't serve core order lookup functionality

**Rationale**: Scope creep is the primary risk for legacy system replacement projects. Clear boundaries prevent feature bloat and keep development focused on essential customer service needs.

### Review Cadence

Constitution review triggered by:
- Major feature additions (requires MINOR or MAJOR version bump)
- Principle violations requiring justification (documented in Complexity Tracking)
- User feedback indicating principle misalignment
- Technology changes affecting core principles (e.g., database migration)

---

**Governance Philosophy**: The constitution defines the MINIMUM viable requirements and MAXIMUM acceptable scope. Features that don't support order lookup for customer service should be rejected. Complexity must serve reliability and user needs, not technical preferences or feature accumulation.
