"""Report generation service using Jinja2 templates."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape

from visual_order_lookup.database.models import OrderHeader


logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating order reports using Jinja2 templates."""

    def __init__(self):
        """Initialize report service with Jinja2 environment."""
        # Get templates directory
        templates_dir = Path(__file__).parent.parent / "templates"

        # Get logo path
        self.logo_path = Path(__file__).parent.parent / "resources" / "images" / "iso9001_logo.png"

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )

        # Add custom filters
        self.env.filters['na'] = self._na_filter
        self.env.filters['currency'] = self._currency_filter

        logger.info("ReportService initialized")

    def _na_filter(self, value, default='N/A'):
        """
        Jinja2 filter to display N/A for None or empty values.

        Args:
            value: Value to check
            default: Default string to display (default: 'N/A')

        Returns:
            Value or default string
        """
        if value is None or (isinstance(value, str) and value.strip() == ''):
            return default
        return value

    def _currency_filter(self, value, currency_id='USD'):
        """
        Jinja2 filter to format currency values.

        Args:
            value: Numeric value
            currency_id: Currency identifier

        Returns:
            Formatted currency string
        """
        if value is None:
            return 'N/A'

        if currency_id == 'USD':
            return f"${value:,.2f}"
        else:
            return f"{currency_id} {value:,.2f}"

    def generate_order_acknowledgement(self, order: OrderHeader) -> str:
        """
        Generate order acknowledgement HTML report.

        Args:
            order: OrderHeader object with complete order information

        Returns:
            HTML string of rendered report

        Raises:
            Exception: If template rendering fails
        """
        try:
            # Load template
            template = self.env.get_template('order_acknowledgement.html')

            # Render template with order data
            html = template.render(
                order=order,
                now=datetime.now(),
                logo_path=str(self.logo_path.absolute())
            )

            logger.info(f"Generated order acknowledgement for order {order.order_id}")
            return html

        except Exception as e:
            logger.error(f"Error generating order acknowledgement: {e}")
            raise Exception(f"Failed to generate report: {str(e)}")

    def validate_order_data(self, order: OrderHeader) -> list[str]:
        """
        Validate order data completeness and return warnings.

        Args:
            order: OrderHeader object to validate

        Returns:
            List of warning messages (empty if all data complete)
        """
        warnings = []

        if not order.customer:
            warnings.append("Customer information is missing")
        elif not order.customer.name:
            warnings.append("Customer name is missing")

        if not order.line_items:
            warnings.append("No line items found for this order")

        if order.total_amount == 0:
            warnings.append("Order total amount is $0.00")

        return warnings
