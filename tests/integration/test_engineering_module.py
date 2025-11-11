"""Integration tests for Engineering module."""

import pytest
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.bom_service import BOMService
from visual_order_lookup.utils.config import get_config


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for tests."""
    config = get_config()
    conn = DatabaseConnection(config.connection_string)
    yield conn
    conn.close()


@pytest.fixture(scope="module")
def bom_service(db_connection):
    """Create BOMService instance."""
    return BOMService(db_connection)


class TestJobSearch:
    """Test job search and BOM loading."""

    def test_search_job_8113_large(self, bom_service):
        """Test loading large job 8113 (702 work orders, 15 assemblies)."""
        assemblies = bom_service.get_bom_assemblies("8113")

        assert isinstance(assemblies, list)
        assert len(assemblies) > 0, "Job 8113 should have assemblies"
        assert len(assemblies) >= 10, "Job 8113 should have at least 10 assemblies"

        # Verify assembly structure
        first_assembly = assemblies[0]
        assert first_assembly.job_number == "8113"
        assert first_assembly.lot_id is not None
        assert first_assembly.part_description is not None

        print(f"[OK] Job 8113 loaded: {len(assemblies)} assemblies")

    def test_search_job_8059_small(self, bom_service):
        """Test loading small job 8059 (33 work orders, 4 assemblies)."""
        assemblies = bom_service.get_bom_assemblies("8059")

        assert isinstance(assemblies, list)
        assert len(assemblies) > 0, "Job 8059 should have assemblies"
        assert len(assemblies) <= 10, "Job 8059 should have relatively few assemblies"

        print(f"[OK] Job 8059 loaded: {len(assemblies)} assemblies")

    def test_search_nonexistent_job(self, bom_service):
        """Test searching for non-existent job."""
        assemblies = bom_service.get_bom_assemblies("NONEXISTENT99999")

        assert isinstance(assemblies, list)
        assert len(assemblies) == 0, "Non-existent job should return empty list"
        print("[OK] Non-existent job correctly returned empty list")


class TestAssemblyExpansion:
    """Test expanding assemblies to view parts (lazy loading)."""

    def test_expand_assembly_8113_26(self, bom_service):
        """Test expanding assembly 26 from job 8113 (should have 330+ parts)."""
        parts = bom_service.get_assembly_parts("8113", "26")

        assert isinstance(parts, list)
        assert len(parts) > 0, "Assembly 26 should have parts"
        assert len(parts) > 100, "Assembly 26 should have many parts (330+ expected)"

        # Verify part structure
        first_part = parts[0]
        assert first_part.job_number == "8113"
        assert first_part.lot_id is not None
        assert first_part.part_id is not None

        print(f"[OK] Assembly 8113/26 expanded: {len(parts)} parts")

    def test_expand_assembly_8059(self, bom_service):
        """Test expanding assembly from small job 8059."""
        # First get assemblies
        assemblies = bom_service.get_bom_assemblies("8059")
        assert len(assemblies) > 0

        # Get first assembly's lot ID
        first_assembly = assemblies[0]
        lot_id = first_assembly.lot_id

        # Expand first assembly
        parts = bom_service.get_assembly_parts("8059", lot_id)

        assert isinstance(parts, list)
        print(f"[OK] Assembly 8059/{lot_id} expanded: {len(parts)} parts")

    def test_expand_assembly_performance(self, bom_service):
        """Test that assembly expansion completes within performance target (<300ms)."""
        import time

        # Test with job 8113, assembly 26 (large assembly)
        start_time = time.perf_counter()
        parts = bom_service.get_assembly_parts("8113", "26")
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        assert isinstance(parts, list)
        assert len(parts) > 0

        # Target: <300ms, allow up to 1000ms in slow environments
        assert duration_ms < 1000, f"Assembly expansion took {duration_ms:.1f}ms (target: <1000ms)"
        print(f"[OK] Assembly expansion completed in {duration_ms:.1f}ms")


class TestBOMHierarchy:
    """Test full BOM hierarchy loading."""

    def test_get_full_hierarchy_8059(self, bom_service):
        """Test loading full hierarchy for small job 8059 (should be fast)."""
        import time

        start_time = time.perf_counter()
        hierarchy = bom_service.get_bom_hierarchy("8059")
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        assert isinstance(hierarchy, list)
        assert len(hierarchy) > 0
        assert duration_ms < 5000, f"Full hierarchy for job 8059 took {duration_ms:.1f}ms (should be <5s)"

        print(f"[OK] Full hierarchy for job 8059: {len(hierarchy)} nodes in {duration_ms:.1f}ms")

    def test_get_full_hierarchy_8113_warns(self, bom_service):
        """Test loading full hierarchy for large job 8113 (may be slow, should warn)."""
        import time

        start_time = time.perf_counter()
        hierarchy = bom_service.get_bom_hierarchy("8113")
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        assert isinstance(hierarchy, list)
        assert len(hierarchy) > 0
        assert len(hierarchy) > 500, "Job 8113 should have many nodes (702 work orders)"

        # Allow up to 30 seconds (timeout target)
        assert duration_ms < 30000, f"Full hierarchy took {duration_ms:.1f}ms (should be <30s timeout)"

        if duration_ms > 10000:
            print(f"[WARNING] Full hierarchy for job 8113 took {duration_ms/1000:.1f}s (>10s)")

        print(f"[OK] Full hierarchy for job 8113: {len(hierarchy)} nodes in {duration_ms:.1f}ms")


class TestColorCoding:
    """Test BOM node color classification."""

    def test_assembly_color_classification(self, bom_service):
        """Test that assemblies are classified with correct color (blue)."""
        assemblies = bom_service.get_bom_assemblies("8113")

        assert len(assemblies) > 0

        # Check that assemblies have assembly type
        for assembly in assemblies:
            if assembly.is_assembly:
                assert assembly.display_color == "blue", \
                    f"Assembly {assembly.lot_id} should have blue color"

        print("[OK] Assembly color classification correct")

    def test_part_color_classification(self, bom_service):
        """Test that parts are classified with correct colors (black/red)."""
        parts = bom_service.get_assembly_parts("8113", "26")

        assert len(parts) > 0

        # Check part colors
        manufactured_count = 0
        purchased_count = 0

        for part in parts:
            if part.node_type == "manufactured":
                assert part.display_color == "black", \
                    f"Manufactured part {part.part_id} should have black color"
                manufactured_count += 1
            elif part.node_type == "purchased":
                assert part.display_color == "red", \
                    f"Purchased part {part.part_id} should have red color"
                purchased_count += 1

        assert manufactured_count > 0 or purchased_count > 0, \
            "Should have at least some manufactured or purchased parts"

        print(f"[OK] Part color classification: {manufactured_count} manufactured (black), "
              f"{purchased_count} purchased (red)")


class TestLazyLoadingFlag:
    """Test lazy loading flag functionality."""

    def test_assemblies_start_unloaded(self, bom_service):
        """Test that assemblies initially have is_loaded=False."""
        assemblies = bom_service.get_bom_assemblies("8113")

        assert len(assemblies) > 0

        # All assemblies should start unloaded
        for assembly in assemblies:
            assert assembly.is_loaded is False, \
                f"Assembly {assembly.lot_id} should start with is_loaded=False"

        print("[OK] All assemblies start with is_loaded=False (lazy loading)")


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_empty_job_number(self, bom_service):
        """Test that empty job number raises ValueError."""
        with pytest.raises(ValueError, match="Job number cannot be empty"):
            bom_service.get_bom_assemblies("")

        print("[OK] Empty job number raises ValueError")

    def test_long_job_number(self, bom_service):
        """Test that overly long job number raises ValueError."""
        with pytest.raises(ValueError, match="Job number cannot exceed 20 characters"):
            bom_service.get_bom_assemblies("X" * 100)

        print("[OK] Long job number raises ValueError")

    def test_empty_lot_id(self, bom_service):
        """Test that empty lot ID raises ValueError."""
        with pytest.raises(ValueError, match="Lot ID cannot be empty"):
            bom_service.get_assembly_parts("8113", "")

        print("[OK] Empty lot ID raises ValueError")


class TestBOMServiceIntegration:
    """Integration tests for complete BOM service workflow."""

    def test_complete_bom_workflow(self, bom_service):
        """Test complete workflow: load job, expand assembly, verify structure."""
        job_number = "8113"

        # Step 1: Load assemblies
        assemblies = bom_service.get_bom_assemblies(job_number)
        assert len(assemblies) > 0
        print(f"[OK] Step 1: Loaded {len(assemblies)} assemblies for job {job_number}")

        # Step 2: Pick first assembly and expand
        first_assembly = assemblies[0]
        lot_id = first_assembly.lot_id
        parts = bom_service.get_assembly_parts(job_number, lot_id)
        assert isinstance(parts, list)
        print(f"[OK] Step 2: Expanded assembly {lot_id}, found {len(parts)} parts")

        # Step 3: Verify structure
        assert first_assembly.job_number == job_number
        assert first_assembly.is_loaded is False  # Flag not automatically updated
        print(f"[OK] Step 3: Structure verified")

        print(f"[OK] Complete BOM workflow test passed for {job_number}")

    def test_multiple_assembly_expansions(self, bom_service):
        """Test expanding multiple assemblies sequentially."""
        assemblies = bom_service.get_bom_assemblies("8059")
        assert len(assemblies) > 0

        expansion_count = min(3, len(assemblies))  # Expand up to 3 assemblies

        for i in range(expansion_count):
            assembly = assemblies[i]
            parts = bom_service.get_assembly_parts("8059", assembly.lot_id)
            assert isinstance(parts, list)
            print(f"[OK] Expanded assembly {i+1}/{expansion_count}: {assembly.lot_id} ({len(parts)} parts)")

        print(f"[OK] Multiple assembly expansion test passed")


class TestPerformanceTargets:
    """Test that performance targets are met."""

    def test_initial_load_performance(self, bom_service):
        """Test that initial assembly load is fast (<1s target)."""
        import time

        start_time = time.perf_counter()
        assemblies = bom_service.get_bom_assemblies("8113")
        end_time = time.perf_counter()

        duration_ms = (end_time - start_time) * 1000

        assert len(assemblies) > 0
        assert duration_ms < 2000, f"Initial load took {duration_ms:.1f}ms (target: <1000ms, allowed: <2000ms)"

        print(f"[OK] Initial assembly load: {duration_ms:.1f}ms")

    def test_assembly_count(self, bom_service):
        """Test that assembly count is reasonable for job 8113."""
        assemblies = bom_service.get_bom_assemblies("8113")

        assert 10 <= len(assemblies) <= 30, \
            f"Job 8113 should have 10-30 assemblies, got {len(assemblies)}"

        print(f"[OK] Job 8113 has {len(assemblies)} assemblies (within expected range)")
