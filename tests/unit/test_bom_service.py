"""Unit tests for BOMService."""

import pytest
from unittest.mock import Mock, MagicMock
from visual_order_lookup.services.bom_service import BOMService
from visual_order_lookup.database.models import BOMNode, Job


class TestBOMServiceInitialization:
    """Test BOMService initialization."""

    def test_initialization(self):
        """Test that BOMService initializes with database connection."""
        mock_db = Mock()
        service = BOMService(mock_db)
        assert service.db_connection == mock_db


class TestBOMNodeColorCalculation:
    """Test BOMNode color calculation logic."""

    def test_assembly_node_color(self):
        """Test that assembly nodes return blue color."""
        node = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="0",
            base_lot_id="8113/26",
            part_id="ASM001",
            part_description="Assembly",
            node_type="assembly",
            is_fabricated=True,
            is_purchased=False,
            depth=0
        )
        assert node.display_color == "blue"

    def test_manufactured_node_color(self):
        """Test that manufactured nodes return black color."""
        node = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="1",
            base_lot_id="8113/26",
            part_id="M001",
            part_description="Manufactured Part",
            node_type="manufactured",
            is_fabricated=True,
            is_purchased=False,
            depth=1
        )
        assert node.display_color == "black"

    def test_purchased_node_color(self):
        """Test that purchased nodes return red color."""
        node = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="2",
            base_lot_id="8113/26",
            part_id="P001",
            part_description="Purchased Part",
            node_type="purchased",
            is_fabricated=False,
            is_purchased=True,
            depth=1
        )
        assert node.display_color == "red"


class TestBOMNodeProperties:
    """Test BOMNode property calculations."""

    def test_is_assembly_property(self):
        """Test is_assembly property for different node types."""
        assembly = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="0",
            base_lot_id="8113/26",
            part_id="ASM001",
            part_description="Assembly",
            node_type="assembly",
            is_fabricated=True,
            is_purchased=False,
            depth=0
        )
        assert assembly.is_assembly is True

        manufactured = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="1",
            base_lot_id="8113/26",
            part_id="M001",
            part_description="Manufactured Part",
            node_type="manufactured",
            is_fabricated=True,
            is_purchased=False,
            depth=1
        )
        assert manufactured.is_assembly is False

    def test_full_lot_id_property(self):
        """Test full_lot_id property calculation."""
        node = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="1",
            base_lot_id="8113",
            part_id="M001",
            part_description="Part",
            node_type="manufactured",
            is_fabricated=True,
            is_purchased=False,
            depth=1
        )
        assert node.full_lot_id == "8113/26"

    def test_lazy_loading_flag(self):
        """Test that is_loaded flag defaults to False."""
        node = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="0",
            base_lot_id="8113/26",
            part_id="ASM001",
            part_description="Assembly",
            node_type="assembly",
            is_fabricated=True,
            is_purchased=False,
            depth=0
        )
        assert node.is_loaded is False


class TestJobModel:
    """Test Job data model."""

    def test_job_initialization(self):
        """Test Job model initialization."""
        job = Job(
            job_number="8113",
            customer_id="ARCADIA",
            customer_name="ARCADIA",
            assembly_count=15
        )
        assert job.job_number == "8113"
        assert job.customer_name == "ARCADIA"
        assert job.assembly_count == 15

    def test_job_formatted_header(self):
        """Test formatted header generation."""
        job = Job(
            job_number="8113",
            customer_id="ARCADIA",
            customer_name="ARCADIA COMPANY",
            assembly_count=15
        )
        expected = "Job 8113 - ARCADIA COMPANY (15 assemblies)"
        assert job.formatted_header() == expected


class TestBOMServiceValidation:
    """Test BOMService input validation."""

    def test_empty_job_number_raises_error(self):
        """Test that empty job number raises ValueError."""
        mock_db = Mock()
        service = BOMService(mock_db)

        with pytest.raises(ValueError, match="Job number cannot be empty"):
            service.get_bom_assemblies("")

    def test_long_job_number_raises_error(self):
        """Test that excessively long job number raises ValueError."""
        mock_db = Mock()
        service = BOMService(mock_db)

        with pytest.raises(ValueError, match="Job number cannot exceed 20 characters"):
            service.get_bom_assemblies("X" * 100)

    def test_empty_lot_id_raises_error(self):
        """Test that empty lot ID raises ValueError."""
        mock_db = Mock()
        service = BOMService(mock_db)

        with pytest.raises(ValueError, match="Lot ID cannot be empty"):
            service.get_assembly_parts("8113", "")


class TestBOMServiceMocking:
    """Test BOMService with mocked database responses."""

    def test_get_bom_assemblies_returns_list(self):
        """Test that get_bom_assemblies returns list of BOMNodes."""
        mock_db = Mock()
        mock_db.execute_query = MagicMock(return_value=[
            {
                'BASE_ID': '8113',
                'LOT_ID': '26',
                'SUB_ID': '0',
                'PART_ID': 'ASM001',
                'DESCRIPTION': 'Assembly 26',
                'FABRICATED': 'Y',
                'PURCHASED': 'N'
            }
        ])

        service = BOMService(mock_db)
        result = service.get_bom_assemblies("8113")

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(node, BOMNode) for node in result)

    def test_get_assembly_parts_calls_database(self):
        """Test that get_assembly_parts executes database query."""
        mock_db = Mock()
        mock_db.execute_query = MagicMock(return_value=[])

        service = BOMService(mock_db)
        result = service.get_assembly_parts("8113", "26")

        # Verify database was called
        mock_db.execute_query.assert_called_once()
        assert isinstance(result, list)


class TestBOMServiceHierarchy:
    """Test BOM hierarchy building logic."""

    def test_hierarchy_depth_calculation(self):
        """Test that BOM nodes have correct depth values."""
        # This would test the actual implementation
        # For now, test that depth is assigned correctly in BOMNode
        root = BOMNode(
            job_number="8113",
            lot_id="00",
            sub_id="0",
            base_lot_id="8113/00",
            part_id="ROOT",
            part_description="Root Assembly",
            node_type="assembly",
            is_fabricated=True,
            is_purchased=False,
            depth=0
        )

        child = BOMNode(
            job_number="8113",
            lot_id="26",
            sub_id="1",
            base_lot_id="8113/26",
            part_id="CHILD001",
            part_description="Child Part",
            node_type="manufactured",
            is_fabricated=True,
            is_purchased=False,
            depth=1
        )

        assert root.depth == 0
        assert child.depth == 1
        assert child.depth > root.depth
