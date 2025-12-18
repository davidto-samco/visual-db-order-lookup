# Visual Order Lookup - Project Structure

## Directory Organization

```
visual-db-order-lookup/
├── .claude/                    # Claude Code configuration
├── .git/                       # Git repository
├── docs/                       # Documentation files
├── scripts/                    # Utility scripts (empty, ready for future use)
├── specs/                      # Feature specifications and plans
│   ├── 001-visual-order-lookup/
│   ├── 002-inventory-where-used-enhancement/
│   └── main/
├── tests/                      # Unit and integration tests
├── venv/                       # Python virtual environment (excluded from git)
├── visual_order_lookup/        # Main application source code
│   ├── database/               # Database connection and queries
│   │   ├── models/             # Data models (WorkOrder, Operation, Requirement, etc.)
│   │   └── queries/            # SQL query functions
│   ├── resources/              # Application resources
│   │   ├── icons/              # Icon files
│   │   ├── images/             # Image assets
│   │   ├── styles/             # QSS stylesheets
│   │   └── templates/          # HTML templates for reports
│   ├── services/               # Business logic layer
│   ├── templates/              # Additional templates
│   ├── ui/                     # User interface components
│   │   └── engineering/        # Engineering module UI
│   └── utils/                  # Utility functions
│       ├── config.py           # Configuration management
│       ├── credential_store.py # Secure credential storage
│       └── formatters.py       # Data formatting utilities
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── CLAUDE.md                   # Claude Code development guidelines
├── pyproject.toml              # Python project configuration
├── pytest.ini                  # Pytest configuration
├── README.md                   # Project documentation
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
└── visual-order-lookup.spec    # PyInstaller build specification

```

## Key Components

### Application Modules
- **Engineering Module**: Work order hierarchy viewer with detailed/simplified views
- **Sales Module**: Order lookup and acknowledgment generation
- **Inventory Module**: Part search and "where used" analysis
- **BOM Module**: Bill of Materials tree view

### Database Layer
- **Connection**: PyODBC-based SQL Server connection
- **Models**: Dataclass models for Work Orders, Operations, Requirements
- **Queries**: Optimized SQL queries with lazy loading

### UI Layer
- **PyQt6-based**: Modern desktop UI framework
- **Tree Widgets**: Hierarchical data display with expand/collapse
- **Dialogs**: Connection, search, and configuration dialogs
- **Styling**: Visual Legacy themed QSS stylesheet

### Utilities
- **Config**: .env-based configuration management
- **Credential Store**: Secure credential storage using Windows Credential Manager
- **Formatters**: Date, currency, and quantity formatting

## Clean Build Process

1. **Remove build artifacts**: `rm -rf build/ dist/`
2. **Clean Python cache**: `find . -type d -name "__pycache__" -exec rm -rf {} +`
3. **Remove logs**: `rm -rf *.log`
4. **Fresh build**: `pyinstaller visual-order-lookup.spec`

## Excluded from Git
- Virtual environment (`venv/`)
- Build artifacts (`build/`, `dist/`)
- Python cache (`__pycache__/`, `*.pyc`)
- Environment files (`.env`)
- IDE settings (`.vscode/`, `.idea/`)
- Test/diagnostic files (`test_*.py`, `diagnostic*.py`)
- Logs (`*.log`)
- Claude context (`.context/`)

## Recent Enhancements
- Engineering module detailed view with color coding
- Operation completion dates and requirement issued dates
- Bold text formatting throughout tree views
- OPERATION_BINARY and REQUIREMENT_BINARY integration
- NULL field handling for edge cases
- Secure credential storage implementation
