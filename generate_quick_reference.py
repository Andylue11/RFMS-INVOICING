#!/usr/bin/env python3
"""
Generate a quick reference guide from Postman collection JSON file.
"""

import json
import sys
import re
from typing import Dict, List, Any


def extract_url_simple(url_obj: Dict) -> str:
    """Extract simple URL string."""
    if url_obj is None:
        return ""
    
    if isinstance(url_obj, str):
        return url_obj
    
    raw = url_obj.get("raw", "")
    if raw:
        return raw
    
    protocol = url_obj.get("protocol", "https") or "https"
    host = url_obj.get("host", []) or []
    path = url_obj.get("path", []) or []
    
    if isinstance(host, list):
        host_str = ".".join(host)
    else:
        host_str = host
    
    path_str = "/".join([p for p in path if p])
    
    return f"{protocol}://{host_str}/{path_str}"


def extract_endpoint_simple(item: Dict, category: str = "") -> Dict[str, Any]:
    """Extract simplified endpoint information."""
    name = item.get("name", "Unknown")
    request = item.get("request", {}) or {}
    method = request.get("method", "GET")
    
    url_info = request.get("url", {}) or {}
    url = extract_url_simple(url_info)
    
    # Clean up URL - replace variables with {var}
    url = re.sub(r'\{\{(\w+)\}\}', r'{\1}', url)
    
    # Get short description (first line or first 100 chars)
    description = item.get("description", "")
    if description:
        # Get first sentence or first 100 chars
        desc_lines = description.split('\n')
        short_desc = desc_lines[0].strip()
        if len(short_desc) > 120:
            short_desc = short_desc[:117] + "..."
    else:
        short_desc = ""
    
    # Check if requires auth
    auth = request.get("auth", {}) or {}
    requires_auth = bool(auth.get("type"))
    
    # Check if has body
    body = request.get("body", {}) or {}
    has_body = bool(body.get("mode") and body.get("mode") != "raw" or 
                    (body.get("mode") == "raw" and body.get("raw")))
    
    return {
        "name": name,
        "category": category,
        "method": method,
        "url": url,
        "description": short_desc,
        "requires_auth": requires_auth,
        "has_body": has_body
    }


def extract_collection_items_simple(items: List[Dict], category: str = "") -> List[Dict]:
    """Recursively extract all endpoints from collection items."""
    endpoints = []
    
    for item in items:
        if "item" in item:
            # This is a folder/category
            folder_name = item.get("name", "")
            sub_items = item.get("item", []) or []
            endpoints.extend(extract_collection_items_simple(sub_items, folder_name))
        else:
            # This is an endpoint
            endpoint = extract_endpoint_simple(item, category)
            endpoints.append(endpoint)
    
    return endpoints


def generate_quick_reference(collection_data: Dict) -> str:
    """Generate quick reference guide from collection data."""
    info = collection_data.get("info", {})
    collection_name = info.get("name", "API Collection")
    collection_desc = info.get("description", "")
    
    # Extract short description
    short_desc = ""
    if collection_desc:
        lines = collection_desc.split('\n')
        for line in lines[:3]:
            if line.strip() and not line.strip().startswith('>'):
                short_desc = line.strip()
                if len(short_desc) > 200:
                    short_desc = short_desc[:197] + "..."
                break
    
    items = collection_data.get("item", [])
    endpoints = extract_collection_items_simple(items)
    
    # Group endpoints by category
    categories = {}
    for endpoint in endpoints:
        category = endpoint["category"] or "Other"
        if category not in categories:
            categories[category] = []
        categories[category].append(endpoint)
    
    # Generate markdown
    md = f"""# {collection_name} - Quick Reference Guide

{short_desc}

> **Total Endpoints:** {len(endpoints)}  
> **Categories:** {len(categories)}

---

## Quick Navigation

"""
    
    # Add quick navigation
    for category in sorted(categories.keys()):
        count = len(categories[category])
        anchor = category.lower().replace(' ', '-').replace('&', '').replace('/', '-')
        md += f"- [{category}](#{anchor}) ({count})\n"
    
    md += "\n---\n\n"
    
    # Generate summary table for all endpoints
    md += "## All Endpoints Summary\n\n"
    md += "| Method | Endpoint | Category | Auth | Body | Description |\n"
    md += "|--------|----------|----------|------|------|-------------|\n"
    
    for endpoint in sorted(endpoints, key=lambda x: (x["category"], x["method"], x["name"])):
        method = endpoint["method"]
        url = endpoint["url"]
        category = endpoint["category"] or "Other"
        auth = "✓" if endpoint["requires_auth"] else ""
        body = "✓" if endpoint["has_body"] else ""
        desc = endpoint["description"] or ""
        
        # Truncate URL if too long
        if len(url) > 60:
            url = url[:57] + "..."
        
        # Truncate description if too long
        if len(desc) > 50:
            desc = desc[:47] + "..."
        
        md += f"| `{method}` | `{url}` | {category} | {auth} | {body} | {desc} |\n"
    
    md += "\n---\n\n"
    
    # Generate detailed sections by category
    for category in sorted(categories.keys()):
        anchor = category.lower().replace(' ', '-').replace('&', '').replace('/', '-')
        md += f"## {category}\n\n"
        md += f"*{len(categories[category])} endpoints*\n\n"
        
        # Category summary table
        md += "| Method | Endpoint | Description |\n"
        md += "|--------|----------|-------------|\n"
        
        for endpoint in sorted(categories[category], key=lambda x: (x["method"], x["name"])):
            method = endpoint["method"]
            url = endpoint["url"]
            desc = endpoint["description"] or ""
            
            # Truncate URL if too long
            if len(url) > 70:
                url = url[:67] + "..."
            
            # Truncate description if too long
            if len(desc) > 80:
                desc = desc[:77] + "..."
            
            md += f"| `{method}` | `{url}` | {desc} |\n"
        
        md += "\n"
        
        # List endpoints with more details
        for endpoint in sorted(categories[category], key=lambda x: (x["method"], x["name"])):
            method = endpoint["method"]
            url = endpoint["url"]
            name = endpoint["name"]
            desc = endpoint["description"] or ""
            auth = endpoint["requires_auth"]
            body = endpoint["has_body"]
            
            md += f"### {name}\n\n"
            md += f"**{method}** `{url}`\n\n"
            
            if desc:
                md += f"{desc}\n\n"
            
            # Add metadata
            metadata = []
            if auth:
                metadata.append("Requires Authentication")
            if body:
                metadata.append("Requires Request Body")
            
            if metadata:
                md += f"*{', '.join(metadata)}*\n\n"
            
            md += "---\n\n"
    
    # Add authentication section
    md += """## Authentication

All API endpoints require authentication using HTTP Basic Authentication.

### Getting Started

1. **Get Store API Credentials:**
   - Sign into RFMS Online Services
   - Open the "RFMS Online" section
   - Press the API button in the toolbar
   - Generate or view your Store API Credentials

2. **Begin a Session:**
   - Use the Store Queue as the Username
   - Use the API Key as the Password
   - Call `POST /v2/session/begin` to get a session token

3. **Use Session Token:**
   - Use the session token as the Password in subsequent requests
   - Use the same Store Queue as the Username
   - Session token expires but is extended with each API call

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v2/session/begin` | Begin a new session and get session token |
| `POST` | `/v2/session/request` | Request Bus ID (for Third Party Developers) |

---

## Base URL

All endpoints use the base URL:

```
https://api.rfms.online
```

---

## Standard Response Format

All API methods return responses in this format:

```json
{
  "status": "success",
  "result": {},
  "detail": {}
}
```

**Status Values:**
- `"success"` - Request completed successfully
- `"waiting"` - Response not yet received
- `"failed"` - Database rejected the request (reason in result)

---

## Common Endpoints by Use Case

### Customer Management
- `POST /v2/customers/find` - Search for customers
- `GET /v2/customer/{customerId}` - Get customer details
- `POST /v2/customer` - Create or update customer

### Order Management
- `POST /v2/orders/find` - Find orders
- `GET /v2/order/{orderNumber}` - Get order details
- `POST /v2/order` - Create order
- `PUT /v2/order/{orderNumber}` - Update order

### Quote Management
- `POST /v2/quotes/find` - Find quotes
- `GET /v2/quote/{quoteNumber}` - Get quote details
- `POST /v2/quote` - Create quote
- `POST /v2/quote/{quoteNumber}/export` - Export quote to order

### Payment Processing
- `POST /v2/order/{orderNumber}/payment` - Record payment
- `GET /v2/order/{orderNumber}/payments` - List payments

---

## Tips

1. **Session Management:** Always begin a session first and use the session token for subsequent requests
2. **Error Handling:** Check the `status` field in responses - `"failed"` indicates an error
3. **Pagination:** Many find/search endpoints support `startIndex` parameter for pagination
4. **Rate Limiting:** Be mindful of API rate limits when making multiple requests
5. **Versioning:** All endpoints use `/v2/` prefix - ensure you're using the correct version

---

## Need More Details?

For detailed documentation with:
- Complete parameter descriptions
- Request/response examples
- Code samples (cURL, Python)
- Response schemas

See: `RFMS_API_DOCUMENTATION_DETAILED.md`

---

*Generated from Postman Collection*
"""
    
    return md


def main():
    """Main function to generate quick reference guide."""
    input_file = "RFMS API 2.postman_collection.json"
    output_file = "RFMS_API_QUICK_REFERENCE.md"
    
    try:
        print(f"Reading Postman collection from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            collection_data = json.load(f)
        
        print("Generating quick reference guide...")
        quick_ref = generate_quick_reference(collection_data)
        
        print(f"Writing quick reference to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(quick_ref)
        
        print(f"✓ Successfully generated quick reference guide to {output_file}")
        
        # Count endpoints
        items = collection_data.get("item", [])
        endpoints = extract_collection_items_simple(items)
        print(f"✓ Generated reference for {len(endpoints)} endpoints")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

