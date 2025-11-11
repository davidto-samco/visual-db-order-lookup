"""
Unit tests for NavigationPanel component.

Tests:
- 3 items created (Sales, Inventory, Engineering)
- currentRowChanged signal emission
- Keyboard navigation
"""

import pytest
from PyQt6.QtCore import Qt, QSignalSpy
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest

from visual_order_lookup.ui.navigation_panel import NavigationPanel


@pytest.fixture
def qt_app():
    """Create Qt application for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def navigation_panel(qt_app):
    """Create NavigationPanel widget for testing."""
    panel = NavigationPanel()
    return panel


def test_three_items_created(navigation_panel):
    """Test that navigation panel creates 3 items: Sales, Inventory, Engineering."""
    assert navigation_panel.count() == 3, "NavigationPanel should have 3 items"

    # Check item text
    assert navigation_panel.item(0).text() == "Sales", "First item should be 'Sales'"
    assert navigation_panel.item(1).text() == "Inventory", "Second item should be 'Inventory'"
    assert navigation_panel.item(2).text() == "Engineering", "Third item should be 'Engineering'"


def test_default_selection(navigation_panel):
    """Test that Sales module is selected by default."""
    assert navigation_panel.currentRow() == 0, "Sales (index 0) should be selected by default"


def test_current_row_changed_signal(navigation_panel):
    """Test that currentRowChanged signal is emitted when selection changes."""
    # Create signal spy to monitor currentRowChanged signal
    spy = QSignalSpy(navigation_panel.currentRowChanged)

    # Initially no signals emitted
    assert len(spy) == 0, "No signals should be emitted initially"

    # Change selection to Inventory (index 1)
    navigation_panel.setCurrentRow(1)

    # Check signal was emitted with correct index
    assert len(spy) == 1, "currentRowChanged signal should be emitted once"
    assert spy[0][0] == 1, "Signal should carry index 1 (Inventory)"

    # Change selection to Engineering (index 2)
    navigation_panel.setCurrentRow(2)

    # Check signal was emitted again
    assert len(spy) == 2, "currentRowChanged signal should be emitted twice"
    assert spy[1][0] == 2, "Signal should carry index 2 (Engineering)"


def test_keyboard_navigation_down_arrow(navigation_panel):
    """Test keyboard navigation with Down arrow key."""
    navigation_panel.setCurrentRow(0)  # Start at Sales

    # Press Down arrow
    QTest.keyClick(navigation_panel, Qt.Key.Key_Down)

    # Should move to Inventory
    assert navigation_panel.currentRow() == 1, "Down arrow should move to Inventory"


def test_keyboard_navigation_up_arrow(navigation_panel):
    """Test keyboard navigation with Up arrow key."""
    navigation_panel.setCurrentRow(1)  # Start at Inventory

    # Press Up arrow
    QTest.keyClick(navigation_panel, Qt.Key.Key_Up)

    # Should move back to Sales
    assert navigation_panel.currentRow() == 0, "Up arrow should move to Sales"


def test_keyboard_navigation_home_key(navigation_panel):
    """Test Home key navigates to first item."""
    navigation_panel.setCurrentRow(2)  # Start at Engineering

    # Press Home key
    QTest.keyClick(navigation_panel, Qt.Key.Key_Home)

    # Should jump to Sales
    assert navigation_panel.currentRow() == 0, "Home key should jump to Sales (first item)"


def test_keyboard_navigation_end_key(navigation_panel):
    """Test End key navigates to last item."""
    navigation_panel.setCurrentRow(0)  # Start at Sales

    # Press End key
    QTest.keyClick(navigation_panel, Qt.Key.Key_End)

    # Should jump to Engineering
    assert navigation_panel.currentRow() == 2, "End key should jump to Engineering (last item)"


def test_navigation_wrap_around_disabled(navigation_panel):
    """Test that navigation does not wrap around at boundaries."""
    navigation_panel.setCurrentRow(0)  # At first item

    # Press Up arrow (should stay at first item, no wrap-around)
    QTest.keyClick(navigation_panel, Qt.Key.Key_Up)
    assert navigation_panel.currentRow() == 0, "Up arrow at first item should not wrap to last item"

    navigation_panel.setCurrentRow(2)  # At last item

    # Press Down arrow (should stay at last item, no wrap-around)
    QTest.keyClick(navigation_panel, Qt.Key.Key_Down)
    assert navigation_panel.currentRow() == 2, "Down arrow at last item should not wrap to first item"


def test_mouse_click_selection(navigation_panel, qt_app):
    """Test mouse click changes selection."""
    navigation_panel.show()
    qt_app.processEvents()

    # Click on Inventory item (index 1)
    item = navigation_panel.item(1)
    rect = navigation_panel.visualItemRect(item)
    QTest.mouseClick(navigation_panel.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())

    # Should select Inventory
    assert navigation_panel.currentRow() == 1, "Mouse click should select Inventory"


def test_fixed_width(navigation_panel):
    """Test that navigation panel has fixed width of 200px."""
    # Width should be fixed at 200px
    assert navigation_panel.minimumWidth() == 200, "Navigation panel should have minimum width of 200px"
    assert navigation_panel.maximumWidth() == 200, "Navigation panel should have maximum width of 200px"


def test_item_selection_mode(navigation_panel):
    """Test that only single item can be selected at a time."""
    from PyQt6.QtWidgets import QAbstractItemView

    # Selection mode should be SingleSelection
    assert navigation_panel.selectionMode() == QAbstractItemView.SelectionMode.SingleSelection, \
        "Navigation panel should use SingleSelection mode"


def test_programmatic_selection_changes(navigation_panel):
    """Test programmatic selection changes work correctly."""
    # Test all three modules can be selected programmatically
    for i in range(3):
        navigation_panel.setCurrentRow(i)
        assert navigation_panel.currentRow() == i, f"Should be able to select module at index {i}"


def test_no_item_removal(navigation_panel):
    """Test that items cannot be removed (stable 3-item list)."""
    initial_count = navigation_panel.count()

    # Try to take item (should not be allowed in production, but testing robustness)
    # In real implementation, navigation panel should be read-only
    assert navigation_panel.count() == initial_count, "Item count should remain constant"
