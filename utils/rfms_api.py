import requests
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class RfmsApi:
    def __init__(self, base_url: str, store_code: str, username: str, api_key: str):
        self.base_url = base_url
        self.store_code = store_code
        self.username = username
        self.api_key = api_key
        self.session_token = None

    def get_session_token(self) -> Optional[str]:
        """Get RFMS API session token."""
        try:
            response = requests.post(
                f"{self.base_url}/v2/session/begin",
                auth=(self.store_code, self.api_key),
                headers={'Content-Type': 'application/json'},
                json={}  # Add empty JSON body
            )
            
            if response.status_code == 200:
                data = response.json()
                self.session_token = data.get('sessionToken')
                return self.session_token
            else:
                logger.error(f"Failed to get session token. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error getting session token: {str(e)}")
            return None

    def find_customers(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for customers in RFMS."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return []

        try:
            payload = {
                "searchText": search_term,
                "includeCustomers": True,
                "includeProspects": False,
                "includeInactive": False,
                "startIndex": 0
            }
            
            response = requests.post(
                f"{self.base_url}/v2/customers/find",
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )

            if response.status_code == 200:
                data = response.json()
                # The API returns customers in the 'detail' field
                if isinstance(data, dict) and 'detail' in data:
                    return data['detail']
                elif isinstance(data, dict) and 'customers' in data:
                    return data['customers']
                elif isinstance(data, list):
                    return data
                else:
                    logger.warning(f"Unexpected response format: {data}")
                    return []
            else:
                logger.error(f"Failed to search customers. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return []
        except Exception as e:
            logger.error(f"Error searching customers: {str(e)}")
            return []

    def create_customer(self, customer_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new customer in RFMS."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return None

        try:
            # Transform the customer data to match RFMS API format
            rfms_payload = {
                "customerType": customer_data.get('customerType', 'COMMERCIAL'),
                "entryType": "Customer",
                "customerAddress": {
                    "lastName": customer_data.get('last_name', ''),
                    "firstName": customer_data.get('first_name', ''),
                    "address1": customer_data.get('address1', ''),
                    "address2": customer_data.get('address2', ''),
                    "city": customer_data.get('city', ''),
                    "state": customer_data.get('state', ''),
                    "postalCode": customer_data.get('postal_code', ''),
                    "county": customer_data.get('county', '')
                },
                "shipToAddress": {
                    "lastName": customer_data.get('last_name', ''),
                    "firstName": customer_data.get('first_name', ''),
                    "address1": customer_data.get('address1', ''),
                    "address2": customer_data.get('address2', ''),
                    "city": customer_data.get('city', ''),
                    "state": customer_data.get('state', ''),
                    "postalCode": customer_data.get('postal_code', ''),
                    "county": customer_data.get('county', '')
                },
                "phone1": customer_data.get('phone', ''),
                "phone2": customer_data.get('mobile', ''),
                "email": customer_data.get('email', ''),
                "taxStatus": "Tax",
                "taxMethod": "SalesTax",
                "preferredSalesperson1": customer_data.get('preferredSalesperson1', ''),
                "preferredSalesperson2": customer_data.get('preferredSalesperson2', '')
            }
            
            response = requests.post(
                f"{self.base_url}/v2/customer",
                json=rfms_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create customer. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            return None

    def create_order(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new order in RFMS using the correct payload structure."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return None

        try:
            # Transform the order data to match RFMS API format (using working example structure)
            dollar_value = order_data.get('dollar_value', 0)
            
            # Ensure we have a valid date format
            completion_date = order_data.get('completion_date', '')
            if not completion_date:
                completion_date = '2024-12-31'  # Default date if none provided
            
            rfms_payload = {
                "category": "Order",
                "poNumber": order_data.get('po_number', ''),
                "estimatedDeliveryDate": completion_date,
                "jobNumber": f"{order_data.get('supervisor_name', '')} {order_data.get('supervisor_phone', '')}".strip(),
                "CustomerSource": "Customer",
                "CustomerSeqNum": order_data.get('sold_to_customer_id', 2),
                "CustomerUpSeqNum": 0,
                "CustomerFirstName": order_data.get('supervisor_name', '').split(' ')[0] if order_data.get('supervisor_name') else 'Test',
                "CustomerLastName": ' '.join(order_data.get('supervisor_name', '').split(' ')[1:]) if order_data.get('supervisor_name') and len(order_data.get('supervisor_name', '').split(' ')) > 1 else 'Sold',
                "CustomerAddress1": order_data.get('sold_to_address1', '123 Test Rd'),
                "CustomerAddress2": "",
                "CustomerCity": order_data.get('sold_to_city', 'Test City'),
                "CustomerState": order_data.get('sold_to_state', 'QLD'),
                "CustomerPostalCode": order_data.get('sold_to_postal_code', '4000'),
                "CustomerCounty": "",
                "Phone1": order_data.get('supervisor_phone', ''),
                "ShipToFirstName": order_data.get('first_name', ''),
                "ShipToLastName": order_data.get('last_name', ''),
                "ShipToAddress1": order_data.get('address1', ''),
                "ShipToAddress2": order_data.get('address2', ''),
                "ShipToCity": order_data.get('city', ''),
                "ShipToState": order_data.get('state', ''),
                "ShipToPostalCode": order_data.get('postal_code', ''),
                "ShipToCounty": "",
                "Phone2": order_data.get('phone', ''),
                "ShipToLocked": False,
                "SalesPerson1": "ZORAN VEKIC",
                "SalesPerson2": "",
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": 49,
                "Email": order_data.get('email', ''),
                "CustomNote": "",
                "privateNotes": f"PDF Extracted - Supervisor: {order_data.get('supervisor_name', '')} | PO: {order_data.get('po_number', '')} | Value: ${order_data.get('dollar_value', 0)} | Phone: {order_data.get('phone', '')} | Email: {order_data.get('email', '')}",
                "publicNotes": order_data.get('description_of_works', ''),
                "adSource": 1,
                "UserOrderType": 12,
                "ServiceType": 9,
                "ContractType": 2,
                "PriceLevel": 5,
                "TaxStatus": "Tax",
                "Occupied": False,
                "Voided": False,
                "TaxStatusLocked": False,
                "TaxInclusive": False,
                "totalAmount": dollar_value
            }
            
            # Debug: Log the payload being sent
            logger.info(f"Order creation payload: {rfms_payload}")
            
            response = requests.post(
                f"{self.base_url}/v2/order/create",
                json=rfms_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create order. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return None

    def create_quote(self, quote_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new quote in RFMS using the same structure as orders."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return None

        try:
            # Transform the quote data to match RFMS API format (using working example structure)
            dollar_value = quote_data.get('dollar_value', 0)
            
            # Ensure we have a valid date format
            completion_date = quote_data.get('completion_date', '')
            if not completion_date:
                completion_date = '2024-12-31'  # Default date if none provided
            
            rfms_payload = {
                "category": "Quote",
                "poNumber": quote_data.get('po_number', ''),
                "estimatedDeliveryDate": completion_date,
                "jobNumber": f"{quote_data.get('supervisor_name', '')} {quote_data.get('supervisor_phone', '')}".strip(),
                "CustomerSource": "Customer",
                "CustomerSeqNum": quote_data.get('sold_to_customer_id', 2),
                "CustomerUpSeqNum": 0,
                "CustomerFirstName": quote_data.get('supervisor_name', '').split(' ')[0] if quote_data.get('supervisor_name') else 'Test',
                "CustomerLastName": ' '.join(quote_data.get('supervisor_name', '').split(' ')[1:]) if quote_data.get('supervisor_name') and len(quote_data.get('supervisor_name', '').split(' ')) > 1 else 'Sold',
                "CustomerAddress1": quote_data.get('sold_to_address1', '123 Test Rd'),
                "CustomerAddress2": "",
                "CustomerCity": quote_data.get('sold_to_city', 'Test City'),
                "CustomerState": quote_data.get('sold_to_state', 'QLD'),
                "CustomerPostalCode": quote_data.get('sold_to_postal_code', '4000'),
                "CustomerCounty": "",
                "Phone1": quote_data.get('supervisor_phone', ''),
                "ShipToFirstName": quote_data.get('first_name', ''),
                "ShipToLastName": quote_data.get('last_name', ''),
                "ShipToAddress1": quote_data.get('address1', ''),
                "ShipToAddress2": quote_data.get('address2', ''),
                "ShipToCity": quote_data.get('city', ''),
                "ShipToState": quote_data.get('state', ''),
                "ShipToPostalCode": quote_data.get('postal_code', ''),
                "ShipToCounty": "",
                "Phone2": quote_data.get('phone', ''),
                "ShipToLocked": False,
                "SalesPerson1": "ZORAN VEKIC",
                "SalesPerson2": "",
                "SalesRepLocked": False,
                "CommisionSplitPercent": 0.0,
                "Store": 49,
                "Email": quote_data.get('email', ''),
                "CustomNote": "",
                "privateNotes": f"PDF Extracted - Supervisor: {quote_data.get('supervisor_name', '')} | PO: {quote_data.get('po_number', '')} | Value: ${quote_data.get('dollar_value', 0)} | Phone: {quote_data.get('phone', '')} | Email: {quote_data.get('email', '')}",
                "publicNotes": quote_data.get('description_of_works', ''),
                "adSource": 1,
                "UserOrderType": 12,
                "ServiceType": 9,
                "ContractType": 2,
                "PriceLevel": 5,
                "TaxStatus": "Tax",
                "Occupied": False,
                "Voided": False,
                "TaxStatusLocked": False,
                "TaxInclusive": False,
                "totalAmount": dollar_value
            }
            
            response = requests.post(
                f"{self.base_url}/v2/quote/create",
                json=rfms_payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create quote. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating quote: {str(e)}")
            return None

    def create_job(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new job in RFMS."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return None

        try:
            response = requests.post(
                f"{self.base_url}/v2/job/create",
                json=job_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create job. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            return None

    def add_to_billing_group(self, job_ids: List[int]) -> Optional[Dict[str, Any]]:
        """Add jobs to a billing group in RFMS."""
        if not self.session_token:
            self.get_session_token()
            if not self.session_token:
                return None

        try:
            billing_data = {"job_ids": job_ids}
            response = requests.post(
                f"{self.base_url}/v2/billing-group/create",
                json=billing_data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                auth=(self.store_code, self.session_token)
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to create billing group. Status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating billing group: {str(e)}")
            return None

    def check_api_status(self) -> bool:
        """Check if the RFMS API is accessible."""
        try:
            response = requests.get(
                f"{self.base_url}/v2/status",
                auth=(self.store_code, self.api_key)
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking API status: {str(e)}")
            return False 