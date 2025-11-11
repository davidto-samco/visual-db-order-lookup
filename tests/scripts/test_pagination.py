"""Test pagination functionality without database."""

import sys
from PyQt6.QtWidgets import QApplication
from visual_order_lookup.ui.part_detail_view import PartDetailView
from visual_order_lookup.database.models import WhereUsed
from datetime import date
from decimal import Decimal

def create_mock_records(count: int):
    """Create mock WhereUsed records for testing."""
    records = []
    for i in range(count):
        record = WhereUsed(
            part_number=f"F0195",
            cust_order_id=f"ORDER{i:04d}" if i % 2 == 0 else None,
            cust_order_line_no=i if i % 2 == 0 else None,
            work_order=f"WO{i:04d}" if i % 2 == 1 else None,
            transaction_date=date(2024, 1, 1 + (i % 28)),
            quantity=Decimal(str(10 + (i % 100))),
            customer_name=f"Customer {i % 50}",
            warehouse_id="MAIN",
            location_id=f"A{i % 10}-{i % 20}"
        )
        records.append(record)
    return records

def main():
    """Test the pagination display."""
    print("="*60)
    print("PAGINATION TEST - Part Detail View")
    print("="*60)

    app = QApplication(sys.argv)

    # Create the widget
    print("\n1. Creating PartDetailView widget...")
    detail_view = PartDetailView()
    detail_view.setWindowTitle("Pagination Test - F0195 (2,137 Records)")
    detail_view.resize(1000, 600)

    # Create mock data simulating F0195's 2,137 where-used records
    print("2. Creating 2,137 mock where-used records...")
    records = create_mock_records(2137)
    print(f"   Created {len(records)} mock records")

    # Test display_where_used
    print("3. Calling display_where_used()...")
    try:
        detail_view.display_where_used(records)
        print("   ✓ display_where_used() completed successfully")
    except Exception as e:
        print(f"   ✗ display_where_used() FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Show the widget
    print("4. Showing widget...")
    detail_view.show()

    # Switch to Where Used tab
    detail_view.tab_widget.setCurrentIndex(1)

    print("\n" + "="*60)
    print("SUCCESS - Widget displayed with pagination!")
    print("="*60)
    print("\nShould display:")
    print(f"  - Page 1 of 43 (2,137 total records)")
    print(f"  - First 50 records in table")
    print(f"  - Navigation buttons enabled/disabled correctly")
    print("\nClose the window to exit...")
    print("="*60 + "\n")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
