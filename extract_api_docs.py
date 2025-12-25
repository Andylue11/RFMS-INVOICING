#!/usr/bin/env python3
"""
Extract detailed API documentation from Postman collection JSON file.
"""

import json
import sys
import re
from typing import Dict, List, Any, Optional


def extract_url_info(url_obj: Dict) -> Dict[str, Any]:
    """Extract URL information from Postman URL object."""
    if url_obj is None:
        return {"raw": "", "protocol": "https", "host": "", "path": "", "path_params": [], "query_params": [], "full_url": ""}
    
    if isinstance(url_obj, str):
        return {"raw": url_obj, "protocol": "https", "host": "", "path": "", "path_params": [], "query_params": [], "full_url": url_obj}
    
    protocol = url_obj.get("protocol", "https") or "https"
    host = url_obj.get("host", []) or []
    path = url_obj.get("path", []) or []
    query = url_obj.get("query", []) or []
    
    # Build full URL
    if isinstance(host, list):
        host_str = ".".join(host)
    else:
        host_str = host
    
    # Extract path parameters (variables like {{customerId}})
    path_params = []
    path_segments = []
    for p in path:
        if p:
            # Check if it's a variable
            var_match = re.match(r'\{\{(\w+)\}\}', p)
            if var_match:
                param_name = var_match.group(1)
                path_params.append({
                    "name": param_name,
                    "variable": p,
                    "required": True
                })
                path_segments.append(f"{{{param_name}}}")
            else:
                path_segments.append(p)
    
    path_str = "/".join(path_segments)
    
    # Extract query parameters with details
    query_params = []
    for q in query:
        if isinstance(q, dict) and not q.get("disabled", False):
            key = q.get("key", "")
            value = q.get("value", "")
            description = q.get("description", "")
            if key:
                query_params.append({
                    "key": key,
                    "value": value,
                    "description": description if isinstance(description, str) else description.get("content", "") if isinstance(description, dict) else ""
                })
    
    full_url = f"{protocol}://{host_str}/{path_str}"
    if query_params:
        query_string = "&".join([f"{q['key']}={q['value']}" if q['value'] else q['key'] for q in query_params])
        full_url += "?" + query_string
    
    return {
        "raw": url_obj.get("raw", full_url),
        "protocol": protocol,
        "host": host_str,
        "path": path_str,
        "path_params": path_params,
        "query_params": query_params,
        "full_url": full_url
    }


def extract_body_info(body_obj: Dict) -> Dict[str, Any]:
    """Extract request body information with parameter details."""
    if not body_obj:
        return {"raw": "", "mode": "", "parameters": []}
    
    mode = body_obj.get("mode", "")
    parameters = []
    raw_body = ""
    
    if mode == "raw":
        raw_body = body_obj.get("raw", "")
        # Try to parse JSON and extract parameter info
        if raw_body:
            try:
                body_json = json.loads(raw_body)
                parameters = extract_json_parameters(body_json)
            except:
                pass
    elif mode == "formdata":
        formdata = body_obj.get("formdata", []) or []
        if formdata:
            params_dict = {}
            for item in formdata:
                if item and item.get("key"):
                    key = item.get("key", "")
                    value = item.get("value", "")
                    description = item.get("description", "")
                    if description is None:
                        description = ""
                    elif not isinstance(description, str):
                        description = description.get("content", "") if isinstance(description, dict) else ""
                    params_dict[key] = value
                    parameters.append({
                        "name": key,
                        "value": value,
                        "type": item.get("type", "text"),
                        "description": description,
                        "required": not item.get("disabled", False)
                    })
            if params_dict:
                raw_body = json.dumps(params_dict, indent=2)
    elif mode == "urlencoded":
        urlencoded = body_obj.get("urlencoded", []) or []
        if urlencoded:
            params_dict = {}
            for item in urlencoded:
                if item and item.get("key"):
                    key = item.get("key", "")
                    value = item.get("value", "")
                    description = item.get("description", "")
                    if description is None:
                        description = ""
                    elif not isinstance(description, str):
                        description = description.get("content", "") if isinstance(description, dict) else ""
                    params_dict[key] = value
                    parameters.append({
                        "name": key,
                        "value": value,
                        "type": "string",
                        "description": description,
                        "required": not item.get("disabled", False)
                    })
            if params_dict:
                raw_body = json.dumps(params_dict, indent=2)
    
    return {
        "raw": raw_body,
        "mode": mode,
        "parameters": parameters
    }


def extract_json_parameters(obj: Any, prefix: str = "") -> List[Dict[str, Any]]:
    """Recursively extract parameters from JSON object."""
    parameters = []
    
    if obj is None:
        return parameters
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            param_name = f"{prefix}.{key}" if prefix else key
            param_type = infer_type(value)
            parameters.append({
                "name": param_name,
                "type": param_type,
                "example": value if not isinstance(value, (dict, list)) else None,
                "required": True
            })
            if isinstance(value, (dict, list)):
                parameters.extend(extract_json_parameters(value, param_name))
    elif isinstance(obj, list) and len(obj) > 0:
        # Analyze first item in array
        if isinstance(obj[0], dict):
            parameters.extend(extract_json_parameters(obj[0], f"{prefix}[0]" if prefix else "[0]"))
    
    return parameters


def infer_type(value: Any) -> str:
    """Infer the type of a value."""
    if isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, str):
        return "string"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    else:
        return "unknown"


def format_description(desc: str) -> str:
    """Format description text."""
    if not desc:
        return ""
    # Clean up markdown-like formatting
    return desc.strip()


def extract_endpoint(item: Dict, category: str = "") -> Dict[str, Any]:
    """Extract endpoint information from a Postman item."""
    name = item.get("name", "Unknown")
    request = item.get("request", {})
    method = request.get("method", "GET")
    
    # Extract URL
    url_info = extract_url_info(request.get("url", {}))
    
    # Extract headers with descriptions
    headers = request.get("header", []) or []
    header_list = []
    header_dict = {}
    for h in headers:
        if h and h.get("key"):
            key = h.get("key", "")
            value = h.get("value", "")
            description = h.get("description", "")
            if description is None:
                description = ""
            elif not isinstance(description, str):
                description = description.get("content", "") if isinstance(description, dict) else ""
            header_dict[key] = value
            header_list.append({
                "key": key,
                "value": value,
                "description": description
            })
    
    # Extract body
    body_info = extract_body_info(request.get("body", {}))
    
    # Extract description
    description = format_description(item.get("description", ""))
    
    # Extract auth info
    auth = request.get("auth", {})
    auth_type = auth.get("type", "")
    auth_info = {}
    if auth_type:
        auth_info = {"type": auth_type}
        if auth_type == "basic":
            basic = auth.get("basic", [])
            for b in basic:
                key = b.get("key", "")
                if key == "username":
                    auth_info["username"] = b.get("value", "")
                elif key == "password":
                    auth_info["password"] = b.get("value", "")
    
    # Extract all responses with headers
    responses = item.get("response", []) or []
    response_examples = []
    for resp in responses:
        if resp is None:
            continue
        resp_headers = resp.get("header", []) or []
        resp_header_dict = {}
        for h in resp_headers:
            if h and h.get("key"):
                resp_header_dict[h.get("key", "")] = h.get("value", "")
        
        resp_info = {
            "name": resp.get("name", ""),
            "status": resp.get("status", ""),
            "code": resp.get("code", 0),
            "body": resp.get("body", ""),
            "headers": resp_header_dict
        }
        response_examples.append(resp_info)
    
    # Extract test scripts for additional info
    events = item.get("event", [])
    test_script = ""
    for event in events:
        if event.get("listen") == "test":
            script = event.get("script", {})
            if isinstance(script, dict):
                exec_lines = script.get("exec", [])
                if isinstance(exec_lines, list):
                    test_script = "\n".join(exec_lines)
    
    return {
        "name": name,
        "category": category,
        "method": method,
        "url": url_info,
        "headers": header_list,
        "header_dict": header_dict,
        "body": body_info,
        "description": description,
        "auth": auth_info,
        "responses": response_examples,
        "test_script": test_script
    }


def extract_collection_items(items: List[Dict], category: str = "") -> List[Dict]:
    """Recursively extract all endpoints from collection items."""
    endpoints = []
    
    for item in items:
        if "item" in item:
            # This is a folder/category
            folder_name = item.get("name", "")
            folder_desc = item.get("description", "")
            sub_items = item.get("item", [])
            endpoints.extend(extract_collection_items(sub_items, folder_name))
        else:
            # This is an endpoint
            endpoint = extract_endpoint(item, category)
            endpoints.append(endpoint)
    
    return endpoints


def generate_curl_example(endpoint: Dict) -> str:
    """Generate a curl example for the endpoint."""
    method = endpoint.get('method', 'GET')
    url_info = endpoint.get('url', {})
    url = url_info.get('full_url', '') or url_info.get('raw', '') or ''
    
    # Replace variables with examples
    url = re.sub(r'\{\{(\w+)\}\}', r'{\1}', url)
    
    curl_cmd = f"curl -X {method}"
    
    # Add authentication
    auth = endpoint.get('auth', {})
    if auth:
        auth_type = auth.get('type', '')
        if auth_type == 'basic':
            username = auth.get('username', 'USERNAME') or 'USERNAME'
            password = auth.get('password', 'PASSWORD') or 'PASSWORD'
            curl_cmd += f" -u '{username}:{password}'"
    
    # Add headers
    headers = endpoint.get('headers', []) or []
    for header in headers:
        if header:
            key = header.get('key', '')
            value = header.get('value', '')
            if key and value:
                curl_cmd += f" -H '{key}: {value}'"
    
    # Add body
    body = endpoint.get('body', {})
    if body and body.get('raw'):
        body_raw = body['raw']
        # Escape single quotes in body
        body_escaped = body_raw.replace("'", "'\\''")
        curl_cmd += f" -d '{body_escaped}'"
    
    curl_cmd += f" '{url}'"
    
    return curl_cmd


def generate_python_example(endpoint: Dict) -> str:
    """Generate a Python requests example for the endpoint."""
    method = endpoint.get('method', 'GET')
    url_info = endpoint.get('url', {})
    url = url_info.get('full_url', '') or url_info.get('raw', '') or ''
    
    # Replace variables with examples
    url = re.sub(r'\{\{(\w+)\}\}', r'{\1}', url)
    
    python_code = "import requests\n\n"
    
    # Build headers
    headers = {}
    header_list = endpoint.get('headers', []) or []
    for header in header_list:
        if header:
            key = header.get('key', '')
            value = header.get('value', '')
            if key and value:
                headers[key] = value
    
    # Build auth
    auth_code = ""
    auth = endpoint.get('auth', {})
    if auth:
        auth_type = auth.get('type', '')
        if auth_type == 'basic':
            username = auth.get('username', 'USERNAME') or 'USERNAME'
            password = auth.get('password', 'PASSWORD') or 'PASSWORD'
            auth_code = f"auth=('{username}', '{password}'),\n    "
    
    # Build data/json
    data_code = ""
    body = endpoint.get('body', {})
    if body and body.get('raw'):
        try:
            body_json = json.loads(body['raw'])
            data_code = f"json={json.dumps(body_json, indent=8)},\n    "
        except:
            data_code = f"data='''{body['raw']}''',\n    "
    
    python_code += f"response = requests.{method.lower()}(\n"
    python_code += f"    '{url}',\n"
    if auth_code:
        python_code += f"    {auth_code}"
    if headers:
        python_code += f"    headers={json.dumps(headers, indent=4)},\n"
    if data_code:
        python_code += f"    {data_code}"
    python_code = python_code.rstrip(",\n    ") + "\n"
    python_code += ")\n\n"
    python_code += "print(response.json())"
    
    return python_code


def generate_markdown_docs(collection_data: Dict) -> str:
    """Generate detailed markdown documentation from collection data."""
    info = collection_data.get("info", {})
    collection_name = info.get("name", "API Collection")
    collection_desc = info.get("description", "")
    
    items = collection_data.get("item", [])
    endpoints = extract_collection_items(items)
    
    # Group endpoints by category
    categories = {}
    for endpoint in endpoints:
        category = endpoint["category"] or "Other"
        if category not in categories:
            categories[category] = []
        categories[category].append(endpoint)
    
    # Generate markdown
    md = f"""# {collection_name}

{collection_desc}

## Table of Contents

"""
    
    # Add table of contents with endpoint counts
    for category in sorted(categories.keys()):
        count = len(categories[category])
        anchor = category.lower().replace(' ', '-').replace('&', '')
        md += f"- [{category}](#{anchor}) ({count} endpoints)\n"
    
    md += "\n---\n\n"
    
    # Generate documentation for each category
    for category in sorted(categories.keys()):
        anchor = category.lower().replace(' ', '-').replace('&', '')
        md += f"## {category}\n\n"
        md += f"*{len(categories[category])} endpoints*\n\n"
        
        for endpoint in categories[category]:
            endpoint_name = endpoint.get('name', 'Unknown Endpoint')
            md += f"### {endpoint_name}\n\n"
            
            description = endpoint.get('description', '')
            if description:
                md += f"{description}\n\n"
            
            # Method and URL
            method = endpoint.get('method', 'GET')
            url_info = endpoint.get('url', {})
            url = url_info.get('full_url', '') or url_info.get('raw', '') or ''
            md += f"**{method}** `{url}`\n\n"
            
            # Path Parameters
            path_params = url_info.get('path_params', []) or []
            if path_params:
                md += "#### Path Parameters\n\n"
                md += "| Parameter | Type | Required | Description |\n"
                md += "|-----------|------|----------|-------------|\n"
                for param in path_params:
                    if param:
                        param_name = param.get('name', '')
                        md += f"| `{param_name}` | string | Yes | Path parameter |\n"
                md += "\n"
            
            # Query Parameters
            query_params = url_info.get('query_params', []) or []
            if query_params:
                md += "#### Query Parameters\n\n"
                md += "| Parameter | Type | Required | Description |\n"
                md += "|-----------|------|----------|-------------|\n"
                for param in query_params:
                    if param:
                        param_key = param.get('key', '')
                        desc = param.get('description', '') or 'Query parameter'
                        md += f"| `{param_key}` | string | No | {desc} |\n"
                md += "\n"
            
            # Authentication
            auth = endpoint.get('auth', {})
            if auth:
                md += "#### Authentication\n\n"
                auth_type = auth.get('type', '')
                if auth_type == 'basic':
                    username = auth.get('username', '')
                    password = auth.get('password', '')
                    md += "This endpoint requires **HTTP Basic Authentication**.\n\n"
                    if username:
                        md += f"- **Username:** `{username}`\n"
                    if password:
                        md += f"- **Password:** `{password}` (API Key or Session Token)\n"
                    md += "\n"
            
            # Headers
            headers = endpoint.get('headers', []) or []
            if headers:
                md += "#### Headers\n\n"
                md += "| Header | Value | Description |\n"
                md += "|--------|-------|-------------|\n"
                for header in headers:
                    if header:
                        key = header.get('key', '')
                        value = header.get('value', '')
                        desc = header.get('description', '') or 'Request header'
                        md += f"| `{key}` | `{value}` | {desc} |\n"
                md += "\n"
            
            # Request Body
            body = endpoint.get('body', {})
            body_raw = body.get('raw', '') if body else ''
            if body_raw:
                md += "#### Request Body\n\n"
                
                # Body Parameters table if available
                body_params = body.get('parameters', []) or [] if body else []
                if body_params:
                    md += "**Parameters:**\n\n"
                    md += "| Parameter | Type | Required | Description |\n"
                    md += "|-----------|------|----------|-------------|\n"
                    for param in body_params[:20]:  # Limit to first 20
                        if param:
                            name = param.get('name', '')
                            param_type = param.get('type', 'string')
                            required = "Yes" if param.get('required', False) else "No"
                            example = param.get('example', '')
                            desc = f"Example: `{example}`" if example else ""
                            md += f"| `{name}` | {param_type} | {required} | {desc} |\n"
                    md += "\n"
                
                md += "**Example:**\n\n"
                md += "```json\n"
                md += body_raw
                md += "\n```\n\n"
            
            # Code Examples
            md += "#### Code Examples\n\n"
            
            # cURL example
            curl_example = generate_curl_example(endpoint)
            md += "**cURL:**\n\n"
            md += "```bash\n"
            md += curl_example
            md += "\n```\n\n"
            
            # Python example
            python_example = generate_python_example(endpoint)
            md += "**Python:**\n\n"
            md += "```python\n"
            md += python_example
            md += "\n```\n\n"
            
            # Response Examples
            responses = endpoint.get('responses', []) or []
            if responses:
                md += "#### Response Examples\n\n"
                for resp in responses:
                    if not resp:
                        continue
                    resp_name = resp.get('name', 'Response') or 'Response'
                    status = resp.get('status', '') or ''
                    code = resp.get('code', 0) or 0
                    
                    md += f"**{resp_name}** ({status} - {code})\n\n"
                    
                    # Response headers if available
                    resp_headers = resp.get('headers', {}) or {}
                    if resp_headers:
                        md += "*Response Headers:*\n\n"
                        for key, value in list(resp_headers.items())[:5]:  # Limit to first 5
                            md += f"- `{key}`: `{value}`\n"
                        md += "\n"
                    
                    resp_body = resp.get('body', '')
                    if resp_body:
                        try:
                            # Try to format as JSON if possible
                            body_json = json.loads(resp_body)
                            md += "```json\n"
                            md += json.dumps(body_json, indent=2)
                            md += "\n```\n\n"
                        except:
                            body_text = str(resp_body)
                            if len(body_text) > 1000:
                                md += "```\n"
                                md += body_text[:1000]
                                md += "\n... (truncated, see full response in Postman collection)\n"
                                md += "```\n\n"
                            else:
                                md += "```\n"
                                md += body_text
                                md += "\n```\n\n"
            
            md += "---\n\n"
    
    return md


def main():
    """Main function to extract API documentation."""
    input_file = "RFMS API 2.postman_collection.json"
    output_file = "RFMS_API_DOCUMENTATION_DETAILED.md"
    
    try:
        print(f"Reading Postman collection from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            collection_data = json.load(f)
        
        print("Extracting API documentation...")
        markdown_docs = generate_markdown_docs(collection_data)
        
        print(f"Writing documentation to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_docs)
        
        print(f"✓ Successfully extracted API documentation to {output_file}")
        
        # Count endpoints
        items = collection_data.get("item", [])
        endpoints = extract_collection_items(items)
        print(f"✓ Extracted {len(endpoints)} endpoints")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

