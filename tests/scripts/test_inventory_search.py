"""Diagnostic script to test inventory module search functionality."""

import sys
import logging
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.services.part_service import PartService
from visual_order_lookup.utils.config import get_config

# Set up logging to see detailed error messages
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_part_search(part_number: str):
    """Test searching for a part number.

    Args:
        part_number: Part number to search for (e.g., 'F0195')
    """
    logger.info(f"Starting diagnostic test for part: {part_number}")

    try:
        # 1. Load configuration
        logger.info("Loading configuration...")
        config = get_config()
        logger.info(f"Connection string loaded: {config.connection_string[:50]}...")

        # 2. Create database connection
        logger.info("Creating database connection...")
        db_connection = DatabaseConnection(config.connection_string)

        # 3. Test connection
        logger.info("Testing database connection...")
        db_connection.connect()
        logger.info("✓ Database connection successful")

        # 4. Create part service
        logger.info("Creating part service...")
        part_service = PartService(db_connection)
        logger.info("✓ Part service created")

        # 5. Search for part
        logger.info(f"Searching for part: {part_number}")
        part = part_service.search_by_part_number(part_number)

        if part:
            logger.info(f"✓ Part found: {part.part_number} - {part.description}")
            logger.info(f"  Unit of Measure: {part.unit_of_measure}")
            logger.info(f"  Material Cost: {part.unit_material_cost}")
            logger.info(f"  Qty On Hand: {part.qty_on_hand}")
            logger.info(f"  Vendor: {part.vendor_name}")

            # Test where-used
            logger.info("\nTesting where-used query...")
            where_used = part_service.get_where_used(part_number)
            logger.info(f"✓ Where-used query successful: {len(where_used)} records found")

            # Test purchase history
            logger.info("\nTesting purchase history query...")
            purchase_history = part_service.get_purchase_history(part_number, limit=10)
            logger.info(f"✓ Purchase history query successful: {len(purchase_history)} records found")

            logger.info("\n" + "="*60)
            logger.info("ALL TESTS PASSED ✓")
            logger.info("="*60)
            return True
        else:
            logger.warning(f"✗ Part not found: {part_number}")
            logger.info("\nThis might be normal if the part doesn't exist in the database.")
            logger.info("Try searching for a known part like: F0195, PF004, or PP001")
            return False

    except ValueError as e:
        logger.error(f"✗ Validation error: {e}")
        logger.info("\nSuggestion: Check that the part number is valid (max 30 characters)")
        return False

    except AttributeError as e:
        logger.error(f"✗ Attribute error: {e}")
        logger.error("\nThis suggests an issue with row column access.")
        logger.error("The database connection might need additional configuration.")
        import traceback
        traceback.print_exc()
        return False

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            db_connection.close()
            logger.info("Database connection closed")
        except:
            pass


if __name__ == "__main__":
    print("\n" + "="*60)
    print("INVENTORY MODULE DIAGNOSTIC TEST")
    print("="*60 + "\n")

    # Default test part number
    test_part = "F0195"

    # Check if user provided a part number
    if len(sys.argv) > 1:
        test_part = sys.argv[1]

    print(f"Testing with part number: {test_part}")
    print("(You can specify a different part: python test_inventory_search.py PART123)\n")

    success = test_part_search(test_part)

    if success:
        print("\n✓ Inventory module search is working correctly!")
        print("\nIf the GUI is still crashing, the issue might be:")
        print("  1. PyQt6/UI thread issue")
        print("  2. Signal/slot connection problem")
        print("  3. Display/rendering issue in the GUI")
    else:
        print("\n✗ There's an issue with the part search functionality.")
        print("\nPlease review the error messages above.")

    sys.exit(0 if success else 1)
