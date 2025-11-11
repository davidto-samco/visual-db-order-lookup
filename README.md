# Visual Database Order Lookup

A Python/PyQt6 desktop application for accessing historical order data from the Visual SQL Server database. Built for Spare Parts staff to browse, search, and view customer orders from 1985 onwards.

---

> **📋 IMPORTANT NOTICE**: This application is currently **run from source only**. There is no standalone .exe file yet. All users must have Python 3.11+ installed and follow the "Run from Source" instructions below. See [Installation → Option 2](#option-2-run-from-source-required---current-method) for setup steps.

---

## Features

### Sales Module (Customer Order Entry)
- 📋 **Browse Recent Orders**: View 100 most recent orders on startup
- 📅 **Date Range Filtering**: Filter orders by start date, end date, or both
- 🔍 **Job Number Search**: Find specific orders by exact job number
- 👥 **Customer Name Search**: Search orders by partial customer name (case-insensitive)
- 📄 **Order Acknowledgement**: View formatted reports with customer info, line items, and totals
- 🖨️ **Print/Export**: Print or save orders as PDF

### Inventory Module (Part Maintenance)
- 🔍 **Part Search**: Find parts by part number (e.g., F0195, PF004, PP001)
- 📊 **Part Details**: View part master data (description, costs, inventory levels)
- 📈 **Where Used**: See usage history showing where parts were consumed
- 💰 **Purchase History**: View purchase orders with pricing and vendor information
- 📤 **Export Data**: Export part info as HTML, where-used and purchase history as CSV

### Engineering Module (Manufacturing Window)
- 🏗️ **BOM Search**: Search jobs by job number (e.g., 8113, 8059)
- 🌲 **Hierarchy Tree**: Visual BOM tree with assemblies, manufactured parts, and purchased parts
- 🔵 **Color-Coded Display**: Blue (assemblies), black (manufactured), red (purchased)
- ⚡ **Lazy Loading**: Fast initial load, parts load on-demand when expanding assemblies
- 🔄 **Expand/Collapse All**: View full BOM hierarchy or collapse to assemblies only
- 🔍 **Filter Parts**: Real-time filtering by part number or description
- 📋 **Cross-Module Navigation**: Right-click any part to view details in Inventory module

### General Features
- ⚠️ **Error Handling**: Clear, user-friendly error messages for network issues
- ⌨️ **Keyboard Shortcuts**: Ctrl+1 (Sales), Ctrl+2 (Inventory), Ctrl+3 (Engineering)
- 🎨 **Windows 95/2000 Aesthetic**: Classic retro styling for nostalgic UI experience

## Screenshots

*Visual Database Order Lookup Main Window*
- Order list displaying recent orders with job numbers, customer names, dates, and amounts
- Date range filter controls
- Search panel with job number and customer name options

## Requirements

### System Requirements

- **Operating System**: Windows 10 or Windows 11
- **Python**: 3.11 or later
- **ODBC Driver**: ODBC Driver 17 for SQL Server (or later)
- **Network**: Access to WLAN network with Visual database server (10.10.10.142:1433)
- **Memory**: Minimum 100MB available RAM
- **Disk Space**: 50MB for application and dependencies

### Database Requirements

- **Database**: SAMCO on SQL Server
- **Access**: Read-only access (SELECT queries only)
- **Connection**: WLAN network connectivity to 10.10.10.142:1433

## Installation

> **Note**: Currently, there is no pre-built executable (.exe) available. All users must run the application from source using Python. See **Option 2** below for instructions.

### Option 1: Run from Executable (Available - Requires Build)

**Status**: ✅ Executable can be built using PyInstaller. See [Development → Building Executable](#building-executable) section below for build instructions.

If you have a pre-built executable:

1. **Download** the latest release:
   - Download `VisualOrderLookup.exe` from the releases page
   - Download `.env.example` configuration template

2. **Install ODBC Driver 17 for SQL Server**:
   - Download from: https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
   - Run installer and follow prompts
   - Verify installation: Open "ODBC Data Sources (64-bit)" from Start menu → Drivers tab → Confirm "ODBC Driver 17 for SQL Server" is listed

3. **Configure Database Connection**:
   ```
   - Rename `.env.example` to `.env`
   - Place `.env` file in same directory as `VisualOrderLookup.exe`
   - Edit `.env` file with your database password:
     MSSQL_CONNECTION_STRING=Server=10.10.10.142;Port=1433;Database=SAMCO;User Id=sa;Password=YOUR_PASSWORD_HERE;TrustServerCertificate=true;
   ```

4. **Run the Application**:
   - Double-click `VisualOrderLookup.exe`
   - Application will connect to database and display recent orders

### Option 2: Run from Source (REQUIRED - Current Method)

1. **Prerequisites**:
   - **Python 3.11 or later**: Download from https://www.python.org/downloads/
     - ⚠️ **IMPORTANT**: Check "Add Python to PATH" during installation
     - Verify installation: Open Command Prompt and run `python --version`
   - **ODBC Driver 17 for SQL Server**: Download from https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
     - Run installer and follow prompts
     - Verify: Open "ODBC Data Sources (64-bit)" from Start menu → Drivers tab → Confirm driver is listed
   - **Network Access**: Ensure you're connected to WLAN with access to database server (10.10.10.142:1433)

2. **Navigate to Project Directory**:
   ```bash
   # Open Command Prompt and navigate to the project folder
   cd C:\path\to\visual-db-order-lookup
   ```

3. **Create Virtual Environment** (Recommended):
   ```bash
   # Windows Command Prompt
   python -m venv venv
   venv\Scripts\activate

   # You should see (venv) appear in your prompt
   ```

4. **Install Dependencies**:
   ```bash
   # Ensure virtual environment is activated (see (venv) in prompt)
   pip install -r requirements.txt

   # This will install PyQt6, pyodbc, Jinja2, and other dependencies
   # Installation may take 2-3 minutes
   ```

5. **Configure Database Connection**:
   ```bash
   # Copy the example configuration file
   copy .env.example .env

   # Edit .env file with your database password
   notepad .env

   # Update this line with the actual password:
   # MSSQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};Server=10.10.10.142,1433;Database=SAMCO;UID=sa;PWD=YOUR_PASSWORD_HERE;TrustServerCertificate=yes;
   ```

6. **Run Application**:
   ```bash
   # Ensure virtual environment is activated
   python -m visual_order_lookup.main

   # Application window should appear and load recent orders within 10 seconds
   # Keep Command Prompt window open while using the application
   ```

**Quick Start Summary**:
```bash
cd C:\path\to\visual-db-order-lookup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env  # Edit with database password
python -m visual_order_lookup.main
```

## Usage

### Getting Started

1. **Launch Application**:
   - Application automatically connects to Visual database
   - Opens in Sales module with 100 most recent orders
   - Loading takes approximately 5-10 seconds

2. **Switch Between Modules**:
   - Click "Sales", "Inventory", or "Engineering" in left navigation panel
   - Or use keyboard shortcuts:
     - **Ctrl+1**: Switch to Sales module
     - **Ctrl+2**: Switch to Inventory module
     - **Ctrl+3**: Switch to Engineering module

### Sales Module Usage

#### Browse Orders

- Scroll through the order list
- Click any order row to view full order acknowledgement
- Order list shows: Job Number, Customer Name, Order Date, Total Amount

### Searching for Orders

#### Search by Job Number

1. Select "Job Number" from search type dropdown
2. Enter job number (e.g., "4049")
3. Click "Search" button
4. Complete order acknowledgement displays immediately

#### Search by Customer Name

1. Select "Customer Name" from search type dropdown
2. Enter customer name or partial name (e.g., "TRANE")
3. Click "Search" button
4. List of matching orders appears
5. Click any order to view full details

### Filtering by Date Range

1. Click "Start Date" picker and select date (or leave blank for all dates from beginning)
2. Click "End Date" picker and select date (or leave blank for all dates to present)
3. Click "Filter" button
4. Order list updates to show only orders within date range (max 1000 results)
5. Click "Clear Filters" to return to recent orders view

#### Viewing Order Details

Order acknowledgement includes:
- **Header**: Job number, order date, customer PO, contact person
- **Customer Information**: Company name, shipping address
- **Billing Address**: Bill-to name and address
- **Line Items**: Quantity, base/lot ID, description, unit price, line total
- **Summary**: Grand total amount

#### Printing or Exporting

1. View any order acknowledgement
2. Click "Print" button to send to printer
3. Click "Save as PDF" to export to PDF file
4. Choose save location when prompted

### Inventory Module Usage

#### Search for Parts

1. Switch to Inventory module (Ctrl+2 or click "Inventory" in navigation)
2. Enter part number in search field (e.g., "F0195", "PF004", "PP001")
3. Press Enter or click "Search"
4. Part details display in three tabs:
   - **Part Info**: Master data (description, costs, inventory, vendor)
   - **Where Used**: Usage transactions (orders, work orders, quantities)
   - **Purchase History**: PO history with pricing and vendors

#### Export Part Data

1. View any part's information
2. Click export buttons on each tab:
   - **Part Info tab**: "Export as HTML" saves formatted part info
   - **Where Used tab**: "Export as CSV" saves usage records
   - **Purchase History tab**: "Export as CSV" saves PO history
3. Choose save location when prompted

### Engineering Module Usage

#### Search for Jobs

1. Switch to Engineering module (Ctrl+3 or click "Engineering")
2. Enter job number in search field (e.g., "8113", "8059")
3. Press Enter or click "Search"
4. BOM tree displays with assemblies collapsed

#### Navigate BOM Tree

- **Expand Assembly**: Click arrow next to assembly to load and view parts
- **Expand All**: Click "Expand All" button to load full hierarchy (warns for large jobs)
- **Collapse All**: Click "Collapse All" button to collapse all assemblies
- **Color Coding**:
  - Blue text = Assemblies (have child parts)
  - Black text = Manufactured parts (fabricated in-house)
  - Red text = Purchased parts (bought from vendors)

#### Filter BOM Parts

1. Enter text in "Filter" field (part number or description)
2. Tree updates in real-time to show only matching parts
3. Click "Clear Filter" to show all parts again

#### View Part Details

1. Right-click any part in BOM tree
2. Select "Show Part Details" from context menu
3. Application switches to Inventory module and loads that part
4. Or select "Copy Part Number" to copy to clipboard

## Test Data

Use these known data points for testing and demonstrations:

### Sales Module Test Data
- **Job 4049**: THE TRANE COMPANY order (existing test case)
- **Job 8113**: Large job with 702 work orders (BOM testing)
- **Job 8059**: Small job with 33 work orders (BOM testing)

### Inventory Module Test Data
- **F0195**: Part with 2137 usage records and 100 purchase orders (high volume)
- **PF004**: Finished part (assembly) with 10 usage records
- **PP001**: Purchased part with limited history

### Engineering Module Test Data
- **Job 8113**: Large BOM hierarchy (702 work orders) - tests lazy loading performance
- **Job 8059**: Small BOM hierarchy (33 work orders) - tests basic functionality

## Troubleshooting

### Application Won't Start

**Problem**: Running `python -m visual_order_lookup.main` shows error or nothing happens

**Solutions**:
1. **Check Python Installation**:
   - Run `python --version` in Command Prompt
   - Should show Python 3.11 or later
   - If not found, Python is not in PATH or not installed

2. **Check Virtual Environment**:
   - Ensure you see `(venv)` in your command prompt
   - If not, run `venv\Scripts\activate`

3. **Check Dependencies**:
   - Run `pip list` to see installed packages
   - Should see PyQt6, pyodbc, Jinja2
   - If missing, run `pip install -r requirements.txt`

4. **Check .env File**:
   - Ensure `.env` file exists in project root directory
   - Verify database connection string is correct
   - Check for extra spaces or formatting issues

5. **Check ODBC Driver**:
   - Verify ODBC Driver 17 is installed (see Installation prerequisites)
   - Try running: `python -c "import pyodbc; print(pyodbc.drivers())"`
   - Should list "ODBC Driver 17 for SQL Server"

### Cannot Connect to Database

**Problem**: "Unable to connect to Visual database" error appears

**Solutions**:
1. **Check WLAN Connection**:
   - Verify you're connected to the correct network
   - Ping database server: `ping 10.10.10.142`

2. **Verify Database Credentials**:
   - Open `.env` file
   - Confirm password is correct
   - Check for extra spaces or formatting issues

3. **Check Firewall**:
   - Ensure firewall allows outbound connection to port 1433
   - Contact IT if firewall rules need adjustment

4. **Test ODBC Driver**:
   - Open "ODBC Data Sources (64-bit)"
   - Click "Add" → Select "ODBC Driver 17 for SQL Server"
   - Enter server: `10.10.10.142,1433`
   - Click "Test Connection"

### Search Returns No Results

**Problem**: Search finds no orders when you know they exist

**Solutions**:
- **Job Number**: Ensure exact match (no spaces, correct number)
- **Customer Name**: Try partial name (e.g., "TRANE" instead of "THE TRANE COMPANY")
- **Date Filter**: Check date range includes the order date
- **Network Issue**: Error message appears after 30 seconds if query times out

### Application Runs Slowly

**Problem**: Queries take longer than 15 seconds

**Solutions**:
- Check WLAN signal strength (weak signal = slow queries)
- Close other applications using network bandwidth
- Try during off-peak hours if database server is busy
- Contact IT if persistent performance issues

### Missing Order Line Items

**Problem**: Order acknowledgement shows no line items

**Solutions**:
- Confirm order has line items in Visual database
- Check if line items are in separate tables (application handles this automatically)
- If order truly has no line items, message "No line items found for this order" appears

### Error: "ODBC Driver Not Found"

**Problem**: pyodbc error about missing driver

**Solutions**:
1. Download and install ODBC Driver 17 for SQL Server
2. Restart application after installation
3. Verify driver in "ODBC Data Sources (64-bit)" program

## Configuration

### Environment Variables

The `.env` file contains configuration settings:

```env
# Database Connection (REQUIRED)
MSSQL_CONNECTION_STRING=Server=10.10.10.142;Port=1433;Database=SAMCO;User Id=sa;Password=YOUR_PASSWORD;TrustServerCertificate=true;

# Application Settings (OPTIONAL)
APP_NAME=Visual Order Lookup
LOG_LEVEL=INFO
```

**Security Warning**: ⚠️ Never commit `.env` file to version control. It contains sensitive database credentials.

### Customizing Report Template

Advanced users can customize the order acknowledgement report format:

1. Locate template file: `visual-order-lookup/templates/order_acknowledgement.html`
2. Edit HTML/CSS as needed
3. Restart application to load changes
4. Template uses Jinja2 syntax for dynamic data

## Architecture

### Technology Stack

- **Language**: Python 3.11+
- **GUI Framework**: PyQt6
- **Database**: pyodbc (SQL Server connectivity)
- **Templates**: Jinja2 (report generation)
- **Configuration**: python-dotenv

### Project Structure

```
visual-order-lookup/
├── visual_order_lookup/        # Main application package
│   ├── main.py                 # Application entry point
│   ├── ui/                     # PyQt6 UI components
│   ├── database/               # Database layer (connection, queries, models)
│   ├── services/               # Business logic (order service, report service)
│   ├── templates/              # Jinja2 report templates
│   ├── utils/                  # Configuration, formatters
│   └── resources/              # Icons, stylesheets
├── tests/                      # Test suite (optional)
├── specs/                      # Design documentation
├── .env                        # Configuration (not in Git)
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

### Database Schema

Application accesses three main tables (read-only):
- **CUSTOMER_ORDER**: Order header information
- **CUSTOMER**: Customer and address information
- **CUST_ORDER_LINE**: Order line items

See `specs/001-visual-order-lookup/contracts/database-schema.sql` for complete schema documentation.

## Development

### Running from Source

See "Installation → Option 2" above for development setup.

### Running Tests

```bash
# Activate virtual environment first
venv\Scripts\activate

# Run all tests
pytest

# Run with coverage
pytest --cov=visual_order_lookup --cov-report=html

# Run specific test file
pytest tests/unit/test_order_service.py -v
```

### Building Executable

Create a standalone .exe file for distribution using PyInstaller:

#### Prerequisites

1. **Complete Development Setup**:
   ```bash
   # Ensure virtual environment is active
   venv\Scripts\activate

   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

2. **Verify Application Works**:
   ```bash
   # Test application runs from source first
   python -m visual_order_lookup.main
   ```

#### Build Process

**Step 1: Generate PyInstaller Spec File**

Create a file named `visual-order-lookup.spec` in the project root:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['visual_order_lookup/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('visual_order_lookup/templates', 'visual_order_lookup/templates'),
        ('visual_order_lookup/resources', 'visual_order_lookup/resources'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        'pyodbc',
        'jinja2',
        'dotenv',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VisualOrderLookup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True for debugging
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add .ico file path if you have an icon
)
```

**Step 2: Build Executable**

```bash
# Ensure virtual environment is active
venv\Scripts\activate

# Build with PyInstaller (takes 2-5 minutes)
pyinstaller visual-order-lookup.spec --clean

# Output location: dist/VisualOrderLookup.exe
```

**Step 3: Test Executable**

```bash
# Navigate to dist folder
cd dist

# Copy .env file for testing
copy ..\.env .env

# Run executable
VisualOrderLookup.exe

# Application should launch and connect to database
```

#### What Gets Bundled

The executable includes:
- ✅ Python interpreter (no Python installation needed on target machines)
- ✅ PyQt6 GUI framework
- ✅ pyodbc SQL Server driver bindings
- ✅ Jinja2 template engine
- ✅ All application code
- ✅ Template files (order_acknowledgement.html)
- ✅ Resource files (stylesheets, icons)
- ✅ .env.example configuration template

**Not included** (must be provided separately):
- ❌ `.env` file with database password (for security)
- ❌ ODBC Driver 17 for SQL Server (users must install separately)

#### Distribution Package

Create a distribution package for users:

```bash
# Create distribution folder
mkdir Visual-Order-Lookup-Distribution
cd Visual-Order-Lookup-Distribution

# Copy executable
copy ..\dist\VisualOrderLookup.exe .

# Copy configuration template
copy ..\.env.example .

# Create README.txt for users
notepad README.txt
```

**README.txt contents**:
```
Visual Order Lookup Application
================================

Installation:
1. Install ODBC Driver 17 for SQL Server:
   https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server

2. Rename .env.example to .env

3. Edit .env file and enter database password:
   MSSQL_CONNECTION_STRING=Server=10.10.10.142;Port=1433;Database=SAMCO;User Id=sa;Password=YOUR_PASSWORD_HERE;TrustServerCertificate=true;

4. Double-click VisualOrderLookup.exe to launch

Requirements:
- Windows 10 or Windows 11
- ODBC Driver 17 for SQL Server
- Network access to 10.10.10.142:1433

For help, see full documentation in the project repository.
```

**Zip the distribution**:
```bash
# Create zip file
powershell Compress-Archive -Path Visual-Order-Lookup-Distribution\* -DestinationPath VisualOrderLookup-v1.0.zip
```

#### Troubleshooting Build Issues

**Issue: "Failed to execute script" error**

Solution: Build with console enabled for debugging:
```python
# In visual-order-lookup.spec, change:
console=True,  # Enable console window
```

**Issue: Missing templates or resources**

Solution: Verify datas paths in spec file:
```python
datas=[
    ('visual_order_lookup/templates', 'visual_order_lookup/templates'),
    ('visual_order_lookup/resources', 'visual_order_lookup/resources'),
],
```

**Issue: ODBC driver not found in executable**

Solution: This is expected - users must install ODBC Driver 17 separately. Include installation instructions in distribution README.

**Issue: Antivirus flags executable**

Solution: This is common with PyInstaller. Options:
1. Add exception in antivirus software
2. Code-sign the executable (requires code signing certificate)
3. Submit to antivirus vendors for whitelisting

#### Build Configuration Options

**One-folder vs One-file**:

Current spec uses one-file mode (`EXE` with all data). For one-folder mode (faster startup):

```python
# Replace EXE section with:
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VisualOrderLookup',
    debug=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VisualOrderLookup',
)
```

**Debug build**:
```bash
# Build with console window for debugging
pyinstaller visual-order-lookup.spec --clean --console
```

**Reduce executable size**:
```bash
# Exclude unnecessary packages
# Add to excludes list in Analysis:
excludes=['matplotlib', 'numpy', 'pandas'],
```

#### Testing Checklist

Before distributing executable:
- [ ] Executable launches without errors
- [ ] Database connection works
- [ ] All three modules (Sales, Inventory, Engineering) functional
- [ ] Module switching works (Ctrl+1/2/3)
- [ ] Search functions work in all modules
- [ ] Export features work (PDF, CSV, HTML)
- [ ] Templates render correctly
- [ ] Stylesheets apply properly (Windows 95/2000 aesthetic)
- [ ] Error dialogs display correctly
- [ ] Application closes cleanly
- [ ] Test on clean Windows machine (no Python installed)
- [ ] Test with and without ODBC driver (should show clear error)

### Code Style

```bash
# Format code with Black
black visual_order_lookup/

# Lint with Flake8
flake8 visual_order_lookup/

# Type check with mypy
mypy visual_order_lookup/
```

## Support

### Getting Help

1. **Check this README**: Most common issues are covered in Troubleshooting section
2. **Review Documentation**: See `specs/001-visual-order-lookup/` for detailed design docs
3. **Contact Development Team**: For bugs or feature requests
4. **Ask Cindy or Efron**: Experienced users who can help with application usage

### Known Limitations

- **Read-Only Access**: Cannot create or modify orders (by design)
- **Windows Only**: Primary target is Windows (macOS/Linux may work but untested)
- **WLAN Required**: Requires network connection to database server
- **No Offline Mode**: Cannot cache data locally (by design, per security requirements)
- **Result Limits**: Date filter limited to 1000 results, customer search to 100 results

### Reporting Issues

When reporting issues, please include:
- Windows version (Windows 10 or 11)
- Python version (if running from source): `python --version`
- ODBC Driver version: Check "ODBC Data Sources (64-bit)"
- Error message (exact text or screenshot)
- Steps to reproduce the issue
- Network conditions (on WLAN or not)

## Changelog

### Version 1.0.0 (2025-11-04)

**Initial Release**

Features:
- Browse 100 most recent orders on startup
- Filter orders by date range
- Search orders by job number (exact match)
- Search orders by customer name (partial match)
- Display formatted order acknowledgement reports
- Error handling for network and database issues
- Print and PDF export functionality

Technical:
- Python 3.11+ with PyQt6 GUI
- pyodbc SQL Server connectivity
- Jinja2 template engine for reports
- Single-file Windows executable via PyInstaller

## License

Internal use only - Spare Parts department

## Credits

- **Developed for**: Spare Parts Department
- **Primary Users**: Pam, Cindy, Efron
- **Database**: Visual SQL Server (SAMCO)
- **Technology**: Python, PyQt6, SQL Server

---

**For detailed developer documentation, see**:
- Implementation Tasks: `specs/001-visual-order-lookup/tasks.md`
- Feature Specification: `specs/001-visual-order-lookup/spec.md`
- Data Model: `specs/001-visual-order-lookup/data-model.md`
- Quickstart Guide: `specs/001-visual-order-lookup/quickstart.md`
