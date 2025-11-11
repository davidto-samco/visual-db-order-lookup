# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Visual Order Lookup application.

Usage:
    pyinstaller visual-order-lookup.spec --clean

Output:
    dist/VisualOrderLookup.exe

This configuration bundles:
- Python interpreter
- PyQt6 GUI framework
- pyodbc database driver
- Jinja2 template engine
- All application code
- Template and resource files

Not included (must be installed separately):
- ODBC Driver 17 for SQL Server (end-user requirement)
- .env configuration file (for security)
"""

block_cipher = None

a = Analysis(
    ['visual_order_lookup/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include template files for report generation
        ('visual_order_lookup/templates', 'visual_order_lookup/templates'),
        # Include resource files (stylesheets, icons)
        ('visual_order_lookup/resources', 'visual_order_lookup/resources'),
        # Include .env.example as template
        ('.env.example', '.'),
    ],
    hiddenimports=[
        # PyQt6 modules
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtPrintSupport',
        # Database and templates
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
    console=False,  # Set to True for debugging (shows console window)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon file path if available (e.g., 'resources/icon.ico')
)

# Alternative: One-folder mode (faster startup, larger distribution)
# Uncomment the COLLECT section and modify EXE to use it:
#
# exe = EXE(
#     pyz,
#     a.scripts,
#     [],
#     exclude_binaries=True,
#     name='VisualOrderLookup',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     console=False,
# )
#
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='VisualOrderLookup',
# )
