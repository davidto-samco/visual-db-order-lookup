"""Integration tests for Inventory module."""

import pytest
from decimal import Decimal
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.part_service import PartService
from visual_order_lookup.utils.config import get_config


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for tests."""
    config = get_config()
    conn = DatabaseConnection(config.connection_string)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def part_service(db_connection):
    """Create PartService instance."""
    return PartService(db_connection)


class TestPartSearch:
    """Test part search functionality."""

    def test_search_existing_part_f0195(self, part_service):
        """Test searching for existing part F0195."""
        part = part_service.search_by_part_number("F0195")

        assert part is not None, "Part F0195 should exist"
        assert part.part_number == "F0195"
        assert part.description is not None
        assert part.unit_of_measure is not None
        print(f"[OK] Part F0195 found: {part.description}")

    def test_search_existing_part_pf004(self, part_service):
        """Test searching for existing part PF004."""
        part = part_service.search_by_part_number("PF004")

        assert part is not None, "Part PF004 should exist"
        assert part.part_number == "PF004"
        assert part.description is not None
        print(f"[OK] Part PF004 found: {part.description}")

    def test_search_existing_part_pp001(self, part_service):
        """Test searching for existing part PP001."""
        part = part_service.search_by_part_number("PP001")

        assert part is not None, "Part PP001 should exist"
        assert part.part_number == "PP001"
        assert part.description is not None
        print(f"[OK] Part PP001 found: {part.description}")

    def test_search_nonexistent_part(self, part_service):
        """Test searching for non-existent part."""
        part = part_service.search_by_part_number("NONEXISTENT99999")

        assert part is None, "Non-existent part should return None"
        print("[OK] Non-existent part correctly returned None")

    def test_part_cost_calculation(self, part_service):
        """Test that part cost fields are properly calculated."""
        part = part_service.search_by_part_number("F0195")

        assert part is not None

        # Check total cost calculation
        expected_total = (
            (part.unit_material_cost or Decimal('0')) +
            (part.unit_labor_cost or Decimal('0')) +
            (part.unit_burden_cost or Decimal('0'))
        )
        assert part.total_unit_cost == expected_total
        print(f"[OK] Part F0195 total cost: {part.formatted_total_cost()}")


class TestWhereUsed:
    """Test where-used functionality."""

    def test_where_used_f0195(self, part_service):
        """Test where-used query for F0195 (should have many records)."""
        records = part_service.get_where_used("F0195")

        assert isinstance(records, list)
        assert len(records) > 0, "F0195 should have usage records"

        # Verify record structure
        first_record = records[0]
        assert first_record.part_number == "F0195"
        assert first_record.transaction_date is not None
        assert first_record.quantity > 0

        print(f"[OK] Found {len(records)} where-used records for F0195")

    def test_where_used_pf004(self, part_service):
        """Test where-used query for PF004."""
        records = part_service.get_where_used("PF004")

        assert isinstance(records, list)
        print(f"[OK] Found {len(records)} where-used records for PF004")

    def test_where_used_nonexistent_part(self, part_service):
        """Test where-used query for non-existent part."""
        records = part_service.get_where_used("NONEXISTENT99999")

        assert isinstance(records, list)
        assert len(records) == 0, "Non-existent part should have no usage records"
        print("[OK] Non-existent part correctly returned empty list")

    def test_where_used_order_reference(self, part_service):
        """Test that where-used records have proper order references."""
        records = part_service.get_where_used("F0195")

        if len(records) > 0:
            # Check that order_reference property works
            first_record = records[0]
            assert first_record.order_reference is not None
            assert len(first_record.order_reference) > 0
            print(f"[OK] Where-used record has reference: {first_record.order_reference}")


class TestPurchaseHistory:
    """Test purchase history functionality."""

    def test_purchase_history_f0195(self, part_service):
        """Test purchase history query for F0195."""
        records = part_service.get_purchase_history("F0195", limit=100)

        assert isinstance(records, list)
        assert len(records) > 0, "F0195 should have purchase history"

        # Verify record structure
        first_record = records[0]
        assert first_record.part_number == "F0195"
        assert first_record.po_number is not None
        assert first_record.vendor_name is not None
        assert first_record.quantity > 0
        assert first_record.unit_price >= 0

        print(f"[OK] Found {len(records)} purchase history records for F0195")

    def test_purchase_history_pf004(self, part_service):
        """Test purchase history query for PF004."""
        records = part_service.get_purchase_history("PF004", limit=100)

        assert isinstance(records, list)
        print(f"[OK] Found {len(records)} purchase history records for PF004")

    def test_purchase_history_limit(self, part_service):
        """Test that purchase history respects limit parameter."""
        records = part_service.get_purchase_history("F0195", limit=10)

        assert isinstance(records, list)
        assert len(records) <= 10, "Should respect limit parameter"
        print(f"[OK] Purchase history limit working: {len(records)} <= 10")

    def test_purchase_history_nonexistent_part(self, part_service):
        """Test purchase history for non-existent part."""
        records = part_service.get_purchase_history("NONEXISTENT99999", limit=100)

        assert isinstance(records, list)
        assert len(records) == 0, "Non-existent part should have no purchase history"
        print("[OK] Non-existent part correctly returned empty list")

    def test_purchase_history_line_total(self, part_service):
        """Test that line totals are calculated correctly."""
        records = part_service.get_purchase_history("F0195", limit=10)

        if len(records) > 0:
            first_record = records[0]
            # Line total should equal qty * unit price (approximately)
            calculated_total = first_record.quantity * first_record.unit_price
            # Allow small rounding differences
            assert abs(first_record.line_total - calculated_total) < Decimal('0.01')
            print(f"[OK] Purchase history line total calculation correct")


class TestPartServiceIntegration:
    """Integration tests for complete part service workflow."""

    def test_complete_part_lookup_workflow(self, part_service):
        """Test complete workflow: search part, get where-used, get purchase history."""
        part_number = "F0195"

        # Step 1: Search for part
        part = part_service.search_by_part_number(part_number)
        assert part is not None
        print(f"[OK] Step 1: Part {part_number} found")

        # Step 2: Get where-used
        where_used = part_service.get_where_used(part_number)
        assert isinstance(where_used, list)
        print(f"[OK] Step 2: Retrieved {len(where_used)} where-used records")

        # Step 3: Get purchase history
        purchase_history = part_service.get_purchase_history(part_number, limit=50)
        assert isinstance(purchase_history, list)
        print(f"[OK] Step 3: Retrieved {len(purchase_history)} purchase records")

        print(f"[OK] Complete workflow test passed for {part_number}")

    def test_multiple_part_lookups(self, part_service):
        """Test looking up multiple parts sequentially."""
        part_numbers = ["F0195", "PF004", "PP001"]

        for part_number in part_numbers:
            part = part_service.search_by_part_number(part_number)
            assert part is not None, f"Part {part_number} should exist"
            assert part.part_number == part_number
            print(f"[OK] Successfully looked up {part_number}")

        print(f"[OK] Multiple part lookup test passed")

    def test_error_handling_invalid_input(self, part_service):
        """Test error handling with invalid inputs."""
        # Empty string should raise ValueError
        with pytest.raises(ValueError, match="Part number cannot be empty"):
            part_service.search_by_part_number("")
        print("[OK] Empty string raises ValueError as expected")

        # Very long string should raise ValueError
        with pytest.raises(ValueError, match="Part number cannot exceed 30 characters"):
            part_service.search_by_part_number("X" * 1000)
        print("[OK] Long string raises ValueError as expected")
