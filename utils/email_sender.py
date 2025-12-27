"""
Email Sender Utility

Sends emails using Microsoft Graph API with OAuth2 authentication.
"""

import os
import logging
import requests
from typing import Dict, Optional
from msal import ConfidentialClientApplication
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Sends emails using Microsoft Graph API with OAuth2 authentication.
    """
    
    def __init__(self):
        """Initialize email sender from environment variables"""
        # Azure AD / Microsoft Entra ID credentials
        self.client_id = os.environ.get('AZURE_CLIENT_ID')
        self.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        self.tenant_id = os.environ.get('AZURE_TENANT_ID')
        
        # Microsoft Graph API endpoint
        self.graph_endpoint = 'https://graph.microsoft.com/v1.0'
        
        # OAuth2 token cache
        self._access_token = None
        self._token_expires_at = None
    
    def _get_access_token(self) -> Optional[str]:
        """
        Get OAuth2 access token for Microsoft Graph API.
        
        Returns:
            Access token string or None if authentication fails
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        if not self.client_id or not self.client_secret or not self.tenant_id:
            logger.error("Azure AD credentials not configured (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)")
            return None
        
        try:
            # Create MSAL app
            authority = f"https://login.microsoftonline.com/{self.tenant_id}"
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=authority
            )
            
            # Request token with client credentials flow (application permissions)
            # Scope for Microsoft Graph API
            scopes = ["https://graph.microsoft.com/.default"]
            
            result = app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                # Token expires in ~1 hour, refresh 5 minutes early
                expires_in = result.get("expires_in", 3600)
                self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                logger.info("Successfully obtained Microsoft Graph API access token")
                return self._access_token
            else:
                error = result.get("error_description", result.get("error", "Unknown error"))
                logger.error(f"Failed to obtain access token: {error}")
                return None
                
        except Exception as e:
            logger.error(f"Error obtaining access token: {e}", exc_info=True)
            return None
    
    def send_email(self, from_address: str, to_address: str, subject: str, 
                   body: str, body_type: str = "HTML") -> bool:
        """
        Send an email using Microsoft Graph API.
        
        Args:
            from_address: Sender email address (must be a mailbox the app has access to)
            to_address: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: Body type - "HTML" or "Text" (default: "HTML")
            
        Returns:
            True if email sent successfully, False otherwise
        """
        token = self._get_access_token()
        if not token:
            logger.error("Cannot send email: No access token available")
            return False
        
        url = f"{self.graph_endpoint}/users/{from_address}/sendMail"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Build email message
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_address
                        }
                    }
                ]
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=message, timeout=30)
            response.raise_for_status()
            logger.info(f"Email sent successfully from {from_address} to {to_address}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error detail: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text[:500]}")
            return False
    
    def send_email_with_attachment(self, from_address: str, to_address: str, subject: str,
                                   body: str, body_type: str = "HTML", attachment_path: str = None,
                                   attachment_name: str = None) -> bool:
        """
        Send an email with attachment using Microsoft Graph API.
        
        Args:
            from_address: Sender email address (must be a mailbox the app has access to)
            to_address: Recipient email address
            subject: Email subject
            body: Email body content
            body_type: Body type - "HTML" or "Text" (default: "HTML")
            attachment_path: Path to attachment file
            attachment_name: Name for the attachment (defaults to filename from path)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        token = self._get_access_token()
        if not token:
            logger.error("Cannot send email: No access token available")
            return False
        
        import base64
        
        # Read attachment if provided
        attachment_data = None
        if attachment_path:
            try:
                with open(attachment_path, 'rb') as f:
                    attachment_data = base64.b64encode(f.read()).decode('utf-8')
                if not attachment_name:
                    import os
                    attachment_name = os.path.basename(attachment_path)
            except Exception as e:
                logger.error(f"Failed to read attachment file: {e}")
                return False
        
        url = f"{self.graph_endpoint}/users/{from_address}/sendMail"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Build email message
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": body_type,
                    "content": body
                },
                "toRecipients": [
                    {
                        "emailAddress": {
                            "address": to_address
                        }
                    }
                ]
            }
        }
        
        # Add attachment if provided
        if attachment_data:
            import mimetypes
            content_type, _ = mimetypes.guess_type(attachment_path)
            if not content_type:
                content_type = 'application/octet-stream'
            
            message["message"]["attachments"] = [
                {
                    "@odata.type": "#microsoft.graph.fileAttachment",
                    "name": attachment_name,
                    "contentType": content_type,
                    "contentBytes": attachment_data
                }
            ]
        
        try:
            response = requests.post(url, headers=headers, json=message, timeout=60)
            response.raise_for_status()
            logger.info(f"Email with attachment sent successfully from {from_address} to {to_address}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email with attachment: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error detail: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text[:500]}")
            return False


def send_no_invoice_notification(order_number: str, supplier_name: str, 
                                 packing_slip_number: str = None, 
                                 order_date: str = None) -> bool:
    """
    Send notification email to accounts when no supplier invoice is found.
    
    Args:
        order_number: Order number
        supplier_name: Supplier name
        packing_slip_number: Packing slip number (optional)
        order_date: Order date (optional)
        
    Returns:
        True if email sent successfully, False otherwise
    """
    from_address = os.environ.get('REPORTS_EMAIL_ADDRESS', 'reports@atozflooringsolutions.com.au')
    to_address = os.environ.get('ACCOUNTS_EMAIL_ADDRESS', 'accounts@atozflooringsolutions.com.au')
    
    subject = f"Stock Received - No Supplier Invoice Found - Order {order_number}"
    
    body = f"""
    <html>
    <body>
        <p>Dear Accounts Team,</p>
        
        <p>Stock has arrived for the following order, however it has not been costed into RFMS due to no matching supplier invoice being found.</p>
        
        <h3>Order Details:</h3>
        <ul>
            <li><strong>Order Number:</strong> {order_number}</li>
            <li><strong>Supplier:</strong> {supplier_name}</li>
            {f'<li><strong>Packing Slip Number:</strong> {packing_slip_number}</li>' if packing_slip_number else ''}
            {f'<li><strong>Order Date:</strong> {order_date}</li>' if order_date else ''}
        </ul>
        
        <p><strong>Action Required:</strong></p>
        <ol>
            <li>Express receive the stock on RFMS Desktop</li>
            <li>Place the consignment note in the costings tray</li>
            <li>Locate the supplier invoice and process accordingly</li>
        </ol>
        
        <p>Please ensure the stock is received and costed as soon as possible.</p>
        
        <p>Thank you,<br>
        RFMS Uploader System</p>
    </body>
    </html>
    """
    
    sender = EmailSender()
    return sender.send_email(from_address, to_address, subject, body)

