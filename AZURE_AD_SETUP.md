# Azure AD / Microsoft Entra ID Setup Guide

## Quick Setup Steps

### 1. App Registration Details (Already Created)

Your app registration is already set up with:
- **Application (client) ID**: `b72d49c0-673c-444e-b33c-d6617caed909`
- **Directory (tenant) ID**: `f2cf196a-ecd1-4355-9260-44bb15362e06`
- **Client Secret**: `x1Q8Q~itHwkJ4x-2_Bn-yMnTTW_Juvcewg9MSdk.`

### 2. Required API Permissions

In Azure Portal → App registrations → RFMS STOCK → API permissions:

Add these **Application permissions** (not Delegated):

1. **Microsoft Graph** → **Mail.Read**
   - Description: Read mail in all mailboxes
   - Type: Application
   - Status: Requires admin consent

2. **Microsoft Graph** → **Mail.ReadBasic** (optional, but recommended)
   - Description: Read basic mail in all mailboxes
   - Type: Application
   - Status: Requires admin consent

### 3. Grant Admin Consent

After adding permissions:
1. Click **"Grant admin consent for [Your Organization]"**
2. Confirm the consent
3. Verify all permissions show "✓ Granted for [Your Organization]"

### 4. Environment Variables

Add to your `.env` file:

```env
EMAIL_ADDRESS=accounts@atozflooringsolutions.com.au
AZURE_CLIENT_ID=b72d49c0-673c-444e-b33c-d6617caed909
AZURE_CLIENT_SECRET=x1Q8Q~itHwkJ4x-2_Bn-yMnTTW_Juvcewg9MSdk.
AZURE_TENANT_ID=f2cf196a-ecd1-4355-9260-44bb15362e06
EMAIL_SUPPLIER_FOLDERS=Suppliers/Supplier1,Suppliers/Supplier2
```

**Important**: Replace `Suppliers/Supplier1,Suppliers/Supplier2` with your actual supplier folder names.

### 5. Verify Setup

The application will:
- Authenticate using OAuth2 client credentials flow
- Access the `accounts@atozflooringsolutions.com.au` mailbox
- Search inbox and supplier folders for invoices
- Download and analyze PDF attachments

## Troubleshooting

### "Insufficient privileges to complete the operation"
- Ensure **Mail.Read** application permission is added
- Ensure **admin consent** has been granted
- Wait a few minutes for permissions to propagate

### "Invalid client secret"
- Verify the client secret value is correct
- Check if the secret has expired (secrets can expire)
- Generate a new secret if needed

### "Folder not found"
- Verify folder names match exactly (case-sensitive)
- Check that folders exist in Outlook under the "Suppliers" section
- Use format: `Suppliers/FolderName` for nested folders

## Security Notes

- Client secrets should be rotated periodically
- Never commit secrets to version control
- Use environment variables or Azure Key Vault for production
- Application permissions allow unattended access (no user interaction required)

