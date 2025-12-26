import requests
import base64
from typing import Dict, List, Optional
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RFMSClient:
    """
    Enhanced RFMS API Client for handling RFMS-specific operations including
    orders, quotes, billing groups, and attachments.
    """
    
    def __init__(self):
        """Initialize RFMS API client from environment variables"""
        self.base_url = os.environ.get('RFMS_BASE_URL', 'https://api.rfms.online')
        self.store_code = os.environ.get('RFMS_STORE_CODE')
        self.api_key = os.environ.get('RFMS_API_KEY')
        self.session_token = None
        self.session_expiry = None  # Track when session token expires (assume 1 hour)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Convert store_code to store_number (store_code is string, store_number is int)
        try:
            self.store_number = int(self.store_code) if self.store_code else None
        except (ValueError, TypeError):
            self.store_number = None
        
    def test_connection(self, force_new_session=False) -> Dict:
        """
        Test RFMS API connection. Reuses existing session if valid.
        
        Args:
            force_new_session: If True, forces a new session. Otherwise reuses existing valid session.
        """
        try:
            # Only start a new session if we don't have a valid one
            self.start_session(force=force_new_session)
            return {
                'success': True,
                'message': 'RFMS connection successful'
            }
        except Exception as e:
            logger.error(f"RFMS connection test failed: {str(e)}")
            # If test fails, clear the session so next attempt will create a new one
            self.session_token = None
            self.session_expiry = None
            return {
                'success': False,
                'message': f'RFMS connection failed: {str(e)}'
            }
    
    def start_session(self, force=False) -> None:
        """
        Start a new session with RFMS API and store the session token.
        
        Args:
            force: If True, create new session even if one exists. Otherwise, only create if expired or missing.
        """
        # Check if we have a valid session that hasn't expired
        if not force and self.session_token and self.session_expiry:
            if datetime.now() < self.session_expiry:
                logger.debug(f"Reusing existing RFMS session (expires in {(self.session_expiry - datetime.now()).total_seconds():.0f}s)")
                return
        
        endpoint = f"{self.base_url}/v2/session/begin"
        
        # Validate credentials before attempting connection
        if not self.store_code or not self.api_key:
            raise ValueError("RFMS credentials not configured. Please set RFMS_STORE_CODE and RFMS_API_KEY environment variables.")
        
        response = requests.post(
            endpoint, 
            auth=(self.store_code, self.api_key)
        )
        
        # Check response status
        if response.status_code != 200:
            logger.error(f"RFMS session begin failed with status {response.status_code}")
            logger.error(f"Response text: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Check if response has content
        if not response.text or not response.text.strip():
            logger.error("RFMS session begin returned empty response")
            raise Exception("RFMS API returned empty response")
        
        try:
            session_data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response text (first 500 chars): {response.text[:500]}")
            raise Exception(f"Invalid JSON response from RFMS API: {response.text[:200]}")
        
        self.session_token = session_data.get('sessionToken')
        if not self.session_token:
            logger.error(f"No session token in response: {session_data}")
            raise Exception("RFMS API did not return a session token")
        
        # Assume session tokens are valid for 55 minutes (refresh before expiry)
        self.session_expiry = datetime.now() + timedelta(minutes=55)
        logger.info(f"RFMS session started: {self.session_token[:20]}...")
        
    def _invalidate_session(self):
        """Invalidate the current session token (call when auth fails)."""
        logger.debug("Invalidating RFMS session token")
        self.session_token = None
        self.session_expiry = None
    
    @property
    def auth(self) -> tuple:
        """Get authentication tuple for requests. Reuses existing session if valid."""
        if not self.session_token or (self.session_expiry and datetime.now() >= self.session_expiry):
            self.start_session()
        return (self.store_code, self.session_token)
    
    def _handle_auth_error(self, response):
        """
        Handle authentication errors (401/403) by invalidating the session.
        
        Args:
            response: The requests.Response object
        """
        if response.status_code in (401, 403):
            logger.warning(f"RFMS authentication failed (HTTP {response.status_code}), invalidating session")
            self._invalidate_session()

    def find_customers(self, search_text: str) -> List[Dict]:
        """
        Search for customers in RFMS.
        
        Args:
            search_text: Text to search for customers
            
        Returns:
            List[Dict]: List of matching customers
        """
        endpoint = f"{self.base_url}/v2/customers/find"
        params = {
            "searchText": search_text,
            "includeCustomers": True,
            "includeProspects": False,
            "includeInactive": True,
            "customerSource": "Customer",
            "referralType": "Standalone"
        }
        
        response = requests.post(
            endpoint, 
            auth=self.auth, 
            json=params, 
            headers=self.headers
        )
        result = response.json()
        
        # Handle different response formats
        if isinstance(result, dict) and 'detail' in result:
            return result['detail']
        elif isinstance(result, list):
            return result
        return []

    def create_order(self, order_data: Dict) -> Dict:
        """
        Create a new order in RFMS.

        Args:
            order_data: Order data including customer and product information
            
        Returns:
            Dict: Response like {"status":"success","result":"AZ003071","detail":{"docId":"5119"}}
        """
        endpoint = f"{self.base_url}/v2/order/create"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=order_data,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for create_order, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to create order. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to create order after retry")

    def create_quote(self, quote_data: Dict) -> Dict:
        """
        Create a new quote in RFMS.

        Args:
            quote_data: Quote data including customer and product information
            
        Returns:
            Dict: Response like {"status":"success","result":"AQ003071","detail":{"docId":"5119"}}
        """
        endpoint = f"{self.base_url}/v2/quote/create"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=quote_data,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for create_quote, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to create quote. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to create quote after retry")

    def add_attachment(self, document_number: str, file_path: str, 
                      document_type: str = "Order", description: str = None) -> Dict:
        """
        Add an attachment to an RFMS document.
        
        Args:
            document_number: The document number to attach to
            file_path: Path to the file to attach
            document_type: Type of document (Order, Quote, etc)
            description: Description/title of the attachment
            
        Returns:
            Dict: Response from the RFMS API
        """
        with open(file_path, 'rb') as file:
            file_binary = file.read()
            file_base64_string = base64.b64encode(file_binary).decode('utf-8')
        
        file_extension = file_path.split('.')[-1].lower()
        
        file_data = {
            "documentNumber": document_number,
            "documentType": document_type,
            "fileExtension": file_extension,
            "description": description or file_path.split('/')[-1],
            "fileData": file_base64_string
        }
        
        endpoint = f"{self.base_url}/v2/attachment"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=file_data,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for add_attachment, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to add attachment. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to add attachment after retry")

    def update_billing_group(self, order_number: str, parent_order: str) -> Dict:
        """
        Update the billing group for an order.
        
        Args:
            order_number: The order number to update
            parent_order: The parent order number
            
        Returns:
            Dict: Response from the RFMS API
        """
        update_data = {
            "number": order_number,
            "billingGroup": {
                "parentOrder": parent_order
            }
        }
        
        endpoint = f"{self.base_url}/v2/order"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=update_data,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for update_billing_group, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to update billing group. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to update billing group after retry")

    def find_order_by_po_number(self, po_number: str) -> Optional[Dict]:
        """
        Search for an order in RFMS by PO number.
        
        Args:
            po_number: PO number to search for
            
        Returns:
            Optional[Dict]: Search results if found, None otherwise
        """
        endpoint = f"{self.base_url}/v2/order/find"
        payload = {"searchText": po_number}
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for find_order_by_po_number, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to find order. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to find order after retry")

    def find_quote_by_qr_number(self, qr_number: str) -> Optional[Dict]:
        """
        Search for a quote in RFMS by QR number.
        
        Args:
            qr_number: QR number to search for
            
        Returns:
            Optional[Dict]: Search results if found, None otherwise
        """
        endpoint = f"{self.base_url}/v2/quote/find"
        payload = {"searchText": qr_number}
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for find_quote_by_qr_number, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to find quote. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to find quote after retry")

    def get_po_prefix(self, po_number: str) -> Optional[str]:
        """
        Extract the logical prefix from a PO/QR number for billing group matching.

        Examples:
            P1BW-1828        -> P1BW-1828        (base order)
            P1BW-1828-A      -> P1BW-1828
            P1BW-1828-A-001  -> P1BW-1828-A
        """
        if not po_number or '-' not in po_number:
            return None

        parts = po_number.split('-')
        if len(parts) == 2:
            # Base document (no suffix letter); keep full number
            po_prefix = po_number
        else:
            po_prefix = '-'.join(parts[:-1])

        logger.info(f'PO Prefix extracted: {po_prefix}')
        return po_prefix

    def find_po_match(self, po_number: str, is_prefix: bool = False) -> Optional[Dict]:
        """
        Find an exact match for a PO number in RFMS.
        
        Args:
            po_number: The PO number to search for
            is_prefix: Whether to search by prefix
            
        Returns:
            The matching order details if found, None otherwise
        """
        if is_prefix:
            search_text = self.get_po_prefix(po_number)
            if not search_text:
                return None
        else:
            search_text = po_number

        search_results = self.find_order_by_po_number(search_text)
        logger.info(f'PO Search Results for {search_text}: {search_results}')
        
        if not search_results.get('result'):
            return None
            
        # Check for exact match in results
        for order in search_results.get('detail', []):
            candidate_po = order.get('poNumber')
            if not candidate_po:
                continue

            if is_prefix:
                if candidate_po == search_text:
                    return order

                candidate_prefix = self.get_po_prefix(candidate_po)
                if candidate_prefix == search_text:
                    return order

                if candidate_po.startswith(f"{search_text}-"):
                    return order
            else:
                if candidate_po == po_number:
                    return order
        
        return None

    def find_qr_match(self, qr_number: str, is_prefix: bool = False) -> Optional[Dict]:
        """
        Find an exact match for a QR number in RFMS.
        
        Args:
            qr_number: The QR number to search for
            is_prefix: Whether to search by prefix
            
        Returns:
            The matching quote details if found, None otherwise
        """
        if is_prefix:
            search_text = self.get_po_prefix(qr_number)  # Same logic for quotes
            if not search_text:
                return None
        else:
            search_text = qr_number

        search_results = self.find_quote_by_qr_number(search_text)
        logger.info(f'QR Search Results for {search_text}: {search_results}')
        
        if not search_results.get('result'):
            return None
            
        # Check for exact match in results
        for quote in search_results.get('detail', []):
            candidate_po = quote.get('poNumber')
            if not candidate_po:
                continue

            if is_prefix:
                if candidate_po == search_text:
                    return quote

                candidate_prefix = self.get_po_prefix(candidate_po)
                if candidate_prefix == search_text:
                    return quote

                if candidate_po.startswith(f"{search_text}-"):
                    return quote
            else:
                if candidate_po == qr_number:
                    return quote
        
        return None

    def create_billing_group(self, order_number: str, description: str = None) -> Dict:
        """
        Create a billing group for an order.
        
        Args:
            order_number: The order number to create billing group for
            description: Description for the billing group
            
        Returns:
            Dict: Response from the RFMS API
        """
        update_data = {
            "number": order_number,
            "billingGroup": {
                "description": description or f"Billing Group - {order_number}",
                "contactList": []
            }
        }
        
        endpoint = f"{self.base_url}/v2/order"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=update_data,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for create_billing_group, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to create billing group. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to create billing group after retry")

    def process_po_order(self, po_number: str, order_data: Dict) -> Dict:
        """
        Process a PO order - checks for existing PO matches and handles billing groups.
        
        Args:
            po_number: The PO number to process
            order_data: The order data to create if no match found
            
        Returns:
            Dict: Response containing the order details and status
        """
        # First check for exact PO match
        logger.info(f"Checking for existing PO: {po_number}")
        exact_match = self.find_po_match(po_number)
        if exact_match:
            logger.info(f"Found exact match: {exact_match}")
            return {
                'status': 'existing_order',
                'order': exact_match,
                'message': f"Order already exists with PO number {po_number}"
            }
            
        # Then check for prefix match (for billing groups)
        if '-' in po_number:
            prefix_match = self.find_po_match(po_number, is_prefix=True)
            logger.info(f"Prefix match result: {prefix_match}")
            if prefix_match:
                # Create the new order
                new_order = self.create_order(order_data)
                if not new_order.get('result'):
                    return {
                        'status': 'error',
                        'message': 'Failed to create new order',
                        'error': new_order
                    }
                    
                # Create billing group on the matched order if it doesn't have one
                prefix_match_groupId = prefix_match.get('billingGroupId')
                if prefix_match_groupId == 0:  # 0 means no billing group
                    self.create_billing_group(prefix_match['documentNumber'])
                    
                # Add new order to the billing group
                self.update_billing_group(
                    new_order['result'],
                    prefix_match['documentNumber']
                )
                
                return {
                    'status': 'billing_group_added',
                    'parent_order': prefix_match,
                    'order': new_order,
                    'message': f"Created new order and added to billing group with {prefix_match['documentNumber']}"
                }
            
        # If no matches found, create new order
        new_order = self.create_order(order_data)
        return {
            'status': 'new_order',
            'parent_order': None,
            'order': new_order,
            'message': 'Created new order'
        }

    def process_quote(self, qr_number: str, quote_data: Dict) -> Dict:
        """
        Process a quotation - checks for existing QR matches.
        
        Args:
            qr_number: The QR number to process
            quote_data: The quote data to create if no match found
            
        Returns:
            Dict: Response containing the quote details and status
        """
        # Check for exact QR match
        logger.info(f"Checking for existing quote: {qr_number}")
        exact_match = self.find_qr_match(qr_number)
        if exact_match:
            logger.info(f"Found exact quote match: {exact_match}")
            return {
                'status': 'existing_quote',
                'order': exact_match,
                'message': f"Quote already exists with QR number {qr_number}"
            }
            
        # If no match found, create new quote
        new_quote = self.create_quote(quote_data)
        return {
            'status': 'new_quote',
            'parent_order': None,
            'order': new_quote,
            'message': 'Created new quote'
        }

    def create_client(self, client_data: Dict) -> int:
        """
        Create a new client in RFMS. If a client with the same name and phone exists,
        returns the existing client ID.
        
        Args:
            client_data: Client data including name, address, and contact information
            
        Returns:
            int: The customer ID (either existing or newly created)
            
        Raises:
            Exception: If the API request fails for a reason other than duplicate client
        """
        endpoint = f"{self.base_url}/v2/customer"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            try:
                response = requests.post(
                    endpoint,
                    auth=self.auth,
                    json=client_data,
                    headers=self.headers,
                    timeout=30
                )
                
                # If authentication error, invalidate session and retry once
                if response.status_code in [401, 403] and attempt == 0:
                    logger.warning(f"Authentication failed for create_client, invalidating session and retrying...")
                    self._handle_auth_error(response)
                    continue
                
                # Check response status code first
                if response.status_code not in [200, 201]:
                    logger.error(f"RFMS API returned status {response.status_code} for customer creation")
                    logger.error(f"Response text: {response.text[:500]}")
                    raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
                
                # Check if response has content
                if not response.text or not response.text.strip():
                    logger.error("RFMS API returned empty response for customer creation")
                    raise Exception("RFMS API returned empty response")
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                except ValueError as e:
                    logger.error(f"Failed to parse JSON response from RFMS API: {e}")
                    logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                    raise Exception(f"Invalid JSON response from RFMS API: {response.text[:200]}")
                
                customer_detail = response_data.get('detail', {})
                
                # If client already exists, return the existing ID
                if response_data.get('status') == 'failed' and 'existingCustomerId' in customer_detail:
                    return customer_detail['existingCustomerId']
                
                # If successful creation, return the new ID
                if response_data.get('status') == 'success' and 'customerSourceId' in customer_detail:
                    return customer_detail['customerSourceId']
                    
                # Log the full response for debugging
                logger.error(f"Unexpected RFMS response structure: {response_data}")
                raise Exception(f"Failed to create client: {response_data}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error calling RFMS API: {str(e)}")
                raise Exception(f"Network error calling RFMS API: {str(e)}")
            except Exception as e:
                # If authentication error on second attempt, raise it
                if attempt == 1:
                    logger.error(f"Failed to create client after retry: {str(e)}")
                    raise
                # Re-raise if it's already our custom exception (but not auth errors)
                if "RFMS" in str(e) or "Failed to create client" in str(e):
                    # Check if it's an auth error that should be retried
                    if response.status_code in [401, 403] and attempt == 0:
                        self._handle_auth_error(response)
                        continue
                    raise
                # Otherwise wrap it
                logger.error(f"Unexpected error creating RFMS client: {str(e)}")
                raise Exception(f"Error creating RFMS client: {str(e)}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to create client after retry")

    def get_order(self, order_number: str, locked: bool = False, include_attachments: bool = True) -> Dict:
        """
        Get order details from RFMS.
        
        Args:
            order_number: The order number to retrieve (will be normalized to uppercase)
            locked: Whether to include locked orders
            include_attachments: Whether to include attachments in response
            
        Returns:
            Dict: Order details including attachments if requested
        """
        # Normalize order number to uppercase (RFMS stores orders in uppercase)
        order_number = str(order_number).strip().upper()
        endpoint = f"{self.base_url}/v2/order/{order_number}"
        params = {
            "locked": str(locked).lower(),
            "includeAttachments": str(include_attachments).lower()
        }
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.get(
                endpoint,
                auth=self.auth,
                params=params,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for order {order_number}, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to get order {order_number}. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to get order {order_number} after retry")

    def get_attachment(self, attachment_id: int) -> Dict:
        """
        Get attachment details from RFMS.
        
        Args:
            attachment_id: The attachment ID to retrieve
            
        Returns:
            Dict: Attachment details including file data
        """
        endpoint = f"{self.base_url}/v2/attachment/{attachment_id}"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for attachment {attachment_id}, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to get attachment {attachment_id}. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to get attachment {attachment_id} after retry")

    def find_jobs_by_date_range(self, start_date: str, end_date: str, crews: List[str] = None, 
                                job_status: List[str] = None, record_status: str = "Both") -> Dict:
        """
        Find scheduled jobs from Schedule Pro by date range.
        
        Uses a 2-prong approach as required by the API:
        1. Record status date range (startDate/endDate) - for jobs inserted/updated in this range
        2. Scheduled date range (scheduledStartDate/scheduledEndDate) - for jobs scheduled in this range
        
        Args:
            start_date: Start date in format MM-DD-YYYY (e.g., "01-01-2025")
            end_date: End date in format MM-DD-YYYY (e.g., "12-31-2025")
            crews: Optional list of crew names to filter by
            job_status: Optional list of job statuses to filter by
            record_status: "Inserted", "Updated", or "Both" (default: "Both")
            
        Returns:
            Dict: Job details including order information
        """
        endpoint = f"{self.base_url}/v2/jobs/find"
        
        # API requires BOTH date ranges: record status range AND scheduled date range
        payload = {
            "startDate": start_date,  # Record status date range start
            "endDate": end_date,      # Record status date range end
            "scheduledStartDate": start_date,  # Scheduled date range start
            "scheduledEndDate": end_date,      # Scheduled date range end
            "installStartDate": start_date,    # Install date range start (same as requested range)
            "installEndDate": end_date,        # Install date range end (same as requested range)
            "recordStatus": record_status
        }
        
        if crews:
            payload["crews"] = crews
        if job_status:
            payload["jobStatus"] = job_status
        
        # Log the request payload for debugging
        logger.info(f"Finding jobs with date range: {start_date} to {end_date} (store: {self.store_code})")
        logger.debug(f"Jobs find payload: {payload}")
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                # Log response summary
                if isinstance(result, dict):
                    jobs_count = 0
                    detail = result.get('detail')
                    if isinstance(detail, list):
                        jobs_count = len(detail)
                    elif isinstance(detail, dict) and 'jobs' in detail:
                        jobs_count = len(detail.get('jobs', []))
                    if 'jobs' in result:
                        jobs_count = len(result.get('jobs', []))
                    logger.info(f"Found {jobs_count} jobs for date range {start_date} to {end_date}")
                return result
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for jobs find, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to find jobs. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to find jobs after retry")

    def find_purchase_order(self, order_number: str, line_number: int = 1) -> Optional[Dict]:
        """
        Find a purchase order by order number and line number.
        
        Args:
            order_number: The order number (e.g., "CG105159", "#ST123", "ST123")
            line_number: The line number (default: 1)
            
        Returns:
            Optional[Dict]: Purchase order details if found, None otherwise
        """
        endpoint = f"{self.base_url}/v2/order/purchaseorder/find"
        payload = {
            "number": order_number,
            "lineNumber": line_number
        }
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('status') == 'success' and result.get('result'):
                    return result.get('result')
                return None
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for find_purchase_order, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, return None (purchase order not found)
            if response.status_code == 404:
                return None
            
            logger.error(f"Failed to find purchase order. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return None
        
        return None
    
    def find_st_order(self, order_number: str) -> Optional[Dict]:
        """
        Find a #ST order (General Warehouse stock order).
        Tries multiple search strategies since #ST orders may be stored differently.
        
        Args:
            order_number: The order number (e.g., "#ST123", "ST123", "#ST-123")
            
        Returns:
            Optional[Dict]: Order details if found, None otherwise
        """
        # Normalize the order number - try with and without #
        order_upper = order_number.upper().strip()
        search_variations = []
        
        if order_upper.startswith('#ST'):
            # Has #, try both with and without
            base = order_upper[1:]  # Remove #
            search_variations = [order_upper, base, f"ST{base[2:]}"]  # Also try without ST prefix
        elif order_upper.startswith('ST'):
            # No #, try with and without
            search_variations = [order_upper, f"#{order_upper}", order_upper[2:]]  # Also try without ST
        
        # Add original
        if order_number not in search_variations:
            search_variations.insert(0, order_number)
        
        logger.info(f"Searching for #ST order with variations: {search_variations}")
        
        # Try regular order search first
        for variation in search_variations:
            orders = self.find_orders_by_search(variation)
            for order in orders:
                order_num = order.get('documentNumber') or order.get('number', '')
                if order_num and (order_num.upper().startswith('#ST') or order_num.upper().startswith('ST')):
                    # Get full order details
                    try:
                        full_order = self.get_order(order_num)
                        if full_order and full_order.get('status') == 'success':
                            return full_order.get('result')
                    except:
                        pass
                    return order
        
        # Try purchase order search (try only line 1 to avoid 500 errors)
        for variation in search_variations:
            # Only try line 1 for #ST orders to avoid excessive 500 errors from RFMS API
            try:
                po_result = self.find_purchase_order(variation, 1)
                if po_result:
                    po_num = po_result.get('number') or po_result.get('orderNumber', '')
                    if po_num and (po_num.upper().startswith('#ST') or po_num.upper().startswith('ST')):
                        # Get full order details
                        try:
                            full_order = self.get_order(po_num)
                            if full_order and full_order.get('status') == 'success':
                                return full_order.get('result')
                        except:
                            pass
                        return po_result
            except Exception as e:
                # Stop trying if we get a 500 error (order doesn't exist in that format)
                if '500' in str(e) or 'error has occurred' in str(e).lower():
                    break
                continue
        
        logger.warning(f"Could not find #ST order: {order_number}")
        return None

    def find_orders_by_search(self, search_text: str) -> List[Dict]:
        """
        Search for orders using search text (can match order numbers, PO numbers, etc.).
        
        Args:
            search_text: Text to search for (order number, PO number, customer name, etc.)
            
        Returns:
            List[Dict]: List of matching orders
        """
        endpoint = f"{self.base_url}/v2/order/find"
        payload = {"searchText": search_text}
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('status') == 'success':
                    return result.get('detail', [])
                return []
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for find_orders_by_search, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors, return empty list
            logger.error(f"Failed to search orders. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return []
        
        return []

    def find_products(self, search_text: str) -> List[Dict]:
        """
        Search for products/stock items.
        
        Args:
            search_text: Text to search for (product code, name, etc.)
            
        Returns:
            List[Dict]: List of matching products
        """
        endpoint = f"{self.base_url}/v2/product/find"
        payload = {"searchText": search_text}
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('status') == 'success':
                    return result.get('detail', [])
                return []
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for find_products, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors, return empty list
            logger.error(f"Failed to search products. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            return []
        
        return []

    def deliver_inventory(self, order_number: str, order_date: str, line_numbers: List[int]) -> Dict:
        """
        Deliver/receive inventory for an order.
        
        Args:
            order_number: The order number (e.g., "CG402092")
            order_date: The order date in format MM-DD-YYYY (e.g., "06-20-2024")
            line_numbers: List of line numbers to deliver
            
        Returns:
            Dict: Response from the RFMS API
        """
        endpoint = f"{self.base_url}/v2/order/inventory/deliver"
        payload = {
            "orderNumber": order_number,
            "orderDate": order_date,
            "lines": line_numbers
        }
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                return response.json()
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for deliver_inventory, invalidating session and retrying...")
                self._handle_auth_error(response)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to deliver inventory. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to deliver inventory after retry")
    
    def passthrough(self, method_name: str, request_payload: Dict, username: str = None) -> Dict:
        """
        Call RFMS passthrough endpoint to execute raw RFMS methods.
        
        Args:
            method_name: The RFMS method name (e.g., "Inventory.ReceiveFromInvoice")
            request_payload: The payload for the method (will be merged with username and legacy)
            username: Username for the request (optional, will use store_code if not provided)
            
        Returns:
            Dict: Response from the RFMS API
        """
        endpoint = f"{self.base_url}/v2/passthrough"
        
        # Get username from environment or use store_code
        if not username:
            username = os.environ.get('RFMS_USERNAME', self.store_code)
        
        payload = {
            "methodName": method_name,
            "requestPayload": {
                "username": username,
                "legacy": False,
                **request_payload
            }
        }
        
        logger.info(f"Calling passthrough method: {method_name}")
        logger.debug(f"Passthrough payload keys: {list(payload.get('requestPayload', {}).keys())}")
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Passthrough response status: {result.get('status')}")
                if result.get('status') == 'success':
                    detail = result.get('detail', {})
                    logger.info(f"Passthrough detail keys: {list(detail.keys()) if detail else 'None'}")
                return result
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for passthrough (HTTP {response.status_code}), invalidating session and retrying...")
                self._handle_auth_error(response)
                try:
                    self.start_session(force=True)
                    logger.info(f"New session started, retrying passthrough call...")
                except Exception as session_error:
                    logger.error(f"Failed to start new session: {session_error}")
                    raise Exception(f"RFMS authentication failed and could not refresh session: {session_error}")
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to call passthrough method {method_name}. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to call passthrough method {method_name} after retry")
    
    def receive_inventory_from_invoice(self, order_number: str, order_date: str, line_numbers: List[int],
                                       supplier_name: str = None, invoice_number: str = None,
                                       satisfy_po: bool = True, line_data: List[Dict] = None) -> Dict:
        """
        Receive inventory using Inventory.ReceiveFromInvoice passthrough method.
        This method can satisfy/close purchase orders when satisfy_po is True.
        
        Args:
            order_number: The order number (e.g., "CG402092")
            order_date: The order date in format MM-DD-YYYY (e.g., "06-20-2024")
            line_numbers: List of line numbers to receive
            supplier_name: Supplier name (optional, will try to get from order if not provided)
            invoice_number: Invoice number (optional, for costing)
            satisfy_po: If True, will satisfy/close the purchase order (default: True)
            line_data: Detailed line data with boxes, measurements, etc. (optional)
            
        Returns:
            Dict: Response from the RFMS API with ReceivingResults and CostingResults
        """
        # Get order details to build inventory data rows
        try:
            order_details = self.get_order(order_number)
            if not order_details or order_details.get('status') != 'success':
                raise Exception(f"Order {order_number} not found")
            
            order_result = order_details.get('result', {})
            lines = order_result.get('lines', []) or order_result.get('lineItems', [])
            
            # Filter lines to only those being received
            lines_to_receive = [line for line in lines if line.get('lineNumber') in line_numbers]
            
            if not lines_to_receive:
                raise Exception(f"No matching lines found for line numbers {line_numbers}")
            
            # Get supplier name from order if not provided
            if not supplier_name:
                # Try to get from first line
                if lines_to_receive and lines_to_receive[0].get('supplierName'):
                    supplier_name = lines_to_receive[0].get('supplierName')
                elif order_result.get('supplierName'):
                    supplier_name = order_result.get('supplierName')
                else:
                    supplier_name = "UNKNOWN SUPPLIER"
            
            # Build inventory data rows
            inventory_data_rows = []
            for line in lines_to_receive:
                line_num = line.get('lineNumber')
                
                # Get corresponding line_data if provided
                line_info = None
                if line_data:
                    line_info = next((ld for ld in line_data if ld.get('line_number') == line_num), None)
                
                # Determine if roll stock or item based on product code
                product_code = str(line.get('productCode', '')).strip()
                is_roll_stock = product_code in ['01', '1'] or 'CARPET' in str(line.get('description', '')).upper()
                
                # Parse date to RFMS format
                date_received = self._parse_date_to_rfms_format(order_date)
                
                # Build inventory row
                inventory_row = {
                    "Seqnum": 0,
                    "Store": order_result.get('storeNumber', self.store_number),  # Use configured store number
                    "ProductCode": product_code,
                    "RollItemNumber": line.get('rollItemNumber', ''),
                    "ItemSequenceNumber": 0,
                    "Supplier": supplier_name,
                    "PrivateSupplier": supplier_name,
                    "StyleItem": line.get('styleName', ''),
                    "ColorDescription": line.get('colorName', ''),
                    "Width": "12",  # Default, may need to get from product
                    "Length": "100",  # Default, may need to get from product
                    "InitialAmount": line.get('quantity', 0),
                    "InitialQuantity": line.get('quantity', 0),
                    "Used": 0,
                    "Reserved": 0,
                    "Available": line.get('quantity', 0),
                    "AvailableQuantity": line.get('quantity', 0),
                    "DateReceived": date_received,
                    "InvoiceNumber": invoice_number or "",
                    "GrossCost": line.get('unitPrice', 0) or 0,
                    "NetCost": line.get('unitPrice', 0) or 0,
                    "Freight": 0,
                    "Load": 0,
                    "Units": line.get('saleUnits', 'SF'),
                    "DyeLot": "",
                    "LadingNumber": "",
                    "SerialNumber": "",
                    "PONumber": order_number,
                    "Sidemark": "",
                    "StyleNumber": line.get('styleNumber', ''),
                    "ColorNumber": line.get('colorNumber', ''),
                    "PriceListSeqNum": 0,
                    "ColorSeqNum": 0,
                    "UnitPrice": line.get('unitPrice', 0) or 0,
                    "TotalValue": line.get('total', 0) or 0,
                    "UseTotalValue": False,
                    "Sku": " ",
                    "ManufacturerSKU": " ",
                    "Manufacturer": "",
                    "Location": "",
                    "InventoryType": "Roll" if is_roll_stock else "Item",
                    "InitialTotalValue": line.get('total', 0) or 0,
                    "CanConsolidate": False,
                    "Collection": "",
                    "PrivateCollection": "",
                    "Builder": "",
                    "SubDivision": "",
                    "Block": "",
                    "Lot": "",
                    "POSeqNum": 0,
                    "ItemWidth": "",
                    "ItemLength": "",
                    "SoftReserve": 0,
                    "Receiving_Backing": 0,
                    "Receiving_Quality": 0,
                    "Receiving_RollCut": "Roll" if is_roll_stock else "Item",
                    "Receiving_FiberType": 0,
                    "Receiving_StyleType": 0,
                    "Receiving_ColorType": 0,
                    "Receiving_Weight": 0,
                    "Receiving_Pile": 0,
                    "Receiving_ToxicityNumber": "",
                    "Receiving_Comments": "",
                    "Receiving_UserReal1": 0,
                    "Receiving_ASNItemSeqNum": 0,
                    "Receiving_RunLot": "",
                    "Receiving_PrintTags": False,
                    "Receiving_SatisfyPo": satisfy_po,  # KEY: This should close the PO!
                    "Receiving_Load": 0
                }
                
                # Update with line_data if available
                if line_info:
                    if line_info.get('boxes'):
                        inventory_row["InitialAmount"] = line_info.get('boxes')
                    if line_info.get('square_meters'):
                        inventory_row["InitialQuantity"] = line_info.get('square_meters')
                    elif line_info.get('linear_meters'):
                        inventory_row["InitialQuantity"] = line_info.get('linear_meters')
                
                inventory_data_rows.append(inventory_row)
            
            # Build the passthrough payload
            passthrough_payload = {
                "inventoryCosting": {
                    "Supplier": supplier_name,
                    "InvoiceNumber": invoice_number or "",
                    "DueDate": date_received,
                    "DiscountRate": 0.0,
                    "Freight": 0.0,
                    "FreightIsDiscountable": False,
                    "ExtraCost1": 0.0,
                    "ExtraCost1IsDiscountable": False,
                    "ExtraCost2": 0.0,
                    "ExtraCost2IsDiscountable": False,
                    "InventoryDataRows": inventory_data_rows,
                    "Payable": None,  # Can be set for AP record creation (future enhancement)
                    "ApplyProductFreightFactor": False
                }
            }
            
            # Call the passthrough method
            logger.info(f"Calling Inventory.ReceiveFromInvoice with satisfy_po={satisfy_po} for order {order_number}")
            result = self.passthrough("Inventory.ReceiveFromInvoice", passthrough_payload)
            
            # Log the receiving results
            if result.get('status') == 'success' and result.get('detail'):
                detail = result.get('detail', {})
                receiving_results = detail.get('ReceivingResults', {})
                if receiving_results:
                    logger.info(f"Receiving result: {receiving_results.get('Message', 'N/A')}")
                    logger.info(f"Receiving method: {receiving_results.get('Method', 'N/A')}")
                    if receiving_results.get('IsError'):
                        logger.error(f"Receiving error: {receiving_results}")
                    else:
                        logger.info(f"Receiving successful - PO satisfied: {satisfy_po}")
                        if satisfy_po:
                            logger.info(f"Purchase order {order_number} should now be closed in RFMS")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in receive_inventory_from_invoice: {str(e)}", exc_info=True)
            raise
    
    def _parse_date_to_rfms_format(self, date_str: str) -> Dict:
        """
        Parse date string to RFMS date format {Year, Month, Day}
        
        Args:
            date_str: Date in MM-DD-YYYY or YYYY-MM-DD format
            
        Returns:
            Dict with Year, Month, Day keys
        """
        try:
            # Try MM-DD-YYYY first
            if '-' in date_str and len(date_str.split('-')[0]) == 2:
                parts = date_str.split('-')
                month, day, year = int(parts[0]), int(parts[1]), int(parts[2])
            # Try YYYY-MM-DD
            elif '-' in date_str and len(date_str.split('-')[0]) == 4:
                parts = date_str.split('-')
                year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
            else:
                # Try to parse as datetime
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                year, month, day = dt.year, dt.month, dt.day
            
            return {
                "Year": year,
                "Month": month,
                "Day": day
            }
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            # Return today's date as fallback
            today = datetime.now()
            return {
                "Year": today.year,
                "Month": today.month,
                "Day": today.day
            }
    
    def create_payable(self, supplier_name: str, invoice_number: str, invoice_date: str, 
                      due_date: str, discountable_amount: float = 0.0, 
                      non_discountable_amount: float = 0.0, discount_rate: float = 0.0,
                      linked_document_number: str = "", internal_notes: str = "",
                      remittance_advice_notes: str = "", detail_lines: List[Dict] = None) -> Dict:
        """
        Create an Accounts Payable record in RFMS.
        This method requires "Plus" level API access.
        
        Args:
            supplier_name: Supplier name (who the bill is from)
            invoice_number: Invoice number (must be unique per supplier)
            invoice_date: Invoice date (format: "M/D/YY" or "MM/DD/YYYY")
            due_date: Due date (format: "M/D/YY" or "MM/DD/YYYY")
            discountable_amount: Discountable amount (default: 0.0)
            non_discountable_amount: Non-discountable amount (default: 0.0)
            discount_rate: Discount rate (default: 0.0)
            linked_document_number: Linked document number (optional)
            internal_notes: Internal notes (optional)
            remittance_advice_notes: Remittance advice notes (optional)
            detail_lines: List of detail line dictionaries, each with:
                - storeNumber: Store number (must be 49, not display code)
                - accountCode: Account code
                - subAccountCode: Sub account code (optional)
                - amount: Amount
                - comment: Comment (optional)
        
        Returns:
            Dict: Response from the RFMS API
        """
        endpoint = f"{self.base_url}/v2/payables"
        
        # Build the payable record
        payable = {
            "supplierName": supplier_name,
            "invoiceNumber": invoice_number,
            "invoiceDate": invoice_date,
            "dueDate": due_date,
            "discountableAmount": discountable_amount,
            "nonDiscountableAmount": non_discountable_amount,
            "discountRate": discount_rate,
            "linkedDocumentNumber": linked_document_number,
            "internalNotes": internal_notes,
            "remittanceAdviceNotes": remittance_advice_notes,
            "detailLines": detail_lines or []
        }
        
        # API expects an array of payables
        payload = [payable]
        
        logger.info(f"Creating payable for supplier {supplier_name}, invoice {invoice_number}")
        logger.debug(f"Payable payload: {payload}")
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Create payable response: {result.get('status')}, result: {result.get('result')}")
                if result.get('status') == 'success':
                    logger.info(f"Payable created successfully: {result.get('result')}")
                return result
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for create_payable, invalidating session and retrying...")
                self._handle_auth_error(response)
                self.start_session(force=True)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to create payable. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to create payable after retry")
    
    def get_suppliers(self) -> Dict:
        """
        Get all suppliers from RFMS.
        
        Returns:
            Dict: Response from the RFMS API with list of suppliers
        """
        endpoint = f"{self.base_url}/v2/suppliers"
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.get(
                endpoint,
                auth=self.auth,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Get suppliers response: {result.get('status')}, count: {len(result.get('detail', []))}")
                return result
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for get_suppliers, invalidating session and retry...")
                self._handle_auth_error(response)
                self.start_session(force=True)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to get suppliers. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to get suppliers after retry")
    
    def find_supplier_by_name(self, supplier_name: str) -> Optional[Dict]:
        """
        Search for a supplier by name (case-insensitive partial match).
        
        Args:
            supplier_name: Supplier name to search for
            
        Returns:
            Dict with supplier details if found, None otherwise
        """
        try:
            suppliers_result = self.get_suppliers()
            if suppliers_result.get('status') != 'success':
                return None
            
            suppliers = suppliers_result.get('detail', [])
            if not isinstance(suppliers, list):
                return None
            
            supplier_name_lower = supplier_name.lower().strip()
            
            # Try exact match first
            for supplier in suppliers:
                if supplier.get('name', '').lower().strip() == supplier_name_lower:
                    return supplier
            
            # Try partial match
            for supplier in suppliers:
                supplier_name_in_list = supplier.get('name', '').lower().strip()
                if supplier_name_lower in supplier_name_in_list or supplier_name_in_list in supplier_name_lower:
                    return supplier
            
            # Try word-by-word matching
            supplier_words = set(supplier_name_lower.split())
            for supplier in suppliers:
                supplier_name_in_list = supplier.get('name', '').lower().strip()
                supplier_words_in_list = set(supplier_name_in_list.split())
                if len(supplier_words.intersection(supplier_words_in_list)) >= 2:
                    return supplier
            
            return None
        except Exception as exc:
            logger.error(f"Error finding supplier by name: {exc}", exc_info=True)
            return None
    
    def post_provider_record(self, document_number: str, line_number: int, 
                            install_date: str, supplier_id: int) -> Dict:
        """
        Post a provider record to an order in RFMS.
        
        Args:
            document_number: Order/document number (e.g., "CG203699")
            line_number: Line number on the order (integer, e.g., 1)
            install_date: Installation date in format "YYYY-MM-DD" (e.g., "2022-04-07")
            supplier_id: RFMS supplier ID (integer, e.g., 71)
        
        Returns:
            Dict: Response from the RFMS API
        """
        endpoint = f"{self.base_url}/v2/order/provider"
        
        payload = {
            "documentNumber": document_number,
            "lineNumber": line_number,
            "installDate": install_date,
            "supplierId": supplier_id
        }
        
        logger.info(f"Posting provider record: {document_number}, line {line_number}, supplier {supplier_id}")
        logger.debug(f"Provider payload: {payload}")
        
        # Try request, retry once if 401/403 (session expired)
        for attempt in range(2):
            response = requests.post(
                endpoint,
                auth=self.auth,
                json=payload,
                headers=self.headers
            )
            
            # If successful, return the data
            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Post provider record response: {result.get('status')}, result: {result.get('result')}")
                if result.get('status') == 'success':
                    logger.info(f"Provider record posted successfully for order {document_number}")
                return result
            
            # If authentication error, invalidate session and retry once
            if response.status_code in [401, 403] and attempt == 0:
                logger.warning(f"Authentication failed for post_provider_record, invalidating session and retrying...")
                self._handle_auth_error(response)
                self.start_session(force=True)
                continue
            
            # For other errors or if retry failed, raise exception
            logger.error(f"Failed to post provider record. Status code: {response.status_code}")
            logger.error(f"Response: {response.text[:500]}")
            raise Exception(f"RFMS API error: HTTP {response.status_code} - {response.text[:200]}")
        
        # Should never reach here, but just in case
        raise Exception(f"RFMS API error: Failed to post provider record after retry")

