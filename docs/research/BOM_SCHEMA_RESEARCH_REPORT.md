# Visual Database Schema Research Report: Engineering - Manufacturing Window (BOM Hierarchies)

**Date**: 2025-11-07
**Database**: Visual Manufacturing ERP
**Scope**: Bill of Materials (BOM) hierarchy structures for Engineering module
**Test Jobs**: 8113, 8059

---

## Executive Summary

The Visual database stores Bill of Materials (BOM) hierarchies within the **WORK_ORDER** table itself, using a combination of `BASE_ID`, `LOT_ID`, and `SUB_ID` to represent parent-child relationships. There is no separate BOM hierarchy table for job-specific assemblies. The hierarchy is encoded through:

1. **BASE_ID + LOT_ID** = Top-level assembly identifier (e.g., "8113/26")
2. **SUB_ID** = Component level within that assembly
   - `SUB_ID = 0` or `1` = Assembly header (often without PART_ID)
   - `SUB_ID >= 2` = Individual components/parts that make up the assembly

---

## 1. WORK_ORDER Table Schema

### Primary Key Fields
| Column | Type | Description |
|--------|------|-------------|
| `BASE_ID` | varchar(30) | Job/Order number (e.g., "8113") |
| `LOT_ID` | varchar(3) | Assembly/lot identifier within job (e.g., "26", "41") |
| `SUB_ID` | varchar(3) | Component sequence within assembly (0=header, 1+=components) |
| `SPLIT_ID` | varchar(3) | Split identifier |

### Part Identification Fields
| Column | Type | Description |
|--------|------|-------------|
| `PART_ID` | varchar(30) | Part number (links to PART.ID) |
| `DRAWING_ID` | varchar(30) | Drawing number for the part |
| `DRAWING_REV_NO` | varchar(8) | Drawing revision |

### Hierarchy/Structure Fields
| Column | Type | Description |
|--------|------|-------------|
| `TYPE` | char(1) | Work order type ('W' = standard work order) |
| `STATUS` | char(1) | Status ('C' = closed, 'O' = open, etc.) |
| `GLOBAL_RANK` | smallint | Ranking/ordering field |
| `DESIRED_QTY` | decimal | Quantity to manufacture |
| `RECEIVED_QTY` | decimal | Quantity completed |

### Job Linking Fields
| Column | Type | Description |
|--------|------|-------------|
| `WBS_CODE` | varchar(30) | Work breakdown structure code |
| `WBS_CUST_ORDER_ID` | varchar(15) | Links to CUSTOMER_ORDER.ID |

### Additional Fields
- Cost tracking: `EST_MATERIAL_COST`, `ACT_MATERIAL_COST`, `EST_LABOR_COST`, etc.
- Scheduling: `SCHED_START_DATE`, `SCHED_FINISH_DATE`, `DESIRED_RLS_DATE`
- Engineering: `ENGINEERED_BY`, `ENGINEERED_DATE`
- User-defined: `USER_1` through `USER_10`

**Total Columns**: 76 columns in WORK_ORDER table

---

## 2. BOM Hierarchy Structure

### How Hierarchy is Represented

The BOM hierarchy for a job is encoded as follows:

```
Job 8113
├── Assembly 8113/01 (LOT_ID = "01")
│   ├── SUB_ID = 0: Assembly header (no PART_ID)
│   ├── SUB_ID = 1: Assembly header (no PART_ID)
│   ├── SUB_ID = 2: Component part 10350
│   ├── SUB_ID = 3: Component part 10435
│   └── SUB_ID = 4+: More components...
│
├── Assembly 8113/26 (LOT_ID = "26")
│   ├── SUB_ID = 0: Assembly header (no PART_ID)
│   ├── SUB_ID = 1: Assembly header (no PART_ID)
│   ├── SUB_ID = 2: Component part 31963 (14 PASSES GREENFIELD ROLLFORMER)
│   ├── SUB_ID = 3: Component part 31927 (4 PASS INBOARD HOUSING)
│   └── SUB_ID = 4-330+: 300+ more components...
│
└── Assembly 8113/41 (LOT_ID = "41")
    └── Components...
```

### Key Findings

1. **No separate WO_COMPONENT table** - components are rows in WORK_ORDER
2. **No PARENT_LOT_ID or SUPER_LOT_ID columns** - hierarchy is by convention
3. **SUB_ID pattern**:
   - `SUB_ID = 0` and `1`: Often have no PART_ID (assembly headers/containers)
   - `SUB_ID >= 2`: Contain actual PART_ID values (components)
4. **BASE_ID + LOT_ID** forms the assembly identifier (e.g., "8113/26")
5. **PLANNING_BOM table exists** but is for generic part BOMs, not job-specific assemblies

---

## 3. PART Table Schema (for Component Metadata)

### Key Fields for BOM Display

| Column | Type | Description |
|--------|------|-------------|
| `ID` | varchar(30) | Part number (primary key) |
| `DESCRIPTION` | varchar(40) | Part description |
| `DRAWING_ID` | varchar(30) | Drawing number |
| `DRAWING_REV_NO` | varchar(8) | Drawing revision |
| `MATERIAL_CODE` | varchar(25) | Material specification (e.g., "4140") |

### Part Classification Fields

| Column | Type | Values | Description |
|--------|------|--------|-------------|
| `FABRICATED` | char(1) | 'Y'/'N' | Manufactured in-house (black in UI) |
| `PURCHASED` | char(1) | 'Y'/'N' | Purchased part (red in UI) |
| `ENGINEERING_MSTR` | varchar(3) | LOT_ID | Links to master engineering record |

### Assembly Identification

Based on sample data from job 8113:
- **Assemblies (White)**: `FABRICATED='Y'`, `PURCHASED='N'`, has subordinate parts
- **Manufactured Parts (Black)**: `FABRICATED='Y'`, `PURCHASED='N'`, no subordinates
- **Purchased Parts (Red)**: `PURCHASED='Y'`

**Note**: The system does NOT have an explicit "assembly" flag. Assembly status is inferred by:
1. Having a PART_ID at `SUB_ID = 0` or low SUB_ID
2. Having multiple child SUB_IDs
3. Potentially checking if PART_ID appears in PLANNING_BOM.PARENT_PLN_PART_ID

---

## 4. Querying BOM Hierarchies

### Query 1: Get All Top-Level Assemblies for a Job

```sql
SELECT DISTINCT
    wo.BASE_ID + '/' + wo.LOT_ID as ASSEMBLY_ID,
    wo.LOT_ID,
    wo.PART_ID,
    wo.DRAWING_ID,
    p.DESCRIPTION,
    p.FABRICATED,
    p.PURCHASED
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = '8113'
    AND wo.SUB_ID IN ('0', '1', '2')  -- Check first few SUB_IDs for assembly part
    AND wo.PART_ID IS NOT NULL
ORDER BY wo.LOT_ID
```

**Result for Job 8113**:
- Found LOT_IDs: 01, 01W, 26, 41, 56, 61, 71, 76, 81, 86, 91, 96, 97, 98, 99
- Total: 702 work orders across 15+ assemblies

### Query 2: Get All Components for a Specific Assembly

```sql
SELECT
    wo.SUB_ID,
    wo.PART_ID,
    wo.DRAWING_ID,
    wo.DESIRED_QTY,
    p.DESCRIPTION,
    p.FABRICATED,
    p.PURCHASED,
    p.MATERIAL_CODE
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = '8113'
    AND wo.LOT_ID = '26'
    AND wo.SUB_ID <> '0'
    AND wo.PART_ID IS NOT NULL
ORDER BY CAST(wo.SUB_ID AS INT)
```

**Result for 8113/26**:
- 300+ child components
- Example: SUB_ID=2: Part 31963 "14 PASSES GREENFIELD ROLLFORMER ASS'Y"
- Example: SUB_ID=3: Part 31927 "4 PASS INBOARD HOUSING ASS'Y"

### Query 3: Hierarchical Tree Query (All Levels)

```sql
WITH BOM_Tree AS (
    -- Level 0: Top assemblies
    SELECT
        wo.BASE_ID,
        wo.LOT_ID,
        wo.SUB_ID,
        wo.PART_ID,
        wo.DRAWING_ID,
        p.DESCRIPTION,
        p.FABRICATED,
        p.PURCHASED,
        0 as LEVEL,
        CAST(wo.LOT_ID + '-' + wo.SUB_ID AS VARCHAR(100)) as PATH
    FROM WORK_ORDER wo WITH (NOLOCK)
    LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
    WHERE wo.BASE_ID = '8113'
        AND wo.SUB_ID IN ('0', '1', '2')
        AND wo.PART_ID IS NOT NULL
)
SELECT
    LEVEL,
    REPLICATE('  ', LEVEL) + BASE_ID + '/' + LOT_ID as ASSEMBLY,
    PART_ID,
    DRAWING_ID,
    DESCRIPTION,
    CASE
        WHEN FABRICATED = 'Y' AND PURCHASED = 'N' THEN 'Manufactured'
        WHEN PURCHASED = 'Y' THEN 'Purchased'
        ELSE 'Unknown'
    END as PART_TYPE
FROM BOM_Tree
ORDER BY PATH
```

**Note**: This is a simplified example. True multi-level BOMs would require recursive CTEs if assemblies contain sub-assemblies.

---

## 5. Part Type Classification (Color Coding)

Based on transcript and database analysis:

| Display Color | Part Type | Database Criteria |
|---------------|-----------|-------------------|
| **White** | Assembly (main drawings) | `FABRICATED='Y'`, has child SUB_IDs, appears as low SUB_ID |
| **Black** | Manufactured parts (M parts) | `FABRICATED='Y'`, `PURCHASED='N'`, typically starts with "M" |
| **Red** | Purchased parts (P parts) | `PURCHASED='Y'` |

### Implementation Logic

```python
def get_part_type(part: Part, has_children: bool) -> str:
    """Determine display type for part in BOM."""
    if part.FABRICATED == 'Y' and not part.PURCHASED == 'Y':
        if has_children:
            return 'ASSEMBLY'  # White
        else:
            return 'MANUFACTURED'  # Black
    elif part.PURCHASED == 'Y':
        return 'PURCHASED'  # Red
    else:
        return 'UNKNOWN'
```

---

## 6. Test Data Validation

### Job 8113
- **Status**: EXISTS in CUSTOMER_ORDER
- **Total Work Orders**: 702
- **Assemblies** (distinct LOT_IDs): 15+
- **Largest Assembly**: LOT_ID="26" with 330+ components
- **Sample Assembly**: 8113/26 = "14 PASSES GREENFIELD ROLLFORMER ASS'Y"

### Job 8059
- **Status**: EXISTS
- **Total Work Orders**: 33
- **Parent-Level (SUB_ID=0)**: 4
- **Distinct LOT_IDs**: 4
- **Smaller job** with simpler structure

---

## 7. Key Tables and Relationships

### Primary Tables

1. **WORK_ORDER** (main BOM storage)
   - Contains all assemblies and components
   - Key: BASE_ID + LOT_ID + SUB_ID + SPLIT_ID
   - Links to PART via PART_ID

2. **PART** (part master data)
   - Part descriptions, drawings, material codes
   - Classification: FABRICATED, PURCHASED flags
   - Key: ID (part number)

3. **CUSTOMER_ORDER** (job/order header)
   - Order-level information
   - Links to WORK_ORDER via BASE_ID = CUSTOMER_ORDER.ID

4. **PLANNING_BOM** (generic part BOMs)
   - NOT used for job-specific assemblies
   - Contains planning-level BOM relationships
   - Columns: PARENT_PLN_PART_ID, SUBORD_PART_ID, PERCENT_PER

### Tables NOT Found

- WO_COMPONENT (does not exist)
- WO_OPERATION (does not exist)
- BOM_STRUCTURE (does not exist)
- ASSEMBLY (does not exist)

---

## 8. Implementation Recommendations

### For Engineering - Manufacturing Window Module

1. **Query Strategy**:
   - First: Get distinct LOT_IDs for BASE_ID where SUB_ID=0 (assemblies)
   - Second: For each LOT_ID, get all SUB_ID > 0 with PART_ID (components)
   - Join with PART table for descriptions, drawings, material

2. **Hierarchy Display**:
   ```
   Job 8113
   ├─ 8113/01 - 10K DOUBLE UNCOILER AIR SCHEMATICS
   │  ├─ 10350 - 10K DOUBLE UNCOILER AIR SCHEMATICS (Assembly)
   │  ├─ 10435 - MANDREL 18" LG, ASSEMBLY STANDARD (Manufactured)
   │  └─ M30249 - Guard component (Manufactured)
   ├─ 8113/26 - 14 PASSES GREENFIELD ROLLFORMER ASS'Y
   │  ├─ 31963 - 14 PASSES GREENFIELD ROLLFORMER ASS'Y (Assembly)
   │  ├─ 31927 - 4 PASS INBOARD HOUSING ASS'Y (Manufactured)
   │  └─ [328 more components...]
   ```

3. **Color Coding Logic**:
   - Check PART.FABRICATED and PART.PURCHASED flags
   - Determine if part has children (appears as parent in other SUB_IDs)
   - Apply color based on type

4. **Drawing Number Display**:
   - Use WORK_ORDER.DRAWING_ID (preferred - job-specific)
   - Fallback to PART.DRAWING_ID if WORK_ORDER.DRAWING_ID is NULL

5. **Material Display**:
   - Use PART.MATERIAL_CODE (e.g., "4140")

---

## 9. Sample SQL Query for BOM Tree

```sql
-- Get hierarchical BOM for job 8113
SELECT
    wo.BASE_ID + '/' + wo.LOT_ID as BASE_LOT_ID,
    wo.LOT_ID,
    wo.SUB_ID,
    wo.PART_ID,
    wo.DRAWING_ID,
    wo.DESIRED_QTY,
    p.DESCRIPTION,
    p.DRAWING_ID as PART_DRAWING_ID,
    p.MATERIAL_CODE,
    CASE
        WHEN p.FABRICATED = 'Y' AND p.PURCHASED <> 'Y' THEN 'M'  -- Manufactured (Black)
        WHEN p.PURCHASED = 'Y' THEN 'P'  -- Purchased (Red)
        ELSE 'A'  -- Assembly (White)
    END as PART_TYPE,
    wo.STATUS,
    wo.CREATE_DATE
FROM WORK_ORDER wo WITH (NOLOCK)
LEFT JOIN PART p WITH (NOLOCK) ON wo.PART_ID = p.ID
WHERE wo.BASE_ID = ?  -- Parameter: job number
    AND wo.TYPE = 'W'
    AND wo.PART_ID IS NOT NULL
ORDER BY
    wo.LOT_ID,
    CAST(wo.SUB_ID AS INT)
```

**Parameters**:
- `?` = Job number (e.g., '8113')

**Returns**:
- Complete BOM hierarchy with all metadata for display
- Sorted by assembly (LOT_ID) then component sequence (SUB_ID)

---

## 10. Additional Notes

### LOT_ID Suffixes
- Some LOT_IDs have suffixes like "01W" (e.g., 8113/01W)
- 'W' suffix may indicate "Weldment" or variant assembly
- Query should handle both numeric and alphanumeric LOT_IDs

### SUB_ID = 0 or 1 Pattern
- Often these rows have no PART_ID (act as container records)
- First actual part appears at SUB_ID=2 or higher
- May need to skip SUB_ID 0/1 when displaying component list

### Global Rank
- GLOBAL_RANK field exists but often NULL or same value (50)
- May not be reliable for ordering
- Use SUB_ID for component ordering instead

### WBS Fields
- WBS_CODE and WBS_CUST_ORDER_ID exist but often NULL
- May be used for project accounting integration
- Not critical for BOM display

---

## Appendix: Related Tables

### Other PART-related tables found:
- PART_ALIAS
- PART_SUBSTITUTE
- PART_LOCATION
- PART_WAREHOUSE
- PART_BINARY (potentially for drawings/attachments)
- VENDOR_PART (purchasing info)

### Inventory tables:
- INVENTORY_TRANS (tracks material movements)
- PART_LOCATION (warehouse locations)

These may be useful for enhanced features (showing inventory, vendor info, etc.) but are not required for basic BOM display.

---

**End of Report**
