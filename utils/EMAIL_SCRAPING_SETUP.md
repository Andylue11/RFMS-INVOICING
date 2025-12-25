# Email Scraping Setup Guide

## Overview

The email scraping feature automatically searches the `accounts@atozflooringsolutions.com.au` email inbox and supplier subfolders for supplier invoices that match consignment notes and orders. It extracts invoice details, matches them to orders, and can automatically create Accounts Payable (AP) records with proper account codes for charges like freight, baling, handling, etc.

**Uses Microsoft Graph API with OAuth2 authentication (Azure AD / Microsoft Entra ID).**

## Features

1. **Email Search**: Searches inbox and supplier subfolders for invoices
2. **Invoice Analysis**: Uses AI to extract invoice data from PDF attachments
3. **Order Matching**: Matches invoices to orders based on order number and supplier name
4. **Charge Extraction**: Extracts additional charges (freight, baling, handling, discounts)
5. **AP Record Creation**: Automatically creates AP records with proper account codes

## Configuration

### Azure AD / Microsoft Entra ID App Registration

The application uses OAuth2 client credentials flow to authenticate with Microsoft Graph API.

#### Required Azure AD App Permissions

Your Azure AD app registration needs the following **Application permissions** (not Delegated):

1. **Mail.Read** - Read mail in all mailboxes
2. **Mail.ReadBasic** - Read basic mail in all mailboxes

**Note**: These are application permissions (not delegated), which means the app can access mailboxes without user interaction.

#### Grant Admin Consent

After adding the permissions, you must **Grant admin consent** for your organization.

### Environment Variables

Add these to your `.env` file:

```env
# Email Configuration
EMAIL_ADDRESS=accounts@atozflooringsolutions.com.au

# Azure AD / Microsoft Entra ID Configuration
AZURE_CLIENT_ID=b72d49c0-673c-444e-b33c-d6617caed909
AZURE_CLIENT_SECRET=x1Q8Q~itHwkJ4x-2_Bn-yMnTTW_Juvcewg9MSdk.
AZURE_TENANT_ID=f2cf196a-ecd1-4355-9260-44bb15362e06

# Supplier Folders (comma-separated, under "Suppliers" section)
EMAIL_SUPPLIER_FOLDERS=Suppliers/Supplier1,Suppliers/Supplier2
```

### Azure AD Credentials

From your Azure portal App registration:

- **Application (client) ID**: `AZURE_CLIENT_ID`
- **Directory (tenant) ID**: `AZURE_TENANT_ID`
- **Client secret value**: `AZURE_CLIENT_SECRET` (from the "Client credentials" section)

**Security Note**: Keep the client secret secure. Never commit it to version control.

### Supplier Folders

List supplier-specific folders (comma-separated) where invoices are stored. These should be subfolders under the "Suppliers" section in Outlook:

- Example: `Suppliers/ACME,Suppliers/SUPPLIER2`
- The folder structure in Outlook should be: `Suppliers > ACME`, `Suppliers > SUPPLIER2`, etc.

## Account Code Mappings

The system uses the following account codes for different charge types (based on your RFMS mapping):

| Charge Type | Account Code | Description |
|------------|--------------|-------------|
| Inventory/Cost of Goods | 1630 | INVENTORY |
| Freight | 5315 | FREIGHT |
| Baling/Handling | 6406 | BALING/HANDLING |
| Supplier Discounts | 5320 | SUPPLIER DISCOUNTS |

## Usage

### Automatic Email Search During Stock Receiving

When receiving stock, you can enable email search and AP record creation:

```javascript
// In the frontend, when submitting the receive form
{
    order_number: "AZ003422",
    order_date: "12-09-2024",
    line_data: [...],
    search_email_for_invoice: true,  // Search for matching invoice
    create_ap_record: true  // Create AP record if invoice found
}
```

### Manual Invoice Search Endpoint

You can also search for invoices manually:

```bash
POST /api/receive-stock/search-invoice
Content-Type: application/json

{
    "order_number": "AZ003422",
    "supplier_name": "ACME SUPPLIER"
}
```

Response:
```json
{
    "success": true,
    "matched_invoices": [
        {
            "email_subject": "Invoice INV-12345",
            "email_from": "supplier@example.com",
            "invoice_number": "INV-12345",
            "invoice_date": "2024-12-01",
            "due_date": "2024-12-31",
            "total": 1000.00,
            "freight": 50.00,
            "baling_handling": 25.00,
            "supplier_discount": 0.00,
            "line_items": [...]
        }
    ],
    "count": 1
}
```

## Workflow

1. **User uploads consignment note** → System extracts order number and supplier
2. **User selects order and receives stock** → System receives inventory
3. **If `search_email_for_invoice` is enabled**:
   - Authenticates with Microsoft Graph API using Azure AD credentials
   - Searches email inbox and supplier folders
   - Downloads PDF attachments
   - Analyzes invoices using AI
   - Matches invoices to orders
4. **If `create_ap_record` is enabled and invoice found**:
   - Extracts charges (freight, baling, handling, discounts)
   - Creates AP record with proper account codes
   - Links AP record to order number

## Invoice Matching Logic

Invoices are matched to orders based on:
- **Supplier name**: Must match (case-insensitive, partial match)
- **Order number**: Normalized comparison (handles variations like `AZ003463-0001` vs `AZ0034630001`)

## Charge Extraction

The system extracts the following charges from invoices:
- **Freight/Shipping/Delivery**: Mapped to account code 5315
- **Baling/Handling**: Mapped to account code 6406
- **Supplier Discounts**: Mapped to account code 5320
- **Cost of Goods**: Mapped to account code 1630 (INVENTORY)

## Error Handling

- Email search failures don't block stock receiving
- AP record creation failures are logged but don't fail the receiving process
- Missing invoices are logged as warnings
- Invalid invoice formats are skipped with warnings
- Authentication failures are logged with detailed error messages

## Security Notes

- Store Azure AD credentials securely (use environment variables, not hardcoded)
- Client secret should be rotated periodically
- Use application permissions (not delegated) for unattended access
- Consider using Azure Key Vault for storing secrets in production
- Email credentials should have read-only access (Mail.Read permission)

## Troubleshooting

### Authentication Issues

- **"Invalid client secret"**: Verify the client secret value is correct and hasn't expired
- **"Insufficient privileges"**: Ensure Mail.Read application permission is granted and admin consent is provided
- **"Token acquisition failed"**: Check that tenant ID, client ID, and client secret are correct

### Email Connection Issues

- Verify Azure AD app has Mail.Read application permission
- Check that admin consent has been granted
- Ensure the email account exists and is accessible
- Verify folder names match exactly (case-sensitive)

### No Invoices Found

- Check supplier folder names match exactly (including case)
- Verify date range (defaults to last 30 days)
- Check if invoices are in PDF format
- Verify email subject/body contains invoice keywords
- Check that the "Suppliers" folder structure exists in Outlook

### Invoice Matching Fails

- Verify order number format matches invoice
- Check supplier name spelling matches
- Review logs for normalization issues

## Microsoft Graph API Limits

- **Rate Limits**: Microsoft Graph API has rate limits. The implementation includes token caching to minimize API calls.
- **Pagination**: Currently fetches up to 50 most recent emails per folder. Can be extended if needed.
- **Throttling**: If you encounter throttling, the system will log errors and retry logic can be added.

## Future Enhancements

- Support for delegated permissions (user-specific access)
- Pagination for large email folders
- Retry logic for rate-limited requests
- Caching of email search results
- Support for multiple email accounts
- Invoice OCR for non-PDF formats
- Automatic invoice categorization
- Email notification when invoices are matched
