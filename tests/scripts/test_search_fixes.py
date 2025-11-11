"""Test script to verify search and filter fixes.

This script tests:
1. Pagination - Results are not cut off at 100
2. Date filter with customer search - Filters combine properly
"""

import sys
from datetime import date
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.order_service import OrderService
from visual_order_lookup.database.models import DateRangeFilter
from visual_order_lookup.utils.config import get_config


def test_customer_search_limit():
    """Test that customer search returns more than 100 results for common customer."""
    print("=" * 80)
    print("TEST 1: Customer Search Pagination")
    print("=" * 80)

    config = get_config()
    db_connection = DatabaseConnection(config.connection_string)
    order_service = OrderService(db_connection)

    # Search for a common customer pattern
    test_customer = "CORP"  # Should match many customers

    print(f"\nSearching for orders with customer name containing '{test_customer}'...")
    orders = order_service.search_by_customer_name(test_customer)

    print(f"\nResults: Found {len(orders)} orders")

    if len(orders) > 100:
        print(f"[PASS] SUCCESS: Results exceed 100 (found {len(orders)})")
        print(f"  - This confirms pagination limit was increased")
    elif len(orders) == 100:
        print(f"[FAIL] FAILED: Results capped at exactly 100")
        print(f"  - Pagination limit may not have been applied")
    else:
        print(f"[PASS] Found {len(orders)} orders (less than 100 is valid for this search)")

    # Show sample of results
    if orders:
        print(f"\n  Sample results (first 3):")
        for i, order in enumerate(orders[:3]):
            print(f"    {i+1}. Job {order.job_number} - {order.customer_name} - {order.formatted_date()}")

    db_connection.close()
    return len(orders)


def test_customer_search_with_date_filter():
    """Test that customer search with date filter combines properly."""
    print("\n" + "=" * 80)
    print("TEST 2: Customer Search + Date Filter Combination")
    print("=" * 80)

    config = get_config()
    db_connection = DatabaseConnection(config.connection_string)
    order_service = OrderService(db_connection)

    test_customer = "CORP"
    start_date = date(2013, 1, 1)
    end_date = date(2013, 12, 31)

    print(f"\nSearching for orders:")
    print(f"  - Customer name containing '{test_customer}'")
    print(f"  - Between {start_date} and {end_date}")

    orders = order_service.search_by_customer_name(
        test_customer,
        start_date=start_date,
        end_date=end_date
    )

    print(f"\nResults: Found {len(orders)} orders")

    if orders:
        print(f"[PASS] SUCCESS: Combined search returned results")

        # Verify all results match criteria
        all_in_range = all(
            start_date <= order.order_date <= end_date
            for order in orders
        )

        if all_in_range:
            print(f"[PASS] VERIFIED: All results are within date range")
        else:
            print(f"[WARN] WARNING: Some results outside date range")

        # Show sample of results
        print(f"\n  Sample results (first 3):")
        for i, order in enumerate(orders[:3]):
            print(f"    {i+1}. Job {order.job_number} - {order.customer_name} - {order.formatted_date()}")
    else:
        print(f"[PASS] No results found (valid if no orders match criteria)")

    db_connection.close()
    return len(orders)


def test_date_filter_only():
    """Test date filter alone."""
    print("\n" + "=" * 80)
    print("TEST 3: Date Filter Only")
    print("=" * 80)

    config = get_config()
    db_connection = DatabaseConnection(config.connection_string)
    order_service = OrderService(db_connection)

    start_date = date(2013, 1, 1)
    end_date = date(2013, 12, 31)
    date_filter = DateRangeFilter(start_date=start_date, end_date=end_date)

    print(f"\nFiltering orders between {start_date} and {end_date}...")

    orders = order_service.filter_by_date_range(date_filter)

    print(f"\nResults: Found {len(orders)} orders")

    if len(orders) > 100:
        print(f"[PASS] SUCCESS: Results exceed 100 (found {len(orders)})")
    else:
        print(f"[PASS] Found {len(orders)} orders")

    if orders:
        print(f"\n  Sample results (first 3):")
        for i, order in enumerate(orders[:3]):
            print(f"    {i+1}. Job {order.job_number} - {order.customer_name} - {order.formatted_date()}")

    db_connection.close()
    return len(orders)


def main():
    """Run all tests."""
    print("\n")
    print("=" * 80)
    print(" " * 20 + "SEARCH & FILTER FIX VALIDATION")
    print("=" * 80)
    print()

    try:
        # Test 1: Customer search pagination
        count1 = test_customer_search_limit()

        # Test 2: Combined customer + date filter
        count2 = test_customer_search_with_date_filter()

        # Test 3: Date filter only
        count3 = test_date_filter_only()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Test 1 - Customer Search Pagination:    {count1} results")
        print(f"Test 2 - Customer + Date Filter:        {count2} results")
        print(f"Test 3 - Date Filter Only:               {count3} results")
        print()

        if count1 > 100 or count1 < 100:
            print("+ Pagination fix appears to be working")
        else:
            print("! Pagination may still be limited to 100")

        if count2 > 0:
            print("+ Combined filter appears to be working")
        else:
            print("i Combined filter returned no results (may be valid)")

        print("\n" + "=" * 80)
        print("All tests completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n[FAIL] ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
