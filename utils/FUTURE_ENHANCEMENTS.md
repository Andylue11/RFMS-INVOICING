# Future Enhancements for Stock Receiving Feature

This document outlines planned future enhancements for the stock receiving feature.

## 1. Email Scraping for Supplier Invoice Matching

### Purpose
Scrape the accounts@atozflrooringsolutions.com.au email account to find matching supplier invoices that can help identify main orders and their invoice numbers.

### Implementation Notes
- **Email Access**: Set up IMAP/POP3 or OAuth2 access to the accounts email account
- **Invoice Extraction**: Use AI analyzer to extract invoice numbers, supplier names, and order references from email attachments
- **Matching Logic**: Match supplier invoices to consignment notes based on:
  - Supplier name
  - Order numbers (with normalization)
  - Invoice dates
  - Product/stock items
- **RFMS Integration**: Use extracted invoice numbers to search RFMS API for main orders
- **Discovery Process**: Enable further order discovery through RFMS API endpoints using invoice numbers

### Files to Create/Modify
- `utils/email_scraper.py` - Email scraping functionality
- `app.py` - Add endpoint `/api/receive-stock/check-email` or similar
- `templates/receive_stock.html` - Add UI option to check email for matches

### Configuration Needed
- Email account credentials (IMAP/POP3 settings or OAuth2)
- Email filtering rules (subject patterns, sender patterns)
- Rate limiting for email API calls

---

## 2. Accounts Payable (AP) Record Creation

### Status: ✅ **IMPLEMENTED** - Ready for Integration

### Purpose
After receiving stock, optionally create Accounts Payable records to cost the stock into the accounts payable section.

### Implementation Notes
- **✅ Method Implemented**: `create_payable()` method added to `RFMSClient` in `utils/rfms_client.py`
- **API Endpoint**: `POST /v2/payables` (requires "Plus" level API access)
- **Optional Feature**: Keep this as a separate/optional step after stock receiving
- **AP Record Creation**: Create AP records via RFMS API POST call
- **Costing**: Cost the received stock items into accounts payable
- **Integration Point**: Add checkbox/option in the receiving form to "Also create AP record"

### API Details
- **Endpoint**: `POST https://api.rfms.online/v2/payables`
- **Authorization**: Requires "Plus" level API access
- **Request Format**: Array of payable objects
- **Unique Constraint**: The combination of `supplierName` and `invoiceNumber` must be unique

### Payable Properties
- `supplierName` - Supplier (who the bill is from)
- `invoiceNumber` - Invoice # (the Supplier's invoice number) - **Must be unique per supplier**
- `invoiceDate` - Invoice Date (format: "M/D/YY" or "MM/DD/YYYY")
- `dueDate` - Due Date (format: "M/D/YY" or "MM/DD/YYYY")
- `discountableAmount` - Discountable amount
- `nonDiscountableAmount` - Non-discountable amount
- `discountRate` - Discount rate
- `linkedDocumentNumber` - Linked document number (optional)
- `internalNotes` - A/P Internal Notes
- `remittanceAdviceNotes` - A/P Remittance Advice Notes
- `detailLines` - Array of detail line objects

### Detail Line Properties
- `storeNumber` - **Must be 49 (not the display code)**
- `accountCode` - Account Code
- `subAccountCode` - Sub Code (optional)
- `amount` - Amount
- `comment` - Comment (optional)

### Files Modified
- ✅ `utils/rfms_client.py` - `create_payable()` method implemented
- ⏳ `app.py` - Update `/api/receive-stock/receive` endpoint to optionally create AP records
- ⏳ `templates/receive_stock.html` - Add checkbox for "Create AP Record" option

### Configuration Needed
- RFMS API "Plus" level access
- Cost calculation logic (from purchase order or manual entry)
- Default account codes for AP entries
- Invoice number (can be obtained from email scraping feature)

### Workflow
1. User receives stock (existing functionality)
2. User optionally checks "Create AP Record"
3. System creates AP record with:
   - Supplier information (from order)
   - Invoice number (if available from email scraping or manual entry)
   - Invoice date and due date
   - Detail lines with store number (49), account codes, amounts
   - Order reference in notes
4. AP record is posted to RFMS accounts payable section

### Example Usage
```python
# After receiving inventory, create AP record
detail_lines = [
    {
        "storeNumber": 49,
        "accountCode": "101",
        "subAccountCode": "",
        "amount": 1000.00,
        "comment": "Stock received for order AZ003422"
    }
]

result = rfms_client.create_payable(
    supplier_name="SUPPLIER NAME",
    invoice_number="INV-12345",
    invoice_date="12/09/2024",
    due_date="01/09/2025",
    discountable_amount=1000.00,
    non_discountable_amount=0.00,
    discount_rate=0.0,
    internal_notes="Stock received from consignment note",
    detail_lines=detail_lines
)
```

---

## 3. Dual Line Assessment for Scotias/Trims/Accessories

### Purpose
For scotias, trims, and accessories, both costing and receiving may be required. This feature will handle the dual line assessment process.

### Implementation Notes
- **Detection**: Scotias/trims are automatically detected by:
  - Product codes starting with "8" (e.g., "81", "84")
  - Descriptions containing "scotia", "trim", or "accessory"
  - Style names containing these keywords
- **Dual Process**: 
  1. **Costing**: Cost the items into inventory/costing system
  2. **Receiving**: Receive the physical stock (already implemented)
- **RFMS API Integration**: May require additional API endpoints for:
  - Costing/scosting items
  - Linking costed items to received items
- **UI Enhancement**: Currently scotias/trims are highlighted in yellow/warning color in the receiving table

### Files to Create/Modify
- `utils/rfms_client.py` - Add `cost_inventory()` or similar method for costing items
- `app.py` - Update `/api/receive-stock/receive` to optionally cost scotia/trim items
- `templates/receive_stock.html` - Add option to "Cost and Receive" for scotia/trim lines

### Configuration Needed
- RFMS API endpoint for costing inventory items
- Cost calculation method (from purchase order pricing or standard costs)
- Mapping between costing and receiving processes

### Workflow
1. User selects lines to receive (including scotias/trims)
2. System detects scotia/trim lines (highlighted in UI)
3. For scotia/trim lines:
   - Option A: Cost first, then receive
   - Option B: Receive first, then cost
   - Option C: Both processes in parallel
4. System tracks which lines have been costed vs received

---

## Implementation Priority

1. **Dual Line Assessment** - High priority (required for scotias/trims)
2. **Email Scraping** - Medium priority (helps with order discovery)
3. **AP Record Creation** - Lower priority (enhancement after core receiving is stable)

All features should be implemented as optional enhancements that don't interfere with the core stock receiving functionality.

