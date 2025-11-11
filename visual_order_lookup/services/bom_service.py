"""BOM (Bill of Materials) service for Engineering module."""

import logging
from typing import List, Optional
from visual_order_lookup.database.connection import DatabaseConnection
from visual_order_lookup.database.models import BOMNode, Job

logger = logging.getLogger(__name__)


class BOMService:
    """Service for BOM-related database operations."""

    def __init__(self, db_connection: DatabaseConnection):
        """Initialize BOM service.

        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection

    def get_job_info(self, job_number: str) -> Optional[Job]:
        """Get job information for header display.

        Args:
            job_number: Job number to search for

        Returns:
            Job object or None if not found
        """
        if not job_number or not job_number.strip():
            raise ValueError("Job number cannot be empty")

        if len(job_number) > 30:
            raise ValueError("Job number cannot exceed 30 characters")

        query = """
            SELECT
                co.ID AS job_number,
                co.CUSTOMER_ID,
                c.NAME AS customer_name,
                COUNT(DISTINCT wo.LOT_ID) AS assembly_count
            FROM CUSTOMER_ORDER co WITH (NOLOCK)
            LEFT JOIN CUSTOMER c WITH (NOLOCK) ON co.CUSTOMER_ID = c.ID
            LEFT JOIN WORK_ORDER wo WITH (NOLOCK)
                ON wo.BASE_ID = co.ID AND wo.LOT_ID = '00'
            WHERE co.ID = ?
            GROUP BY co.ID, co.CUSTOMER_ID, c.NAME
        """

        try:
            logger.debug(f"Querying job info for {job_number}")
            result = self.db_connection.execute_query(query, (job_number,), timeout=30)

            if result and len(result) > 0:
                row = result[0]
                job = Job(
                    job_number=row[0],
                    customer_id=row[1],
                    customer_name=row[2] or "Unknown Customer",
                    assembly_count=row[3] or 0,
                )
                logger.debug(f"Found job: {job.job_number} with {job.assembly_count} assemblies")
                return job

            logger.debug(f"Job {job_number} not found")
            return None

        except Exception as e:
            logger.error(f"Error querying job info: {e}")
            raise

    def get_bom_assemblies(self, job_number: str) -> List[BOMNode]:
        """Get top-level assemblies for a job (LOT_ID = '00').

        Args:
            job_number: Job number to query

        Returns:
            List of BOMNode objects representing top-level assemblies
        """
        if not job_number or not job_number.strip():
            raise ValueError("Job number cannot be empty")

        query = """
            SELECT
                wo.BASE_ID AS job_number,
                wo.LOT_ID,
                wo.SUB_ID,
                wo.BASE_LOT_ID,
                wo.PART_ID,
                p.DESCRIPTION AS part_description,
                p.FABRICATED AS is_fabricated,
                p.PURCHASED AS is_purchased
            FROM WORK_ORDER wo WITH (NOLOCK)
            LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
            WHERE wo.BASE_ID = ? AND wo.LOT_ID = '00'
            ORDER BY wo.SUB_ID
        """

        try:
            logger.info(f"Loading assemblies for job {job_number}")
            results = self.db_connection.execute_query(query, (job_number,), timeout=30)

            nodes = []
            for row in results:
                is_fabricated = bool(row[6]) if row[6] is not None else False
                is_purchased = bool(row[7]) if row[7] is not None else False

                # Determine node type
                # Assemblies (LOT_ID = '00') are always treated as assemblies
                node_type = "assembly"

                node = BOMNode(
                    job_number=row[0],
                    lot_id=row[1],
                    sub_id=row[2],
                    base_lot_id=row[3],
                    part_id=row[4],
                    part_description=row[5],
                    node_type=node_type,
                    is_fabricated=is_fabricated,
                    is_purchased=is_purchased,
                    depth=0,
                    is_loaded=False,  # Lazy loading flag
                )
                nodes.append(node)

            logger.info(f"Found {len(nodes)} assemblies for job {job_number}")
            return nodes

        except Exception as e:
            logger.error(f"Error loading assemblies: {e}")
            raise

    def get_assembly_parts(self, job_number: str, lot_id: str) -> List[BOMNode]:
        """Get parts for a specific assembly (BASE_LOT_ID = lot_id).

        Args:
            job_number: Job number
            lot_id: Parent assembly's LOT_ID

        Returns:
            List of BOMNode objects representing parts in this assembly
        """
        query = """
            SELECT
                wo.BASE_ID AS job_number,
                wo.LOT_ID,
                wo.SUB_ID,
                wo.BASE_LOT_ID,
                wo.PART_ID,
                p.DESCRIPTION AS part_description,
                p.FABRICATED AS is_fabricated,
                p.PURCHASED AS is_purchased,
                -- Check if this part has children (is it an assembly?)
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM WORK_ORDER wo2 WITH (NOLOCK)
                        WHERE wo2.BASE_ID = wo.BASE_ID
                        AND wo2.BASE_LOT_ID = wo.LOT_ID
                    ) THEN 1
                    ELSE 0
                END AS has_children
            FROM WORK_ORDER wo WITH (NOLOCK)
            LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
            WHERE wo.BASE_ID = ? AND wo.BASE_LOT_ID = ?
            ORDER BY wo.SUB_ID
        """

        try:
            logger.debug(f"Loading parts for assembly {job_number}/{lot_id}")
            results = self.db_connection.execute_query(
                query, (job_number, lot_id), timeout=30
            )

            nodes = []
            for row in results:
                is_fabricated = bool(row[6]) if row[6] is not None else False
                is_purchased = bool(row[7]) if row[7] is not None else False
                has_children = bool(row[8]) if row[8] is not None else False

                # Determine node type
                if has_children:
                    node_type = "assembly"
                elif is_purchased:
                    node_type = "purchased"
                else:
                    node_type = "manufactured"

                node = BOMNode(
                    job_number=row[0],
                    lot_id=row[1],
                    sub_id=row[2],
                    base_lot_id=row[3],
                    part_id=row[4],
                    part_description=row[5],
                    node_type=node_type,
                    is_fabricated=is_fabricated,
                    is_purchased=is_purchased,
                    depth=1,  # Children are always at least depth 1
                    is_loaded=not has_children,  # Assemblies not loaded yet
                )
                nodes.append(node)

            logger.debug(f"Found {len(nodes)} parts for assembly {job_number}/{lot_id}")
            return nodes

        except Exception as e:
            logger.error(f"Error loading assembly parts: {e}")
            raise

    def get_bom_hierarchy(self, job_number: str) -> List[BOMNode]:
        """Get full BOM hierarchy for export or expand-all.

        This loads all assemblies and their parts recursively.
        Warning: Can be slow for large jobs (>700 work orders).

        Args:
            job_number: Job number to query

        Returns:
            List of BOMNode objects in hierarchical order
        """
        all_nodes = []

        try:
            logger.info(f"Loading full BOM hierarchy for job {job_number}")

            # Get top-level assemblies
            assemblies = self.get_bom_assemblies(job_number)
            all_nodes.extend(assemblies)

            # Recursively load parts for each assembly
            for assembly in assemblies:
                self._load_hierarchy_recursive(
                    job_number, assembly.lot_id, all_nodes, depth=1
                )

            logger.info(f"Loaded full hierarchy: {len(all_nodes)} total nodes")
            return all_nodes

        except Exception as e:
            logger.error(f"Error loading full hierarchy: {e}")
            raise

    def _load_hierarchy_recursive(
        self, job_number: str, lot_id: str, all_nodes: List[BOMNode], depth: int
    ):
        """Recursively load parts for an assembly.

        Args:
            job_number: Job number
            lot_id: Current assembly's LOT_ID
            all_nodes: List to append nodes to
            depth: Current depth level
        """
        parts = self.get_assembly_parts(job_number, lot_id)

        for part in parts:
            part.depth = depth
            all_nodes.append(part)

            # If this part is an assembly, recursively load its children
            if part.is_assembly:
                self._load_hierarchy_recursive(
                    job_number, part.lot_id, all_nodes, depth + 1
                )
