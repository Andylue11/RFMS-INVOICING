"""
Email Scraper for Supplier Invoice Matching

This module scrapes the accounts@atozflooringsolutions.com.au email account
to find supplier invoices that match consignment notes and orders.

Uses Microsoft Graph API with OAuth2 authentication.
"""

import os
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
import tempfile
import base64
from msal import ConfidentialClientApplication
from utils.supplier_folders import get_supplier_folder_paths

logger = logging.getLogger(__name__)


class EmailScraper:
    """
    Scrapes email account for supplier invoices and matches them to orders.
    Uses Microsoft Graph API with OAuth2 authentication.
    """
    
    def __init__(self):
        """Initialize email scraper from environment variables"""
        self.email_address = os.environ.get('EMAIL_ADDRESS', 'accounts@atozflooringsolutions.com.au')
        
        # Azure AD / Microsoft Entra ID credentials
        self.client_id = os.environ.get('AZURE_CLIENT_ID')
        self.client_secret = os.environ.get('AZURE_CLIENT_SECRET')
        self.tenant_id = os.environ.get('AZURE_TENANT_ID')
        
        # Microsoft Graph API endpoint
        self.graph_endpoint = 'https://graph.microsoft.com/v1.0'
        
        # Supplier folders to search (under "Suppliers" section)
        supplier_folders_str = os.environ.get('EMAIL_SUPPLIER_FOLDERS', '')
        self.supplier_folders = [f.strip() for f in supplier_folders_str.split(',') if f.strip()] if supplier_folders_str else []
        
        # Account code mappings for different charge types
        self.account_code_mappings = {
            'freight': '5315',  # FREIGHT
            'baling': '6406',   # BALING/HANDLING
            'handling': '6406',  # BALING/HANDLING
            'supplier_discount': '5320',  # SUPPLIER DISCOUNTS
            'cost_of_goods': '1630',  # INVENTORY
        }
        
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
    
    def _make_graph_request(self, endpoint: str, method: str = 'GET', params: Dict = None, data: Dict = None) -> Optional[Dict]:
        """
        Make a request to Microsoft Graph API.
        
        Args:
            endpoint: API endpoint (relative to graph_endpoint)
            method: HTTP method (GET, POST, etc.)
            params: Query parameters
            data: Request body data
            
        Returns:
            Response JSON as dictionary or None if request fails
        """
        token = self._get_access_token()
        if not token:
            return None
        
        url = f"{self.graph_endpoint}{endpoint}"
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            else:
                response = requests.request(method, url, headers=headers, json=data, params=params, timeout=30)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Error detail: {error_detail}")
                except:
                    logger.error(f"Response text: {e.response.text[:500]}")
            return None
    
    def _get_mail_folder_id(self, folder_name: str) -> Optional[str]:
        """
        Get the folder ID for a mail folder by name.
        
        Args:
            folder_name: Folder name (e.g., "INBOX", "Suppliers/Supplier1")
            
        Returns:
            Folder ID or None if not found
        """
        # Handle special folder names (use well-known folder names)
        folder_map = {
            'INBOX': 'inbox',
            'Sent Items': 'sentitems',
            'Drafts': 'drafts',
            'Deleted Items': 'deleteditems',
            'Junk Email': 'junkemail'
        }
        
        # Check if it's a special folder
        if folder_name.upper() in folder_map:
            return folder_map[folder_name.upper()]
        
        # For custom folders, search recursively
        if '/' in folder_name:
            # Handle nested folders like "Suppliers/Supplier1"
            parts = folder_name.split('/')
            current_id = None
            
            # Start from root mailFolders
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                
                if current_id is None:
                    # Search root folders
                    current_id = self._find_folder_in_list(part, None)
                else:
                    # Search child folders
                    current_id = self._find_folder_in_list(part, current_id)
                
                if current_id is None:
                    return None
            
            return current_id
        else:
            # Single folder name - search all folders
            return self._find_folder_in_list(folder_name, None)
    
    def _find_folder_in_list(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find a folder by name in a list of folders.
        
        Args:
            folder_name: Name of folder to find
            parent_id: Parent folder ID (None for root folders)
            
        Returns:
            Folder ID or None if not found
        """
        if parent_id:
            endpoint = f"/users/{self.email_address}/mailFolders/{parent_id}/childFolders"
        else:
            endpoint = f"/users/{self.email_address}/mailFolders"
        
        result = self._make_graph_request(endpoint)
        if not result or 'value' not in result:
            return None
        
        folder_name_lower = folder_name.lower()
        for folder in result['value']:
            display_name = folder.get('displayName', '')
            if display_name.lower() == folder_name_lower:
                return folder.get('id')
        
        return None
    
    def search_invoices(self, supplier_name: str = None, order_number: str = None, 
                       packing_slip_number: str = None, date_from: datetime = None, 
                       date_to: datetime = None) -> List[Dict]:
        """
        Search for supplier invoices in email inbox and supplier folders.
        
        Args:
            supplier_name: Filter by supplier name (optional)
            order_number: Filter by order number (optional)
            packing_slip_number: Packing slip number or supplier invoice reference (SI-, INV, etc.) (optional)
            date_from: Search emails from this date (optional, defaults to last 30 days)
            date_to: Search emails to this date (optional, defaults to today)
            
        Returns:
            List of email dictionaries with invoice information
        """
        if not self.client_id or not self.client_secret or not self.tenant_id:
            logger.warning("Azure AD credentials not configured, skipping email search")
            return []
        
        # Default date range: last 30 days
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
        if not date_to:
            date_to = datetime.now()
        
        all_emails = []
        
        # ALWAYS search inbox first (invoices may not have been moved yet)
        logger.info(f"Searching inbox for invoices from {date_from.date()} to {date_to.date()}")
        inbox_emails = self._search_folder('INBOX', supplier_name, order_number, packing_slip_number, date_from, date_to)
        all_emails.extend(inbox_emails)
        
        # Get supplier folder paths based on supplier name
        supplier_folder_paths = []
        if supplier_name:
            supplier_folder_paths = get_supplier_folder_paths(supplier_name)
            logger.info(f"Matched supplier '{supplier_name}' to {len(supplier_folder_paths)} folder(s)")
        
        # Also search manually configured supplier folders
        all_supplier_folders = list(set(supplier_folder_paths + self.supplier_folders))
        
        # Search in supplier folders
        for folder in all_supplier_folders:
            if folder:
                logger.info(f"Searching supplier folder: {folder}")
                folder_emails = self._search_folder(folder, supplier_name, order_number, packing_slip_number, date_from, date_to)
                all_emails.extend(folder_emails)
        
        # Remove duplicates (same email ID)
        seen_ids = set()
        unique_emails = []
        for email in all_emails:
            email_id = email.get('id')
            if email_id and email_id not in seen_ids:
                seen_ids.add(email_id)
                unique_emails.append(email)
        
        logger.info(f"Found {len(unique_emails)} unique potential invoice emails")
        return unique_emails
    
    def _search_folder(self, folder_name: str, supplier_name: str = None,
                      order_number: str = None, packing_slip_number: str = None,
                      date_from: datetime = None, date_to: datetime = None) -> List[Dict]:
        """
        Search a specific email folder for invoices.
        
        Args:
            folder_name: Folder name to search
            supplier_name: Filter by supplier name
            order_number: Filter by order number
            date_from: Date from
            date_to: Date to
            
        Returns:
            List of email dictionaries
        """
        emails = []
        
        try:
            # Get folder ID
            folder_id = self._get_mail_folder_id(folder_name)
            if not folder_id:
                logger.warning(f"Could not find folder: {folder_name}")
                return emails
            
            # Build search query
            search_query_parts = []
            
            # Date filter
            if date_from:
                date_from_str = date_from.strftime('%Y-%m-%dT%H:%M:%SZ')
                search_query_parts.append(f"receivedDateTime ge {date_from_str}")
            if date_to:
                date_to_str = date_to.strftime('%Y-%m-%dT%H:%M:%SZ')
                search_query_parts.append(f"receivedDateTime le {date_to_str}")
            
            # Invoice keywords - subject line will likely say "INVOICE"
            invoice_keywords = "(subject:invoice OR subject:inv)"
            search_query_parts.append(invoice_keywords)
            
            # If packing slip number provided, search for it in subject/body
            # Patterns: SI-, INV, INV-, SALES INVOICE I..., SALES INVOICE-PSI..., or just the number
            if packing_slip_number:
                # Clean the packing slip number
                psn_clean = packing_slip_number.strip().upper()
                # Add to search - search in subject and body
                search_query_parts.append(f"(subject:{psn_clean} OR body:{psn_clean})")
            
            # Build filter query
            filter_query = ' AND '.join(search_query_parts) if search_query_parts else None
            
            # Get messages
            endpoint = f"/users/{self.email_address}/mailFolders/{folder_id}/messages"
            params = {
                '$top': 50,  # Limit to 50 most recent
                '$orderby': 'receivedDateTime desc',
                '$filter': filter_query
            } if filter_query else {
                '$top': 50,
                '$orderby': 'receivedDateTime desc'
            }
            
            result = self._make_graph_request(endpoint, params=params)
            if not result or 'value' not in result:
                return emails
            
            # Process each message
            for message in result['value']:
                try:
                    email_data = self._parse_message(message, folder_name)
                    if email_data:
                        # Filter by supplier name if provided
                        if supplier_name:
                            supplier_lower = supplier_name.lower()
                            subject_lower = email_data.get('subject', '').lower()
                            from_lower = email_data.get('from', '').lower()
                            body_lower = email_data.get('body', '').lower()
                            
                            # Check if supplier name appears in subject, from, or body
                            if (supplier_lower not in subject_lower and 
                                supplier_lower not in from_lower and
                                supplier_lower not in body_lower):
                                continue
                        
                        # Filter by order number if provided
                        if order_number:
                            order_normalized = order_number.replace('-', '').upper()
                            subject_upper = email_data.get('subject', '').upper()
                            body_upper = email_data.get('body', '').upper()
                            
                            if (order_normalized not in subject_upper.replace('-', '') and 
                                order_normalized not in body_upper.replace('-', '')):
                                continue
                        
                        # Filter by packing slip number if provided
                        if packing_slip_number:
                            psn_clean = packing_slip_number.strip().upper()
                            subject_upper = email_data.get('subject', '').upper()
                            body_upper = email_data.get('body', '').upper()
                            
                            # Check for various patterns: SI-XXX, INV-XXX, INVXXX, SALES INVOICE IXXX, etc.
                            found = False
                            if psn_clean in subject_upper or psn_clean in body_upper:
                                found = True
                            # Also check for patterns like "SI-" + number, "INV-" + number, etc.
                            if not found:
                                # Remove common prefixes and check if number matches
                                psn_numeric = re.sub(r'^[A-Z\-]+', '', psn_clean)
                                if psn_numeric and (psn_numeric in subject_upper or psn_numeric in body_upper):
                                    found = True
                            
                            if not found:
                                continue
                        
                        emails.append(email_data)
                except Exception as e:
                    logger.warning(f"Error processing email: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error searching folder {folder_name}: {e}", exc_info=True)
        
        return emails
    
    def _parse_message(self, message: Dict, folder_name: str) -> Optional[Dict]:
        """
        Parse a Microsoft Graph message object into our email format.
        
        Args:
            message: Graph API message object
            folder_name: Folder name
            
        Returns:
            Dictionary with email data or None
        """
        try:
            # Get message body
            message_id = message.get('id')
            if not message_id:
                return None
            
            # Get full message with body
            full_message = self._make_graph_request(f"/users/{self.email_address}/messages/{message_id}")
            if not full_message:
                return None
            
            # Extract body text
            body = ''
            body_content = full_message.get('body', {})
            if body_content:
                body = body_content.get('content', '')
                # Remove HTML tags if HTML
                if body_content.get('contentType') == 'html':
                    import re
                    body = re.sub(r'<[^>]+>', '', body)
            
            # Get attachments
            attachments = []
            attachments_data = full_message.get('attachments', [])
            for att in attachments_data:
                attachments.append({
                    'id': att.get('id'),
                    'filename': att.get('name', ''),
                    'content_type': att.get('contentType', ''),
                    'size': att.get('size', 0)
                })
            
            # Extract sender
            from_addr = ''
            sender = full_message.get('sender', {})
            if sender:
                email_address = sender.get('emailAddress', {})
                if email_address:
                    from_addr = email_address.get('address', '')
            
            return {
                'id': message_id,
                'folder': folder_name,
                'subject': full_message.get('subject', ''),
                'from': from_addr,
                'date': full_message.get('receivedDateTime', ''),
                'body': body,
                'attachments': attachments,
                'is_invoice': self._is_likely_invoice(full_message.get('subject', ''), body, attachments)
            }
            
        except Exception as e:
            logger.warning(f"Error parsing message: {e}")
            return None
    
    def _is_likely_invoice(self, subject: str, body: str, attachments: List[Dict]) -> bool:
        """Check if email is likely an invoice"""
        invoice_keywords = ['invoice', 'inv', 'bill', 'statement', 'payment due']
        subject_lower = subject.lower()
        body_lower = body.lower()
        
        # Check subject or body for invoice keywords
        if any(keyword in subject_lower for keyword in invoice_keywords):
            return True
        if any(keyword in body_lower for keyword in invoice_keywords):
            return True
        
        # Check attachments for PDF invoices
        for att in attachments:
            filename_lower = att.get('filename', '').lower()
            if 'invoice' in filename_lower or 'inv' in filename_lower:
                if filename_lower.endswith('.pdf'):
                    return True
        
        return False
    
    def download_invoice_attachment(self, email_data: Dict, attachment_index: int = 0) -> Optional[bytes]:
        """
        Download an invoice attachment from an email.
        
        Args:
            email_data: Email dictionary from search_invoices
            attachment_index: Index of attachment to download (default: 0)
            
        Returns:
            Attachment file bytes or None
        """
        if not self.client_id or not self.client_secret or not self.tenant_id:
            return None
        
        try:
            message_id = email_data.get('id')
            if not message_id:
                return None
            
            # Get attachments
            attachments_endpoint = f"/users/{self.email_address}/messages/{message_id}/attachments"
            result = self._make_graph_request(attachments_endpoint)
            if not result or 'value' not in result:
                return None
            
            attachments = result['value']
            if attachment_index >= len(attachments):
                return None
            
            attachment = attachments[attachment_index]
            
            # Get attachment content
            attachment_id = attachment.get('id')
            if not attachment_id:
                return None
            
            attachment_data = self._make_graph_request(f"/users/{self.email_address}/messages/{message_id}/attachments/{attachment_id}")
            if not attachment_data:
                return None
            
            # Decode base64 content
            content_bytes = attachment_data.get('contentBytes')
            if not content_bytes:
                return None
            
            return base64.b64decode(content_bytes)
            
        except Exception as e:
            logger.error(f"Error downloading attachment: {e}", exc_info=True)
            return None
    
    def match_invoice_to_order(self, invoice_data: Dict, order_number: str = None, 
                              supplier_name: str = None, packing_slip_number: str = None) -> bool:
        """
        Check if an invoice matches an order based on order number, supplier, and/or packing slip number.
        
        Args:
            invoice_data: Invoice data extracted from email/PDF
            order_number: Order number to match (optional)
            supplier_name: Supplier name to match (optional)
            packing_slip_number: Packing slip number or supplier reference to match (optional)
            
        Returns:
            True if invoice matches order
        """
        invoice_order_ref = invoice_data.get('order_number', '') or invoice_data.get('po_number', '')
        invoice_supplier = invoice_data.get('supplier_name', '')
        invoice_number = invoice_data.get('invoice_number', '')
        
        # Check supplier name match
        if supplier_name and invoice_supplier:
            supplier_lower = supplier_name.lower()
            invoice_supplier_lower = invoice_supplier.lower()
            if supplier_lower not in invoice_supplier_lower and \
               invoice_supplier_lower not in supplier_lower:
                return False
        
        # Check order number match (with normalization)
        order_match = False
        if order_number and invoice_order_ref:
            # Remove hyphens and compare
            order_normalized = order_number.replace('-', '').upper()
            invoice_normalized = invoice_order_ref.replace('-', '').upper()
            
            # Check if order number is contained in invoice reference or vice versa
            if order_normalized in invoice_normalized or invoice_normalized in order_normalized:
                order_match = True
            
            # Check base order number (without suffix)
            if not order_match:
                order_base = re.sub(r'[0-9]{4}$', '', order_normalized)  # Remove last 4 digits
                invoice_base = re.sub(r'[0-9]{4}$', '', invoice_normalized)
                if order_base and order_base == invoice_base:
                    order_match = True
        
        # Check packing slip number match
        packing_slip_match = False
        if packing_slip_number:
            psn_clean = packing_slip_number.strip().upper()
            
            # Check against invoice number
            if invoice_number:
                invoice_num_upper = invoice_number.upper()
                # Direct match
                if psn_clean in invoice_num_upper or invoice_num_upper in psn_clean:
                    packing_slip_match = True
                # Check for patterns: SI-XXX, INV-XXX, INVXXX, SALES INVOICE IXXX, etc.
                if not packing_slip_match:
                    # Remove common prefixes and check if number matches
                    psn_numeric = re.sub(r'^[A-Z\-\s]+', '', psn_clean)
                    invoice_numeric = re.sub(r'^[A-Z\-\s]+', '', invoice_num_upper)
                    if psn_numeric and invoice_numeric and psn_numeric in invoice_numeric:
                        packing_slip_match = True
        
        # Match if either order number OR packing slip number matches (and supplier matches if provided)
        # If supplier is provided, it must match
        if supplier_name and not invoice_supplier:
            return False
        
        # If supplier matches (or not provided), check order number or packing slip
        return order_match or packing_slip_match


def extract_invoice_charges(invoice_data: Dict) -> Dict:
    """
    Extract additional charges from invoice data.
    
    Args:
        invoice_data: Invoice data dictionary from AI analyzer
        
    Returns:
        Dictionary with charge breakdown:
        - freight: Freight charges
        - baling_handling: Baling and handling charges
        - supplier_discount: Supplier discounts
        - other_charges: Other miscellaneous charges
        - subtotal: Subtotal before charges
        - total: Total amount
    """
    charges = {
        'freight': 0.0,
        'baling_handling': 0.0,
        'supplier_discount': 0.0,
        'other_charges': 0.0,
        'subtotal': 0.0,
        'total': 0.0
    }
    
    # Extract from invoice data (already parsed by AI)
    if 'freight' in invoice_data and invoice_data['freight']:
        try:
            charges['freight'] = float(invoice_data['freight'])
        except:
            pass
    
    if 'baling_handling' in invoice_data and invoice_data['baling_handling']:
        try:
            charges['baling_handling'] = float(invoice_data['baling_handling'])
        except:
            pass
    
    if 'supplier_discount' in invoice_data and invoice_data['supplier_discount']:
        try:
            charges['supplier_discount'] = float(invoice_data['supplier_discount'])
        except:
            pass
    
    if 'subtotal' in invoice_data and invoice_data['subtotal']:
        try:
            charges['subtotal'] = float(invoice_data['subtotal'])
        except:
            pass
    
    if 'total' in invoice_data and invoice_data['total']:
        try:
            charges['total'] = float(invoice_data['total'])
        except:
            pass
    
    # Extract other charges
    if 'other_charges' in invoice_data and isinstance(invoice_data['other_charges'], dict):
        for charge_name, charge_amount in invoice_data['other_charges'].items():
            try:
                charges['other_charges'] += float(charge_amount)
            except:
                pass
    
    return charges
