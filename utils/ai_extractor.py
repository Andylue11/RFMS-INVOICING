from google import genai
import json
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger(__name__)

class AIExtractor:
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.model_name = 'gemini-2.5-flash'
        
    def extract_data_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from PDF text using Google Gemini.
        """
        try:
            prompt = self._create_extraction_prompt(text)
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            
            extracted_text = response.text.strip()
            
            # Try to parse as JSON
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_text = extracted_text.strip()
                if cleaned_text.startswith('```json'):
                    cleaned_text = cleaned_text[7:]  # Remove ```json
                if cleaned_text.endswith('```'):
                    cleaned_text = cleaned_text[:-3]  # Remove ```
                cleaned_text = cleaned_text.strip()
                
                extracted_data = json.loads(cleaned_text)
                logger.info("Successfully extracted data using Gemini AI")
                return extracted_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                logger.error(f"AI Response: {extracted_text}")
                return self._fallback_extraction(text)
                
        except Exception as e:
            logger.error(f"Error in AI extraction: {str(e)}")
            return self._fallback_extraction(text)
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a detailed prompt for AI extraction."""
        return f"""
You are an expert at extracting structured data from construction work orders and invoices. 

Extract the following information from this document text and return it as a clean JSON object:

{text}

IMPORTANT EXTRACTION RULES:
1. For customer_name: Extract ONLY the actual customer/client name, not labels or other text
2. For scope_of_work: Extract the detailed description of work to be performed, including room details and materials
3. For po_number: Look for "Work Order Number", "Job Number", "Client Reference", or "PO" fields
4. For addresses: Parse the full address into components (street, city, state, postal code)
5. For phone numbers: Distinguish between customer contact and supervisor contact
6. For dates: Extract actual dates, not just the word "Date"

Return a JSON object with these exact fields:
{{
    "customer_name": "Clean customer name only (e.g., 'Derek Mathieson')",
    "business_name": "Business or company name if mentioned",
    "po_number": "Work order number or reference (e.g., 'TB-5173-3329')",
    "scope_of_work": "Detailed work description including room and materials (e.g., 'MEDIA ROOM - 5.5m w x 2.7m L, supply and install medium grade carpet with underlay')",
    "dollar_value": "Total dollar amount as number only (e.g., 1298.33)",
    "first_name": "Customer's first name only",
    "last_name": "Customer's last name only", 
    "address1": "Street address (e.g., '2 Kinloch Road')",
    "address2": "Additional address info if present",
    "city": "City name (e.g., 'Daisy Hill')",
    "state": "State or province (e.g., 'QLD')",
    "postal_code": "Postal code (e.g., '4127')",
    "phone": "Customer contact phone number",
    "mobile": "Mobile phone if different from main phone",
    "email": "Email address",
    "commencement_date": "Start date if mentioned",
    "completion_date": "Completion date if mentioned",
    "supervisor_name": "Supervisor name (e.g., 'Petra Ririnui')",
    "supervisor_phone": "Supervisor phone number",
    "description_of_works": "Alternative work description",
    "builder_type": "Company name (e.g., 'A to Z Flooring Solutions')"
}}

CRITICAL: 
- Extract ONLY the actual values, not labels or surrounding text
- Be precise with field separation
- If a field is not found, use null or empty string
- Return ONLY the JSON object, no additional text
"""
    
    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using basic text parsing."""
        logger.info("Using fallback extraction method")
        
        # Basic extraction patterns
        import re
        
        extracted = {
            "customer_name": "",
            "business_name": "",
            "po_number": "",
            "scope_of_work": "",
            "dollar_value": 0,
            "first_name": "",
            "last_name": "",
            "address1": "",
            "address2": "",
            "city": "",
            "state": "",
            "postal_code": "",
            "phone": "",
            "mobile": "",
            "email": "",
            "commencement_date": "",
            "completion_date": "",
            "supervisor_name": "",
            "supervisor_phone": "",
            "description_of_works": "",
            "builder_type": ""
        }
        
        # Basic patterns for common fields
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, text)
        if email_match:
            extracted["email"] = email_match.group(0)
        
        phone_pattern = r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
        phone_matches = re.findall(phone_pattern, text)
        if phone_matches:
            extracted["phone"] = phone_matches[0]
            if len(phone_matches) > 1:
                extracted["mobile"] = phone_matches[1]
        
        # Dollar amount pattern
        dollar_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        dollar_matches = re.findall(dollar_pattern, text)
        if dollar_matches:
            try:
                # Convert to float, removing commas
                amount = float(dollar_matches[-1].replace(',', ''))
                extracted["dollar_value"] = amount
            except ValueError:
                pass
        
        return extracted
