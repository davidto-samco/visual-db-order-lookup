# Tasks: Fix Order Report Data Fields

**Context**: Order report for 6045 is missing several fields when compared to the correct output
**Issue**: Sales Rep shows ID instead of name, Factory Acceptance Date not displayed, default Payment Terms not shown

**Root Cause Analysis**:
- DESIRED_SHIP_DATE exists in database but not mapped to Factory Acceptance Test Date field
- SALESREP_ID returns code "PSNET" but full name "PAM SNETSINGER ext.249" is not in database
- TERMS_DESCRIPTION is NULL in database, need to provide default "Due on receipt"
- Line item details (7T4, 7T2) and additional notes are NOT in database schema
- Contact Fax IS in database and IS being queried, but may not be displaying

**Organization**: Prioritized by what can be fixed programmatically

---

## Phase 1: Database Fields - Can Be Fixed (Priority: P1)

**Goal**: Fix fields that exist in database but aren't being used correctly

### Task 1: Map DESIRED_SHIP_DATE to Factory Acceptance Test Date

- [ ] T001 Update OrderHeader model to use desired_ship_date for factory_acceptance_date_estimated field in visual_order_lookup/database/models.py
  - Change property/method to return desired_ship_date value
  - Add formatted_factory_acceptance_date() method

- [ ] T002 Update order acknowledgement template to display Factory Acceptance Test Date in visual_order_lookup/templates/order_acknowledgement.html
  - Use factory_acceptance_date_estimated field
  - Format as M/D/YYYY (e.g., "3/1/2006")
  - Show "N/A" if NULL

### Task 2: Add Default Payment Terms

- [ ] T003 Update OrderHeader to provide default payment terms in visual_order_lookup/database/models.py
  - Add property that returns terms_description if not NULL, otherwise "Due on receipt"
  - This provides sensible default for orders without explicit terms

- [ ] T004 Update template to use the payment terms property in visual_order_lookup/templates/order_acknowledgement.html
  - Display payment terms with default handling

### Task 3: Verify Contact Fax Display

- [ ] T005 Check if contact_fax is being displayed in template in visual_order_lookup/templates/order_acknowledgement.html
  - Fax IS being queried (confirmed: "724-676-5926" for order 6045)
  - Ensure it's displayed in the Contact section
  - Format should match existing contact phone display

---

## Phase 2: Sales Rep Mapping - Requires Lookup Table (Priority: P2)

**Goal**: Map SALESREP_ID codes to full names with extensions

**Challenge**: SALESREP table doesn't exist in database. Full names must come from external source.

### Task 4: Create Sales Rep Lookup

- [ ] T006 Create sales rep mapping dictionary in visual_order_lookup/utils/salesrep_lookup.py
  - Hardcoded mapping: "PSNET" → "PAM SNETSINGER ext.249"
  - Can be extended with other reps as discovered
  - Falls back to showing ID if not in map

- [ ] T007 Update queries.py to use sales rep lookup in visual_order_lookup/database/queries.py
  - Import salesrep_lookup module
  - When setting sales_rep field, lookup full name from SALESREP_ID
  - Format: lookup_salesrep_name(salesrep_id)

---

## Phase 3: Data NOT in Database - Cannot Be Fixed Automatically (Priority: P3)

**Goal**: Document what cannot be fixed programmatically

### Fields That Cannot Be Retrieved:

**Line Item Detail Text** (e.g., "7T4", "7T2"):
- NOT FOUND in: CUST_ORDER_LINE.MISC_REFERENCE (shows only "ROLL")
- NOT FOUND in: CUST_ORDER_LINE.USER_1 through USER_10 (all NULL)
- NOT FOUND in: CUST_ORDER_LINE.PART_ID, CUSTOMER_PART_ID (both NULL)
- NOT FOUND in: WORK_ORDER table (no rows for order 6045)
- **Conclusion**: This data was manually typed into the original report or exists in a separate system

**Additional Line Notes** (e.g., "LINE 4714-46", "SHIP UPS ACCOUNT NUMBER: 3W353A"):
- NOT FOUND in any CUST_ORDER_LINE fields
- **Conclusion**: Manually added notes, not in database

**Project Description** (e.g., "SPARE PART ORDER"):
- NOT FOUND in: CUSTOMER_ORDER.DESCRIPTION (column doesn't exist)
- NOT FOUND in: CUSTOMER_ORDER.USER_1 through USER_5 (all NULL)
- **Conclusion**: Manually added or derived from order type

### Recommendations:

1. **Accept current output as correct** - The database only contains what it contains
2. **Add manual entry fields** - If these details are critical, add UI for users to enter them
3. **Document discrepancy** - Note in README that some fields from legacy reports are not in database

---

## Dependencies & Execution Order

### Task Dependencies

- **T001-T002**: Factory Acceptance Date (can be done together)
- **T003-T004**: Payment Terms (can be done together)
- **T005**: Contact Fax verification (independent)
- **T006-T007**: Sales Rep lookup (T007 depends on T006)

### Parallel Opportunities

- T001, T003, T005, and T006 can all be started in parallel
- T002, T004, and T007 depend on their corresponding model/data changes

---

## Implementation Strategy

### Recommended Approach

1. **Start with T001-T002** (Factory Acceptance Date) - High impact, easy fix
2. **Then T003-T004** (Payment Terms) - Simple default value
3. **Then T005** (Verify Fax) - Quick check
4. **Then T006-T007** (Sales Rep) - Requires creating lookup module
5. **Document Phase 3 items** - Let user know what can't be fixed

### Testing

After each task group, test with order 6045:
1. Run application
2. Search for order "6045"
3. Verify order acknowledgement displays correctly
4. Compare with expected output

---

## Success Criteria

- ✅ Factory Acceptance Test Date shows "3/1/2006" for order 6045
- ✅ Payment Terms shows "Due on receipt" (or database value if present)
- ✅ Contact Fax shows "724-676-5926"
- ✅ Sales Rep shows "PAM SNETSINGER ext.249" instead of "PSNET"
- ⚠️ Line detail text (7T4, 7T2) will NOT match - data not in database
- ⚠️ Additional notes will NOT match - data not in database

---

## Notes

- This is a data availability issue, not a code bug
- The correct PDF may have been manually enhanced with details not in the database
- The application can only display what exists in the SAMCO database
- Some legacy Visual software features may have relied on external data sources or manual entry
