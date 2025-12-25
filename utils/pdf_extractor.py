import pdfplumber
import re
import os
from typing import Dict, Optional, Any
from .template_detector import TemplateDetector, BuilderType
from .ai_extractor import AIExtractor

class PDFExtractor:
    def __init__(self):
        self.template_detector = TemplateDetector()
        # Initialize AI extractor if API key is available
        self.ai_extractor = None
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if gemini_api_key:
            try:
                self.ai_extractor = AIExtractor(gemini_api_key)
                print("AI extraction enabled with Gemini API")
            except Exception as e:
                print(f"Failed to initialize AI extractor: {e}")
                self.ai_extractor = None

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from PDF file.
        """
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
            # Debug: Print first 2500 characters of extracted text
            print("\n=== FIRST 2500 CHARACTERS OF EXTRACTED TEXT ===")
            print(text[:2500])
            print("=== END OF EXTRACTED TEXT SAMPLE ===\n")
        except Exception as e:
            print(f"Error extracting text from PDF: {str(e)}")
            return ""
        return text

    def parse_address(self, address_text: str) -> Dict[str, str]:
        """
        Parse address text into components.
        """
        address_parts = {
            'address1': '',
            'address2': '',
            'city': '',
            'state': '',
            'postal_code': ''
        }

        if not address_text:
            return address_parts

        # Split address into lines
        lines = [line.strip() for line in address_text.split('\n') if line.strip()]
        
        if not lines:
            return address_parts

        # First line is usually street address
        address_parts['address1'] = lines[0]

        # Second line might be additional address info
        if len(lines) > 1:
            address_parts['address2'] = lines[1]

        # Last line usually contains city, state, and postal code
        if len(lines) > 2:
            last_line = lines[-1]
            # Try to match state and postal code pattern
            state_postal_match = re.search(r'([A-Z]{2,3})\s+(\d{4})', last_line)
            if state_postal_match:
                address_parts['state'] = state_postal_match.group(1)
                address_parts['postal_code'] = state_postal_match.group(2)
                # City is everything before the state
                city = last_line[:state_postal_match.start()].strip()
                address_parts['city'] = city

        return address_parts

    def parse_name(self, name_text: str) -> Dict[str, str]:
        """
        Parse full name into first and last name.
        """
        name_parts = {
            'first_name': '',
            'last_name': ''
        }

        if not name_text:
            return name_parts

        # Split name into parts
        parts = name_text.strip().split()
        if len(parts) >= 2:
            name_parts['first_name'] = parts[0]
            name_parts['last_name'] = ' '.join(parts[1:])
        elif len(parts) == 1:
            name_parts['last_name'] = parts[0]

        return name_parts

    def extract_data_from_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract data from PDF using AI first, then fallback to template detection.
        """
        # Extract text from PDF
        text = self.extract_text_from_pdf(pdf_path)
        if not text:
            return {'error': 'Could not extract text from PDF'}

        # Try AI extraction first if available
        if self.ai_extractor:
            print("\n=== Using AI-powered extraction ===")
            try:
                ai_data = self.ai_extractor.extract_data_from_text(text)
                if ai_data and not ai_data.get('error'):
                    print("AI extraction successful!")
                    return ai_data
                else:
                    print("AI extraction failed, falling back to template detection")
            except Exception as e:
                print(f"AI extraction error: {e}, falling back to template detection")

        # Fallback to template detection
        print("\n=== Using template-based extraction ===")
        return self._extract_with_templates(text)

    def _extract_with_templates(self, text: str) -> Dict[str, Any]:
        """
        Extract data using comprehensive pattern matching (fallback method).
        """
        print("\n=== Using enhanced pattern-based extraction ===")
        
        # Initialize with empty values
        extracted_data = {
            'customer_name': '',
            'business_name': '',
            'po_number': '',
            'scope_of_work': '',
            'dollar_value': 0,
            'first_name': '',
            'last_name': '',
            'address1': '',
            'address2': '',
            'city': '',
            'state': '',
            'postal_code': '',
            'phone': '',
            'mobile': '',
            'email': '',
            'commencement_date': '',
            'completion_date': '',
            'supervisor_name': '',
            'supervisor_phone': '',
            'description_of_works': '',
            'builder_type': 'Unknown'
        }

        # Try template detection first
        try:
            builder_type, patterns = self.template_detector.detect_template(text)
            if patterns:
                print(f"Detected template type: {builder_type.value}")
                extracted_data['builder_type'] = builder_type.value
                
                # Extract using template patterns
                extracted_data['po_number'] = self.template_detector.extract_field(text, patterns.po_pattern)
                extracted_data['dollar_value'] = self.template_detector.extract_dollar_value(text, patterns.dollar_value_pattern)
                extracted_data['description_of_works'] = self.template_detector.extract_field(text, patterns.description_pattern)
                extracted_data['supervisor_name'] = self.template_detector.extract_field(text, patterns.supervisor_pattern)
                
                # Extract customer name
                customer_name = self.template_detector.extract_field(text, patterns.customer_name_pattern)
                if customer_name:
                    name_parts = self.parse_name(customer_name)
                    extracted_data.update(name_parts)
                    extracted_data['customer_name'] = customer_name
                
                # Extract address
                address_text = self.template_detector.extract_field(text, patterns.address_pattern)
                if address_text:
                    address_parts = self.parse_address(address_text)
                    extracted_data.update(address_parts)
                
                # Extract dates
                if patterns.commencement_date_pattern:
                    commencement_date = self.template_detector.extract_field(text, patterns.commencement_date_pattern)
                    if commencement_date:
                        extracted_data['commencement_date'] = commencement_date
                
                if patterns.completion_date_pattern:
                    completion_date = self.template_detector.extract_field(text, patterns.completion_date_pattern)
                    if completion_date:
                        extracted_data['completion_date'] = completion_date
        except Exception as e:
            print(f"Template detection failed: {e}")

        # Enhanced pattern matching for common fields
        self._extract_common_patterns(text, extracted_data)
        
        # Set default dollar value if none found
        if not extracted_data.get('dollar_value') or extracted_data['dollar_value'] == 0:
            extracted_data['dollar_value'] = 1.0
            print("No dollar value found, setting default to $1.00")
        
        # Debug: Print extracted fields
        print("\nExtracted fields:")
        for key, value in extracted_data.items():
            if value:  # Only print non-empty values
                print(f"{key}: {value}")

        return extracted_data

    def _extract_common_patterns(self, text: str, extracted_data: Dict[str, Any]):
        """Extract common patterns from text."""
        
        # Email patterns
        email_patterns = [
            r'[\w\.-]+@[\w\.-]+\.\w+',
            r'Email:\s*([\w\.-]+@[\w\.-]+\.\w+)',
            r'E-mail:\s*([\w\.-]+@[\w\.-]+\.\w+)'
        ]
        for pattern in email_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                extracted_data['email'] = match.group(1) if match.groups() else match.group(0)
                break

        # Phone number patterns
        phone_patterns = [
            r'Phone:\s*(\d[\d\s\-\(\)]+)',
            r'Mobile:\s*(\d[\d\s\-\(\)]+)',
            r'Contact No\.:\s*(\d[\d\s\-\(\)]+)',
            r'Phone1:\s*(\d[\d\s\-\(\)]+)',
            r'Phone2:\s*(\d[\d\s\-\(\)]+)',
            r'Home:\s*(\d[\d\s\-\(\)]+)',
            r'Work:\s*(\d[\d\s\-\(\)]+)',
            r'Tel:\s*(\d[\d\s\-\(\)]+)',
            r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
            r'(\d{4}[-.\s]?\d{3}[-.\s]?\d{3})'
        ]
        
        phones = []
        for pattern in phone_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                phone = re.sub(r'[^\d]', '', match)  # Remove non-digits
                if len(phone) >= 8:  # Valid phone number length
                    phones.append(match.strip())
        
        if phones:
            extracted_data['phone'] = phones[0]
            if len(phones) > 1:
                extracted_data['mobile'] = phones[1]

        # Dollar amount patterns
        dollar_patterns = [
            r'Total[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Subtotal[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Amount[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Price[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'Cost[\s:]*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'
        ]
        
        for pattern in dollar_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if amount > extracted_data['dollar_value']:  # Take the largest amount
                        extracted_data['dollar_value'] = amount
                except ValueError:
                    pass

        # PO Number patterns - improved for work orders
        po_patterns = [
            r'Work Order Number[\s:]+([A-Z0-9\-]+)',
            r'Job Number[\s:]+([A-Z0-9\-]+)',
            r'Client Reference[\s:]+([A-Z0-9\-]+)',
            r'PO[\s#:]*([A-Z0-9\-]+)',
            r'Purchase Order[\s#:]*([A-Z0-9\-]+)',
            r'Order Number[\s#:]*([A-Z0-9\-]+)',
            r'Reference[\s#:]*([A-Z0-9\-]+)',
            r'Job[\s#:]*([A-Z0-9\-]+)'
        ]
        
        for pattern in po_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not extracted_data['po_number']:
                extracted_data['po_number'] = match.group(1).strip()

        # Name patterns - improved for work orders
        name_patterns = [
            r'Customer Name[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)',
            r'Client Name[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)',
            r'Customer[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)',
            r'Client[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)',
            r'Contact[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)',
            r'Name[\s:]+([^\n]+?)(?:\s+Supervisor|\s+Contact|\s+Phone|\s+Address|$)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and not extracted_data['customer_name']:
                name = match.group(1).strip()
                # Clean up the name - remove extra text
                name = re.sub(r'\s+(Supervisor|Contact|Phone|Address).*$', '', name, flags=re.IGNORECASE)
                if len(name) > 2 and len(name) < 50:  # Valid name length
                    extracted_data['customer_name'] = name
                    name_parts = self.parse_name(name)
                    extracted_data.update(name_parts)
                    break

        # Address patterns
        address_patterns = [
            r'Address[\s:]+([^\n]+(?:\n[^\n]+){0,2})',
            r'Location[\s:]+([^\n]+(?:\n[^\n]+){0,2})',
            r'Site[\s:]+([^\n]+(?:\n[^\n]+){0,2})'
        ]
        
        for pattern in address_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match and not extracted_data['address1']:
                address_text = match.group(1).strip()
                address_parts = self.parse_address(address_text)
                extracted_data.update(address_parts)
                break

        # Scope of work patterns - improved for work orders
        work_patterns = [
            r'Total Labour and Materials for flooring of the following description:[\s\S]+?following description,([^$]+?)(?=Totals|$)',
            r'Scope of Work[\s:]+([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
            r'Description[\s:]+([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
            r'Work[\s:]+([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
            r'Details[\s:]+([\s\S]+?)(?=\n\n|\n[A-Z]|$)',
            r'MEDIA ROOM[\s\S]+?([^$]+?)(?=Totals|$)',
            r'Flooring Material Labour[\s\S]+?([^$]+?)(?=Totals|$)'
        ]
        
        for pattern in work_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match and not extracted_data['scope_of_work']:
                work_text = match.group(1).strip()
                # Clean up the work description
                work_text = re.sub(r'\s+', ' ', work_text)  # Normalize whitespace
                work_text = work_text.replace('N/A', '').strip()
                if len(work_text) > 10:  # Valid description length
                    extracted_data['scope_of_work'] = work_text
                    break

        # Date patterns
        date_patterns = [
            r'Start[\s:]+([^\n]+)',
            r'Commence[\s:]+([^\n]+)',
            r'Begin[\s:]+([^\n]+)',
            r'Complete[\s:]+([^\n]+)',
            r'Finish[\s:]+([^\n]+)',
            r'End[\s:]+([^\n]+)'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_text = match.group(1).strip()
                if 'commence' in pattern.lower() or 'start' in pattern.lower() or 'begin' in pattern.lower():
                    if not extracted_data['commencement_date']:
                        extracted_data['commencement_date'] = date_text
                elif 'complete' in pattern.lower() or 'finish' in pattern.lower() or 'end' in pattern.lower():
                    if not extracted_data['completion_date']:
                        extracted_data['completion_date'] = date_text 