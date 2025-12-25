# RFMS API 2

Access your RFMS Business Management System data within your own application using a standard REST API.

> _Note that we do not consider adding keys to response objects a breaking change, so the shape of objects may change without notice. However, existing keys will not be changed nor removed without notice._ 
  

# Standard Response

Calling a method for results always returns a structure like this:

```
{
  "status": "success",
  "result": {}
}

 ```

_status_ indicates whether or not the store has replied. A value of "success" means it has and the results are included as the "result" element. A value of "waiting" means the message response has not yet arrived. Finally, "failed" means the database rejected the request, a reason will be included as the result.

## Table of Contents

- [API Data Pass Through](#api-data-pass-through) (1 endpoints)
- [Accounts Payable](#accounts-payable) (1 endpoints)
- [Authentication](#authentication) (2 endpoints)
- [Customers](#customers) (10 endpoints)
- [Order Entry](#order-entry) (51 endpoints)
- [Order History](#order-history) (1 endpoints)
- [Other](#other) (2 endpoints)
- [Reports](#reports) (2 endpoints)
- [Schedule Pro](#schedule-pro) (17 endpoints)
- [Store Settings](#store-settings) (1 endpoints)

---

## API Data Pass Through

*1 endpoints*

### API Pass Through

**POST** `https://api.rfms.online/v2/passthrough`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `methodName` | string | Yes | Example: `Method.Name` |
| `requestPayload` | object | Yes |  |
| `requestPayload.username` | string | Yes | Example: `Username` |
| `requestPayload.legacy` | boolean | Yes |  |

**Example:**

```json
{
    "methodName": "Method.Name",
    "requestPayload": {
        "username": "Username",
        "legacy": false
    }
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "methodName": "Method.Name",
    "requestPayload": {
        "username": "Username",
        "legacy": false
    }
}' 'https://api.rfms.online/v2/passthrough'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/passthrough',
    json={
        "methodName": "Method.Name",
        "requestPayload": {
                "username": "Username",
                "legacy": false
        }
}
)

print(response.json())
```

#### Response Examples

**Raw Query** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `671`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "DidCosting": true,
    "IsError": true,
    "ReceivingResults": {
      "Method": "UpdateOrderLines",
      "Code": 0,
      "Message": "Receiving complete",
      "IsError": false,
      "ReceivedRollsItems": [
        {
          "RollLadingNumber": "31",
          "PONumber": "",
          "IsRoll": true,
          "SeqNumSystemRefNum": 123
        }
      ]
    },
    "CostingResults": {
      "IsNull": false,
      "IsError": true,
      "IsValidationError": true,
      "IsModelError": true,
      "IsException": false,
      "Messages": "No Invoice Number Provided\r\nInvoice Date can not be null\r\nPayable can not be nullThere are errors with the costing data",
      "ValidationMessages": "No Invoice Number Provided\r\nInvoice Date can not be null\r\nPayable can not be null",
      "ExceptionMessage": ""
    }
  }
}
```

---

## Accounts Payable

*1 endpoints*

### Record Payables

**POST** `https://api.rfms.online/v2/payables`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `[0].supplierName` | string | Yes | Example: `ACME` |
| `[0].invoiceNumber` | string | Yes | Example: `XS101` |
| `[0].invoiceDate` | string | Yes | Example: `9/24/19` |
| `[0].dueDate` | string | Yes | Example: `10/24/19` |
| `[0].discountableAmount` | integer | Yes | Example: `10` |
| `[0].nonDiscountableAmount` | integer | Yes | Example: `90` |
| `[0].discountRate` | number | Yes | Example: `0.1` |
| `[0].linkedDocumentNumber` | string | Yes |  |
| `[0].internalNotes` | string | Yes | Example: `Internal note` |
| `[0].remittanceAdviceNotes` | string | Yes | Example: `Remit note` |
| `[0].detailLines` | array | Yes |  |
| `[0].detailLines[0].storeNumber` | integer | Yes | Example: `32` |
| `[0].detailLines[0].accountCode` | string | Yes | Example: `101` |
| `[0].detailLines[0].subAccountCode` | string | Yes |  |
| `[0].detailLines[0].amount` | integer | Yes | Example: `100` |
| `[0].detailLines[0].comment` | string | Yes | Example: `detail line` |

**Example:**

```json
[
  {
    "supplierName": "ACME",
    "invoiceNumber": "XS101",
    "invoiceDate": "9/24/19",
    "dueDate": "10/24/19",
    "discountableAmount": 10,
    "nonDiscountableAmount": 90,
    "discountRate": 0.1,
    "linkedDocumentNumber": "",
    "internalNotes": "Internal note",
    "remittanceAdviceNotes": "Remit note",
    "detailLines": [
      {
        "storeNumber": 32,
        "accountCode": "101",
        "subAccountCode": "",
        "amount": 100,
        "comment": "detail line"
      }
    ]
  }
]
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '[
  {
    "supplierName": "ACME",
    "invoiceNumber": "XS101",
    "invoiceDate": "9/24/19",
    "dueDate": "10/24/19",
    "discountableAmount": 10,
    "nonDiscountableAmount": 90,
    "discountRate": 0.1,
    "linkedDocumentNumber": "",
    "internalNotes": "Internal note",
    "remittanceAdviceNotes": "Remit note",
    "detailLines": [
      {
        "storeNumber": 32,
        "accountCode": "101",
        "subAccountCode": "",
        "amount": 100,
        "comment": "detail line"
      }
    ]
  }
]' 'https://api.rfms.online/v2/payables'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/payables',
    headers={
    "Content-Type": "application/json"
},
    json=[
        {
                "supplierName": "ACME",
                "invoiceNumber": "XS101",
                "invoiceDate": "9/24/19",
                "dueDate": "10/24/19",
                "discountableAmount": 10,
                "nonDiscountableAmount": 90,
                "discountRate": 0.1,
                "linkedDocumentNumber": "",
                "internalNotes": "Internal note",
                "remittanceAdviceNotes": "Remit note",
                "detailLines": [
                        {
                                "storeNumber": 32,
                                "accountCode": "101",
                                "subAccountCode": "",
                                "amount": 100,
                                "comment": "detail line"
                        }
                ]
        }
]
)

print(response.json())
```

#### Response Examples

**Record Payables** ( - 0)

```json
{
  "status": "success",
  "result": "ACME - XS101 Added",
  "detail": null
}
```

---

## Authentication

*2 endpoints*

### Begin a new session

**POST** `https://api.rfms.online/v2/session/begin`

#### Authentication

This endpoint requires **HTTP Basic Authentication**.

- **Username:** `store-afa99b8c68ac42d7b6984091fda29ab0`
- **Password:** `{{apikey}}` (API Key or Session Token)

#### Code Examples

**cURL:**

```bash
curl -X POST -u 'store-afa99b8c68ac42d7b6984091fda29ab0:{{apikey}}' 'https://api.rfms.online/v2/session/begin'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/session/begin',
    auth=('store-afa99b8c68ac42d7b6984091fda29ab0', '{{apikey}}')
)

print(response.json())
```

#### Response Examples

**Begin a new session** (OK - 200)

```json
{
  "authorized": true,
  "sessionToken": "1598c4a37c1c54552732bb907013176d",
  "sessionExpires": "3/5/2018 7:00:39 PM +00:00"
}
```

---

### Request Bus ID

**POST** `https://api.rfms.online/v2/session/request`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rfmsBusId` | integer | Yes | Example: `99999` |
| `reason` | string | Yes | Example: `PRACTICE: To provide access to TPD's App` |

**Example:**

```json
{
  "rfmsBusId": 99999,
  "reason": "PRACTICE: To provide access to TPD's App"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "rfmsBusId": 99999,
  "reason": "PRACTICE: To provide access to TPD'\''s App"
}' 'https://api.rfms.online/v2/session/request'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/session/request',
    headers={
    "Content-Type": "application/json"
},
    json={
        "rfmsBusId": 99999,
        "reason": "PRACTICE: To provide access to TPD's App"
}
)

print(response.json())
```

---

## Customers

*10 endpoints*

### Find Customers

**POST** `https://api.rfms.online/v2/customers/find`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `blackmore` |
| `includeCustomers` | string | Yes | Example: `true` |
| `includeProspects` | string | Yes | Example: `false` |
| `includeInactive` | string | Yes | Example: `false` |

**Example:**

```json
{
  "searchText": "blackmore",
  "includeCustomers": "true",
  "includeProspects": "false",
  "includeInactive": "false"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "searchText": "blackmore",
  "includeCustomers": "true",
  "includeProspects": "false",
  "includeInactive": "false"
}' 'https://api.rfms.online/v2/customers/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/customers/find',
    headers={
    "Content-Type": "application/json"
},
    json={
        "searchText": "blackmore",
        "includeCustomers": "true",
        "includeProspects": "false",
        "includeInactive": "false"
}
)

print(response.json())
```

#### Response Examples

**Customers Find** (OK - 200)

```json
{
  "status": "success",
  "result": [],
  "detail": [
    {
      "customerSource": "Customer",
      "customerSourceId": 12345,
      "salesLeadId": 0,
      "lmsId": "",
      "customerName": "GROKMAN",
      "customerFirstName": "ISAAK",
      "actualCustomerFirstName": "ISAAK",
      "customerLastName": "GROKMAN",
      "customerBusinessName": "BIZ",
      "customerAddress": "2 CASTA WAY",
      "customerAddress2": "UNIT 3",
      "customerCity": "FAYETTE",
      "customerState": "AL",
      "customerZIP": "35555",
      "customerPhone": "(808) 978 74",
      "customerPhone2": "",
      "customerPhone3": "",
      "useSoldToBusinessName": false,
      "customerEmail": "issak@castaway.abc",
      "customerCounty": "FAYETTE",
      "shipToName": "GROKMAN",
      "shipToFirstName": "ISAAK",
      "shipToLastName": "GROKMAN",
      "shipToBusinessName": "BIZ",
      "actualShipToFirstName": "ISAAK",
      "shipToAddress": "3 CASTA WAY",
      "shipToAddress2": "UNIT 2",
      "shipToCity": "FAUNSDALE",
      "shipToState": "AL",
      "shipToZIP": "36738",
      "shipToCounty": "MARENGO",
      "useShipToBusinessName": false,
      "customerType": "ACCOMMODATIONS",
      "referralType": "Standalone",
      "referralMemberId": 0,
      "referralMemberName": "",
      "taxStatus": "Tax",
      "taxMethod": "UseTax",
      "taxId": "",
      "preferredPriceLevel": 1,
      "preferredSalesperson1": "",
      "preferredSalesperson2": "",
      "jobNumberOverride": null,
      "entryType": "Customer",
      "terms": "",
      "termDays": 0,
      "creditLimit": 0,
      "defaultStore": 32,
      "internalNotes": "",
      "remarks": []
    }
  ]
}
```

---

### Advanced Customers Find

**POST** `https://api.rfms.online/v2/customers/find/advanced`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `car` |
| `stores` | array | Yes |  |
| `activeOnly` | boolean | Yes |  |
| `dateCreatedFrom` | string | Yes | Example: `01-01-2021` |
| `customerTypes` | array | Yes |  |

**Example:**

```json
{
    "searchText": "car",
    "stores": [32, 50],
    "activeOnly": false,
    "dateCreatedFrom": "01-01-2021",
    "customerTypes": ["Commercial"]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "searchText": "car",
    "stores": [32, 50],
    "activeOnly": false,
    "dateCreatedFrom": "01-01-2021",
    "customerTypes": ["Commercial"]
}' 'https://api.rfms.online/v2/customers/find/advanced'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/customers/find/advanced',
    json={
        "searchText": "car",
        "stores": [
                32,
                50
        ],
        "activeOnly": false,
        "dateCreatedFrom": "01-01-2021",
        "customerTypes": [
                "Commercial"
        ]
}
)

print(response.json())
```

#### Response Examples

**Advanced Customers Find** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `7675`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "phone3": "",
      "contact1": "MAX ERNST",
      "contact2": "",
      "active": true,
      "dateCreated": "2021-03-23T15:12:50",
      "createdBy": "kwilson",
      "dateUpdated": "2023-10-30T10:39:44",
      "updatedBy": "CBanuelos",
      "customerId": 75688,
      "customerAddress": {
        "businessName": "BANUELOS LLC",
        "lastName": "BANUELOS2",
        "firstName": "CARLTON",
        "address1": "123 Apple Rd",
        "address2": "",
        "city": "AKRON",
        "state": "AL",
        "postalCode": "35441",
        "county": "HALE",
        "country": null
      },
      "shipToAddress": {
        "businessName": "BANUELOS LLC",
        "lastName": "BANUELOS2",
        "firstName": "CARLTON",
        "address1": "14 INDUSTRIAL WAY",
        "address2": "STE 23",
        "city": "AKRON",
        "state": "AL",
        "postalCode": "35441",
        "county": "HALE",
        "country": null
      },
      "customerType": "COMMERCIAL",
      "entryType": "Customer",
      "phone1": "2052062071",
      "phone2": "",
      "email": "cbanllc@banllc.com",
      "preferredSalesperson1": "KAY SAGE",
      "preferredSalesperson2": "",
      "storeNumber": 50,
      "referralType": "Standalone",
      "referralMemberId": 0,
      "referralMemberName": ""
    },
    {
      "phone3": "",
      "contact1": "FIRST CONTACT",
      "contact2": "",
      "active": true,
      "dateCreated": "2021-04-08T10:53:53",
      "createdBy": "CBanuelos",
      "dateUpdated": "2021-04-08T10:53:53",
      "updatedBy": "CBanuelos",
      "customerId": 75693,
      "customerAddress": {
        "businessName": "ODYSSEY INC",
        "lastName": "HOMER",
        "firstName": "SIMPSON",
        "address1": "1222 NE SW North Blvd",
        "address2": "2L",
        "city": "ALAMOGORDO",
        "state": "NM",
        "postalCode": "88310",
        "county": "OTERO",
        "country": "UNITED STATES"
      },
      "shipToAddress": {
        "businessName": "ODYSSEY INC",
        "lastName": "HOMER",
        "firstName": "SIMPSON",
        "address1": "1222 NE SW North Blvd",
        "address2": "2L",
        "city": "ALAMOGORDO",
        "state": "NM",
        "postalCode": "88310",
        "county": "OTERO",
        "country": "UNITED STATES"
      },
      "customerType": "COMMERCIAL",
      "entryType": "Customer",
      "phone1": "2054445555",
      "phone2": "",
      "email": "ODYSSEY@SIMPSON.COM",
      "preferredSalesperson1": "CARLS BAD",
      "preferredSalesperson2": "",
      "storeNumber": 32,
      "referralType": "Standalone",
      "referralMemberId": 0,
      "referralMemberName": ""
    },
    {
      "phone3": "",
      "contact1": "",
      "contact2": "",
      "active": true,
      "dateCreated": "2021-04-13T10:21:27",
      "createdBy": "CBanuelos",
      "dateUpdated": "2021-04-13T11:07:04",
      "updatedBy": "CBanuelos",
      "customerId": 75696,
      "customerAddress": {
        "businessName": "ABC CONTRACTORS",
        "lastName": "LETTERMAN",
        "firstName": "DILON",
        "address1": "123 FOUR DR",
        "address2": "FLOOR 1",
        "city": "ALABASTER",
        "state": "AL",
        "postalCode": "35007",
        "county": "JEFFERSON",
        "country": null
      },
      "shipToAddress": {
        "businessName": "ABC CONTRACTORS",
        "lastName": "LETTERMAN",
        "firstName": "DILON",
        "address1": "123 FOUR DR",
        "address2": "FLOOR 1",
        "city": "ALABASTER",
        "state": "AL",
        "postalCode": "35007",
        "county": "JEFFERSON",
        "country": null
      },
      "customerType": "COMMERCIAL",
      "entryType": "Customer",
      "phone1": "2052042031",
      "phone2": "9371567",
      "email": "CB@TESTING.COM",
      "preferredSalesperson1": "CARLS GOOD",
      "preferredSalesperson2": "",
      "storeNumber": 32,
      "referralType": "Standalone",
      "referralMemberId": 0,
      "referralMemberName": ""
    }
  ],
  "detail": null
}
```

---

### Get Customer

**GET** `https://api.rfms.online/v2/customer/{customerId}`

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customerId` | string | Yes | Path parameter |

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/customer/{customerId}'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/customer/{customerId}',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Customer** (OK - 200)

```json
{
  "status": "success",
  "result": {
    "customerId": 12345,
    "customerType": "ACCOMMODATIONS",
    "entryType": "Customer",
    "customerAddress": {
      "businessName": "BIZ",
      "lastName": "GROKMAN",
      "firstName": "ISAAK",
      "address1": "2 CASTA WAY",
      "address2": "UNIT 1",
      "city": "FAYETTE",
      "state": "AL",
      "postalCode": "35555",
      "county": ""
    },
    "shipToAddress": {
      "businessName": "BIZ",
      "lastName": "GROKMAN",
      "firstName": "ISAAK",
      "address1": "3 CASTA WAY",
      "address2": "UNIT 2",
      "city": "FAUNSDALE",
      "state": "AL",
      "postalCode": "36738",
      "county": ""
    },
    "phone1": "(808) 978 74",
    "phone2": "",
    "email": "issak@castaway.abc",
    "taxStatus": "Tax",
    "taxMethod": "UseTax",
    "preferredSalesperson1": "JOE SHMO",
    "preferredSalesperson2": "",
    "storeNumber": 32,
    "notes": "",
    "referralType": "Standalone",
    "referralMemberId": 0,
    "referralMemberName": "",
    "lmsId": ""
  },
  "detail": {
    "customerSource": "Customer",
    "customerSourceId": 12345,
    "salesLeadId": 0,
    "lmsId": "",
    "customerName": "GROKMAN",
    "customerFirstName": "ISAAK",
    "actualCustomerFirstName": "ISAAK",
    "customerLastName": "GROKMAN",
    "customerBusinessName": "BIZ",
    "customerAddress": "2 CASTA WAY",
    "customerAddress2": "UNIT 1",
    "customerCity": "FAYETTE",
    "customerState": "AL",
    "customerZIP": "35555",
    "customerPhone": "(808) 978 74",
    "customerPhone2": "",
    "customerPhone3": "",
    "useSoldToBusinessName": false,
    "customerEmail": "issak@castaway.abc",
    "customerCounty": "",
    "shipToName": "GROKMAN",
    "shipToFirstName": "ISAAK",
    "shipToLastName": "GROKMAN",
    "shipToBusinessName": "BIZ",
    "actualShipToFirstName": "ISAAK",
    "shipToAddress": "3 CASTA WAY",
    "shipToAddress2": "UNIT 2",
    "shipToCity": "FAUNSDALE",
    "shipToState": "AL",
    "shipToZIP": "36738",
    "shipToCounty": "",
    "useShipToBusinessName": false,
    "customerType": "ACCOMMODATIONS",
    "referralType": "Standalone",
    "referralMemberId": 0,
    "referralMemberName": "",
    "taxStatus": "Tax",
    "taxMethod": "UseTax",
    "taxId": "",
    "preferredPriceLevel": 1,
    "preferredSalesperson1": "JOE SHMO",
    "preferredSalesperson2": "",
    "jobNumberOverride": null,
    "entryType": "Customer",
    "terms": "",
    "termDays": 0,
    "creditLimit": 0,
    "defaultStore": 32,
    "internalNotes": "",
    "remarks": []
  }
}
```

**Get Customer - Internal Note** (OK - 200)

```json
{
  "status": "success",
  "result": {
    "customerId": 75526,
    "customerType": "CASH & CARRY",
    "entryType": "Customer",
    "customerAddress": {
      "businessName": null,
      "lastName": "APARTMENTS",
      "firstName": "CB",
      "address1": "123 TEST AVE",
      "address2": "",
      "city": "SAN DIEGO",
      "state": "CA",
      "postalCode": "92026",
      "county": null
    },
    "shipToAddress": {
      "businessName": null,
      "lastName": "BANUELOS",
      "firstName": "CARLOS",
      "address1": "123 TEST AVE",
      "address2": "",
      "city": "SAN DIEGO",
      "state": "CA",
      "postalCode": "92026",
      "county": null
    },
    "phone1": "2051234567",
    "phone2": "",
    "email": "TEST@TEST.COM",
    "taxStatus": "Tax",
    "taxMethod": "SalesTax",
    "preferredSalesperson1": "CARLOS BANUELOS",
    "preferredSalesperson2": "",
    "storeNumber": 32,
    "notes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Courier New';font-size:9pt;color:#000000;;\">Customer Internal Note for CB Apartments</span></p>\n</div>\n</div>"
  },
  "detail": {
    "customerSource": "Customer",
    "customerSourceId": 75526,
    "salesLeadId": 0,
    "customerName": "APARTMENTS",
    "customerFirstName": "CB",
    "actualCustomerFirstName": "CB",
    "customerLastName": "APARTMENTS",
    "customerBusinessName": "CARLOS BANUELOS",
    "customerAddress": "123 TEST AVE",
    "customerAddress2": "",
    "customerCity": "SAN DIEGO",
    "customerState": "CA",
    "customerZIP": "92026",
    "customerPhone": "2051234567",
    "customerPhone2": "",
    "customerPhone3": "",
    "customerEmail": "TEST@TEST.COM",
    "customerCounty": null,
    "shipToName": "BANUELOS",
    "shipToFirstName": "CARLOS",
    "shipToLastName": "BANUELOS",
    "shipToBusinessName": "",
    "actualShipToFirstName": "CARLOS",
    "shipToAddress": "123 TEST AVE",
    "shipToAddress2": "",
    "shipToCity": "SAN DIEGO",
    "shipToState": "CA",
    "shipToZIP": "92026",
    "shipToCounty": null,
    "customerType": "CASH & CARRY",
    "referralType": "Standalone",
    "referralMemberId": 0,
    "referralMemberName": "",
    "taxStatus": "Tax",
    "taxMethod": "SalesTax",
    "preferredPriceLevel": 0,
    "preferredSalesperson1": "CARLOS BANUELOS",
    "preferredSalesperson2": "",
    "jobNumberOverride": null,
    "entryType": "Customer",
    "terms": "",
    "termDays": 0,
    "creditLimit": 0,
    "defaultStore": 32,
    "internalNotes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Courier New';font-size:9pt;color:#000000;;\">Customer Internal Note for CB Apartments</span></p>\n</div>\n</div>",
    "remarks": []
  }
}
```

---

### Get Customer Values

**GET** `https://api.rfms.online/v2/customers`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/customers'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/customers'
)

print(response.json())
```

#### Response Examples

**Get Customer Values** (OK - 200)

```json
{
  "customerType": [
    "ACCOMMODATIONS",
    "CASH & CARRY",
    "COMMERCIAL",
    "INSTALLER",
    "REMODELING"
  ],
  "entryType": [
    "Customer",
    "Prospect"
  ],
  "taxStatus": [
    "Tax",
    "Exempt",
    "Resale"
  ],
  "taxMethod": [
    "SalesTax",
    "UseTax",
    "LineTax"
  ],
  "preferredSalesperson1": [
    "BOB",
    "ANDREW",
    "HOUSE",
    "FRANK"
  ],
  "preferredSalesperson2": [
    "BOB",
    "ANDREW",
    "HOUSE",
    "FRANK"
  ],
  "stores": [
    {
      "id": 32,
      "name": "ACME CARPET WEST",
      "displayCode": " "
    },
    {
      "id": 50,
      "name": "ACME CARPET EAST",
      "displayCode": "2"
    }
  ]
}
```

---

### Create or Update a Customer

**POST** `https://api.rfms.online/v2/customer`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `customerType` | string | Yes | Example: `COMMERCIAL` |
| `entryType` | string | Yes | Example: `Customer` |
| `customerAddress` | object | Yes |  |
| `customerAddress.lastName` | string | Yes | Example: `DOE` |
| `customerAddress.firstName` | string | Yes | Example: `JOHN` |
| `customerAddress.address1` | string | Yes | Example: `1234 MAIN ST` |
| `customerAddress.address2` | string | Yes | Example: `STE 33` |
| `customerAddress.city` | string | Yes | Example: `ANYTOWN` |
| `customerAddress.state` | string | Yes | Example: `CA` |
| `customerAddress.postalCode` | string | Yes | Example: `91332` |
| `customerAddress.county` | string | Yes | Example: `LOS ANGELES` |
| `shipToAddress` | object | Yes |  |
| `shipToAddress.lastName` | string | Yes | Example: `DOE` |
| `shipToAddress.firstName` | string | Yes | Example: `JOHN` |
| `shipToAddress.address1` | string | Yes | Example: `1234 MAIN ST` |
| `shipToAddress.address2` | string | Yes | Example: `STE 33` |
| `shipToAddress.city` | string | Yes | Example: `ANYTOWN` |
| `shipToAddress.state` | string | Yes | Example: `CA` |
| `shipToAddress.postalCode` | string | Yes | Example: `91332` |
| `shipToAddress.county` | string | Yes | Example: `LOS ANGELES` |

**Example:**

```json
{
  "customerType": "COMMERCIAL",
  "entryType": "Customer",          
  "customerAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "shipToAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "phone1": "661-555-1212",
  "phone2": "818-298-0000",
  "email": "john.doe@gmail.com",
  "taxStatus": "Tax",               
  "taxMethod": "SalesTax",          
  "preferredSalesperson1": "BOB",
  "preferredSalesperson2": "",
  "storeNumber": 32
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "customerType": "COMMERCIAL",
  "entryType": "Customer",          
  "customerAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "shipToAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "phone1": "661-555-1212",
  "phone2": "818-298-0000",
  "email": "john.doe@gmail.com",
  "taxStatus": "Tax",               
  "taxMethod": "SalesTax",          
  "preferredSalesperson1": "BOB",
  "preferredSalesperson2": "",
  "storeNumber": 32
}' 'https://api.rfms.online/v2/customer'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/customer',
    headers={
    "Content-Type": "application/json"
},
    json={
        "customerType": "COMMERCIAL",
        "entryType": "Customer",
        "customerAddress": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "shipToAddress": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "phone1": "661-555-1212",
        "phone2": "818-298-0000",
        "email": "john.doe@gmail.com",
        "taxStatus": "Tax",
        "taxMethod": "SalesTax",
        "preferredSalesperson1": "BOB",
        "preferredSalesperson2": "",
        "storeNumber": 32
}
)

print(response.json())
```

#### Response Examples

**Create a New Customer** (OK - 200)

**Update a Customer** (OK - 200)

---

### Create an Opportunity

**POST** `https://api.rfms.online/v2/opportunity`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `createOrder` | boolean | Yes |  |
| `notes` | string | Yes | Example: `SAMPLE NOTES` |
| `estimatedDeliveryDate` | string | Yes | Example: `3/1/2019` |
| `storeNumber` | integer | Yes | Example: `32` |
| `customerType` | string | Yes | Example: `COMMERCIAL` |
| `entryType` | string | Yes | Example: `Customer` |
| `customerAddress` | object | Yes |  |
| `customerAddress.businessName` | string | Yes | Example: `ACME` |
| `customerAddress.lastName` | string | Yes | Example: `DOE` |
| `customerAddress.firstName` | string | Yes | Example: `JOHN` |
| `customerAddress.address1` | string | Yes | Example: `1234 MAIN ST` |
| `customerAddress.address2` | string | Yes | Example: `STE 33` |
| `customerAddress.city` | string | Yes | Example: `ANYTOWN` |
| `customerAddress.state` | string | Yes | Example: `CA` |
| `customerAddress.postalCode` | string | Yes | Example: `91332` |
| `customerAddress.county` | string | Yes | Example: `LOS ANGELES` |
| `shipToAddress` | object | Yes |  |
| `shipToAddress.lastName` | string | Yes | Example: `DOE` |
| `shipToAddress.firstName` | string | Yes | Example: `JOHN` |
| `shipToAddress.address1` | string | Yes | Example: `1234 MAIN ST` |

**Example:**

```json
{
  "createOrder": false,
  "notes": "SAMPLE NOTES",
  "estimatedDeliveryDate": "3/1/2019",
  "storeNumber": 32,
  "customerType": "COMMERCIAL",
  "entryType": "Customer",          
  "customerAddress": {
  	"businessName": "ACME",
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "shipToAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "phone1": "661-555-1212",
  "phone2": "818-298-0000",
  "email": "john.doe@gmail.com",
  "taxStatus": "Tax",               
  "taxMethod": "SalesTax",          
  "preferredSalesperson1": "BOB",
  "preferredSalesperson2": "",
  "poNumber": "12346",
  "jobNumber": "X22333"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "createOrder": false,
  "notes": "SAMPLE NOTES",
  "estimatedDeliveryDate": "3/1/2019",
  "storeNumber": 32,
  "customerType": "COMMERCIAL",
  "entryType": "Customer",          
  "customerAddress": {
  	"businessName": "ACME",
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "shipToAddress": {
    "lastName": "DOE",
    "firstName": "JOHN",
    "address1": "1234 MAIN ST",
    "address2": "STE 33",
    "city": "ANYTOWN",
    "state": "CA",
    "postalCode": "91332",
    "county": "LOS ANGELES"
  },
  "phone1": "661-555-1212",
  "phone2": "818-298-0000",
  "email": "john.doe@gmail.com",
  "taxStatus": "Tax",               
  "taxMethod": "SalesTax",          
  "preferredSalesperson1": "BOB",
  "preferredSalesperson2": "",
  "poNumber": "12346",
  "jobNumber": "X22333"
}' 'https://api.rfms.online/v2/opportunity'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/opportunity',
    headers={
    "Content-Type": "application/json"
},
    json={
        "createOrder": false,
        "notes": "SAMPLE NOTES",
        "estimatedDeliveryDate": "3/1/2019",
        "storeNumber": 32,
        "customerType": "COMMERCIAL",
        "entryType": "Customer",
        "customerAddress": {
                "businessName": "ACME",
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "shipToAddress": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "phone1": "661-555-1212",
        "phone2": "818-298-0000",
        "email": "john.doe@gmail.com",
        "taxStatus": "Tax",
        "taxMethod": "SalesTax",
        "preferredSalesperson1": "BOB",
        "preferredSalesperson2": "",
        "poNumber": "12346",
        "jobNumber": "X22333"
}
)

print(response.json())
```

#### Response Examples

**Create a New Opportunity** (OK - 200)

```json
{
  "status": "success",
  "result": "ES803274"
}
```

---

### Get CRM Opportunities

**GET** `https://api.rfms.online/v2/opportunities`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/opportunities'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/opportunities'
)

print(response.json())
```

#### Response Examples

**Get CRM Opportunities ** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": [
    {
      "id": "N07W7BPIXY",
      "title": "DANNY WILSON",
      "customerId": "1472",
      "salesperson": "kurt@rfmstest.com",
      "store": 32,
      "dateCreated": "3/17/2021",
      "lastModified": "6/28/2021 1:58 PM",
      "totalValue": 22402.21,
      "stage": "Quote",
      "quotes": [
        "ES103292",
        "undefined"
      ],
      "quoteApproval": "undefined",
      "orders": [],
      "products": []
    },
    {
      "id": "IVUWQJ2SQX",
      "title": "MCM-1370, MCM-1370",
      "customerId": "75691",
      "salesperson": "justin@branch.com",
      "store": 57,
      "dateCreated": "4/5/2021",
      "lastModified": "6/28/2021 1:50 PM",
      "totalValue": 17261.02,
      "stage": "Quote",
      "quotes": [
        "ES103329"
      ],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 963816,
          "colorId": 7602135,
          "quantity": 1200,
          "sampleCheckedOut": false,
          "price": 3.99
        }
      ]
    },
    {
      "id": "9I9D9U503A",
      "title": "SERGEEV, ALYOSHA",
      "customerId": "75557",
      "salesperson": "justestimator@rfmstest.com",
      "store": 50,
      "dateCreated": "5/6/2021",
      "lastModified": "6/28/2021 1:50 PM",
      "totalValue": 1422,
      "stage": "Products",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1038121,
          "colorId": 8371554,
          "quantity": 600,
          "sampleCheckedOut": true,
          "price": 2
        },
        {
          "id": 918873,
          "colorId": 6989115,
          "quantity": 600,
          "sampleCheckedOut": false,
          "price": 2.37
        }
      ]
    }
  ],
  "detail": null
}
```

---

### Get CRM Opportunities  By Stage

**GET** `https://api.rfms.online/v2/opportunities/:stage`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/opportunities/:stage'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/opportunities/:stage'
)

print(response.json())
```

#### Response Examples

**Get CRM Opportunities  By Stage** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": [
    {
      "id": "DP3LP1E3C7",
      "title": "KONG, KING",
      "customerId": "75065",
      "salesperson": "giul@branch.com",
      "store": 0,
      "dateCreated": "11/27/2019",
      "lastModified": "6/7/2021 11:42 AM",
      "totalValue": 254.62,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "2GLKH6725E",
      "title": "JAMES SMITH",
      "customerId": "1392",
      "salesperson": "SNEAKY PETE",
      "store": 0,
      "dateCreated": "2/27/2020",
      "lastModified": "11/16/2020 9:56 AM",
      "totalValue": 3588.19,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 986136,
          "colorId": 7813587,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 8.39
        }
      ]
    },
    {
      "id": "VB4HGK5BZ3",
      "title": "BEERHAUS, ARCHIE",
      "customerId": "75434",
      "salesperson": "th@rfmstest.com",
      "store": 0,
      "dateCreated": "5/27/2020",
      "lastModified": "9/3/2020 8:10 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "AY4N0JJQQ6",
      "title": "1569610676320, JOETRUSTWORTHY 2020-05-28",
      "customerId": "74500",
      "salesperson": "th@rfmstest.com",
      "store": 32,
      "dateCreated": "5/28/2020",
      "lastModified": "7/29/2020 9:44 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "MD26PWPVUL",
      "title": "BUILDER, BOB",
      "customerId": "75483",
      "salesperson": "justin@branch.com",
      "store": 32,
      "dateCreated": "7/10/2020",
      "lastModified": "8/26/2020 10:42 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 963816,
          "colorId": 7602150,
          "quantity": 20,
          "sampleCheckedOut": false,
          "price": 1.68
        }
      ]
    },
    {
      "id": "84IL5GNF8T",
      "title": "MM-3044, TIFFANY",
      "customerId": "75509",
      "salesperson": "test1@branch.com",
      "store": 32,
      "dateCreated": "8/28/2020",
      "lastModified": "9/2/2020 11:28 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1002684,
          "colorId": 7973480,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 5.03
        }
      ]
    },
    {
      "id": "TAAPR8N5VA",
      "title": "MM-3044, LAURA",
      "customerId": "75510",
      "salesperson": "test1@branch.com",
      "store": 32,
      "dateCreated": "8/28/2020",
      "lastModified": "8/27/2020 10:17 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1002684,
          "colorId": 7973463,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 5.03
        }
      ]
    },
    {
      "id": "UYYHUFO7CQ",
      "title": "FRIEDMAN, JONATHAN",
      "customerId": "3129",
      "salesperson": "th@rfmstest.com",
      "store": 32,
      "dateCreated": "9/3/2020",
      "lastModified": "5/26/2021 3:55 PM",
      "totalValue": 10000,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1034528,
          "colorId": 8354181,
          "quantity": 1200,
          "sampleCheckedOut": false,
          "price": 4.32
        }
      ]
    },
    {
      "id": "VXZNBN367O",
      "title": "BANUELOS, CARLOS",
      "customerId": "75515",
      "salesperson": "eta@branch.com",
      "store": 0,
      "dateCreated": "9/9/2020",
      "lastModified": "10/1/2020 12:29 PM",
      "totalValue": 2723.94,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "GVYA07WGZH",
      "title": "BEVERLY SMITH",
      "customerId": "1286",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "10/6/2020",
      "lastModified": "10/6/2020 11:10 AM",
      "totalValue": 3687,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "PEV0NZMMAG",
      "title": "BRANDON SMITH",
      "customerId": "968",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "10/6/2020",
      "lastModified": "10/6/2020 11:16 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "60TSWOVWE0",
      "title": "EVAN SMITH",
      "customerId": "2068",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "10/6/2020",
      "lastModified": "10/25/2020 11:47 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "K0ZSRDY7AO",
      "title": "BEVERLY SMITH",
      "customerId": "1286",
      "salesperson": "th@rfmstest.com",
      "store": 32,
      "dateCreated": "10/7/2020",
      "lastModified": "10/20/2020 11:40 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "OGVIKY86T2",
      "title": "1, MMTEST",
      "customerId": "75552",
      "salesperson": "carlos@branch.com",
      "store": 0,
      "dateCreated": "10/8/2020",
      "lastModified": "10/8/2020 9:42 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "V47LRF2ZZL",
      "title": "UNREF, UNREF",
      "customerId": "75571",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "10/22/2020",
      "lastModified": "3/1/2021 3:12 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 963816,
          "colorId": 7602159,
          "quantity": 216,
          "sampleCheckedOut": false,
          "price": 3.99
        },
        {
          "id": 1037747,
          "colorId": 8371147,
          "quantity": 100,
          "sampleCheckedOut": false,
          "price": 0.71
        }
      ]
    },
    {
      "id": "O3L7KV8Y8Z",
      "title": "BALAKITSIS, THOMAS",
      "customerId": "2762",
      "salesperson": "th@rfmstest.com",
      "store": 32,
      "dateCreated": "1/11/2021",
      "lastModified": "1/11/2021 3:45 PM",
      "totalValue": 744.75,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "WFJ8Q004NI",
      "title": "BRANDON SMITH",
      "customerId": "968",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "1/15/2021",
      "lastModified": "1/14/2021 7:46 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "HO4MBSYAI2",
      "title": "WILSON, KURT & SARAH",
      "customerId": "75632",
      "salesperson": "kurt@rfmstest.com",
      "store": 50,
      "dateCreated": "1/15/2021",
      "lastModified": "7/7/2021 11:02 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "M11UIYCQEN",
      "title": "BROWN, JAMES",
      "customerId": "75633",
      "salesperson": "kurt@rfmstest.com",
      "store": 50,
      "dateCreated": "1/15/2021",
      "lastModified": "1/19/2021 1:16 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1038121,
          "colorId": 8371554,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        },
        {
          "id": 1038133,
          "colorId": 8371627,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        },
        {
          "id": 1038337,
          "colorId": 8374248,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        },
        {
          "id": 1038131,
          "colorId": 8371603,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        }
      ]
    },
    {
      "id": "IDZ14UPJMM",
      "title": "HURBERD THOMAS",
      "customerId": "667",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "1/19/2021",
      "lastModified": "1/19/2021 3:48 PM",
      "totalValue": 1602.86,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "0QJN8XLA4H",
      "title": "CONWELL, THOMAS",
      "customerId": "2763",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "1/19/2021",
      "lastModified": "1/19/2021 5:37 PM",
      "totalValue": 1240.52,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "IS7X7IAB4I",
      "title": "BEVERLY SMITH",
      "customerId": "1286",
      "salesperson": "th@rfmstest.com",
      "store": 50,
      "dateCreated": "1/19/2021",
      "lastModified": "1/19/2021 5:44 PM",
      "totalValue": 1240.52,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "PHTHYZ70O8",
      "title": "CONWELL, THOMAS",
      "customerId": "2763",
      "salesperson": "th@rfmstest.com",
      "store": 32,
      "dateCreated": "1/25/2021",
      "lastModified": "1/25/2021 11:46 AM",
      "totalValue": 689.13,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "D7NCGLH77H",
      "title": "CONWELL, THOMAS",
      "customerId": "2763",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "1/27/2021",
      "lastModified": "4/27/2021 3:11 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "XGXYQBJZZW",
      "title": "VELAND, RUDY",
      "customerId": "72239",
      "salesperson": "newipad@rfmstest.com",
      "store": 32,
      "dateCreated": "2/5/2021",
      "lastModified": "7/15/2021 9:43 AM",
      "totalValue": 5915.28,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1002684,
          "colorId": 7973519,
          "quantity": 1176,
          "sampleCheckedOut": false,
          "price": 5.03
        }
      ]
    },
    {
      "id": "E7S3HV5WYJ",
      "title": "CRM-377 multi option",
      "customerId": "72239",
      "salesperson": "newipad@rfmstest.com",
      "store": 32,
      "dateCreated": "2/5/2021",
      "lastModified": "7/5/2021 1:12 PM",
      "totalValue": 18392.64,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 992048,
          "colorId": 7814432,
          "quantity": 1176,
          "sampleCheckedOut": false,
          "price": 3.35
        },
        {
          "id": 1002684,
          "colorId": 7973480,
          "quantity": 1176,
          "sampleCheckedOut": false,
          "price": 12.29
        },
        {
          "id": 1002684,
          "colorId": 7973519,
          "quantity": 1176,
          "sampleCheckedOut": true,
          "price": 6.72
        },
        {
          "id": 992048,
          "colorId": 7814424,
          "quantity": 1176,
          "sampleCheckedOut": true,
          "price": 1.42
        },
        {
          "id": 992048,
          "colorId": 7814429,
          "quantity": 1176,
          "sampleCheckedOut": false,
          "price": 1.17
        },
        {
          "id": 1002684,
          "colorId": 7973463,
          "quantity": 1176,
          "sampleCheckedOut": false,
          "price": 5.65
        }
      ]
    },
    {
      "id": "DSJ2PT4QF9",
      "title": "DANNY WILSON",
      "customerId": "1472",
      "salesperson": "kurt@rfmstest.com",
      "store": 50,
      "dateCreated": "3/5/2021",
      "lastModified": "7/15/2021 9:43 AM",
      "totalValue": 3531.84,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 988174,
          "colorId": 7783472,
          "quantity": 800,
          "sampleCheckedOut": false,
          "price": 3.12
        },
        {
          "id": 963552,
          "colorId": 7595238,
          "quantity": 89,
          "sampleCheckedOut": false,
          "price": 3.04
        },
        {
          "id": 988174,
          "colorId": 7783458,
          "quantity": 900,
          "sampleCheckedOut": false,
          "price": 3.12
        },
        {
          "id": 918196,
          "colorId": 6983586,
          "quantity": 696,
          "sampleCheckedOut": false,
          "price": 1.04
        }
      ]
    },
    {
      "id": "61Y53UEEBT",
      "title": "MARTINEZ, STEVE",
      "customerId": "75653",
      "salesperson": "carlos2@branch.com",
      "store": 50,
      "dateCreated": "3/5/2021",
      "lastModified": "10/27/2021 9:49 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1038521,
          "colorId": 8377046,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        },
        {
          "id": 1038520,
          "colorId": 8377045,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        }
      ]
    },
    {
      "id": "EASWFSG0VC",
      "title": "JACKSON, LAMAR",
      "customerId": "75686",
      "salesperson": "carlos2@branch.com",
      "store": 32,
      "dateCreated": "3/22/2021",
      "lastModified": "9/29/2021 2:32 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1038520,
          "colorId": 8377045,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        },
        {
          "id": 1038521,
          "colorId": 8377046,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        }
      ]
    },
    {
      "id": "8BD68QW51V",
      "title": "TESTINGLN, TESTINGFN",
      "customerId": "75689",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "4/2/2021",
      "lastModified": "6/30/2021 6:13 PM",
      "totalValue": 178,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1019787,
          "colorId": 8199835,
          "quantity": 89,
          "sampleCheckedOut": false,
          "price": 2
        }
      ]
    },
    {
      "id": "LYXS2CQ1R8",
      "title": "BANUELOS2, CARLOS",
      "customerId": "75561",
      "salesperson": "carlos@branch.com",
      "store": 0,
      "dateCreated": "5/5/2021",
      "lastModified": "5/5/2021 11:02 AM",
      "totalValue": 1089.83,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "N6Q1627CRG",
      "title": "DONALD SMITHs",
      "customerId": "804",
      "salesperson": "test1@branch.com",
      "store": 32,
      "dateCreated": "5/10/2021",
      "lastModified": "6/7/2021 12:08 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1020164,
          "colorId": 0,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        }
      ]
    },
    {
      "id": "EBF1VS1CMY",
      "title": "CRM-510, WALLY",
      "customerId": "75744",
      "salesperson": "newipad@rfmstest.com",
      "store": 32,
      "dateCreated": "7/27/2021",
      "lastModified": "8/26/2021 3:56 PM",
      "totalValue": 1157.1,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1002684,
          "colorId": 7973463,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 5.03
        }
      ]
    },
    {
      "id": "KPA1B2GLFI",
      "title": "Carlos, Carlos",
      "customerId": "75767",
      "salesperson": "carlos@branch.com",
      "store": 0,
      "dateCreated": "9/10/2021",
      "lastModified": "9/29/2021 2:21 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 1038520,
          "colorId": 8377045,
          "quantity": 0,
          "sampleCheckedOut": false,
          "price": 0
        }
      ]
    },
    {
      "id": "GGY9M4WPZ7",
      "title": "!, ROOM",
      "customerId": "75860",
      "salesperson": "carlos@branch.com",
      "store": 53,
      "dateCreated": "9/24/2021",
      "lastModified": "9/24/2021 2:34 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "RNEVLAM1GK",
      "title": "PM, NEW",
      "customerId": "75861",
      "salesperson": "carlos@branch.com",
      "store": 53,
      "dateCreated": "9/24/2021",
      "lastModified": "9/24/2021 2:39 PM",
      "totalValue": 1203.11,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "CEQ4OWSLZG",
      "title": "BANCASH, CARCASH",
      "customerId": "75863",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "10/4/2021",
      "lastModified": "11/16/2021 3:55 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "4YYGYMCYOS",
      "title": "MOE-1044, RUDY",
      "customerId": "75641",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "10/11/2021",
      "lastModified": "10/27/2021 10:52 AM",
      "totalValue": 49.92,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": [
        {
          "id": 992048,
          "colorId": 7814434,
          "quantity": 48,
          "sampleCheckedOut": false,
          "price": 1.04
        }
      ]
    },
    {
      "id": "1DEPWDKS3J",
      "title": "BBUILDER, CBUILDER",
      "customerId": "75865",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "10/12/2021",
      "lastModified": "10/22/2021 3:11 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "T8GBXQOWM7",
      "title": "CORBIN CUSTOM HOMEBUILDERS",
      "customerId": "354",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "10/12/2021",
      "lastModified": "11/15/2021 1:33 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "382Q58TCE4",
      "title": "BANUELOS, CHRIS",
      "customerId": "75702",
      "salesperson": "carlos@branch.com",
      "store": 32,
      "dateCreated": "11/1/2021",
      "lastModified": "11/1/2021 10:21 AM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "MOYBSM1F5U",
      "title": "BANUELOS, CARLOS",
      "customerId": "75515",
      "salesperson": "carlos@branch.com",
      "store": 65,
      "dateCreated": "11/3/2021",
      "lastModified": "11/3/2021 2:51 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "KI1GLT7R8K",
      "title": "BANUELOS, CARLOS",
      "customerId": "75741",
      "salesperson": "carlos@branch.com",
      "store": 65,
      "dateCreated": "11/3/2021",
      "lastModified": "11/15/2021 1:31 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "MQDVW3KE0Y",
      "title": "BANUELOS, CARLOS",
      "customerId": "75608",
      "salesperson": "carlos@branch.com",
      "store": 65,
      "dateCreated": "11/3/2021",
      "lastModified": "11/3/2021 3:16 PM",
      "totalValue": 0,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    },
    {
      "id": "LEDQPKZQZF",
      "title": "BANUELOS, CARLOS",
      "customerId": "75608",
      "salesperson": "carlos@branch.com",
      "store": 65,
      "dateCreated": "11/3/2021",
      "lastModified": "11/12/2021 1:24 PM",
      "totalValue": 1032.88,
      "stage": "Measure",
      "quotes": [],
      "quoteApproval": null,
      "orders": [],
      "products": []
    }
  ],
  "detail": null
}
```

---

### Get Opportunity Change Logs

**GET** `https://api.rfms.online/v2/opportunities/lastmodified`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/opportunities/lastmodified'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/opportunities/lastmodified'
)

print(response.json())
```

#### Response Examples

**Get Opportunity Change Logs** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Transfer-Encoding`: `chunked`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "opportunityId": "3X4R7W4WYW",
      "opportunityName": "CIDER, APPLE",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/15/2021 4:28:00 PM",
      "user": "Carlos Banuelos",
      "detail": "Quote -> Measure"
    },
    {
      "opportunityId": "O3RP9Z0XO6",
      "opportunityName": "KELLY, TAURUS",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/15/2021 4:29:00 PM",
      "user": "Carlos Banuelos",
      "detail": "Won -> Quote"
    },
    {
      "opportunityId": "O3RP9Z0XO6",
      "opportunityName": "KELLY, TAURUS",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/15/2021 4:29:00 PM",
      "user": "Carlos Banuelos",
      "detail": "Quote -> Measure"
    },
    {
      "opportunityId": "LFWQD7C9I3",
      "opportunityName": "JENKINS, LEROY",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/15/2021 4:30:00 PM",
      "user": "Carlos Banuelos",
      "detail": "Won -> Quote"
    },
    {
      "opportunityId": "LFWQD7C9I3",
      "opportunityName": "JENKINS, LEROY",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/15/2021 4:30:00 PM",
      "user": "Carlos Banuelos",
      "detail": "Quote -> Measure"
    },
    {
      "opportunityId": "MVBY3Y7DTT",
      "opportunityName": "WILSON, SHANE",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/16/2021 4:37:00 PM",
      "user": "Carlos Banuelos",
      "detail": "To Do -> Measure"
    },
    {
      "opportunityId": "63DLK8ZCZQ",
      "opportunityName": "SHIPTO, TESTING",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/16/2021 4:43:00 PM",
      "user": "Carlos Banuelos",
      "detail": "To Do -> Measure"
    },
    {
      "opportunityId": "IY5EKWW05D",
      "opportunityName": "MM-1617, STORY",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/16/2021 9:11:00 PM",
      "user": "lindsey",
      "detail": "Quote -> Won"
    },
    {
      "opportunityId": "7TVFEGMO1S",
      "opportunityName": "SERGEEV, ALYOSHA",
      "eventName": "OPPORTUNITY CREATED",
      "eventTime": "12/20/2021 7:34:00 PM",
      "user": "lindsey",
      "detail": "To Do"
    },
    {
      "opportunityId": "7TVFEGMO1S",
      "opportunityName": "SERGEEV, ALYOSHA",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/20/2021 8:06:00 PM",
      "user": "lindsey",
      "detail": "To Do -> Contact"
    },
    {
      "opportunityId": "7TVFEGMO1S",
      "opportunityName": "SERGEEV, ALYOSHA",
      "eventName": "STAGE CHANGED",
      "eventTime": "12/20/2021 8:07:00 PM",
      "user": "lindsey",
      "detail": "Contact -> Products"
    }
  ],
  "detail": null
}
```

---

### Get Opportunity

**GET** `https://api.rfms.online/v2/opportunity/:id`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/opportunity/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/opportunity/:id'
)

print(response.json())
```

#### Response Examples

**Get Opportunity** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": {
    "id": "NNUZ1RHDJE",
    "title": "TRUBISKY, MITCH",
    "customerId": "75685",
    "salesperson": "carlos2@branch.com",
    "store": 32,
    "dateCreated": "3/22/2021",
    "lastModified": "7/2/2021 12:37 PM",
    "totalValue": 374.84,
    "stage": "Quote",
    "quotes": [
      "ES103494"
    ],
    "quoteApproval": "ES103494",
    "orders": [],
    "products": [
      {
        "id": 918196,
        "colorId": 6983585,
        "quantity": 300,
        "sampleCheckedOut": false,
        "price": 1.04
      }
    ]
  },
  "detail": null
}
```

---

## Order Entry

*51 endpoints*

### Get order values

**GET** `https://api.rfms.online/v2/order`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/order'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get order values** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `247`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "userOrderTypeId": [
    {
      "id": 1,
      "name": "APPROVED"
    },
    {
      "id": 3,
      "name": "IN REVIEW"
    },
    {
      "id": 2,
      "name": "REJECTED"
    }
  ],
  "serviceTypeId": [
    {
      "id": 1,
      "name": "CERTIFICATE "
    }
  ],
  "contractTypeId": [
    {
      "id": 1,
      "name": "CONTRACT SAMPLE"
    }
  ]
}
```

---

### Get Quote

**GET** `https://api.rfms.online/v2/quote/:number?locked=false&includeAttachments=true`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locked` | string | No | Lock the quote |
| `includeAttachments` | string | No | Returns attachments associated with the quote |

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/quote/:number?locked=false&includeAttachments=true'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/quote/:number?locked=false&includeAttachments=true',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Quote** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `2161`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": {
    "id": "35813",
    "number": "ES002971",
    "originalNumber": "ES002971",
    "category": "OriginalInvoice",
    "soldTo": {
      "customerId": 75515,
      "phone1": "000-000-0205",
      "phone2": "",
      "email": "TEST@TEST.COM",
      "customerType": "RETAIL-INSTALL",
      "businessName": null,
      "lastName": "BANUELOS",
      "firstName": "CARLOS",
      "address1": "123 TEST TUSCALOOSA AVE",
      "address2": "",
      "city": "TUSCALOOSA",
      "state": "AL",
      "postalCode": "35405",
      "county": "TUSCALOOSA"
    },
    "shipTo": {
      "businessName": null,
      "lastName": "BANUELOS",
      "firstName": "CARLOS",
      "address1": "123 TEST TUSCALOOSA AVE",
      "address2": "",
      "city": "TUSCALOOSA",
      "state": "AL",
      "postalCode": "35405",
      "county": "TUSCALOOSA"
    },
    "salesperson1": "KURT WILSON",
    "salesperson2": "",
    "salespersonSplitPercent": 1,
    "storeCode": " ",
    "storeNumber": 32,
    "jobNumber": "GRAIL",
    "poNumber": "",
    "privateNotes": "",
    "publicNotes": "",
    "workOrderNotes": "",
    "estimatedDeliveryDate": "2021-04-20",
    "enteredDate": "2020-10-01",
    "measureDate": "",
    "taxStatus": "Tax",
    "taxMethod": "SalesTax",
    "adSource": null,
    "userOrderTypeId": 0,
    "serviceTypeId": 0,
    "contractTypeId": 0,
    "totals": {
      "material": 144000,
      "labor": 0,
      "misc": 0,
      "total": 156960,
      "salesTax": 12960,
      "miscTax": 0,
      "grandTotal": 156960,
      "recycleFee": 0
    },
    "lines": [
      {
        "id": 217399,
        "lineNumber": 1,
        "productCode": "01",
        "rollItemNumber": "",
        "styleName": "AIMCO LIVING - 12'",
        "colorName": "AMERICANA",
        "supplierName": "MOHAWK INDUSTRIES",
        "quantity": 11999.9997,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 12,
        "total": 144000,
        "isUseTaxLine": false,
        "notes": "",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": "None",
        "inTransit": false,
        "promiseDate": "",
        "attachments": [],
        "workOrderLines": [
          {
            "lineNumber": 1,
            "areaName": "TEST2 FOR API2",
            "quantity": 11999.9997,
            "rate": 0,
            "notes": ""
          }
        ]
      }
    ],
    "attachments": [],
    "storeSpecific": null,
    "isExportedToOrder": false,
    "quoteDate": "2020-10-01",
    "orderNumber": "CG100223",
    "orderDate": "2020-10-01",
    "deliveryDate": "",
    "dueDate": "",
    "closedDate": "",
    "billedDate": "",
    "completedDate": "",
    "billingGroup": null,
    "payment": {
      "paidDate": "",
      "paidAmount": 0,
      "balanceDue": 156960
    }
  },
  "detail": {
    "id": "35813",
    "documentNumber": "ES002971",
    "category": "OriginalInvoice",
    "originalDocumentNumber": "ES002971",
    "isWebOrder": false,
    "documentType": 0,
    "customer": {
      "customerSource": "Customer",
      "customerSourceId": 75515,
      "salesLeadId": 0,
      "customerName": "BANUELOS",
      "customerFirstName": "CARLOS",
      "actualCustomerFirstName": null,
      "customerLastName": null,
      "customerBusinessName": null,
      "customerAddress": "123 TEST TUSCALOOSA AVE",
      "customerAddress2": "",
      "customerCity": "TUSCALOOSA",
      "customerState": "AL",
      "customerZIP": "35405",
      "customerPhone": "000-000-0205",
      "customerPhone2": "",
      "customerPhone3": null,
      "customerEmail": "TEST@TEST.COM",
      "customerCounty": "TUSCALOOSA",
      "shipToName": "BANUELOS",
      "shipToFirstName": "CARLOS",
      "shipToLastName": null,
      "shipToBusinessName": null,
      "actualShipToFirstName": null,
      "shipToAddress": "123 TEST TUSCALOOSA AVE",
      "shipToAddress2": "",
      "shipToCity": "TUSCALOOSA",
      "shipToState": "AL",
      "shipToZIP": "35405",
      "shipToCounty": "TUSCALOOSA",
      "customerType": "RETAIL-INSTALL",
      "referralType": null,
      "referralMemberId": 0,
      "referralMemberName": null,
      "taxStatus": "Tax",
      "taxMethod": "SalesTax",
      "preferredPriceLevel": 0,
      "preferredSalesperson1": null,
      "preferredSalesperson2": null,
      "jobNumberOverride": null,
      "entryType": null,
      "terms": null,
      "termDays": 0,
      "creditLimit": 0,
      "defaultStore": 0,
      "internalNotes": null,
      "remarks": null
    },
    "salesperson": "KURT WILSON",
    "salesperson2": "",
    "salespersonCommissionSplitPercent": 1,
    "billingGroup": null,
    "measureDate": null,
    "estimatedDeliveryDate": "2021-04-20T00:00:00",
    "orderDate": "2020-10-01T00:00:00",
    "dueDate": null,
    "paidDate": null,
    "enteredDate": "2020-10-01T00:00:00",
    "deliveryDate": null,
    "closedDate": null,
    "billedDate": null,
    "completedDate": null,
    "poNumber": "",
    "storeNumber": 32,
    "storeDisplayCode": " ",
    "isOccupied": false,
    "timeSlot": 0,
    "privateNotes": "",
    "publicNotes": "",
    "workOrderNotes": "",
    "adSource": 0,
    "jobNumber": "GRAIL",
    "modelName": null,
    "userOrderType": 0,
    "serviceType": 0,
    "contractType": 0,
    "totalTax": 12960,
    "state": {
      "documentId": 35813,
      "documentNumber": "ES002971",
      "documentType": 0,
      "originalDocumentNumber": "ES002971",
      "isExported": false,
      "isVoided": false,
      "salesTax": 12960,
      "grandTotal": 156960,
      "materialTotal": 144000,
      "laborTotal": 0,
      "miscCharges": 0,
      "invoiceTotal": 156960,
      "miscTax": 0,
      "recycleFee": 0,
      "totalPaid": 0,
      "balanceDue": 156960
    },
    "proSource": {
      "memberNumber": 0,
      "memberName": "",
      "businessName": ""
    },
    "lines": [
      {
        "lineId": 217399,
        "lineAction": null,
        "lineStatus": "None",
        "inTransit": false,
        "productCode": "01",
        "tabKey": null,
        "calcMethod": null,
        "saleUnits": "SF",
        "rollItemNumber": "",
        "styleSeqNumber": 1020356,
        "styleName": "AIMCO LIVING - 12'",
        "styleNumber": "",
        "colorSeqNumber": 8211669,
        "colorName": "AMERICANA",
        "colorCode": null,
        "quantity": 11999.9997,
        "orderLength": 1000,
        "rollWidth": 12,
        "rollWidthInInches": 0,
        "lineNotes": "",
        "internalNotes": "",
        "unitPrice": 12,
        "lineNumber": 1,
        "lineTotal": 144000,
        "fixedTotal": false,
        "load": 0,
        "freight": 0,
        "salesTax": 0,
        "priceLevelNumber": 0,
        "inventorySeqNum": 0,
        "sampleTaken": false,
        "supplierName": "MOHAWK INDUSTRIES",
        "unitCost": 0,
        "useTaxLine": false,
        "componentsAreRoll": false,
        "subtype": null,
        "calcMatchType": null,
        "calcMatchTab": null,
        "lineGroupId": 0,
        "profitPercent": 144000,
        "areaName": null,
        "specialPOCostRef": null,
        "specialPOCost": 0,
        "specialPOCostComment": "",
        "promiseDate": null,
        "deliveryDate": "2021-04-20T00:00:00",
        "hide": false,
        "components": [
          {
            "lineNumber": 1,
            "name": "TEST2 FOR API2",
            "quantity": 11999.9997,
            "rate": 0,
            "lengthInInches": 0,
            "notes": ""
          }
        ],
        "attachedFiles": []
      }
    ],
    "attachedFiles": [],
    "lockInfo": null,
    "companyId": null
  }
}
```

---

### Create Quote

**POST** `https://api.rfms.online/v2/quote/create`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |
| `token` | `` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poNumber` | string | Yes | Example: `987654` |
| `adSource` | string | Yes | Example: `BILLBOARD` |
| `quoteDate` | string | Yes | Example: `2019-07-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2019-08-01` |
| `jobNumber` | string | Yes | Example: `ABC123` |
| `soldTo` | object | Yes |  |
| `soldTo.lastName` | string | Yes | Example: `DOE` |
| `soldTo.firstName` | string | Yes | Example: `JOHN` |
| `soldTo.address1` | string | Yes | Example: `1234 MAIN ST` |
| `soldTo.address2` | string | Yes | Example: `STE 33` |
| `soldTo.city` | string | Yes | Example: `ANYTOWN` |
| `soldTo.state` | string | Yes | Example: `CA` |
| `soldTo.postalCode` | string | Yes | Example: `91332` |
| `soldTo.county` | string | Yes | Example: `LOS ANGELES` |
| `storeNumber` | integer | Yes | Example: `50` |
| `privateNotes` | string | Yes | Example: `PRIVATE` |
| `publicNotes` | string | Yes | Example: `PUBLIC` |
| `workOrderNotes` | string | Yes | Example: `WORK ORDER NOTES` |
| `salesperson1` | string | Yes | Example: `JOHN` |
| `salesperson2` | string | Yes | Example: `FRANK` |

**Example:**

```json
{
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 1,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 2,
    "isOccupied": false,
    "phase": "1",
    "model": "The Dystopian",
    "unit": "101",    
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3",
            "lineGroupId": 14
    	}
	]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 1,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 2,
    "isOccupied": false,
    "phase": "1",
    "model": "The Dystopian",
    "unit": "101",    
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3",
            "lineGroupId": 14
    	}
	]
}' 'https://api.rfms.online/v2/quote/create'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/quote/create',
    headers={
    "Content-Type": "application/json"
},
    json={
        "poNumber": "987654",
        "adSource": "BILLBOARD",
        "quoteDate": "2019-07-01",
        "estimatedDeliveryDate": "2019-08-01",
        "jobNumber": "ABC123",
        "soldTo": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "storeNumber": 50,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "workOrderNotes": "WORK ORDER NOTES",
        "salesperson1": "JOHN",
        "salesperson2": "FRANK",
        "userOrderTypeId": 1,
        "serviceTypeId": 1,
        "contractTypeId": 1,
        "timeSlot": 2,
        "isOccupied": false,
        "phase": "1",
        "model": "The Dystopian",
        "unit": "101",
        "lines": [
                {
                        "productId": 992048,
                        "colorId": 7814430,
                        "quantity": 12.0,
                        "priceLevel": "Price3",
                        "lineGroupId": 14
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Create Quote using referenced line** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "ES903428",
  "detail": null
}
```

**Create Quote using unreferenced line** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "ES903428",
  "detail": null
}
```

**Create Quote With Work Order Lines** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `182`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "ES103603",
  "detail": {
    "docId": "37433"
  }
}
```

---

### Update Quote

**POST** `https://api.rfms.online/v2/quote`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `CG903368` |
| `poNumber` | string | Yes | Example: `987654` |
| `adSource` | string | Yes | Example: `BILLBOARD` |
| `quoteDate` | string | Yes | Example: `2019-07-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2019-08-01` |
| `jobNumber` | string | Yes | Example: `ABC123` |
| `soldTo` | object | Yes |  |
| `soldTo.customerType` | string | Yes | Example: `DECORATOR` |
| `storeNumber` | integer | Yes | Example: `50` |
| `privateNotes` | string | Yes | Example: `PRIVATE` |
| `publicNotes` | string | Yes | Example: `PUBLIC` |
| `workOrderNotes` | string | Yes | Example: `WORK ORDER NOTES` |
| `salesperson1` | string | Yes | Example: `JOHN` |
| `salesperson2` | string | Yes | Example: `FRANK` |
| `userOrderTypeId` | integer | Yes | Example: `2` |
| `serviceTypeId` | integer | Yes | Example: `1` |
| `contractTypeId` | integer | Yes | Example: `1` |
| `timeSlot` | integer | Yes | Example: `2` |
| `isOccupied` | boolean | Yes |  |
| `phase` | string | Yes | Example: `2` |

**Example:**

```json
{
    "number": "CG903368",
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { "customerType": "DECORATOR" },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 2,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 2,
    "isOccupied": false,
    "phase": "2",
    "model": "The Dystopian",
    "unit": "101"   
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "number": "CG903368",
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { "customerType": "DECORATOR" },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 2,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 2,
    "isOccupied": false,
    "phase": "2",
    "model": "The Dystopian",
    "unit": "101"   
}' 'https://api.rfms.online/v2/quote'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/quote',
    headers={
    "Content-Type": "application/json"
},
    json={
        "number": "CG903368",
        "poNumber": "987654",
        "adSource": "BILLBOARD",
        "quoteDate": "2019-07-01",
        "estimatedDeliveryDate": "2019-08-01",
        "jobNumber": "ABC123",
        "soldTo": {
                "customerType": "DECORATOR"
        },
        "storeNumber": 50,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "workOrderNotes": "WORK ORDER NOTES",
        "salesperson1": "JOHN",
        "salesperson2": "FRANK",
        "userOrderTypeId": 2,
        "serviceTypeId": 1,
        "contractTypeId": 1,
        "timeSlot": 2,
        "isOccupied": false,
        "phase": "2",
        "model": "The Dystopian",
        "unit": "101"
}
)

print(response.json())
```

---

### Find Quotes

**POST** `https://api.rfms.online/v2/quote/find`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `Smith` |
| `dateCreatedFrom` | string | Yes | Example: `1/1/2018` |
| `salesperson1` | string | Yes | Example: `Kurt Wilson` |
| `pageResultNumber` | integer | Yes | Example: `3` |

**Example:**

```json
{
	"searchText": "Smith",
	"dateCreatedFrom": "1/1/2018",
	"salesperson1": "Kurt Wilson",
	"pageResultNumber": 3
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
	"searchText": "Smith",
	"dateCreatedFrom": "1/1/2018",
	"salesperson1": "Kurt Wilson",
	"pageResultNumber": 3
}' 'https://api.rfms.online/v2/quote/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/quote/find',
    headers={
    "Content-Type": "application/json"
},
    json={
        "searchText": "Smith",
        "dateCreatedFrom": "1/1/2018",
        "salesperson1": "Kurt Wilson",
        "pageResultNumber": 3
}
)

print(response.json())
```

#### Response Examples

**Find Quotes** ( - 0)

```json
{
  "status": "success",
  "result": [
    {
      "documentNumber": "ES903247",
      "customerFirst": "JIM",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2019-09-04T00:00:00",
      "grandTotal": 12.6,
      "status": "Exported"
    },
    {
      "documentNumber": "ES803033",
      "customerFirst": "JIM",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2018-06-26T00:00:00",
      "grandTotal": 6433.47,
      "status": "Exported"
    }
  ],
  "detail": [
    {
      "documentNumber": "ES903247",
      "documentType": 0,
      "description": "",
      "customerFirst": "JIM",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2019-09-04T00:00:00",
      "grandTotal": 12.6,
      "status": "Exported"
    },
    {
      "documentNumber": "ES803033",
      "documentType": 0,
      "description": "",
      "customerFirst": "JIM",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2018-06-26T00:00:00",
      "grandTotal": 6433.47,
      "status": "Exported"
    }
  ]
}
```

**Find Quotes - View Additional Pages** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `796`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "documentNumber": "ES903145",
      "customerFirst": "TOMMY",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2019-06-11T00:00:00",
      "grandTotal": 8863.64,
      "status": "Open"
    },
    {
      "documentNumber": "ES903030",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-27T00:00:00",
      "grandTotal": 4877.04,
      "status": "Open"
    },
    {
      "documentNumber": "ES902963",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-15T00:00:00",
      "grandTotal": 0.0,
      "status": "Open"
    },
    {
      "documentNumber": "ES902953",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 1021.95,
      "status": "Open"
    },
    {
      "documentNumber": "ES902954",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.55,
      "status": "Open"
    },
    {
      "documentNumber": "ES902956",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.56,
      "status": "Open"
    },
    {
      "documentNumber": "ES902957",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.56,
      "status": "Open"
    },
    {
      "documentNumber": "ES902907",
      "customerFirst": "JOHNNY",
      "customerLast": "SMITH",
      "customerType": "CASH & CARRY",
      "createdDate": "2019-02-22T00:00:00",
      "grandTotal": 0.0,
      "status": "Open"
    },
    {
      "documentNumber": "ES902852",
      "customerFirst": "",
      "customerLast": "SMITH & SMITH CONST.",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-01-23T00:00:00",
      "grandTotal": 906.51,
      "status": "Open"
    },
    {
      "documentNumber": "ES902839",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-01-16T00:00:00",
      "grandTotal": 19305.39,
      "status": "Open"
    }
  ],
  "detail": [
    {
      "documentNumber": "ES903145",
      "documentType": 0,
      "description": "",
      "customerFirst": "TOMMY",
      "customerLast": "BUILDER",
      "customerType": "BUILDER",
      "createdDate": "2019-06-11T00:00:00",
      "grandTotal": 8863.64,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES903030",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-27T00:00:00",
      "grandTotal": 4877.04,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902963",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-15T00:00:00",
      "grandTotal": 0.0,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902953",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 1021.95,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902954",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.55,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902956",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.56,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902957",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-03-08T00:00:00",
      "grandTotal": 257.56,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902907",
      "documentType": 0,
      "description": "",
      "customerFirst": "JOHNNY",
      "customerLast": "SMITH",
      "customerType": "CASH & CARRY",
      "createdDate": "2019-02-22T00:00:00",
      "grandTotal": 0.0,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902852",
      "documentType": 0,
      "description": "",
      "customerFirst": "",
      "customerLast": "SMITH & SMITH CONST.",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-01-23T00:00:00",
      "grandTotal": 906.51,
      "status": "Open",
      "isTemplate": false
    },
    {
      "documentNumber": "ES902839",
      "documentType": 0,
      "description": "",
      "customerFirst": "DANNY",
      "customerLast": "SMITH CONSTRUCTION",
      "customerType": "NEW RESIDENTIAL",
      "createdDate": "2019-01-16T00:00:00",
      "grandTotal": 19305.39,
      "status": "Open",
      "isTemplate": false
    }
  ]
}
```

---

### Get Quote Gross Profit

**GET** `https://api.rfms.online/v2/quote/grossprofit/ES803033`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/quote/grossprofit/ES803033'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/quote/grossprofit/ES803033'
)

print(response.json())
```

#### Response Examples

**Get Quote Gross Profit** ( - 0)

*Response Headers:*

- `Content-Length`: `103`
- `Content-Type`: `text/html`
- `Server`: `Microsoft-IIS/10.0`
- `X-Powered-By`: `ASP.NET`
- `Date`: `Thu, 18 Jun 2020 00:31:34 GMT`

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "InvoiceNumber": "ES803033",
    "GrossProfitPercent": 67.98,
    "GrossProfit": 3975.87,
    "TotalTransaction": 6433.47,
    "NetSales": 5848.61,
    "MaterialGrossCost": 1658.64,
    "LaborCost": 0.0,
    "FreightCost": 29.81,
    "Load": 0.0,
    "MiscOverheadCost": 184.29,
    "MiscExtraCost": 0.0,
    "TaxCost": 584.86,
    "ReferralTotal": 0.0
  }
}
```

---

### Export Quote to Order

**POST** `https://api.rfms.online/v2/quote/ES903214/export`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' 'https://api.rfms.online/v2/quote/ES903214/export'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/quote/ES903214/export',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Export Quote to Order** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `169`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": "CG903534"
}
```

---

### Get Order

**GET** `https://api.rfms.online/v2/order/:number?locked=false&includeAttachments=true`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `locked` | string | No | Lock the order |
| `includeAttachments` | string | No | Returns attachments associated with the order |

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/order/:number?locked=false&includeAttachments=true'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order/:number?locked=false&includeAttachments=true',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Order** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `1302`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": {
    "id": "83307",
    "number": "CG003659",
    "originalNumber": "",
    "category": "OriginalInvoice",
    "soldTo": {
      "customerId": 75515,
      "phone1": "205-555-5555",
      "phone2": "",
      "email": "TEST@TEST.COM",
      "customerType": "RETAIL-INSTALL",
      "businessName": null,
      "lastName": "BANUELOS",
      "firstName": "CARLOS",
      "address1": "555 TUSCALOOSA AVE",
      "address2": "",
      "city": "TUSCALOOSA",
      "state": "AL",
      "postalCode": "35405",
      "county": "TUSCALOOSA"
    },
    "shipTo": {
      "businessName": null,
      "lastName": "BANUELOS",
      "firstName": "CARLOS",
      "address1": "555 TUSCALOOSA AVE",
      "address2": "",
      "city": "TUSCALOOSA",
      "state": "AL",
      "postalCode": "35405",
      "county": "TUSCALOOSA"
    },
    "salesperson1": "CARLOS BANUELOS",
    "salesperson2": "",
    "salespersonSplitPercent": 1,
    "storeCode": " ",
    "storeNumber": 32,
    "jobNumber": "",
    "poNumber": "",
    "privateNotes": "",
    "publicNotes": "",
    "workOrderNotes": "",
    "estimatedDeliveryDate": "2020-10-13",
    "enteredDate": "2020-09-16",
    "measureDate": "",
    "taxStatus": "Tax",
    "taxMethod": "SalesTax",
    "adSource": null,
    "userOrderTypeId": 1,
    "serviceTypeId": 0,
    "contractTypeId": 1,
    "totals": {
      "material": 73740,
      "labor": 0,
      "misc": 0,
      "total": 80376.6,
      "salesTax": 6636.6,
      "miscTax": 0,
      "grandTotal": 80376.6,
      "recycleFee": 0
    },
    "lines": [
      {
        "id": 201045,
        "lineNumber": 1,
        "productCode": "01",
        "rollItemNumber": "TEST3.5",
        "styleName": "AMERICANA - 12'",
        "colorName": "ADIRONDACK",
        "supplierName": "MASLAND",
        "quantity": 240.0003,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 12.29,
        "total": 2949.6,
        "isUseTaxLine": false,
        "notes": "",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": "Reserved",
        "inTransit": false,
        "promiseDate": "",
        "attachments": [],
        "workOrderLines": [
          {
            "lineNumber": 1,
            "areaName": "",
            "quantity": 240.0003,
            "rate": 0.3889,
            "notes": ""
          }
        ]
      },
      {
        "id": 201046,
        "lineNumber": 2,
        "productCode": "01",
        "rollItemNumber": "CG0036590002",
        "styleName": "AMERICANA - 12'",
        "colorName": "ADOBE",
        "supplierName": "MASLAND",
        "quantity": 2999.9997,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 12.29,
        "total": 36870,
        "isUseTaxLine": false,
        "notes": "",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": "Reserved",
        "inTransit": false,
        "promiseDate": "",
        "attachments": [
          {
            "id": 14655,
            "description": "file.pdf",
            "fileExtension": "pdf"
          }
        ],
        "workOrderLines": [
          {
            "lineNumber": 2,
            "areaName": "",
            "quantity": 2999.9997,
            "rate": 0.3889,
            "notes": ""
          }
        ]
      },
      {
        "id": 201123,
        "lineNumber": 3,
        "productCode": "01",
        "rollItemNumber": "TEST1.98",
        "styleName": "AMERICANA - 12'",
        "colorName": "ADIRONDACK",
        "supplierName": "MASLAND",
        "quantity": 2760.0003,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 12.29,
        "total": 33920.4,
        "isUseTaxLine": false,
        "notes": "",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": "Reserved",
        "inTransit": false,
        "promiseDate": "",
        "attachments": [],
        "workOrderLines": [
          {
            "lineNumber": 3,
            "areaName": "TEST AREA FOR API",
            "quantity": 2760.0003,
            "rate": 3.4989,
            "notes": ""
          }
        ]
      }
    ],
    "attachments": [],
    "storeSpecific": null,
    "isExportedToOrder": false,
    "quoteDate": "2020-09-16",
    "orderNumber": "",
    "orderDate": "2020-09-16",
    "deliveryDate": "",
    "dueDate": "",
    "closedDate": "",
    "billedDate": "",
    "completedDate": "",
    "billingGroup": null,
    "payment": {
      "paidDate": "",
      "paidAmount": 0,
      "balanceDue": 80376.6
    }
  },
  "detail": null
}
```

---

### Create Order

**POST** `https://api.rfms.online/v2/order/create`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |
| `token` | `` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poNumber` | string | Yes | Example: `987655` |
| `adSource` | string | Yes | Example: `BILLBOARD` |
| `quoteDate` | string | Yes | Example: `2021-04-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2021-05-04` |
| `jobNumber` | string | Yes | Example: `XYZ123` |
| `soldTo` | object | Yes |  |
| `soldTo.lastName` | string | Yes | Example: `DOE` |
| `soldTo.firstName` | string | Yes | Example: `JOHN` |
| `soldTo.address1` | string | Yes | Example: `1234 MAIN ST` |
| `soldTo.address2` | string | Yes | Example: `STE 33` |
| `soldTo.city` | string | Yes | Example: `ANYTOWN` |
| `soldTo.state` | string | Yes | Example: `CA` |
| `soldTo.postalCode` | string | Yes | Example: `91332` |
| `soldTo.county` | string | Yes | Example: `LOS ANGELES` |
| `storeNumber` | integer | Yes | Example: `50` |
| `privateNotes` | string | Yes | Example: `PRIVATE` |
| `publicNotes` | string | Yes | Example: `PUBLIC` |
| `workOrderNotes` | string | Yes | Example: `WORK ORDER NOTES` |
| `salesperson1` | string | Yes | Example: `JOHN` |
| `salesperson2` | string | Yes | Example: `FRANK` |

**Example:**

```json
{
    "poNumber": "987655",
    "adSource": "BILLBOARD",
    "quoteDate": "2021-04-01",
    "estimatedDeliveryDate": "2021-05-04",
    "jobNumber": "XYZ123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 3,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 4,
    "isOccupied": false,
    "phase": "1",
    "model": "The Base Model",
    "unit": "60",
    "tract": "Tract A",
    "block": "Block A",
    "lot": "Lot A",
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3",
            "lineGroupId": 14
    	}
	]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "poNumber": "987655",
    "adSource": "BILLBOARD",
    "quoteDate": "2021-04-01",
    "estimatedDeliveryDate": "2021-05-04",
    "jobNumber": "XYZ123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 3,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 4,
    "isOccupied": false,
    "phase": "1",
    "model": "The Base Model",
    "unit": "60",
    "tract": "Tract A",
    "block": "Block A",
    "lot": "Lot A",
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3",
            "lineGroupId": 14
    	}
	]
}' 'https://api.rfms.online/v2/order/create'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/create',
    headers={
    "Content-Type": "application/json"
},
    json={
        "poNumber": "987655",
        "adSource": "BILLBOARD",
        "quoteDate": "2021-04-01",
        "estimatedDeliveryDate": "2021-05-04",
        "jobNumber": "XYZ123",
        "soldTo": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "storeNumber": 50,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "workOrderNotes": "WORK ORDER NOTES",
        "salesperson1": "JOHN",
        "salesperson2": "FRANK",
        "userOrderTypeId": 3,
        "serviceTypeId": 1,
        "contractTypeId": 1,
        "timeSlot": 4,
        "isOccupied": false,
        "phase": "1",
        "model": "The Base Model",
        "unit": "60",
        "tract": "Tract A",
        "block": "Block A",
        "lot": "Lot A",
        "lines": [
                {
                        "productId": 992048,
                        "colorId": 7814430,
                        "quantity": 12.0,
                        "priceLevel": "Price3",
                        "lineGroupId": 14
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Create Quote using referenced line** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "ES903428",
  "detail": null
}
```

**Create Quote using unreferenced line** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "ES903428",
  "detail": null
}
```

**Create a Non-Web Order Using Category Field** ( - 0)

**Create Order and Set Order Values** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `182`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "CG105041",
  "detail": {
    "docId": "83692"
  }
}
```

---

### Update Order

**POST** `https://api.rfms.online/v2/order`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `CG903368` |
| `poNumber` | string | Yes | Example: `987654` |
| `adSource` | string | Yes | Example: `BILLBOARD` |
| `orderDate` | string | Yes | Example: `2019-07-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2019-08-01` |
| `jobNumber` | string | Yes | Example: `ABC123` |
| `soldTo` | object | Yes |  |
| `soldTo.customerType` | string | Yes | Example: `DECORATOR` |
| `storeNumber` | integer | Yes | Example: `50` |
| `privateNotes` | string | Yes | Example: `PRIVATE` |
| `publicNotes` | string | Yes | Example: `PUBLIC` |
| `workOrderNotes` | string | Yes | Example: `WORK ORDER NOTES` |
| `salesperson1` | string | Yes | Example: `JOHN` |
| `salesperson2` | string | Yes | Example: `FRANK` |
| `userOrderTypeId` | integer | Yes | Example: `2` |
| `serviceTypeId` | integer | Yes | Example: `1` |
| `contractTypeId` | integer | Yes | Example: `1` |
| `timeSlot` | integer | Yes | Example: `3` |
| `isOccupied` | boolean | Yes |  |
| `phase` | string | Yes | Example: `1` |

**Example:**

```json
{
    "number": "CG903368",
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "orderDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { "customerType": "DECORATOR" },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 2,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 3,
    "isOccupied": false,
    "phase": "1",
    "model": "The Base Model",
    "unit": "50",
    "tract": "Tract A",
    "block": "Block A",
    "lot": "Lot A"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "number": "CG903368",
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "orderDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { "customerType": "DECORATOR" },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "userOrderTypeId": 2,
    "serviceTypeId": 1,
    "contractTypeId": 1,
    "timeSlot": 3,
    "isOccupied": false,
    "phase": "1",
    "model": "The Base Model",
    "unit": "50",
    "tract": "Tract A",
    "block": "Block A",
    "lot": "Lot A"
}' 'https://api.rfms.online/v2/order'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order',
    headers={
    "Content-Type": "application/json"
},
    json={
        "number": "CG903368",
        "poNumber": "987654",
        "adSource": "BILLBOARD",
        "orderDate": "2019-07-01",
        "estimatedDeliveryDate": "2019-08-01",
        "jobNumber": "ABC123",
        "soldTo": {
                "customerType": "DECORATOR"
        },
        "storeNumber": 50,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "workOrderNotes": "WORK ORDER NOTES",
        "salesperson1": "JOHN",
        "salesperson2": "FRANK",
        "userOrderTypeId": 2,
        "serviceTypeId": 1,
        "contractTypeId": 1,
        "timeSlot": 3,
        "isOccupied": false,
        "phase": "1",
        "model": "The Base Model",
        "unit": "50",
        "tract": "Tract A",
        "block": "Block A",
        "lot": "Lot A"
}
)

print(response.json())
```

---

### Add Notes to Order

**POST** `https://api.rfms.online/v2/order/notes`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `CG003804` |
| `publicNotes` | string | Yes | Example: `A public note` |
| `privateNotes` | string | Yes | Example: `Private note` |
| `lineNotes` | array | Yes |  |
| `lineNotes[0].id` | integer | Yes | Example: `201379` |
| `lineNotes[0].note` | string | Yes | Example: `new line note` |

**Example:**

```json
{
    "number": "CG003804",
    "publicNotes": "A public note",
    "privateNotes": "Private note",
    "lineNotes": [
        {
            "id": 201379,
            "note": "new line note"
        }
    ]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "number": "CG003804",
    "publicNotes": "A public note",
    "privateNotes": "Private note",
    "lineNotes": [
        {
            "id": 201379,
            "note": "new line note"
        }
    ]
}' 'https://api.rfms.online/v2/order/notes'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/notes',
    headers={
    "Content-Type": "application/json"
},
    json={
        "number": "CG003804",
        "publicNotes": "A public note",
        "privateNotes": "Private note",
        "lineNotes": [
                {
                        "id": 201379,
                        "note": "new line note"
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Add Notes to Order** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `162`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": null
}
```

---

### Switch Line Status None To GenPO

**POST** `https://api.rfms.online/v2/order/save/linestatus`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | string | Yes | Example: `CG903341` |
| `lineId` | integer | Yes | Example: `200380` |
| `setToGeneratePO` | boolean | Yes | Example: `True` |

**Example:**

```json
{
	"orderNumber": "CG903341",
	"lineId": 200380,
	"setToGeneratePO": true
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
	"orderNumber": "CG903341",
	"lineId": 200380,
	"setToGeneratePO": true
}' 'https://api.rfms.online/v2/order/save/linestatus'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/save/linestatus',
    json={
        "orderNumber": "CG903341",
        "lineId": 200380,
        "setToGeneratePO": true
}
)

print(response.json())
```

#### Response Examples

**Update Multiple Line Statuses** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `78`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "Status updated for lines: 203542 203543",
  "detail": null
}
```

**Update Single Line Status** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `78`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "Status updated for lines: 203544",
  "detail": null
}
```

---

### Find Orders

**POST** `https://api.rfms.online/v2/order/find`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `sol` |
| `dateCreatedFrom` | string | Yes | Example: `2024-08-01` |
| `dateCreatedTo` | string | Yes | Example: `2024-08-20` |
| `resultPageNumber` | integer | Yes | Example: `1` |
| `viewBilledOnly` | boolean | Yes | Example: `True` |

**Example:**

```json
{
    "searchText": "sol",
    "dateCreatedFrom": "2024-08-01",
    "dateCreatedTo": "2024-08-20",
    "resultPageNumber": 1,
    "viewBilledOnly": true
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "searchText": "sol",
    "dateCreatedFrom": "2024-08-01",
    "dateCreatedTo": "2024-08-20",
    "resultPageNumber": 1,
    "viewBilledOnly": true
}' 'https://api.rfms.online/v2/order/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/find',
    json={
        "searchText": "sol",
        "dateCreatedFrom": "2024-08-01",
        "dateCreatedTo": "2024-08-20",
        "resultPageNumber": 1,
        "viewBilledOnly": true
}
)

print(response.json())
```

#### Response Examples

**Find Orders** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `917`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "documentNumber": "CG402188",
      "customerFirst": "JACOB",
      "customerLast": "SOLANTO",
      "customerType": "ACCOMMODATIONS",
      "createdDate": "2024-08-19T00:00:00",
      "grandTotal": 35,
      "status": "Job Costed",
      "balanceDue": 35
    }
  ],
  "detail": [
    {
      "documentNumber": "CG402188",
      "databaseId": 84847,
      "documentType": 1,
      "description": "PO number: 12345",
      "customerFirst": "JACOB",
      "customerLast": "SOLANTO",
      "customerType": "ACCOMMODATIONS",
      "createdDate": "2024-08-19T00:00:00",
      "enteredDate": "2024-08-19T00:00:00",
      "deliveryDate": null,
      "grandTotal": 35,
      "status": "Job Costed",
      "isTemplate": false,
      "customerAddress1": "66 CRIMSON STREET",
      "customerAddress2": "",
      "customerCity": "1234",
      "customerState": "AL",
      "customerPostalCode": "35401",
      "customerCounty": "",
      "phone1": "000/000-1394",
      "email": "jakesolanto@gmail.com",
      "jobNumber": "",
      "poNumber": "12345",
      "salesperson1": "TIM HAN",
      "salesperson2": "",
      "storeId": 32,
      "balanceDue": 35,
      "billingGroupId": 0
    }
  ]
}
```

---

### Advanced Order Search

**POST** `https://api.rfms.online/v2/order/find/advanced`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `car` |
| `stores` | array | Yes |  |
| `estimatedDeliveryFrom` | string | Yes | Example: `2023-01-01` |

**Example:**

```json
{
    "searchText": "car",
    "stores": [32, 50],
    "estimatedDeliveryFrom": "2023-01-01"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "searchText": "car",
    "stores": [32, 50],
    "estimatedDeliveryFrom": "2023-01-01"
}' 'https://api.rfms.online/v2/order/find/advanced'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/find/advanced',
    json={
        "searchText": "car",
        "stores": [
                32,
                50
        ],
        "estimatedDeliveryFrom": "2023-01-01"
}
)

print(response.json())
```

#### Response Examples

**Advanced Order Search** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `2040`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "id": 84337,
      "documentNumber": "WO394853",
      "customer": {
        "customerId": 75515,
        "phone1": "2055555556",
        "phone2": "",
        "email": "TEST@TEST.COM",
        "customerType": "RETAIL-INSTALL",
        "businessName": null,
        "lastName": "BANUELOS, CARLOS",
        "firstName": null,
        "address1": "555 TUSCALOOSA AVE",
        "address2": "",
        "city": "TUSCALOOSA",
        "state": "AL",
        "postalCode": "35405",
        "county": "TUSCALOOSA"
      },
      "shipTo": {
        "businessName": null,
        "lastName": "BANUELOS, CARLOS",
        "firstName": null,
        "address1": "1201 6TH AVE. NW",
        "address2": "",
        "city": "ALABASER",
        "state": "AL",
        "postalCode": "35007",
        "county": "ALABASER"
      },
      "deliveryDate": "",
      "poNumber": "",
      "invoiceType": "OriginalInvoice",
      "jobNumber": "",
      "orderDate": "2022-07-08",
      "estimatedDeliveryDate": "2023-02-15",
      "dateEntered": "2022-07-08",
      "adSource": "",
      "orderType": "",
      "contractType": "",
      "serviceType": "",
      "balanceDue": 361.6,
      "orderTotal": 361.6,
      "grandTotal": 361.6,
      "measureDate": "",
      "salesperson1": "CARLOS BANUELOS",
      "salesperson2": "",
      "store": 32,
      "paid": 0,
      "invoiceDate": "",
      "occupied": false,
      "closedDate": "",
      "voided": false
    },
    {
      "id": 84509,
      "documentNumber": "PM1023",
      "customer": {
        "customerId": 75887,
        "phone1": "2052062071",
        "phone2": "2059056051",
        "email": "CBANUELOS@TEST.COM",
        "customerType": "INSTALLER",
        "businessName": null,
        "lastName": "BANUELOS, CARLOS",
        "firstName": null,
        "address1": "3073 PALISADES CT.",
        "address2": "",
        "city": "TUSCALOOSA",
        "state": "AL",
        "postalCode": "35405",
        "county": "TUSCALOOSA"
      },
      "shipTo": {
        "businessName": null,
        "lastName": "CARLOS, BANUELOS",
        "firstName": null,
        "address1": "3074 PALISADES CT.",
        "address2": "",
        "city": "TUSCALOOSA",
        "state": "AL",
        "postalCode": "35405",
        "county": "TUSCALOOSA"
      },
      "deliveryDate": "",
      "poNumber": "",
      "invoiceType": "OriginalInvoice",
      "jobNumber": "",
      "orderDate": "2023-02-08",
      "estimatedDeliveryDate": "2023-01-12",
      "dateEntered": "2023-02-08",
      "adSource": "",
      "orderType": "",
      "contractType": "",
      "serviceType": "",
      "balanceDue": 4409.6,
      "orderTotal": 4409.6,
      "grandTotal": 4409.6,
      "measureDate": "",
      "salesperson1": "CARLOS BANUELOS",
      "salesperson2": "",
      "store": 50,
      "paid": 0,
      "invoiceDate": "",
      "occupied": false,
      "closedDate": "",
      "voided": false
    }
  ],
  "detail": null
}
```

---

### Get Order Gross Profit

**GET** `https://api.rfms.online/v2/order/grossprofit/CG003607`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/order/grossprofit/CG003607'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order/grossprofit/CG003607'
)

print(response.json())
```

#### Response Examples

**Get Gross Profit** ( - 0)

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "InvoiceNumber": "CG003607",
    "GrossProfitPercent": -6.84,
    "GrossProfit": -0.24,
    "TotalTransaction": 3.86,
    "NetSales": 3.51,
    "MaterialGrossCost": 2.04,
    "LaborCost": 0,
    "FreightCost": 0.16,
    "Load": 1.49,
    "MiscOverheadCost": 0.06,
    "MiscExtraCost": 0,
    "TaxCost": 0.35,
    "ReferralTotal": 0
  }
}
```

---

### Get Payment Values

**GET** `https://api.rfms.online/v2/payments`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/payments'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/payments',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Payment Values** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `333`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "receiptAccounts": [
    {
      "id": 5,
      "name": "AMEX (MAIN BRANCH)",
      "creditCardPrefixes": [
        3
      ]
    },
    {
      "id": 4,
      "name": "DISCOVER (MAIN BRANCH)",
      "creditCardPrefixes": [
        6
      ]
    },
    {
      "id": 1,
      "name": "PRIMARY RECEIPT FILE (MAIN BRANCH)",
      "creditCardPrefixes": []
    }
  ]
}
```

---

### Record Payment

**POST** `https://api.rfms.online/v2/payment`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |
| `messageId` | `MESSAGE_ID` | Optional Http header that will allow for retrieval of a message not immediately processed by a store |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documentNumber` | string | Yes | Example: `CG903367` |
| `paymentMethod` | string | Yes | Example: `creditcard` |
| `paymentAmount` | number | Yes | Example: `10.0` |
| `approvalCode` | string | Yes | Example: `12345` |
| `receiptAccountId` | integer | Yes | Example: `2` |
| `paymentFee` | number | Yes | Example: `2.16` |
| `paymentReference` | string | Yes | Example: `ABA123` |

**Example:**

```json
{
	"documentNumber": "CG903367",
	"paymentMethod": "creditcard",
	"paymentAmount": 10.00,
	"approvalCode": "12345",
	"receiptAccountId": 2,
    "paymentFee": 2.16,
    "paymentReference": "ABA123"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -H 'messageId: MESSAGE_ID' -d '{
	"documentNumber": "CG903367",
	"paymentMethod": "creditcard",
	"paymentAmount": 10.00,
	"approvalCode": "12345",
	"receiptAccountId": 2,
    "paymentFee": 2.16,
    "paymentReference": "ABA123"
}' 'https://api.rfms.online/v2/payment'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/payment',
    headers={
    "Content-Type": "application/json",
    "messageId": "MESSAGE_ID"
},
    json={
        "documentNumber": "CG903367",
        "paymentMethod": "creditcard",
        "paymentAmount": 10.0,
        "approvalCode": "12345",
        "receiptAccountId": 2,
        "paymentFee": 2.16,
        "paymentReference": "ABA123"
}
)

print(response.json())
```

#### Response Examples

**Record Payment** (OK - 200)

*Response Headers:*

- `Content-Length`: `103`
- `Content-Type`: `text/html`
- `Server`: `Microsoft-IIS/10.0`
- `X-Powered-By`: `ASP.NET`
- `Date`: `Tue, 06 Aug 2019 21:18:55 GMT`

```json
{
  "status": "success",
  "result": {
    "InvoiceNumber": "CG903367",
    "Balance": 9637.73
  }
}
```

---

### Get Recently Jobcosted Orders

**GET** `https://api.rfms.online/v2/orders/jobcosted`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/orders/jobcosted'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/orders/jobcosted',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

---

### Find Purchase Orders

**POST** `https://api.rfms.online/v2/order/purchaseorder/find`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `CG105159` |
| `lineNumber` | integer | Yes | Example: `1` |

**Example:**

```json
{
    "number": "CG105159",
    "lineNumber": 1
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "number": "CG105159",
    "lineNumber": 1
}' 'https://api.rfms.online/v2/order/purchaseorder/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/purchaseorder/find',
    json={
        "number": "CG105159",
        "lineNumber": 1
}
)

print(response.json())
```

#### Response Examples

**Find Purchase Orders** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": {
    "purchaseOrderNumber": "CG1051590001",
    "referenceNumber": "123456789",
    "supplierName": "MOHAWK INDUSTRIES",
    "styleName": "TOWN CENTER II 30 - 12'",
    "colorName": "POWDER INDIGO",
    "manufacturerName": "ALADDIN",
    "amountOrdered": 1200,
    "amountReceived": 0,
    "amountRemaining": 1200,
    "units": "SF",
    "freightCarrier": "FEDEX FLOORS",
    "trackingNumber": "UA5E6D5E1FGD5E",
    "orderDate": "2021-08-19T00:00:00",
    "promiseDate": "2021-12-09T00:00:00",
    "requiredDate": "2021-12-10T00:00:00",
    "requestedShipDate": null,
    "status": "Open",
    "orderedBy": "CBANUELOS",
    "takenBy": "CARLOS",
    "comments": "NICE COMMENT"
  },
  "detail": null
}
```

---

### Calculate Taxes

**POST** `https://api.rfms.online/v2/calculatetaxes`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poNumber` | string | Yes | Example: `12345` |
| `adSource` | string | Yes | Example: `Website` |
| `jobNumber` | string | Yes | Example: `ZAGZIG5` |
| `quoteDate` | string | Yes | Example: `2020-12-02` |
| `estimatedDeliveryDate` | string | Yes | Example: `2020-12-29` |
| `soldTo` | object | Yes |  |
| `soldTo.lastName` | string | Yes | Example: `Rimsky-Korsakov` |
| `soldTo.firstName` | string | Yes | Example: `Nikolai` |
| `soldTo.address1` | string | Yes | Example: `1 Bumblebee Dr` |
| `soldTo.address2` | string | Yes | Example: `STE 5` |
| `soldTo.email` | string | Yes | Example: `nik@classicalcarpets.com` |
| `soldTo.city` | string | Yes | Example: `BESSEMER` |
| `soldTo.state` | string | Yes | Example: `AL` |
| `soldTo.postalCode` | string | Yes | Example: `35020` |
| `shipTo` | object | Yes |  |
| `shipTo.lastName` | string | Yes | Example: `Zolotoy` |
| `shipTo.firstName` | string | Yes | Example: `Vitaly` |
| `shipTo.address1` | string | Yes | Example: `14 Wide Rd` |
| `shipTo.city` | string | Yes | Example: `Alabaster` |
| `shipTo.state` | string | Yes | Example: `AL` |

**Example:**

```json
{
    "poNumber": "12345",
    "adSource": "Website",
    "jobNumber": "ZAGZIG5",
    "quoteDate": "2020-12-02",
    "estimatedDeliveryDate": "2020-12-29",
    "soldTo": {
        "lastName": "Rimsky-Korsakov",
        "firstName": "Nikolai",
        "address1": "1 Bumblebee Dr",
        "address2": "STE 5",
        "email": "nik@classicalcarpets.com",
        "city": "BESSEMER",
        "state": "AL",
        "postalCode": "35020"
    },
    "shipTo":
    {
        "lastName": "Zolotoy",
        "firstName": "Vitaly",
        "address1": "14 Wide Rd",
        "city": "Alabaster",
        "state": "AL",
        "postalCode": "35007"
    },
    "storeNumber": 50,
    "salesperson1": "Pyotr",
    "taxStatus": "Tax",
    "lines": [
        {
            "productCode": "01",
            "lineTotal": 4245.33,
            "useLineTax": false
        },
        {
            "productCode": "01",
            "lineTotal": 1123.45,
            "useLineTax": true
        },
        {
            "productCode": "81",
            "lineTotal": "4453.23",
            "useLineTax": true
        }
    ]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "poNumber": "12345",
    "adSource": "Website",
    "jobNumber": "ZAGZIG5",
    "quoteDate": "2020-12-02",
    "estimatedDeliveryDate": "2020-12-29",
    "soldTo": {
        "lastName": "Rimsky-Korsakov",
        "firstName": "Nikolai",
        "address1": "1 Bumblebee Dr",
        "address2": "STE 5",
        "email": "nik@classicalcarpets.com",
        "city": "BESSEMER",
        "state": "AL",
        "postalCode": "35020"
    },
    "shipTo":
    {
        "lastName": "Zolotoy",
        "firstName": "Vitaly",
        "address1": "14 Wide Rd",
        "city": "Alabaster",
        "state": "AL",
        "postalCode": "35007"
    },
    "storeNumber": 50,
    "salesperson1": "Pyotr",
    "taxStatus": "Tax",
    "lines": [
        {
            "productCode": "01",
            "lineTotal": 4245.33,
            "useLineTax": false
        },
        {
            "productCode": "01",
            "lineTotal": 1123.45,
            "useLineTax": true
        },
        {
            "productCode": "81",
            "lineTotal": "4453.23",
            "useLineTax": true
        }
    ]
}' 'https://api.rfms.online/v2/calculatetaxes'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/calculatetaxes',
    json={
        "poNumber": "12345",
        "adSource": "Website",
        "jobNumber": "ZAGZIG5",
        "quoteDate": "2020-12-02",
        "estimatedDeliveryDate": "2020-12-29",
        "soldTo": {
                "lastName": "Rimsky-Korsakov",
                "firstName": "Nikolai",
                "address1": "1 Bumblebee Dr",
                "address2": "STE 5",
                "email": "nik@classicalcarpets.com",
                "city": "BESSEMER",
                "state": "AL",
                "postalCode": "35020"
        },
        "shipTo": {
                "lastName": "Zolotoy",
                "firstName": "Vitaly",
                "address1": "14 Wide Rd",
                "city": "Alabaster",
                "state": "AL",
                "postalCode": "35007"
        },
        "storeNumber": 50,
        "salesperson1": "Pyotr",
        "taxStatus": "Tax",
        "lines": [
                {
                        "productCode": "01",
                        "lineTotal": 4245.33,
                        "useLineTax": false
                },
                {
                        "productCode": "01",
                        "lineTotal": 1123.45,
                        "useLineTax": true
                },
                {
                        "productCode": "81",
                        "lineTotal": "4453.23",
                        "useLineTax": true
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Calculate Taxes** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `195`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "SalesTax": 982.2,
    "MiscTax": 0,
    "UseTax": 0
  }
}
```

---

### List Payments

**GET** `https://api.rfms.online/v2/order/payments/:number`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/order/payments/:number'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order/payments/:number'
)

print(response.json())
```

#### Response Examples

**List Payments** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": [
    {
      "documentNumber": "CG105152",
      "paymentNumber": 132,
      "paymentMethod": "creditcard",
      "paymentAmount": 127.53,
      "approvalCode": null,
      "receiptAccountId": 7,
      "paymentReference": "Visa - 1443",
      "paymentDate": "2021-08-18",
      "orderDate": "2021-08-17",
      "beginningBalance": 127.53,
      "remainingBalance": 0,
      "discountAmount": 0,
      "discountAccountNumber": "405",
      "financingCharge": 0,
      "customerName": "JACK, WILSON",
      "storeNumber": 32,
      "notes": ""
    },
    {
      "documentNumber": "CG105152",
      "paymentNumber": 133,
      "paymentMethod": "creditcard",
      "paymentAmount": 0.01,
      "approvalCode": null,
      "receiptAccountId": 7,
      "paymentReference": "Mastercard - 8919",
      "paymentDate": "2021-08-19",
      "orderDate": "2021-08-17",
      "beginningBalance": 1438.8,
      "remainingBalance": 1438.79,
      "discountAmount": 0,
      "discountAccountNumber": "405",
      "financingCharge": 0,
      "customerName": "JACK, WILSON",
      "storeNumber": 32,
      "notes": ""
    },
    {
      "documentNumber": "CG105152",
      "paymentNumber": 134,
      "paymentMethod": "creditcard",
      "paymentAmount": 0.01,
      "approvalCode": null,
      "receiptAccountId": 7,
      "paymentReference": "Mastercard - 8919",
      "paymentDate": "2021-08-19",
      "orderDate": "2021-08-17",
      "beginningBalance": 1438.79,
      "remainingBalance": 1438.78,
      "discountAmount": 0,
      "discountAccountNumber": "405",
      "financingCharge": 0,
      "customerName": "JACK, WILSON",
      "storeNumber": 32,
      "notes": ""
    }
  ],
  "detail": null
}
```

---

### Get Attachment

**GET** `https://api.rfms.online/v2/attachment/:id`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/attachment/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/attachment/:id',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Attachment** ( - 0)

```json
{
  "status": "success",
  "result": "OK",
  "detail": "** BASE64 ENCODED DATA **"
}
```

---

### Add Attachment

**POST** `https://api.rfms.online/v2/attachment`

#### Code Examples

**cURL:**

```bash
curl -X POST 'https://api.rfms.online/v2/attachment'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/attachment'
)

print(response.json())
```

#### Response Examples

**Add Attachment To Document** ( - 0)

```json
{
  "documentNumber": "ES903371",
  "documentType": "Quote",
  "fileExtension": "jpg",
  "description": "Describe attachment contents here",
  "fileData": "Insert Base64 Encoded File here"
}
```

**Add Attachment To Product** ( - 0)

```json
{
  "productId": 1023581,
  "fileExtension": "jpg",
  "description": "Describe attachment contents here",
  "fileData": "Base64 encoded file data here"
}
```

---

### Get Paperless Document Types

**POST** `https://api.rfms.online/v2/attachment/paperless/doctype`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user` | string | Yes | Example: `admin` |
| `group` | string | Yes | Example: `HeaderPictures` |

**Example:**

```json
{
    "user": "admin",
    "group": "HeaderPictures"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "user": "admin",
    "group": "HeaderPictures"
}' 'https://api.rfms.online/v2/attachment/paperless/doctype'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/attachment/paperless/doctype',
    json={
        "user": "admin",
        "group": "HeaderPictures"
}
)

print(response.json())
```

#### Response Examples

**Get Paperless Document Types** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `170`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "id": 100001,
      "name": "Invoice"
    },
    {
      "id": 100005,
      "name": "Receiving Ticket"
    },
    {
      "id": 200004,
      "name": "Header Pictures Document"
    }
  ],
  "detail": null
}
```

---

### List Attachments

**POST** `https://api.rfms.online/v2/attachments`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `productId` | integer | Yes | Example: `123387` |
| `isService` | boolean | Yes | Example: `True` |

**Example:**

```json
{
    "productId": 123387,
    "isService": true
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "productId": 123387,
    "isService": true
}' 'https://api.rfms.online/v2/attachments'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/attachments',
    json={
        "productId": 123387,
        "isService": true
}
)

print(response.json())
```

#### Response Examples

**List Attachments - Service** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `7345`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "id": 18289,
      "path": "\\\\path\\to\\file\\Image123.png",
      "fileExtension": "png",
      "size": 9053,
      "description": "photo.png",
      "fileData": "base64 encoded file data"
    }
  ],
  "detail": null
}
```

---

### Delete Attachment

**DELETE** `https://api.rfms.online/v2/attachment/:id`

#### Code Examples

**cURL:**

```bash
curl -X DELETE 'https://api.rfms.online/v2/attachment/:id'
```

**Python:**

```python
import requests

response = requests.delete(
    'https://api.rfms.online/v2/attachment/:id'
)

print(response.json())
```

---

### Get Estimate

**GET** `https://api.rfms.online/v2/estimate/:number`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Code Examples

**cURL:**

```bash
curl -X GET -H 'Content-Type: application/json' 'https://api.rfms.online/v2/estimate/:number'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/estimate/:number',
    headers={
    "Content-Type": "application/json"
}
)

print(response.json())
```

#### Response Examples

**Get Estimate** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `1546`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": {
    "id": "4875",
    "number": "JE100250",
    "originalNumber": "",
    "category": "",
    "soldTo": {
      "customerId": 373,
      "phone1": "",
      "phone2": "",
      "email": "",
      "customerType": "CASH & CARRY",
      "businessName": null,
      "lastName": "",
      "firstName": "NANCY",
      "address1": "17557 GOLD FINCH DRIVE",
      "address2": "",
      "city": "BUHL",
      "state": "AL",
      "postalCode": "35446-",
      "county": ""
    },
    "shipTo": {
      "businessName": null,
      "lastName": "SMITH",
      "firstName": "NANCY",
      "address1": "17557 GOLD FINCH DRIVE",
      "address2": "",
      "city": "BUHL",
      "state": "AL",
      "postalCode": "35446-",
      "county": ""
    },
    "salesperson1": "ANDREW",
    "salesperson2": "",
    "salespersonSplitPercent": 0,
    "storeCode": null,
    "storeNumber": 32,
    "jobNumber": "",
    "poNumber": "",
    "privateNotes": "",
    "publicNotes": "",
    "workOrderNotes": "",
    "estimatedDeliveryDate": "2016-05-13",
    "enteredDate": "",
    "measureDate": "2016-05-13",
    "taxStatus": "Tax",
    "taxMethod": null,
    "adSource": null,
    "userOrderTypeId": 0,
    "serviceTypeId": 0,
    "contractTypeId": 0,
    "totals": {
      "material": 2547.36,
      "labor": 920.36,
      "misc": 0,
      "total": 3467.72,
      "salesTax": 0,
      "miscTax": 0,
      "grandTotal": 3467.72,
      "recycleFee": 0
    },
    "lines": [
      {
        "id": 14287,
        "lineNumber": 1,
        "productCode": "01",
        "rollItemNumber": null,
        "styleName": "CALL TO THE POST",
        "colorName": "BEFORE DARK",
        "supplierName": "RFMS",
        "quantity": 732,
        "saleUnits": "SF",
        "freight": 0.06,
        "unitPrice": 2.79,
        "total": 2042.28,
        "isUseTaxLine": false,
        "notes": "COMBINED AREAS:\rCUT GROUP 1 (MASTER BEDROOM,BED 3)  QTY: 358 SF\nCUT GROUP 2 (BED 2,MASTER BEDROOM,BED 3)  QTY: 374 SF",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": null,
        "inTransit": false,
        "promiseDate": "",
        "attachments": []
      },
      {
        "id": 14290,
        "lineNumber": 4,
        "productCode": "81",
        "rollItemNumber": null,
        "styleName": "HEALTHIER LIVING-(BASIC)",
        "colorName": "",
        "supplierName": "",
        "quantity": 732,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 0.72,
        "total": 527.04,
        "isUseTaxLine": false,
        "notes": "(SHEET-LEVEL)",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": null,
        "inTransit": false,
        "promiseDate": "",
        "attachments": []
      },
      {
        "id": 14291,
        "lineNumber": 5,
        "productCode": "84",
        "rollItemNumber": null,
        "styleName": "TAKEUP GLUED CPT",
        "colorName": "",
        "supplierName": "",
        "quantity": 627.74,
        "saleUnits": "SF",
        "freight": 0,
        "unitPrice": 0.3,
        "total": 188.32,
        "isUseTaxLine": false,
        "notes": "(SHEET-LEVEL)",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": null,
        "inTransit": false,
        "promiseDate": "",
        "attachments": []
      },
      {
        "id": 14288,
        "lineNumber": 2,
        "productCode": "04",
        "rollItemNumber": null,
        "styleName": "BRONZE-BASIC",
        "colorName": "3.5# REBOND-7/16\"",
        "supplierName": "CARPENTER",
        "quantity": 732,
        "saleUnits": "SF",
        "freight": 0.01,
        "unitPrice": 0.69,
        "total": 505.08,
        "isUseTaxLine": false,
        "notes": "(SHEET-LEVEL)",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": null,
        "inTransit": false,
        "promiseDate": "",
        "attachments": []
      },
      {
        "id": 14289,
        "lineNumber": 3,
        "productCode": "80",
        "rollItemNumber": null,
        "styleName": "MOVE FURNITURE",
        "colorName": "",
        "supplierName": "",
        "quantity": 2,
        "saleUnits": "HR",
        "freight": 0,
        "unitPrice": 102.5,
        "total": 205,
        "isUseTaxLine": false,
        "notes": "(SHEET-LEVEL)",
        "productId": 0,
        "colorId": 0,
        "delete": false,
        "priceLevel": null,
        "lineStatus": null,
        "inTransit": false,
        "promiseDate": "",
        "attachments": []
      }
    ],
    "attachments": [
      {
        "id": 7037,
        "description": "Room Plan  5/13/2016 11:35AM",
        "fileExtension": "jpg                             "
      },
      {
        "id": 7038,
        "description": "Seam Plan  5/13/2016 11:35AM",
        "fileExtension": "jpg                             "
      },
      {
        "id": 7039,
        "description": "Cut Plan (Page 1)  5/13/2016 11:35AM",
        "fileExtension": "jpg"
      },
      {
        "id": 7040,
        "description": "Cut Plan (Page 2)  5/13/2016 11:35AM",
        "fileExtension": "jpg"
      }
    ],
    "storeSpecific": null,
    "isExportedToOrder": false,
    "quoteDate": "2016-05-13",
    "orderNumber": "",
    "orderDate": "2016-05-13",
    "deliveryDate": "",
    "dueDate": "",
    "closedDate": "",
    "billedDate": "",
    "completedDate": "",
    "billingGroup": null,
    "payment": {
      "paidDate": "",
      "paidAmount": 0,
      "balanceDue": 0
    }
  },
  "detail": null
}
```

---

### Create Estimate

**POST** `https://api.rfms.online/v2/estimate/create`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poNumber` | string | Yes | Example: `00504` |
| `measureDate` | string | Yes | Example: `2021-03-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2021-03-29` |
| `jobNumber` | string | Yes | Example: `WERS997` |
| `soldTo` | object | Yes |  |
| `soldTo.lastName` | string | Yes | Example: `Orwell` |
| `soldTo.firstName` | string | Yes | Example: `George` |
| `soldTo.address1` | string | Yes | Example: `77 Almaz BLVD` |
| `soldTo.address2` | string | Yes | Example: `STE 101` |
| `soldTo.city` | string | Yes | Example: `NOWHERE` |
| `soldTo.state` | string | Yes | Example: `NE` |
| `soldTo.postalCode` | string | Yes | Example: `56332` |
| `soldTo.phone1` | string | Yes | Example: `403-333-1000` |
| `soldTo.email` | string | Yes | Example: `gorwell1@dystopiancoverings.com` |
| `soldTo.customerType` | string | Yes | Example: `REMODELING` |
| `shipTo` | object | Yes |  |
| `shipTo.lastName` | string | Yes | Example: `Orwell` |
| `shipTo.firstName` | string | Yes | Example: `George` |
| `shipTo.address1` | string | Yes | Example: `77 Almaz BLVD` |
| `shipTo.address2` | string | Yes | Example: `STE 102` |

**Example:**

```json
{
    "poNumber": "00504",
    "measureDate": "2021-03-01",
    "estimatedDeliveryDate": "2021-03-29",
    "jobNumber": "WERS997",
    "soldTo": {
        "lastName": "Orwell",
        "firstName": "George",
        "address1": "77 Almaz BLVD",
        "address2": "STE 101",
        "city": "NOWHERE",
        "state": "NE",
        "postalCode": "56332",
        "phone1": "403-333-1000",
        "email": "gorwell1@dystopiancoverings.com",
        "customerType": "REMODELING"
    },
    "shipTo":
    {
        "lastName": "Orwell",
        "firstName": "George",
        "address1": "77 Almaz BLVD",
        "address2": "STE 102",
        "city": "NOWHERE",
        "state": "NE",
        "postalCode": "56332"
    },
    "storeNumber": 32,
    "privateNotes": "PRIVATE - ORDER DELAYED",
    "publicNotes": "PUBLIC",
    "salesperson1": "Igor",
    "lines": [
    	{
    		"productId": 1018473,
    		"colorId": 8173202,
    		"quantity": 17.00,
    		"priceLevel": "Price3"
    	},
        {
            "productId": 988660,
            "colorId": 7792812,
            "quantity": 56.00,
            "priceLevel": "Price1"
        }
	]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "poNumber": "00504",
    "measureDate": "2021-03-01",
    "estimatedDeliveryDate": "2021-03-29",
    "jobNumber": "WERS997",
    "soldTo": {
        "lastName": "Orwell",
        "firstName": "George",
        "address1": "77 Almaz BLVD",
        "address2": "STE 101",
        "city": "NOWHERE",
        "state": "NE",
        "postalCode": "56332",
        "phone1": "403-333-1000",
        "email": "gorwell1@dystopiancoverings.com",
        "customerType": "REMODELING"
    },
    "shipTo":
    {
        "lastName": "Orwell",
        "firstName": "George",
        "address1": "77 Almaz BLVD",
        "address2": "STE 102",
        "city": "NOWHERE",
        "state": "NE",
        "postalCode": "56332"
    },
    "storeNumber": 32,
    "privateNotes": "PRIVATE - ORDER DELAYED",
    "publicNotes": "PUBLIC",
    "salesperson1": "Igor",
    "lines": [
    	{
    		"productId": 1018473,
    		"colorId": 8173202,
    		"quantity": 17.00,
    		"priceLevel": "Price3"
    	},
        {
            "productId": 988660,
            "colorId": 7792812,
            "quantity": 56.00,
            "priceLevel": "Price1"
        }
	]
}' 'https://api.rfms.online/v2/estimate/create'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/estimate/create',
    json={
        "poNumber": "00504",
        "measureDate": "2021-03-01",
        "estimatedDeliveryDate": "2021-03-29",
        "jobNumber": "WERS997",
        "soldTo": {
                "lastName": "Orwell",
                "firstName": "George",
                "address1": "77 Almaz BLVD",
                "address2": "STE 101",
                "city": "NOWHERE",
                "state": "NE",
                "postalCode": "56332",
                "phone1": "403-333-1000",
                "email": "gorwell1@dystopiancoverings.com",
                "customerType": "REMODELING"
        },
        "shipTo": {
                "lastName": "Orwell",
                "firstName": "George",
                "address1": "77 Almaz BLVD",
                "address2": "STE 102",
                "city": "NOWHERE",
                "state": "NE",
                "postalCode": "56332"
        },
        "storeNumber": 32,
        "privateNotes": "PRIVATE - ORDER DELAYED",
        "publicNotes": "PUBLIC",
        "salesperson1": "Igor",
        "lines": [
                {
                        "productId": 1018473,
                        "colorId": 8173202,
                        "quantity": 17.0,
                        "priceLevel": "Price3"
                },
                {
                        "productId": 988660,
                        "colorId": 7792812,
                        "quantity": 56.0,
                        "priceLevel": "Price1"
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Create BidPro Estimate** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `181`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "JE100281",
  "detail": {
    "docId": "4907"
  }
}
```

---

### Update Estimate

**POST** `https://api.rfms.online/v2/estimate`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `JE100281` |
| `estimatedDeliveryDate` | string | Yes | Example: `2021-04-23` |
| `privateNotes` | string | Yes | Example: `SHIPPING DELAYS EXPECTED` |

**Example:**

```json
{
    "number": "JE100281",
    "estimatedDeliveryDate": "2021-04-23",
    "privateNotes": "SHIPPING DELAYS EXPECTED"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "number": "JE100281",
    "estimatedDeliveryDate": "2021-04-23",
    "privateNotes": "SHIPPING DELAYS EXPECTED"
}' 'https://api.rfms.online/v2/estimate'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/estimate',
    json={
        "number": "JE100281",
        "estimatedDeliveryDate": "2021-04-23",
        "privateNotes": "SHIPPING DELAYS EXPECTED"
}
)

print(response.json())
```

#### Response Examples

**Update Estimate** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `163`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": "true"
}
```

---

### Find Estimate

**POST** `https://api.rfms.online/v2/estimate/find`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `Jacob Solanto` |
| `dateCreatedFrom` | string | Yes | Example: `2023-06-20` |
| `dateCreatedTo` | string | Yes | Example: `2023-06-28` |
| `viewExportedOnly` | boolean | Yes | Example: `True` |
| `viewOpenOnly` | boolean | Yes |  |

**Example:**

```json
{
	"searchText": "Jacob Solanto",
    "dateCreatedFrom": "2023-06-20",
    "dateCreatedTo": "2023-06-28",
    "viewExportedOnly": true,
    "viewOpenOnly": false
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
	"searchText": "Jacob Solanto",
    "dateCreatedFrom": "2023-06-20",
    "dateCreatedTo": "2023-06-28",
    "viewExportedOnly": true,
    "viewOpenOnly": false
}' 'https://api.rfms.online/v2/estimate/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/estimate/find',
    json={
        "searchText": "Jacob Solanto",
        "dateCreatedFrom": "2023-06-20",
        "dateCreatedTo": "2023-06-28",
        "viewExportedOnly": true,
        "viewOpenOnly": false
}
)

print(response.json())
```

---

### Create Claim

**POST** `https://api.rfms.online/v2/claim/create`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |
| `token` | `` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `poNumber` | string | Yes | Example: `987654` |
| `adSource` | string | Yes | Example: `BILLBOARD` |
| `quoteDate` | string | Yes | Example: `2019-07-01` |
| `estimatedDeliveryDate` | string | Yes | Example: `2019-08-01` |
| `jobNumber` | string | Yes | Example: `ABC123` |
| `soldTo` | object | Yes |  |
| `soldTo.lastName` | string | Yes | Example: `DOE` |
| `soldTo.firstName` | string | Yes | Example: `JOHN` |
| `soldTo.address1` | string | Yes | Example: `1234 MAIN ST` |
| `soldTo.address2` | string | Yes | Example: `STE 33` |
| `soldTo.city` | string | Yes | Example: `ANYTOWN` |
| `soldTo.state` | string | Yes | Example: `CA` |
| `soldTo.postalCode` | string | Yes | Example: `91332` |
| `soldTo.county` | string | Yes | Example: `LOS ANGELES` |
| `storeNumber` | integer | Yes | Example: `50` |
| `privateNotes` | string | Yes | Example: `PRIVATE` |
| `publicNotes` | string | Yes | Example: `PUBLIC` |
| `workOrderNotes` | string | Yes | Example: `WORK ORDER NOTES` |
| `salesperson1` | string | Yes | Example: `JOHN` |
| `salesperson2` | string | Yes | Example: `FRANK` |

**Example:**

```json
{
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3"
    	}
	]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "poNumber": "987654",
    "adSource": "BILLBOARD",
    "quoteDate": "2019-07-01",
    "estimatedDeliveryDate": "2019-08-01",
    "jobNumber": "ABC123",
    "soldTo": { 
	    "lastName": "DOE",
	    "firstName": "JOHN",
	    "address1": "1234 MAIN ST",
	    "address2": "STE 33",
	    "city": "ANYTOWN",
	    "state": "CA",
	    "postalCode": "91332",
	    "county": "LOS ANGELES"
    },
    "storeNumber": 50,
    "privateNotes": "PRIVATE",
    "publicNotes": "PUBLIC",
    "workOrderNotes": "WORK ORDER NOTES",
    "salesperson1": "JOHN",
    "salesperson2": "FRANK",
    "lines": [
    	{
    		"productId": 992048,
    		"colorId": 7814430,
    		"quantity": 12.00,
    		"priceLevel": "Price3"
    	}
	]
}' 'https://api.rfms.online/v2/claim/create'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/claim/create',
    headers={
    "Content-Type": "application/json"
},
    json={
        "poNumber": "987654",
        "adSource": "BILLBOARD",
        "quoteDate": "2019-07-01",
        "estimatedDeliveryDate": "2019-08-01",
        "jobNumber": "ABC123",
        "soldTo": {
                "lastName": "DOE",
                "firstName": "JOHN",
                "address1": "1234 MAIN ST",
                "address2": "STE 33",
                "city": "ANYTOWN",
                "state": "CA",
                "postalCode": "91332",
                "county": "LOS ANGELES"
        },
        "storeNumber": 50,
        "privateNotes": "PRIVATE",
        "publicNotes": "PUBLIC",
        "workOrderNotes": "WORK ORDER NOTES",
        "salesperson1": "JOHN",
        "salesperson2": "FRANK",
        "lines": [
                {
                        "productId": 992048,
                        "colorId": 7814430,
                        "quantity": 12.0,
                        "priceLevel": "Price3"
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Create Claim** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "CL903428",
  "detail": null
}
```

---

### Add Notes to Claim

**POST** `https://api.rfms.online/v2/claim/notes`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `number` | string | Yes | Example: `CL000015` |
| `publicNotes` | string | Yes | Example: `A public note` |
| `privateNotes` | string | Yes | Example: `Private note` |
| `workOrderNotes` | string | Yes | Example: `Work order notes` |

**Example:**

```json
{
    "number": "CL000015",
    "publicNotes": "A public note",
    "privateNotes": "Private note",
    "workOrderNotes": "Work order notes"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "number": "CL000015",
    "publicNotes": "A public note",
    "privateNotes": "Private note",
    "workOrderNotes": "Work order notes"
}' 'https://api.rfms.online/v2/claim/notes'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/claim/notes',
    headers={
    "Content-Type": "application/json"
},
    json={
        "number": "CL000015",
        "publicNotes": "A public note",
        "privateNotes": "Private note",
        "workOrderNotes": "Work order notes"
}
)

print(response.json())
```

#### Response Examples

**Add Notes to Claim** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `162`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": null
}
```

---

### Get Product Codes

**GET** `https://api.rfms.online/v2/product/get/productcodes`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/product/get/productcodes'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/product/get/productcodes'
)

print(response.json())
```

#### Response Examples

**Get Product Codes** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `737`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "productCodes": [
    {
      "productCode": "01",
      "title": "01 - CARPET"
    },
    {
      "productCode": "02",
      "title": "02 - VINYL"
    },
    {
      "productCode": "03",
      "title": "03 - AREA RUGS"
    },
    {
      "productCode": "04",
      "title": "04 - CUSHION"
    },
    {
      "productCode": "05",
      "title": "05 - WALL COVERINGS"
    },
    {
      "productCode": "06",
      "title": "06 - CERAMIC"
    },
    {
      "productCode": "07",
      "title": "07 - HARDWOOD"
    },
    {
      "productCode": "08",
      "title": "08 - SUPPLIES"
    },
    {
      "productCode": "09",
      "title": "09 - SUNDRIES & CLEANERS"
    },
    {
      "productCode": "10",
      "title": "10 - IN STORE USE"
    },
    {
      "productCode": "11",
      "title": "11 - VCT & COVEBASE"
    },
    {
      "productCode": "12",
      "title": "12 - WINDOWS & DRAPES"
    },
    {
      "productCode": "13",
      "title": "13 - LAMINATES"
    },
    {
      "productCode": "14",
      "title": "14 - SAMPLES"
    },
    {
      "productCode": "15",
      "title": "15 - EVERGUARD"
    },
    {
      "productCode": "16",
      "title": "16 - TOOLS"
    },
    {
      "productCode": "17",
      "title": "17 - CARPET TILES"
    },
    {
      "productCode": "18",
      "title": "18 - REMNANTS"
    },
    {
      "productCode": "80",
      "title": "80 - MISCELLANEOUS"
    },
    {
      "productCode": "81",
      "title": "81 - CARPET INSTALLATION"
    },
    {
      "productCode": "82",
      "title": "82 - VINYL INSTALLATION"
    },
    {
      "productCode": "83",
      "title": "83 - LAMINATE LABOR"
    },
    {
      "productCode": "84",
      "title": "84 - CARPET REMOVAL"
    },
    {
      "productCode": "85",
      "title": "85 - VINYL REMOVAL"
    },
    {
      "productCode": "86",
      "title": "86 - CERAMIC LABOR"
    },
    {
      "productCode": "87",
      "title": "87 - WOOD INSTALLATION"
    },
    {
      "productCode": "88",
      "title": "88 - WOOD/SAND & FINISH"
    },
    {
      "productCode": "89",
      "title": "89 - UNDERLAYMENT LABOR"
    },
    {
      "productCode": "90",
      "title": "90 - VCT INSTALLATION"
    },
    {
      "productCode": "91",
      "title": "91 - TRIP CHARGE"
    },
    {
      "productCode": "92",
      "title": "92 - APPLIANCES"
    },
    {
      "productCode": "93",
      "title": "93 - COVE BASE LABOR"
    },
    {
      "productCode": "94",
      "title": "94 - STEPS"
    },
    {
      "productCode": "95",
      "title": "95 - GRANITE WORK"
    },
    {
      "productCode": "97",
      "title": "97 - MODULAR CARPET TILE"
    },
    {
      "productCode": "98",
      "title": "98 - TOOL CARE"
    },
    {
      "productCode": "99",
      "title": "99 - CARPET ONE CLEANING"
    }
  ]
}
```

---

### Get Products

**POST** `https://api.rfms.online/v2/product/get`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `products` | array | Yes |  |

**Example:**

```json
{
    "products" :["88419", "88168", "1021622"]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "products" :["88419", "88168", "1021622"]
}' 'https://api.rfms.online/v2/product/get'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/product/get',
    json={
        "products": [
                "88419",
                "88168",
                "1021622"
        ]
}
)

print(response.json())
```

#### Response Examples

**Get Products** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `3635`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "rollNumber": "",
      "supplierName": "SHAW INDUSTRIES, INC",
      "privateSupplierName": "CARPET ONE",
      "manufacturerName": "PHILADELPHIA MAINSTR 40",
      "rollLengthInches": 2400,
      "activeProduct": true,
      "sellByQuantity": 0,
      "notes": "",
      "inventoryUnits": "",
      "priceListings": {
        "Price1": 3.79,
        "Price2": 2.12,
        "Price3": 1.74,
        "Price4": 1.59,
        "Price5": 1.55,
        "Price8": 5.68,
        "Price9": 2.31,
        "Price10": 5.78,
        "Price11": 2.41,
        "Price12": 1.04,
        "Cut": 1.04,
        "Roll": 0.92
      },
      "colorOptions": [
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157177",
          "colorName": "BANK BAG",
          "colorNumber": "106",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157172",
          "colorName": "BANKER S PINSTR",
          "colorNumber": "68401",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157170",
          "colorName": "CASH FLOW",
          "colorNumber": "108",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157178",
          "colorName": "COIN WRAPPER",
          "colorNumber": "109",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157169",
          "colorName": "CURRENCY",
          "colorNumber": "110",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157179",
          "colorName": "DAY TRADER",
          "colorNumber": "111",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157182",
          "colorName": "DIVIDEND",
          "colorNumber": "112",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157166",
          "colorName": "DOLLAR SIGN",
          "colorNumber": "113",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157165",
          "colorName": "FRANKLIN MINT",
          "colorNumber": "114",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157180",
          "colorName": "IN THE RED",
          "colorNumber": "100",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157168",
          "colorName": "INTEREST RATE",
          "colorNumber": "115",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157171",
          "colorName": "LADY LIBERTY",
          "colorNumber": "116",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157176",
          "colorName": "LOOSE CHANGE",
          "colorNumber": "117",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157181",
          "colorName": "MUTUAL FUND",
          "colorNumber": "104",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157173",
          "colorName": "NIGHT DEPOSIT",
          "colorNumber": "105",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157167",
          "colorName": "PRESIDENT S DAY",
          "colorNumber": "68302",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157175",
          "colorName": "SILVER DOLLAR",
          "colorNumber": "102",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1157174",
          "colorName": "STOCK MARKET",
          "colorNumber": "103",
          "SKU": ""
        }
      ],
      "attachments": [
        {
          "id": 12345,
          "description": "Red.jpg",
          "fileExtension": "jpg",
          "url": ""
        }
      ],
      "id": "88168",
      "productCode": "01",
      "storeNumber": 32,
      "styleName": "EARNEST - 12'",
      "styleNumber": "5498029",
      "defaultPrice": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0
    },
    {
      "rollNumber": "",
      "supplierName": "SHAW INDUSTRIES, INC",
      "privateSupplierName": "CARPET ONE",
      "manufacturerName": "PHILADELPHIA MAINSTR 40",
      "rollLengthInches": 2400,
      "activeProduct": true,
      "sellByQuantity": 0,
      "notes": "<div><p style=\"margin-left:0pt; margin-top:0pt; margin-right:0pt; margin-bottom:0pt; text-indent:0pt;\"><span style=\"font:10pt 'Courier New'; color:#000000;\">Test note on Product Style</span></p></div>",
      "inventoryUnits": "",
      "priceListings": {
        "Price1": 5.59,
        "Price2": 3.12,
        "Price3": 2.58,
        "Price4": 2.36,
        "Price5": 2.3,
        "Price8": 8.38,
        "Price9": 3.4,
        "Price10": 8.48,
        "Price11": 3.5,
        "Price12": 1.57,
        "Cut": 1.57,
        "Roll": 1.43
      },
      "colorOptions": [
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161697",
          "colorName": "ATLANTIC BLUE",
          "colorNumber": "105",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161698",
          "colorName": "BLACKTOP",
          "colorNumber": "106",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161693",
          "colorName": "BRIARWOOD",
          "colorNumber": "101",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161702",
          "colorName": "CAROLINA BLOSSO",
          "colorNumber": "70801",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161703",
          "colorName": "ETERNAL JEWEL",
          "colorNumber": "111",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161692",
          "colorName": "FRANKLIN GREEN",
          "colorNumber": "100",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161696",
          "colorName": "FROZEN LAKE",
          "colorNumber": "104",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161701",
          "colorName": "PARADISE BEACH",
          "colorNumber": "109",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161704",
          "colorName": "PURPLE DREAM",
          "colorNumber": "112",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161695",
          "colorName": "QUINTON EVERGRE",
          "colorNumber": "70304",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161694",
          "colorName": "TIDEWATER",
          "colorNumber": "102",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161699",
          "colorName": "TUSCANY",
          "colorNumber": "107",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "1161700",
          "colorName": "WESTSIDE",
          "colorNumber": "108",
          "SKU": ""
        }
      ],
      "attachments": [
        {
          "id": 12345,
          "description": "Red.jpg",
          "fileExtension": "jpg",
          "url": ""
        }
      ],
      "id": "88419",
      "productCode": "01",
      "storeNumber": 32,
      "styleName": "COPIOUS - 12'",
      "styleNumber": "10100871",
      "defaultPrice": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0
    },
    {
      "rollNumber": "",
      "supplierName": "KRAUS CARPET MILLS LIMITED",
      "privateSupplierName": "CARPET ONE",
      "manufacturerName": "KRAUS CARPET MILLS LIMITED",
      "rollLengthInches": 0,
      "activeProduct": true,
      "sellByQuantity": 0,
      "inventoryUnits": "",
      "priceListings": {
        "Cut": 0,
        "Roll": 0
      },
      "colorOptions": [
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227105",
          "colorName": "FAIRY MOSS",
          "colorNumber": "79",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227109",
          "colorName": "FATISIA",
          "colorNumber": "29",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227107",
          "colorName": "FELICITA",
          "colorNumber": "76",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227096",
          "colorName": "FELT",
          "colorNumber": "81",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227101",
          "colorName": "FENNEL",
          "colorNumber": "10",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227110",
          "colorName": "FETTERBUSH",
          "colorNumber": "14",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227102",
          "colorName": "FILBERT",
          "colorNumber": "32",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227108",
          "colorName": "FILLY CURLS",
          "colorNumber": "07",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227112",
          "colorName": "FLEECE",
          "colorNumber": "54",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227099",
          "colorName": "FOAMFLOWER",
          "colorNumber": "80",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227094",
          "colorName": "FOGGY",
          "colorNumber": "90",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227097",
          "colorName": "FOLKLORE",
          "colorNumber": "48",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227100",
          "colorName": "FORGET-ME-NOT",
          "colorNumber": "83",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227111",
          "colorName": "FOSTER",
          "colorNumber": "41",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227103",
          "colorName": "FOUNTAIN GRASS",
          "colorNumber": "50",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227106",
          "colorName": "FOXTAIL",
          "colorNumber": "82",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227104",
          "colorName": "FRAGMENT",
          "colorNumber": "91",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227098",
          "colorName": "FRANKLINIA",
          "colorNumber": "58",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227113",
          "colorName": "FREESIAS",
          "colorNumber": "77",
          "SKU": ""
        },
        {
          "relatedProductAvailable": false,
          "activeColor": true,
          "attactments": [],
          "id": "8227095",
          "colorName": "FRENCH LACE",
          "colorNumber": "78",
          "SKU": ""
        }
      ],
      "id": "1021622",
      "productCode": "01",
      "storeNumber": 32,
      "styleName": "FLORET - 12'",
      "styleNumber": "2013",
      "defaultPrice": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0
    }
  ],
  "detail": [
    {
      "patternDropFraction": 0,
      "cutGapInInches": 4,
      "cutGapMethod": 0,
      "allowedTseams": 2,
      "cutSquare": true,
      "extraWastePercent": 18,
      "unitCost": 1.04,
      "supplier": "SHAW INDUSTRIES, INC",
      "privateSupplier": "CARPET ONE",
      "manufacturer": "PHILADELPHIA MAINSTR 40",
      "sellQuantity": 0,
      "inventoryUnit": "",
      "rollNumber": "",
      "rollLengthInInches": 2400,
      "active": true,
      "colors": [
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157177",
          "colorName": "BANK BAG",
          "colorNumber": "106"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157172",
          "colorName": "BANKER S PINSTR",
          "colorNumber": "68401"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157170",
          "colorName": "CASH FLOW",
          "colorNumber": "108"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157178",
          "colorName": "COIN WRAPPER",
          "colorNumber": "109"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157169",
          "colorName": "CURRENCY",
          "colorNumber": "110"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157179",
          "colorName": "DAY TRADER",
          "colorNumber": "111"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157182",
          "colorName": "DIVIDEND",
          "colorNumber": "112"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157166",
          "colorName": "DOLLAR SIGN",
          "colorNumber": "113"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157165",
          "colorName": "FRANKLIN MINT",
          "colorNumber": "114"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157180",
          "colorName": "IN THE RED",
          "colorNumber": "100"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157168",
          "colorName": "INTEREST RATE",
          "colorNumber": "115"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157171",
          "colorName": "LADY LIBERTY",
          "colorNumber": "116"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157176",
          "colorName": "LOOSE CHANGE",
          "colorNumber": "117"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157181",
          "colorName": "MUTUAL FUND",
          "colorNumber": "104"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157173",
          "colorName": "NIGHT DEPOSIT",
          "colorNumber": "105"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157167",
          "colorName": "PRESIDENT S DAY",
          "colorNumber": "68302"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157175",
          "colorName": "SILVER DOLLAR",
          "colorNumber": "102"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1157174",
          "colorName": "STOCK MARKET",
          "colorNumber": "103"
        }
      ],
      "id": "88168",
      "productCode": "01",
      "storeId": 32,
      "styleNumber": "5498029",
      "styleName": "EARNEST - 12'",
      "supplierName": "SHAW INDUSTRIES, INC",
      "manufacturerName": "PHILADELPHIA MAINSTR 40",
      "defaultPrice": 2.12,
      "defaultPriceLevel": 2,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0,
      "prices": {
        "Price1": 3.79,
        "Price2": 2.12,
        "Price3": 1.74,
        "Price4": 1.59,
        "Price5": 1.55,
        "Price8": 5.68,
        "Price9": 2.31,
        "Price10": 5.78,
        "Price11": 2.41,
        "Price12": 1.04,
        "Cut": 1.04,
        "Roll": 0.92
      }
    },
    {
      "patternDropFraction": 0,
      "cutGapInInches": 4,
      "cutGapMethod": 0,
      "allowedTseams": 2,
      "cutSquare": true,
      "extraWastePercent": 18,
      "unitCost": 1.57,
      "supplier": "SHAW INDUSTRIES, INC",
      "privateSupplier": "CARPET ONE",
      "manufacturer": "PHILADELPHIA MAINSTR 40",
      "sellQuantity": 0,
      "inventoryUnit": "",
      "rollNumber": "",
      "rollLengthInInches": 2400,
      "active": true,
      "colors": [
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161697",
          "colorName": "ATLANTIC BLUE",
          "colorNumber": "105"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161698",
          "colorName": "BLACKTOP",
          "colorNumber": "106"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161693",
          "colorName": "BRIARWOOD",
          "colorNumber": "101"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161702",
          "colorName": "CAROLINA BLOSSO",
          "colorNumber": "70801"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161703",
          "colorName": "ETERNAL JEWEL",
          "colorNumber": "111"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161692",
          "colorName": "FRANKLIN GREEN",
          "colorNumber": "100"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161696",
          "colorName": "FROZEN LAKE",
          "colorNumber": "104"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161701",
          "colorName": "PARADISE BEACH",
          "colorNumber": "109"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161704",
          "colorName": "PURPLE DREAM",
          "colorNumber": "112"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161695",
          "colorName": "QUINTON EVERGRE",
          "colorNumber": "70304"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161694",
          "colorName": "TIDEWATER",
          "colorNumber": "102"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161699",
          "colorName": "TUSCANY",
          "colorNumber": "107"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "1161700",
          "colorName": "WESTSIDE",
          "colorNumber": "108"
        }
      ],
      "id": "88419",
      "productCode": "01",
      "storeId": 32,
      "styleNumber": "10100871",
      "styleName": "COPIOUS - 12'",
      "supplierName": "SHAW INDUSTRIES, INC",
      "manufacturerName": "PHILADELPHIA MAINSTR 40",
      "defaultPrice": 3.12,
      "defaultPriceLevel": 2,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0,
      "prices": {
        "Price1": 5.59,
        "Price2": 3.12,
        "Price3": 2.58,
        "Price4": 2.36,
        "Price5": 2.3,
        "Price8": 8.38,
        "Price9": 3.4,
        "Price10": 8.48,
        "Price11": 3.5,
        "Price12": 1.57,
        "Cut": 1.57,
        "Roll": 1.43
      }
    },
    {
      "patternDropFraction": 0,
      "cutGapInInches": 4,
      "cutGapMethod": 0,
      "allowedTseams": 2,
      "cutSquare": true,
      "extraWastePercent": 18,
      "unitCost": 0,
      "supplier": "KRAUS CARPET MILLS LIMITED",
      "privateSupplier": "CARPET ONE",
      "manufacturer": "KRAUS CARPET MILLS LIMITED",
      "sellQuantity": 0,
      "inventoryUnit": "",
      "rollNumber": "",
      "rollLengthInInches": 0,
      "active": true,
      "colors": [
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227105",
          "colorName": "FAIRY MOSS",
          "colorNumber": "79"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227109",
          "colorName": "FATISIA",
          "colorNumber": "29"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227107",
          "colorName": "FELICITA",
          "colorNumber": "76"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227096",
          "colorName": "FELT",
          "colorNumber": "81"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227101",
          "colorName": "FENNEL",
          "colorNumber": "10"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227110",
          "colorName": "FETTERBUSH",
          "colorNumber": "14"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227102",
          "colorName": "FILBERT",
          "colorNumber": "32"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227108",
          "colorName": "FILLY CURLS",
          "colorNumber": "07"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227112",
          "colorName": "FLEECE",
          "colorNumber": "54"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227099",
          "colorName": "FOAMFLOWER",
          "colorNumber": "80"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227094",
          "colorName": "FOGGY",
          "colorNumber": "90"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227097",
          "colorName": "FOLKLORE",
          "colorNumber": "48"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227100",
          "colorName": "FORGET-ME-NOT",
          "colorNumber": "83"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227111",
          "colorName": "FOSTER",
          "colorNumber": "41"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227103",
          "colorName": "FOUNTAIN GRASS",
          "colorNumber": "50"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227106",
          "colorName": "FOXTAIL",
          "colorNumber": "82"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227104",
          "colorName": "FRAGMENT",
          "colorNumber": "91"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227098",
          "colorName": "FRANKLINIA",
          "colorNumber": "58"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227113",
          "colorName": "FREESIAS",
          "colorNumber": "77"
        },
        {
          "relatedProductAvailable": false,
          "sku": "",
          "active": true,
          "attachments": [],
          "id": "8227095",
          "colorName": "FRENCH LACE",
          "colorNumber": "78"
        }
      ],
      "id": "1021622",
      "productCode": "01",
      "storeId": 32,
      "styleNumber": "2013",
      "styleName": "FLORET - 12'",
      "supplierName": "KRAUS CARPET MILLS LIMITED",
      "manufacturerName": "KRAUS CARPET MILLS LIMITED",
      "defaultPrice": 0,
      "defaultPriceLevel": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 12,
      "patternLengthInInches": 21,
      "prices": {
        "Cut": 0,
        "Roll": 0
      }
    }
  ]
}
```

---

### Find Products

**POST** `https://api.rfms.online/v2/product/find`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `searchText` | string | Yes | Example: `adobe` |
| `storeNumber` | integer | Yes | Example: `32` |
| `productCode` | string | Yes | Example: `01` |
| `ecProductId` | string | Yes | Example: `123AB` |

**Example:**

```json
{
  "searchText": "adobe",
  "storeNumber": 32,
  "productCode": "01",
  "ecProductId": "123AB"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "searchText": "adobe",
  "storeNumber": 32,
  "productCode": "01",
  "ecProductId": "123AB"
}' 'https://api.rfms.online/v2/product/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/product/find',
    headers={
    "Content-Type": "application/json"
},
    json={
        "searchText": "adobe",
        "storeNumber": 32,
        "productCode": "01",
        "ecProductId": "123AB"
}
)

print(response.json())
```

#### Response Examples

**Find Products** ( - 0)

```json
{
  "status": "success",
  "result": [
    {
      "id": "1025333",
      "productCode": "01",
      "storeNumber": 32,
      "styleName": "ABBEY COURT - 12'",
      "styleNumber": "HGL85",
      "defaultPrice": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0,
      "colorOptions": [
        {
          "id": "8293005",
          "colorName": "ACORN",
          "colorNumber": "00703",
          "SKU": ""
        },
        {
          "id": "8293009",
          "colorName": "ADOBE SHADOW",
          "colorNumber": "00101",
          "SKU": ""
        },
        {
          "id": "8292988",
          "colorName": "AEGEAN",
          "colorNumber": "00403",
          "SKU": ""
        }
      ]
    },
    {
      "id": "1019427",
      "productCode": "01",
      "storeNumber": 32,
      "styleName": "AC53B - 12'",
      "styleNumber": "AC53B",
      "defaultPrice": 0,
      "saleUnits": "SF",
      "rollWidthInInches": 144,
      "patternWidthInInches": 0,
      "patternLengthInInches": 0,
      "colorOptions": [
        {
          "id": "8191661",
          "colorName": "ADOBE",
          "colorNumber": "04",
          "SKU": ""
        },
        {
          "id": "8191662",
          "colorName": "AZTEC SAND",
          "colorNumber": "10",
          "SKU": ""
        },
        {
          "id": "8191663",
          "colorName": "CASHMERE",
          "colorNumber": "06",
          "SKU": ""
        }
      ]
    }
  ],
  "detail": null
}
```

---

### Get Product Bundles

**POST** `https://api.rfms.online/v2/product/get/productbundle`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `productId` | integer | Yes | Example: `1017786` |
| `colorId` | integer | Yes | Example: `8166321` |

**Example:**

```json
{
    "productId": 1017786,
    "colorId": 8166321
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "productId": 1017786,
    "colorId": 8166321
}' 'https://api.rfms.online/v2/product/get/productbundle'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/product/get/productbundle',
    json={
        "productId": 1017786,
        "colorId": 8166321
}
)

print(response.json())
```

#### Response Examples

**Get Product Bundles** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `649`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "id": 346678,
      "name": "ACAPELLA FLOOR TILE - 13X13 - BRUN - 13x13 - GATEWAY",
      "products": [
        {
          "rollNumber": "",
          "supplierName": "MOHAWK INDUSTRIES",
          "privateSupplierName": "CARPET ONE",
          "manufacturerName": "MOHAWK INDUSTRIES",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Cut": 0,
            "Roll": 0
          },
          "colorOptions": [
            {
              "relatedProductAvailable": false,
              "activeColor": true,
              "attactments": [],
              "id": "8166247",
              "colorName": "BRUN",
              "colorNumber": "AH92",
              "SKU": ""
            }
          ],
          "id": "1017766",
          "productCode": "06",
          "storeNumber": 32,
          "styleName": "ACAPELLA BULLNOSE - 3X13",
          "styleNumber": "T793PBN",
          "defaultPrice": 0,
          "saleUnits": "EA",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        },
        {
          "rollNumber": "",
          "supplierName": "MOHAWK INDUSTRIES",
          "privateSupplierName": "CARPET ONE",
          "manufacturerName": "MOHAWK INDUSTRIES",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Cut": 0,
            "Roll": 0
          },
          "colorOptions": [
            {
              "relatedProductAvailable": false,
              "activeColor": true,
              "attactments": [],
              "id": "8166292",
              "colorName": "BRUN",
              "colorNumber": "AH92",
              "SKU": ""
            }
          ],
          "id": "1017777",
          "productCode": "06",
          "storeNumber": 32,
          "styleName": "ACAPELLA SURFACE BULLNOSE - 3X10",
          "styleNumber": "T793PSBN",
          "defaultPrice": 0,
          "saleUnits": "EA",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        }
      ]
    }
  ],
  "detail": null
}
```

---

### Get Product Templates

**GET** `https://api.rfms.online/v2/product/templates/:id`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/product/templates/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/product/templates/:id'
)

print(response.json())
```

#### Response Examples

**Get Product Templates** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `1157`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "id": 1,
      "name": "STANDARD CERAMIC FLOORS",
      "products": [
        {
          "rollNumber": "",
          "supplierName": "WCO",
          "privateSupplierName": "WCO",
          "manufacturerName": "WCO",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Price1": 4.45,
            "Price2": 3.95,
            "Price12": 2.15,
            "Cut": 2.15,
            "Roll": 2.15
          },
          "colorOptions": [],
          "id": "110141",
          "productCode": "86",
          "storeNumber": 32,
          "styleName": "FLOOR-TILE STRAIGHT",
          "styleNumber": "FT-ST",
          "defaultPrice": 0,
          "saleUnits": "SF",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        },
        {
          "rollNumber": "",
          "supplierName": "SOUTHERN WHOLESALE",
          "privateSupplierName": "",
          "manufacturerName": "GREENEBOARD",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0.5,
          "inventoryUnits": "",
          "priceListings": {
            "Price1": 35.49,
            "Price2": 22.62,
            "Price3": 18.79,
            "Price4": 17.22,
            "Price5": 16.32,
            "Price7": 15.16,
            "Price8": 17.65,
            "Cut": 11.59,
            "Roll": 11.59
          },
          "colorOptions": [
            {
              "relatedProductAvailable": false,
              "activeColor": true,
              "attactments": [],
              "id": "6963161",
              "colorName": "1/2\" (3'X5\")",
              "colorNumber": "",
              "SKU": ""
            }
          ],
          "id": "909192",
          "productCode": "06",
          "storeNumber": 32,
          "styleName": "UNDERLAY-GREENEBOARD",
          "styleNumber": "GB1/2",
          "defaultPrice": 0,
          "saleUnits": "SH",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        },
        {
          "rollNumber": "",
          "supplierName": "CT",
          "privateSupplierName": "CT",
          "manufacturerName": "KDB",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Cut": 0.75,
            "Roll": 0.75
          },
          "colorOptions": [],
          "id": "1036964",
          "productCode": "86",
          "storeNumber": 32,
          "styleName": "CERAMIC FLOOR TEAR OUT",
          "styleNumber": "CT3333",
          "defaultPrice": 0,
          "saleUnits": "SF",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        }
      ]
    },
    {
      "id": 2,
      "name": "FREIGHT AND MISC",
      "products": [
        {
          "rollNumber": "",
          "supplierName": "WCO",
          "privateSupplierName": "WCO",
          "manufacturerName": "WCO",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Price1": 51.5,
            "Price2": 46,
            "Price12": 25,
            "Cut": 25,
            "Roll": 25
          },
          "colorOptions": [],
          "id": "97436",
          "productCode": "80",
          "storeNumber": 32,
          "styleName": "TOILET - TAKE UP ",
          "styleNumber": "TUT",
          "defaultPrice": 0,
          "saleUnits": "EA",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        },
        {
          "rollNumber": "",
          "supplierName": "WCO",
          "privateSupplierName": "",
          "manufacturerName": "WCO",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Price1": 87.5,
            "Price2": 78,
            "Cut": 42.5,
            "Roll": 42.5
          },
          "colorOptions": [],
          "id": "123361",
          "productCode": "91",
          "storeNumber": 32,
          "styleName": "TRIP CHARGE-1ST HOUR",
          "styleNumber": "TC/CV",
          "defaultPrice": 0,
          "saleUnits": "EA",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        },
        {
          "rollNumber": "",
          "supplierName": "WCO",
          "privateSupplierName": "",
          "manufacturerName": "WCO",
          "rollLengthInches": 0,
          "activeProduct": true,
          "sellByQuantity": 0,
          "inventoryUnits": "",
          "priceListings": {
            "Price1": 0.11,
            "Price2": 0.1,
            "Cut": 0.05,
            "Roll": 0.05
          },
          "colorOptions": [],
          "id": "316865",
          "productCode": "80",
          "storeNumber": 32,
          "styleName": "HAUL-OFF FEE",
          "styleNumber": "HAULOFF",
          "defaultPrice": 0,
          "saleUnits": "SF",
          "rollWidthInInches": 0,
          "patternWidthInInches": 0,
          "patternLengthInInches": 0
        }
      ]
    }
  ],
  "detail": null
}
```

---

### Get Product ETaggs

**GET** `https://api.rfms.online/v2/product/etaggs`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/product/etaggs'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/product/etaggs'
)

print(response.json())
```

#### Response Examples

**Get Product ETaggs** (OK - 200)

*Response Headers:*

- `Content-Type`: `application/json`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "SeqNum": 87602,
      "StoreCode": 32,
      "StoreCaptionLong": "[\" \"] CYNCLY'S CARPET STORE",
      "StoreCaptionShort": "[\" \"]",
      "ProductCode": "01",
      "PrivateLabelCo": "CARPET ONE",
      "PrivateStyleNumber": "10101978",
      "PrivateStyle": "PERIMETER PLACE - HSC - 12' - 12'",
      "Supplier": "SHAW INDUSTRIES, INC",
      "Style": "ASHFORD 12 - 12'",
      "StyleNumber": "7R342",
      "Collection": "",
      "SerialNumber": "",
      "Manufacturer": "PHILADELPHIA 02",
      "Price1": 2.79,
      "Price2": 1.52,
      "Price3": 1.25,
      "Price4": 1.14,
      "Price5": 1.11,
      "Price6": 0.0,
      "Price7": 0.0,
      "Price8": 4.19,
      "Price9": 1.66,
      "Price10": 4.28,
      "Price11": 1.76,
      "Price12": 0.74,
      "MSRP": 0.0,
      "Units": "SY",
      "Backing": "AK-106",
      "FiberType": "OLEFIN",
      "StyleType": "BERBER LOOP W/F",
      "Species": "",
      "Warranty": "",
      "Quality": "BRONZE",
      "ItemLength": "",
      "ItemWidth": "",
      "RollLength": 150.0,
      "RollWidth": 12.0,
      "ItemThickness": 0.0,
      "ThicknessUOM": "",
      "FreeText_": "12'",
      "FHANum": "",
      "SellConversion": 0.0,
      "SellUnit": "",
      "BuyConversion": 0.0,
      "BuyUnit": "",
      "ToxicityNum": "",
      "PatternWidth": 0.0,
      "PatternLength": 0.0,
      "TransactionDate": {
        "Year": 2017,
        "Month": 10,
        "Day": 30
      },
      "Status": "Active",
      "DisplayName": "HOME SHOWCASE CPT",
      "RollMin": "75",
      "SellQuantity": 0.0
    },
    {
      "SeqNum": 96900,
      "StoreCode": 32,
      "StoreCaptionLong": "[\" \"] CYNCLY'S CARPET STORE",
      "StoreCaptionShort": "[\" \"]",
      "ProductCode": "01",
      "PrivateLabelCo": "CARPET ONE",
      "PrivateStyleNumber": "10102393",
      "PrivateStyle": "GUARDIAN 26 - 12'",
      "Supplier": "SHAW INDUSTRIES, INC",
      "Style": "LANGAN II 26 - 12'",
      "StyleNumber": "7V472",
      "Collection": "",
      "SerialNumber": "",
      "Manufacturer": "PHILADELPHIA MAINSTR 40",
      "Price1": 3.49,
      "Price2": 1.92,
      "Price3": 1.6,
      "Price4": 1.47,
      "Price5": 1.43,
      "Price6": 0.0,
      "Price7": 0.0,
      "Price8": 5.24,
      "Price9": 2.09,
      "Price10": 5.33,
      "Price11": 2.19,
      "Price12": 0.96,
      "MSRP": 0.0,
      "Units": "SY",
      "Backing": "10X20",
      "FiberType": "OLEFIN",
      "StyleType": "LOOP W/OUT FLEC",
      "Species": "",
      "Warranty": "",
      "Quality": "BRONZE",
      "ItemLength": "",
      "ItemWidth": "",
      "RollLength": 125.0,
      "RollWidth": 12.0,
      "ItemThickness": 0.0,
      "ThicknessUOM": "",
      "FreeText_": "12'",
      "FHANum": "",
      "SellConversion": 0.0,
      "SellUnit": "",
      "BuyConversion": 0.0,
      "BuyUnit": "",
      "ToxicityNum": "",
      "PatternWidth": 0.0,
      "PatternLength": 0.0,
      "TransactionDate": {
        "Year": 2017,
        "Month": 10,
        "Day": 30
      },
      "Status": "Active",
      "DisplayName": "Workspaces",
      "RollMin": "75",
      "SellQuantity": 0.0
    }
  ]
}
```

---

### Check Available Inventory

**POST** `https://api.rfms.online/v2/product/inventorycheck`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `productCode` | string | Yes | Example: `01` |
| `styleName` | string | Yes | Example: `FOREIGNER - SOLID - 12'` |
| `colorName` | string | Yes | Example: `FENCE POST` |

**Example:**

```json
{
  "productCode": "01",
  "styleName": "FOREIGNER - SOLID - 12'",
  "colorName": "FENCE POST"
}

```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
  "productCode": "01",
  "styleName": "FOREIGNER - SOLID - 12'\''",
  "colorName": "FENCE POST"
}
' 'https://api.rfms.online/v2/product/inventorycheck'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/product/inventorycheck',
    headers={
    "Content-Type": "application/json"
},
    json={
        "productCode": "01",
        "styleName": "FOREIGNER - SOLID - 12'",
        "colorName": "FENCE POST"
}
)

print(response.json())
```

#### Response Examples

**Check Available Inventory** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `455`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": [
    {
      "storeId": 32,
      "productCode": "01",
      "styleName": "FOREIGNER - SOLID - 12'",
      "colorName": "FENCE POST",
      "styleNumber": "28593",
      "colorNumber": "456367",
      "lotName": "22192401",
      "supplierName": "BEAULIEU OF AMERICA",
      "manufacturerName": "BEAULIEU OF AMERICA",
      "availableQuantity": 165,
      "unitPrice": 1.46,
      "saleUnits": "SF",
      "location": "",
      "availableLengthInInches": 165,
      "isOnOrder": false,
      "rollWidth": "12",
      "inventoryLink": {
        "inventoryId": 0,
        "rollNumber": "36165578"
      }
    }
  ],
  "detail": null
}
```

---

### Reserve Inventory

**POST** `https://api.rfms.online/v2/order/inventory/reserve`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | string | Yes | Example: `CG903520` |
| `lineNumber` | integer | Yes | Example: `1` |
| `inventoryLink` | object | Yes |  |
| `inventoryLink.inventoryId` | integer | Yes | Example: `39` |
| `inventoryLink.rollNumber` | string | Yes | Example: `D2001` |

**Example:**

```json
{
	"orderNumber": "CG903520",
	"lineNumber": 1,
    "inventoryLink": {
        "inventoryId": 39,
        "rollNumber": "D2001"
    }
}

```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
	"orderNumber": "CG903520",
	"lineNumber": 1,
    "inventoryLink": {
        "inventoryId": 39,
        "rollNumber": "D2001"
    }
}
' 'https://api.rfms.online/v2/order/inventory/reserve'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/inventory/reserve',
    headers={
    "Content-Type": "application/json"
},
    json={
        "orderNumber": "CG903520",
        "lineNumber": 1,
        "inventoryLink": {
                "inventoryId": 39,
                "rollNumber": "D2001"
        }
}
)

print(response.json())
```

#### Response Examples

**Reserve Inventory** ( - 0)

```json
{
  "status": "success",
  "result": "Line 1: Assigned",
  "detail": null
}
```

---

### Cut Inventory

**POST** `https://api.rfms.online/v2/order/inventory/cut`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | string | Yes | Example: `CG903520` |
| `lineNumber` | integer | Yes | Example: `1` |
| `inventoryLink` | object | Yes |  |
| `inventoryLink.inventoryId` | integer | Yes | Example: `39` |
| `inventoryLink.rollNumber` | string | Yes | Example: `D2001` |

**Example:**

```json
{
	"orderNumber": "CG903520",
	"lineNumber": 1,
    "inventoryLink": {
        "inventoryId": 39,
        "rollNumber": "D2001"
    }
}

```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
	"orderNumber": "CG903520",
	"lineNumber": 1,
    "inventoryLink": {
        "inventoryId": 39,
        "rollNumber": "D2001"
    }
}
' 'https://api.rfms.online/v2/order/inventory/cut'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/inventory/cut',
    headers={
    "Content-Type": "application/json"
},
    json={
        "orderNumber": "CG903520",
        "lineNumber": 1,
        "inventoryLink": {
                "inventoryId": 39,
                "rollNumber": "D2001"
        }
}
)

print(response.json())
```

---

### Stage Lines

**POST** `https://api.rfms.online/v2/order/inventory/stage`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | string | Yes | Example: `CG402100` |
| `orderDate` | string | Yes | Example: `07-09-2024` |
| `lines` | array | Yes |  |

**Example:**

```json
{
    "orderNumber": "CG402100",
    "orderDate": "07-09-2024",
    "lines": [5]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "orderNumber": "CG402100",
    "orderDate": "07-09-2024",
    "lines": [5]
}' 'https://api.rfms.online/v2/order/inventory/stage'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/inventory/stage',
    json={
        "orderNumber": "CG402100",
        "orderDate": "07-09-2024",
        "lines": [
                5
        ]
}
)

print(response.json())
```

#### Response Examples

**Stage Lines** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `68`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "Staged Lines Processed",
  "detail": null
}
```

---

### Deliver Lines

**POST** `https://api.rfms.online/v2/order/inventory/deliver`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | string | Yes | Example: `CG402092` |
| `orderDate` | string | Yes | Example: `06-20-2024` |
| `lines` | array | Yes |  |

**Example:**

```json
{
    "orderNumber": "CG402092",
    "orderDate": "06-20-2024",
    "lines": [3]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "orderNumber": "CG402092",
    "orderDate": "06-20-2024",
    "lines": [3]
}' 'https://api.rfms.online/v2/order/inventory/deliver'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/inventory/deliver',
    json={
        "orderNumber": "CG402092",
        "orderDate": "06-20-2024",
        "lines": [
                3
        ]
}
)

print(response.json())
```

#### Response Examples

**Deliver Lines** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `65`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "Cut Lines Processed",
  "detail": null
}
```

---

### Set Inventory Location

**POST** `https://api.rfms.online/v2/inventory/location`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `productCode` | string | Yes | Example: `01` |
| `location` | string | Yes | Example: `A-2` |
| `id` | integer | Yes | Example: `123` |

**Example:**

```json
{
    "productCode": "01",
    "location": "A-2",
    "id": 123
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "productCode": "01",
    "location": "A-2",
    "id": 123
}' 'https://api.rfms.online/v2/inventory/location'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/inventory/location',
    json={
        "productCode": "01",
        "location": "A-2",
        "id": 123
}
)

print(response.json())
```

#### Response Examples

**Set Inventory Location** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `48`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": null
}
```

---

### Get Visible Stores To Salesperson

**GET** `https://api.rfms.online/v2/stores/:id`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/stores/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/stores/:id'
)

print(response.json())
```

#### Response Examples

**Get Visible Stores - Salesperson** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
[
  {
    "storeId": 32,
    "isDefault": false
  },
  {
    "storeId": 50,
    "isDefault": true
  },
  {
    "storeId": 52,
    "isDefault": false
  },
  {
    "storeId": 53,
    "isDefault": false
  },
  {
    "storeId": 54,
    "isDefault": false
  },
  {
    "storeId": 75,
    "isDefault": false
  }
]
```

---

### Post Provider Record From Order

**POST** `https://api.rfms.online/v2/order/provider`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documentNumber` | string | Yes | Example: `CG203699` |
| `lineNumber` | integer | Yes | Example: `1` |
| `installDate` | string | Yes | Example: `2022-04-07` |
| `supplierId` | integer | Yes | Example: `71` |

**Example:**

```json
{
    "documentNumber": "CG203699",
    "lineNumber": 1,
    "installDate": "2022-04-07",
    "supplierId": 71
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "documentNumber": "CG203699",
    "lineNumber": 1,
    "installDate": "2022-04-07",
    "supplierId": 71
}' 'https://api.rfms.online/v2/order/provider'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/order/provider',
    json={
        "documentNumber": "CG203699",
        "lineNumber": 1,
        "installDate": "2022-04-07",
        "supplierId": 71
}
)

print(response.json())
```

#### Response Examples

**Post Provide Record From Order** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `48`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": null
}
```

---

### Get Suppliers

**GET** `https://api.rfms.online/v2/suppliers`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/suppliers'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/suppliers'
)

print(response.json())
```

#### Response Examples

**Get Suppliers** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `54659`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 1059,
      "name": "84 LUMBER COMPANY",
      "contactPhone": "128-8820",
      "accountNumber": "123",
      "email": ""
    },
    {
      "id": 2005,
      "name": "A AND D HOME IMPROVEMENT",
      "contactPhone": "",
      "accountNumber": "",
      "email": ""
    },
    {
      "id": 17,
      "name": "ALAGASCO",
      "contactPhone": "759-2501",
      "accountNumber": "",
      "email": ""
    },
    {
      "id": 1953,
      "name": "C & W CONTRACTING",
      "contactPhone": "468-0471",
      "accountNumber": "",
      "email": ""
    },
    {
      "id": 60,
      "name": "CABINESS",
      "contactPhone": "345-6080",
      "accountNumber": "",
      "email": ""
    },
    {
      "id": 1952,
      "name": "CAM SOLUTIONS LLC",
      "contactPhone": "639-0300",
      "accountNumber": "ALA123",
      "email": ""
    },
    {
      "id": 1495,
      "name": "CAMBRIDGE COMMERCIAL",
      "contactPhone": "800-451-1250",
      "accountNumber": "1234",
      "email": ""
    },
    {
      "id": 617,
      "name": "WZBQ-FM",
      "contactPhone": "349-3200",
      "accountNumber": "ABS",
      "email": ""
    }
  ]
}
```

---

### Get Personnel

**GET** `https://api.rfms.online/v2/personnel`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/personnel'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/personnel'
)

print(response.json())
```

#### Response Examples

**Get Personnel** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `198`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 2,
      "firstName": "CARLOS",
      "lastName": "PROVIDER"
    },
    {
      "id": 3,
      "firstName": "LINDSEY",
      "lastName": "PROVIDER"
    },
    {
      "id": 1,
      "firstName": "KURT",
      "lastName": "WILSON"
    }
  ]
}
```

---

### Create Remark

**POST** `https://api.rfms.online/v2/remark`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Example: `38166` |
| `isPublicRemark` | boolean | Yes | Example: `True` |
| `entityType` | string | Yes | Example: `Quote` |
| `remarkType` | string | Yes | Example: `INFORMATION` |
| `remark` | string | Yes | Example: `Another remark! Mark remarked at the market with marked surprise.` |

**Example:**

```json
{
    "id": 38166,
    "isPublicRemark": true,
    "entityType": "Quote",
    "remarkType": "INFORMATION",
    "remark": "Another remark! Mark remarked at the market with marked surprise."
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "id": 38166,
    "isPublicRemark": true,
    "entityType": "Quote",
    "remarkType": "INFORMATION",
    "remark": "Another remark! Mark remarked at the market with marked surprise."
}' 'https://api.rfms.online/v2/remark'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/remark',
    json={
        "id": 38166,
        "isPublicRemark": true,
        "entityType": "Quote",
        "remarkType": "INFORMATION",
        "remark": "Another remark! Mark remarked at the market with marked surprise."
}
)

print(response.json())
```

#### Response Examples

**Create Remark** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `181`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": {
    "remarkId": 2822,
    "isPublic": true,
    "remarkType": "INFORMATION",
    "remark": "Another remark! Mark remarked at the market with marked surprise."
  },
  "detail": null
}
```

---

### Get Remark Types

**GET** `https://api.rfms.online/v2/remark/types`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/remark/types'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/remark/types'
)

print(response.json())
```

#### Response Examples

**Get Remark Types** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `266`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 4,
      "type": "CUSTOMER SERVICE"
    },
    {
      "id": 5,
      "type": "DIRECT MAIL"
    },
    {
      "id": 1,
      "type": "INFORMATION"
    },
    {
      "id": 7,
      "type": "LOST - GENERAL"
    },
    {
      "id": 2,
      "type": "SALES FOLLOW UP"
    }
  ]
}
```

---

### Unlock Document

**GET** `https://api.rfms.online/v2/unlock/:id`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/unlock/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/unlock/:id'
)

print(response.json())
```

---

## Order History

*1 endpoints*

### Get Order History

**GET** `https://api.rfms.online/v2/order/history/:number`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/order/history/:number'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order/history/:number'
)

print(response.json())
```

#### Response Examples

**Get Order History** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `170`
- `Content-Type`: `application/json; charset=utf-8`
- `Content-Encoding`: `gzip`

```json
{
  "status": "success",
  "result": "OK",
  "detail": "JE100250.1"
}
```

---

## Other

*2 endpoints*

### Get Jobs Scheduled for Tomorrow

**GET** `https:///`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https:///'
```

**Python:**

```python
import requests

response = requests.get(
    'https:///'
)

print(response.json())
```

---

### New Request

**GET** `https:///`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https:///'
```

**Python:**

```python
import requests

response = requests.get(
    'https:///'
)

print(response.json())
```

---

## Reports

*2 endpoints*

### Generate Report

**POST** `https://api.rfms.online/v2/quote/report/generate`

#### Headers

| Header | Value | Description |
|--------|-------|-------------|
| `Content-Type` | `application/json` | Request header |

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documentNumber` | string | Yes | Example: `ES103271` |
| `options` | object | Yes |  |
| `options.showLogo` | boolean | Yes | Example: `True` |
| `options.storeAddress` | boolean | Yes | Example: `True` |
| `options.storeName` | boolean | Yes | Example: `True` |
| `options.showRoomPlan` | boolean | Yes | Example: `True` |
| `options.showSeams` | boolean | Yes | Example: `True` |
| `options.showGrandTotal` | boolean | Yes | Example: `True` |
| `options.showColorChip` | boolean | Yes | Example: `True` |
| `options.showQuantity` | boolean | Yes | Example: `True` |
| `options.showUnitPrice` | boolean | Yes | Example: `True` |
| `options.showLineTotal` | boolean | Yes | Example: `True` |
| `options.showApprove` | boolean | Yes | Example: `True` |
| `options.showDeliveryDate` | boolean | Yes | Example: `True` |
| `options.showPhotos` | boolean | Yes | Example: `True` |
| `options.showLineNotes` | boolean | Yes | Example: `True` |
| `options.showLineGroups` | boolean | Yes | Example: `True` |
| `options.showPayment` | boolean | Yes | Example: `True` |
| `options.showSignature` | boolean | Yes | Example: `True` |
| `options.showAuthorization` | boolean | Yes | Example: `True` |

**Example:**

```json
{
    "documentNumber": "ES103271",
    "options": {
        "showLogo": true,
        "storeAddress": true,
        "storeName": true,
        "showRoomPlan": true,
        "showSeams": true,
        "showGrandTotal": true,
        "showColorChip": true,
        "showQuantity": true,
        "showUnitPrice": true, 
        "showLineTotal": true, 
        "showApprove": true,
        "showDeliveryDate": true,
        "showPhotos": true,
        "showLineNotes": true, 
        "showLineGroups": true, 
        "showPayment": true, 
        "showSignature": true,
        "showAuthorization": true, 
        "allowAuthorization": true,
        "allowPayment": false,
        "termsToShow": ["Terms and Conditions", "Bullet Point Terms"],
        "defaultShareMessage": "Here are some options" 
    }
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -H 'Content-Type: application/json' -d '{
    "documentNumber": "ES103271",
    "options": {
        "showLogo": true,
        "storeAddress": true,
        "storeName": true,
        "showRoomPlan": true,
        "showSeams": true,
        "showGrandTotal": true,
        "showColorChip": true,
        "showQuantity": true,
        "showUnitPrice": true, 
        "showLineTotal": true, 
        "showApprove": true,
        "showDeliveryDate": true,
        "showPhotos": true,
        "showLineNotes": true, 
        "showLineGroups": true, 
        "showPayment": true, 
        "showSignature": true,
        "showAuthorization": true, 
        "allowAuthorization": true,
        "allowPayment": false,
        "termsToShow": ["Terms and Conditions", "Bullet Point Terms"],
        "defaultShareMessage": "Here are some options" 
    }
}' 'https://api.rfms.online/v2/quote/report/generate'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/quote/report/generate',
    headers={
    "Content-Type": "application/json"
},
    json={
        "documentNumber": "ES103271",
        "options": {
                "showLogo": true,
                "storeAddress": true,
                "storeName": true,
                "showRoomPlan": true,
                "showSeams": true,
                "showGrandTotal": true,
                "showColorChip": true,
                "showQuantity": true,
                "showUnitPrice": true,
                "showLineTotal": true,
                "showApprove": true,
                "showDeliveryDate": true,
                "showPhotos": true,
                "showLineNotes": true,
                "showLineGroups": true,
                "showPayment": true,
                "showSignature": true,
                "showAuthorization": true,
                "allowAuthorization": true,
                "allowPayment": false,
                "termsToShow": [
                        "Terms and Conditions",
                        "Bullet Point Terms"
                ],
                "defaultShareMessage": "Here are some options"
        }
}
)

print(response.json())
```

#### Response Examples

**Generate Report** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "https://myflooringlink.com/#/view/25cf5abb7eb047958d2756c1e28f5934",
  "detail": null
}
```

---

### Get Terms

**GET** `https://api.rfms.online/v2/report/terms`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/report/terms'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/report/terms'
)

print(response.json())
```

#### Response Examples

**Get Terms** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `659`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "storeId": "default",
      "terms": [
        "Terms and Conditions",
        "Terms",
        "TERMS",
        "New Terms",
        "Even Newer Terms",
        "Bullet Point Terms",
        "Mutiple Choice T&C"
      ]
    },
    {
      "storeId": " ",
      "terms": [
        "Terms and Conditions"
      ]
    },
    {
      "storeId": "2",
      "terms": [
        "Terms and Conditions"
      ]
    },
    {
      "storeId": "4",
      "terms": [
        "TERMS",
        "Even Newer Terms"
      ]
    },
    {
      "storeId": "5",
      "terms": [
        "default store"
      ]
    },
    {
      "storeId": "6",
      "terms": [
        "Terms and Conditions"
      ]
    },
    {
      "storeId": "9",
      "terms": [
        "Terms and Conditions",
        "Terms #2"
      ]
    },
    {
      "storeId": "A",
      "terms": [
        "Terms and Conditions",
        "Bullet Point Terms"
      ]
    },
    {
      "storeId": "B",
      "terms": [
        "Terms and Conditions"
      ]
    },
    {
      "storeId": "K",
      "terms": [
        "Terms and Conditions"
      ]
    }
  ],
  "detail": null
}
```

---

## Schedule Pro

*17 endpoints*

### Get Job

**GET** `https://api.rfms.online/v2/job/:id`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/job/:id'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/job/:id'
)

print(response.json())
```

#### Response Examples

**Get Job** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `1420`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "customerName": "SOL GUGGENHEIM",
    "depotName": "IN HOUSE                      ",
    "secondaryCrew": "",
    "timeSlot": "",
    "orderInternalNote": "",
    "orderCustomNote": "",
    "workOrderNote": "",
    "jobLock": null,
    "orderLock": null,
    "lines": [
      {
        "jobId": 17475,
        "crewName": "CREW A                        ",
        "documentNumber": "CG203671",
        "productCode": "01",
        "lineStatus": "",
        "scheduledDate": "2022-04-07",
        "orderLineNote": "",
        "woLineNote": "",
        "notes": "",
        "delete": false,
        "lineId": 183286,
        "lineNumber": 1,
        "material": "CARPET                        ",
        "styleName": "ABOVE & BEYOND - 13'2\"                                                          ",
        "colorName": "SHINE                                                                           ",
        "units": "SF    ",
        "quantity": 22,
        "scheduledStartTime": "0008:30:00",
        "scheduledEndTime": "0014:00:00"
      }
    ],
    "jobId": 17475,
    "jobName": "POST MODERN UPDATE",
    "jobNumber": "                              ",
    "documentNumber": "CG203671",
    "storeNumber": 32,
    "address": "15 GUGGENHEIM DR                                                 ",
    "address2": "",
    "city": "NOWHERE                       ",
    "state": "NE   ",
    "ZIP": "00331     ",
    "phone1": "            ",
    "phone2": "            ",
    "salesperson": "                              ",
    "jobStatus": "",
    "crewName": "CREW A                        ",
    "scheduledStart": "2022-04-01",
    "scheduledEnd": "2022-04-07",
    "notes": "",
    "skipSaturday": false,
    "skipSunday": false,
    "laborTotal": 0
  }
}
```

---

### Get All Scheduled Jobs

**GET** `https://api.rfms.online/v2/order/jobs/:number`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/order/jobs/:number'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/order/jobs/:number'
)

print(response.json())
```

#### Response Examples

**Get Scheduled Jobs** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "jobId": 17458,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG105092",
      "documentIsClaim": false,
      "address": "123",
      "address2": "",
      "city": "",
      "state": "",
      "ZIP": "",
      "phone1": "2059371144",
      "phone2": "",
      "salesperson": null,
      "jobStatus": "CONTINUED",
      "availableStatuses": null,
      "crewName": "CREW A",
      "scheduledStart": "20210617",
      "scheduledEnd": "20210622",
      "startTime": "08:00:00",
      "endTime": "17:00:00",
      "notes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">Add a new work order note here as a replacement</span></p>\n</div>\n</div>",
      "workTicketNotes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">WORK TICKET NOTE BLAH BLAH BLAH</span></p>\n</div>\n</div>",
      "certificateOfCompletion": null,
      "laborTotal": 0,
      "balanceDue": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false,
      "jobNumber": null,
      "jobNumberCaption": null,
      "lines": [
        {
          "lineId": 182860,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182861,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182862,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182863,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182864,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182865,
          "lineNumber": 1,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "AIMCO LIVING - 12'",
          "colorName": "AMERICANA",
          "quantity": 20,
          "units": "SF",
          "length": 10,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "11:00:00",
          "scheduledEndTime": "17:00:00",
          "areas": null,
          "attachedFiles": null
        }
      ],
      "attachedFiles": null
    },
    {
      "jobId": 17459,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG105092",
      "documentIsClaim": false,
      "address": "123",
      "address2": "",
      "city": "",
      "state": "",
      "ZIP": "",
      "phone1": "2059371144",
      "phone2": "",
      "salesperson": null,
      "jobStatus": "CONTINUED",
      "availableStatuses": null,
      "crewName": "CREW B",
      "scheduledStart": "20210628",
      "scheduledEnd": "20210701",
      "startTime": "08:00:00",
      "endTime": "17:00:00",
      "notes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">Add a new work order note here as a replacement</span></p>\n</div>\n</div>",
      "workTicketNotes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">Add a new work ticket note here</span></p>\n</div>\n</div>",
      "certificateOfCompletion": null,
      "laborTotal": 0,
      "balanceDue": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false,
      "jobNumber": null,
      "jobNumberCaption": null,
      "lines": [
        {
          "lineId": 182866,
          "lineNumber": 2,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BAR HARBOR",
          "quantity": 300,
          "units": "SF",
          "length": 100,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "05:00:00",
          "scheduledEndTime": "14:30:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182867,
          "lineNumber": 2,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BAR HARBOR",
          "quantity": 300,
          "units": "SF",
          "length": 100,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "05:00:00",
          "scheduledEndTime": "14:30:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182868,
          "lineNumber": 2,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BAR HARBOR",
          "quantity": 300,
          "units": "SF",
          "length": 100,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "05:00:00",
          "scheduledEndTime": "14:30:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182869,
          "lineNumber": 2,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BAR HARBOR",
          "quantity": 300,
          "units": "SF",
          "length": 100,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "05:00:00",
          "scheduledEndTime": "14:30:00",
          "areas": null,
          "attachedFiles": null
        }
      ],
      "attachedFiles": null
    },
    {
      "jobId": 17460,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG105092",
      "documentIsClaim": false,
      "address": "123",
      "address2": "",
      "city": "",
      "state": "",
      "ZIP": "",
      "phone1": "2059371144",
      "phone2": "",
      "salesperson": null,
      "jobStatus": "CONTINUED",
      "availableStatuses": null,
      "crewName": "CREW C",
      "scheduledStart": "20210704",
      "scheduledEnd": "20210708",
      "startTime": "08:00:00",
      "endTime": "17:00:00",
      "notes": "<div>\n<div>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">Add a new work order note here as a replacement</span></p>\n</div>\n</div>",
      "workTicketNotes": "<div>\n<div>\n<p style=\"margin:5pt 0pt 5pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;font-weight:bold;\">Carlos 6/29/2021, 1:33:56 PM</span></p>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">Work Ticket</span></p>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><img src=\"images\\image1.png\" width=\"740\" height=\"2\" alt=\"\"></p>\n<p style=\"margin:5pt 0pt 5pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;font-weight:bold;\">Carlos Banuelos 7/29/2021, 8:16:39 AM</span></p>\n<p style=\"margin:0pt 0pt 0pt 0pt;line-height:normal;\"><span style=\"font-family:'Times New Roman';font-size:12pt;color:#000000;;\">New Work Ticket Note</span></p>\n</div>\n</div>",
      "certificateOfCompletion": null,
      "laborTotal": 0,
      "balanceDue": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false,
      "jobNumber": null,
      "jobNumberCaption": null,
      "lines": [
        {
          "lineId": 182870,
          "lineNumber": 3,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BUCKSKIN",
          "quantity": 2400,
          "units": "SF",
          "length": 1000,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "07:00:00",
          "scheduledEndTime": "18:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182871,
          "lineNumber": 3,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BUCKSKIN",
          "quantity": 2400,
          "units": "SF",
          "length": 1000,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "07:00:00",
          "scheduledEndTime": "18:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182872,
          "lineNumber": 3,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BUCKSKIN",
          "quantity": 2400,
          "units": "SF",
          "length": 1000,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "07:00:00",
          "scheduledEndTime": "18:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182873,
          "lineNumber": 3,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BUCKSKIN",
          "quantity": 2400,
          "units": "SF",
          "length": 1000,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "07:00:00",
          "scheduledEndTime": "18:00:00",
          "areas": null,
          "attachedFiles": null
        },
        {
          "lineId": 182874,
          "lineNumber": 3,
          "lineGroup": 0,
          "material": "CARPET",
          "styleName": "ALLESANDRO II 30 - 12'",
          "colorName": "BUCKSKIN",
          "quantity": 2400,
          "units": "SF",
          "length": 1000,
          "width": 12,
          "laborTotal": 0,
          "displayColor": "FFFF68",
          "notesWorkOrder": null,
          "notesWorkTicket": "",
          "rollNumber": null,
          "scheduledStartTime": "07:00:00",
          "scheduledEndTime": "18:00:00",
          "areas": null,
          "attachedFiles": null
        }
      ],
      "attachedFiles": null
    }
  ]
}
```

---

### Get Scheduled Jobs for Crews

**GET** `https://api.rfms.online/v2/jobs/:crew`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/jobs/:crew'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/jobs/:crew'
)

print(response.json())
```

#### Response Examples

**Get Scheduled Jobs for Crews** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "jobId": 17455,
      "jobName": "BROWN, CHARLIE",
      "documentNumber": "CG105053",
      "address": "1 MAIN ST",
      "address2": "",
      "city": "BIRMINGHAM",
      "state": "AL",
      "ZIP": "",
      "phone1": "201-575-0731",
      "phone2": "",
      "salesperson": null,
      "jobStatus": "GROUT",
      "availableStatuses": null,
      "crewName": "CREW A",
      "secondaryCrewName": "",
      "scheduledStart": "20210510",
      "scheduledEnd": "20210519",
      "startTime": "08:00:00",
      "endTime": "17:00:00",
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    },
    {
      "jobId": 17458,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG105092",
      "address": "123",
      "address2": "",
      "city": "",
      "state": "",
      "ZIP": "",
      "phone1": "2059371144",
      "phone2": "",
      "salesperson": null,
      "jobStatus": "CONTINUED",
      "availableStatuses": null,
      "crewName": "CREW A",
      "secondaryCrewName": "",
      "scheduledStart": "20210617",
      "scheduledEnd": "20210622",
      "startTime": "08:00:00",
      "endTime": "17:00:00",
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    }
  ]
}
```

---

### Get Jobs For Crew - POST

**POST** `https://api.rfms.online/v2/jobs/crew`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `crew` | string | Yes | Example: `Bed, Bath, & Beyond` |

**Example:**

```json
{
    "crew": "Bed, Bath, & Beyond"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "crew": "Bed, Bath, & Beyond"
}' 'https://api.rfms.online/v2/jobs/crew'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/jobs/crew',
    json={
        "crew": "Bed, Bath, & Beyond"
}
)

print(response.json())
```

---

### Get Active Job Statuses

**GET** `https://api.rfms.online/v2/statuses`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/statuses'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/statuses'
)

print(response.json())
```

#### Response Examples

**Job Statuses** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`
- `Server`: `Microsoft-IIS/10.0`

```json
{
  "activeStatuses": [
    "CONTINUED",
    "FINISH",
    "ONE DAY COMPLETE",
    "DELIVER TO ACCLIMATE",
    "TAKE UP ONLY",
    "GROUT",
    "MOVE FURNITURE",
    "START"
  ]
}
```

---

### Change Job Status

**POST** `https://api.rfms.online/v2/job/status`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | integer | Yes | Example: `1234` |
| `status` | string | Yes | Example: `START` |

**Example:**

```json
{
    "jobId": 1234,
    "status": "START"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "jobId": 1234,
    "status": "START"
}' 'https://api.rfms.online/v2/job/status'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job/status',
    json={
        "jobId": 1234,
        "status": "START"
}
)

print(response.json())
```

---

### Add Notes To Job

**POST** `https://api.rfms.online/v2/job/notes`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `id` | integer | Yes | Example: `17459` |
| `workOrderNotes` | string | Yes | Example: `Add a new work order note` |

**Example:**

```json
{
    "id": 17459,
    "workOrderNotes": "Add a new work order note"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "id": 17459,
    "workOrderNotes": "Add a new work order note"
}' 'https://api.rfms.online/v2/job/notes'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job/notes',
    json={
        "id": 17459,
        "workOrderNotes": "Add a new work order note"
}
)

print(response.json())
```

---

### Get Crews

**GET** `https://api.rfms.online/v2/crews`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/crews'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/crews'
)

print(response.json())
```

#### Response Examples

**Get Crews** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `7080`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 94,
      "name": "A-FLOORING PROS",
      "description": "",
      "depot": "IN HOUSE",
      "nickname": "A-FLOORING PROS",
      "rfmsName": "",
      "telephone1": "",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": false,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": false
      }
    },
    {
      "id": 8,
      "name": "COLLAZO, JESUS",
      "description": "CERAMIC TILE",
      "depot": "IN HOUSE",
      "nickname": "COLLAZO/T VALENCIA/J VALENCIA",
      "rfmsName": "JESUS COLLAZO-ALVARADO",
      "telephone1": "205-562-0258",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": true,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": true
      }
    },
    {
      "id": 97,
      "name": "CREW A",
      "description": "CREW A DESCRIPTION",
      "depot": "IN HOUSE",
      "nickname": "CREW A NICKNAME",
      "rfmsName": "DON'S CARPET ONE",
      "telephone1": "205-822-4334",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": false,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": false
      }
    },
    {
      "id": 98,
      "name": "CREW B",
      "description": "CREW B DESCRIPTION",
      "depot": "IN HOUSE",
      "nickname": "CREW B NICKNAME",
      "rfmsName": "",
      "telephone1": "2052222222",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": false,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": false
      }
    },
    {
      "id": 99,
      "name": "CREW C",
      "description": "CREW C DESCRIPTION",
      "depot": "IN HOUSE",
      "nickname": "CREW C NICKNAME",
      "rfmsName": "",
      "telephone1": "2053333333",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": false,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": false
      }
    },
    {
      "id": 78,
      "name": "EVANS, JEFF",
      "description": "GENERAL",
      "depot": "IN HOUSE",
      "nickname": "EVANS/MOSELY",
      "rfmsName": "JEFFERY EVANS",
      "telephone1": "205-333-0919",
      "telephone1Description": "",
      "telephone2": "",
      "telephone2Description": "",
      "availability": {
        "Sunday": false,
        "Monday": true,
        "Tuesday": true,
        "Wednesday": true,
        "Thursday": false,
        "Friday": true,
        "Saturday": true
      }
    }
  ]
}
```

---

### Find Jobs

**POST** `https://api.rfms.online/v2/jobs/find`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `startDate` | string | Yes | Example: `01-01-2017` |
| `endDate` | string | Yes | Example: `02-15-2022` |
| `scheduledStartDate` | string | Yes | Example: `01-01-2017` |
| `scheduledEndDate` | string | Yes | Example: `03-10-2022` |
| `installStartDate` | string | Yes | Example: `01-01-2022` |
| `installEndDate` | string | Yes | Example: `0401-2022` |
| `crews` | array | Yes |  |
| `secondaryCrews` | array | Yes |  |
| `jobStatus` | array | Yes |  |
| `recordStatus` | string | Yes | Example: `Both` |

**Example:**

```json
{
    "startDate": "01-01-2017",
    "endDate": "02-15-2022",
    "scheduledStartDate": "01-01-2017",
    "scheduledEndDate": "03-10-2022",
    "installStartDate": "01-01-2022",
    "installEndDate": "0401-2022",
    "crews": ["EVANS, TONY"],
    "secondaryCrews": ["SLEDGE, GLENN"],
    "jobStatus": ["Continued"],
    "recordStatus": "Both"
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "startDate": "01-01-2017",
    "endDate": "02-15-2022",
    "scheduledStartDate": "01-01-2017",
    "scheduledEndDate": "03-10-2022",
    "installStartDate": "01-01-2022",
    "installEndDate": "0401-2022",
    "crews": ["EVANS, TONY"],
    "secondaryCrews": ["SLEDGE, GLENN"],
    "jobStatus": ["Continued"],
    "recordStatus": "Both"
}' 'https://api.rfms.online/v2/jobs/find'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/jobs/find',
    json={
        "startDate": "01-01-2017",
        "endDate": "02-15-2022",
        "scheduledStartDate": "01-01-2017",
        "scheduledEndDate": "03-10-2022",
        "installStartDate": "01-01-2022",
        "installEndDate": "0401-2022",
        "crews": [
                "EVANS, TONY"
        ],
        "secondaryCrews": [
                "SLEDGE, GLENN"
        ],
        "jobStatus": [
                "Continued"
        ],
        "recordStatus": "Both"
}
)

print(response.json())
```

#### Response Examples

**Find Jobs** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `2466`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": [
    {
      "jobId": 17430,
      "jobName": "",
      "documentNumber": "CG003776",
      "address": "                                                                 ",
      "address2": "",
      "city": "                              ",
      "state": "     ",
      "ZIP": "          ",
      "phone1": "            ",
      "phone2": "205-926-9988",
      "salesperson": null,
      "jobStatus": "",
      "availableStatuses": null,
      "crewName": "EVANS, TONY                   ",
      "secondaryCrewName": "SLEDGE, GLENN",
      "scheduledStart": "20201109",
      "scheduledEnd": "20201109",
      "startTime": "MIXED                         ",
      "endTime": null,
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    },
    {
      "jobId": 17431,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG003773",
      "address": "123 TEST AVE                                                     ",
      "address2": "",
      "city": "SAN DIEGO                     ",
      "state": "CA   ",
      "ZIP": "92026     ",
      "phone1": "2051234567  ",
      "phone2": "            ",
      "salesperson": null,
      "jobStatus": "",
      "availableStatuses": null,
      "crewName": "EVANS, TONY                   ",
      "secondaryCrewName": "SLEDGE, GLENN",
      "scheduledStart": "20201117",
      "scheduledEnd": "20201126",
      "startTime": "MIXED                         ",
      "endTime": null,
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    }
  ],
  "detail": [
    {
      "jobId": 17430,
      "jobName": "",
      "documentNumber": "CG003776",
      "address": "                                                                 ",
      "address2": "",
      "city": "                              ",
      "state": "     ",
      "ZIP": "          ",
      "phone1": "            ",
      "phone2": "205-926-9988",
      "salesperson": null,
      "jobStatus": "",
      "availableStatuses": null,
      "crewName": "EVANS, TONY                   ",
      "secondaryCrewName": "SLEDGE, GLENN",
      "scheduledStart": "20201109",
      "scheduledEnd": "20201109",
      "startTime": "MIXED                         ",
      "endTime": null,
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    },
    {
      "jobId": 17431,
      "jobName": "BANUELOS, CARLOS",
      "documentNumber": "CG003773",
      "address": "123 TEST AVE                                                     ",
      "address2": "",
      "city": "SAN DIEGO                     ",
      "state": "CA   ",
      "ZIP": "92026     ",
      "phone1": "2051234567  ",
      "phone2": "            ",
      "salesperson": null,
      "jobStatus": "",
      "availableStatuses": null,
      "crewName": "EVANS, TONY                   ",
      "secondaryCrewName": "SLEDGE, GLENN",
      "scheduledStart": "20201117",
      "scheduledEnd": "20201126",
      "startTime": "MIXED                         ",
      "endTime": null,
      "laborTotal": 0,
      "storeNumber": 0,
      "skipSaturday": false,
      "skipSunday": false
    }
  ]
}
```

---

### Create Job From Order

**POST** `https://api.rfms.online/v2/job/create`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `orderNumber` | integer | Yes | Example: `83818` |
| `orderLines` | array | Yes |  |

**Example:**

```json
{
    "orderNumber": 83818,
    "orderLines": [2478]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "orderNumber": 83818,
    "orderLines": [2478]
}' 'https://api.rfms.online/v2/job/create'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job/create',
    json={
        "orderNumber": 83818,
        "orderLines": [
                2478
        ]
}
)

print(response.json())
```

#### Response Examples

**Create Job From Order** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `67`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "CG203515",
  "detail": {
    "docId": "17462"
  }
}
```

---

### Create Job

**POST** `https://api.rfms.online/v2/job`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobName` | string | Yes | Example: `Post Modern Designs` |
| `jobNumber` | string | Yes | Example: `ABC123` |
| `documentNumber` | string | Yes | Example: `CG203671` |
| `storeNumber` | integer | Yes | Example: `32` |
| `address` | string | Yes | Example: `14 Vassar Dr` |
| `address2` | string | Yes | Example: `Block 40` |
| `city` | string | Yes | Example: `Somewhere` |
| `state` | string | Yes | Example: `NE` |
| `zip` | string | Yes | Example: `00331` |
| `phone1` | string | Yes | Example: `002-343-2214` |
| `phone2` | string | Yes | Example: `893-222-2461` |
| `salesperson` | string | Yes | Example: `Ray Stata` |
| `crewName` | string | Yes | Example: `CREW A` |
| `secondaryCrew` | string | Yes | Example: `CREW B` |
| `unassigned` | boolean | Yes |  |
| `depotName` | string | Yes | Example: `IN HOUSE` |
| `scheduledStart` | string | Yes | Example: `2022-04-05` |
| `scheduledEnd` | string | Yes | Example: `2022-04-07` |
| `customerName` | string | Yes | Example: `Frank Gehry` |
| `notes` | string | Yes | Example: `Test notes` |

**Example:**

```json
{
    "jobName": "Post Modern Designs",
    "jobNumber": "ABC123",
    "documentNumber": "CG203671",
    "storeNumber": 32,
    "address": "14 Vassar Dr",
    "address2": "Block 40",
    "city": "Somewhere",
    "state": "NE",
    "zip": "00331",
    "phone1": "002-343-2214",
    "phone2": "893-222-2461",
    "salesperson": "Ray Stata",
    "crewName": "CREW A",
    "secondaryCrew": "CREW B",
    "unassigned": false,
    "depotName": "IN HOUSE",
    "scheduledStart": "2022-04-05",
    "scheduledEnd": "2022-04-07",
    "customerName": "Frank Gehry",
    "notes": "Test notes",
    "track1Description": "DELIVER GOODS TO ACCLIMATE",
    "track2Description": "ALTERNATE-INSURANCE CLAIM",
    "laborTotal": "3421.94",
    "lines": [
        {
            "documentNumber": "CG203671",
            "lineNumber": 1,
            "crewName": "Crew A",
            "material" : "Carpet",
            "productCode": "01",
            "styleName": "ABOVE & BEYOND - 13'2\"",
            "colorName": "SHINE",
            "units": "SF",
            "quantity": 22.0,
            "scheduledDate": "2022-04-05",
            "scheduledStartTime": "0008:30:00",
            "scheduledEndTime": "0014:00:00" ,
            "notes": "line notes"
      }
     
   ]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "jobName": "Post Modern Designs",
    "jobNumber": "ABC123",
    "documentNumber": "CG203671",
    "storeNumber": 32,
    "address": "14 Vassar Dr",
    "address2": "Block 40",
    "city": "Somewhere",
    "state": "NE",
    "zip": "00331",
    "phone1": "002-343-2214",
    "phone2": "893-222-2461",
    "salesperson": "Ray Stata",
    "crewName": "CREW A",
    "secondaryCrew": "CREW B",
    "unassigned": false,
    "depotName": "IN HOUSE",
    "scheduledStart": "2022-04-05",
    "scheduledEnd": "2022-04-07",
    "customerName": "Frank Gehry",
    "notes": "Test notes",
    "track1Description": "DELIVER GOODS TO ACCLIMATE",
    "track2Description": "ALTERNATE-INSURANCE CLAIM",
    "laborTotal": "3421.94",
    "lines": [
        {
            "documentNumber": "CG203671",
            "lineNumber": 1,
            "crewName": "Crew A",
            "material" : "Carpet",
            "productCode": "01",
            "styleName": "ABOVE & BEYOND - 13'\''2\"",
            "colorName": "SHINE",
            "units": "SF",
            "quantity": 22.0,
            "scheduledDate": "2022-04-05",
            "scheduledStartTime": "0008:30:00",
            "scheduledEndTime": "0014:00:00" ,
            "notes": "line notes"
      }
     
   ]
}' 'https://api.rfms.online/v2/job'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job',
    json={
        "jobName": "Post Modern Designs",
        "jobNumber": "ABC123",
        "documentNumber": "CG203671",
        "storeNumber": 32,
        "address": "14 Vassar Dr",
        "address2": "Block 40",
        "city": "Somewhere",
        "state": "NE",
        "zip": "00331",
        "phone1": "002-343-2214",
        "phone2": "893-222-2461",
        "salesperson": "Ray Stata",
        "crewName": "CREW A",
        "secondaryCrew": "CREW B",
        "unassigned": false,
        "depotName": "IN HOUSE",
        "scheduledStart": "2022-04-05",
        "scheduledEnd": "2022-04-07",
        "customerName": "Frank Gehry",
        "notes": "Test notes",
        "track1Description": "DELIVER GOODS TO ACCLIMATE",
        "track2Description": "ALTERNATE-INSURANCE CLAIM",
        "laborTotal": "3421.94",
        "lines": [
                {
                        "documentNumber": "CG203671",
                        "lineNumber": 1,
                        "crewName": "Crew A",
                        "material": "Carpet",
                        "productCode": "01",
                        "styleName": "ABOVE & BEYOND - 13'2\"",
                        "colorName": "SHINE",
                        "units": "SF",
                        "quantity": 22.0,
                        "scheduledDate": "2022-04-05",
                        "scheduledStartTime": "0008:30:00",
                        "scheduledEndTime": "0014:00:00",
                        "notes": "line notes"
                }
        ]
}
)

print(response.json())
```

#### Response Examples

**Create Or Update Job** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `67`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "CG203671",
  "detail": {
    "docId": "17473"
  }
}
```

**Update Job** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `67`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "CG203671",
  "detail": {
    "docId": "17475"
  }
}
```

**Create Job** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `67`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "CG203671",
  "detail": {
    "docId": "17476"
  }
}
```

**Create Job - Validation Response** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `332`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "failed",
  "result": "Error saving job",
  "detail": [
    {
      "JobCheckType": "Track1NoSelection",
      "RestrictLevel": "Warning",
      "Message": "NO SELECTION HAS BEEN MADE FOR SERVICE REASON",
      "Override": null
    },
    {
      "JobCheckType": "Track2NoSelection",
      "RestrictLevel": "Warning",
      "Message": "NO SELECTION HAS BEEN MADE FOR ALTERNATE LIST",
      "Override": null
    }
  ]
}
```

---

### Update Job

**POST** `https://api.rfms.online/v2/job`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | integer | Yes | Example: `17475` |
| `unassigned` | boolean | Yes |  |
| `lines` | array | Yes |  |
| `lines[0].lineId` | integer | Yes | Example: `183286` |
| `lines[0].documentNumber` | string | Yes | Example: `CG203671` |
| `lines[0].lineNumber` | integer | Yes | Example: `1` |

**Example:**

```json
{
    "jobId": 17475,
    "unassigned": false,
    "lines": [
        {
            "lineId": 183286,
            "documentNumber": "CG203671",
            "lineNumber": 1
        }
    ]
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "jobId": 17475,
    "unassigned": false,
    "lines": [
        {
            "lineId": 183286,
            "documentNumber": "CG203671",
            "lineNumber": 1
        }
    ]
}' 'https://api.rfms.online/v2/job'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job',
    json={
        "jobId": 17475,
        "unassigned": false,
        "lines": [
                {
                        "lineId": 183286,
                        "documentNumber": "CG203671",
                        "lineNumber": 1
                }
        ]
}
)

print(response.json())
```

---

### Post Provider Record From Job

**POST** `https://api.rfms.online/v2/job/provider`

#### Request Body

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `jobId` | integer | Yes | Example: `17475` |
| `jobLineId` | integer | Yes | Example: `183286` |

**Example:**

```json
{
    "jobId": 17475,
    "jobLineId": 183286
}
```

#### Code Examples

**cURL:**

```bash
curl -X POST -d '{
    "jobId": 17475,
    "jobLineId": 183286
}' 'https://api.rfms.online/v2/job/provider'
```

**Python:**

```python
import requests

response = requests.post(
    'https://api.rfms.online/v2/job/provider',
    json={
        "jobId": 17475,
        "jobLineId": 183286
}
)

print(response.json())
```

#### Response Examples

**Post Provider Record From Job** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `48`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": null
}
```

---

### Get Time Slots

**GET** `https://api.rfms.online/v2/timeslots`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/timeslots'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/timeslots'
)

print(response.json())
```

#### Response Examples

**Get Time Slots** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `1375`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 1,
      "slot": "MIXED",
      "startTime": "0008:00:00",
      "endTime": "0017:00:00"
    },
    {
      "id": 2,
      "slot": "MORNING",
      "startTime": "0008:00:00",
      "endTime": "0012:00:00"
    },
    {
      "id": 3,
      "slot": "AFTERNOON",
      "startTime": "0013:00:00",
      "endTime": "0017:00:00"
    },
    {
      "id": 4,
      "slot": "CONTINUED",
      "startTime": "0008:00:00",
      "endTime": "0008:30:00"
    },
    {
      "id": 5,
      "slot": "FINISH",
      "startTime": "0008:00:00",
      "endTime": "0017:00:00"
    },
    {
      "id": 6,
      "slot": "1 DAY",
      "startTime": "0008:00:00",
      "endTime": "0017:00:00"
    }
  ]
}
```

---

### Get Job Track Listings

**GET** `https://api.rfms.online/v2/job/tracklist`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/job/tracklist'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/job/tracklist'
)

print(response.json())
```

#### Response Examples

**Get Job Track Listings** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `931`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": {
    "track1Listings": [
      {
        "id": 1,
        "description": "CERAMIC REPAIR"
      },
      {
        "id": 2,
        "description": "DELIVER GOODS TO ACCLIMATE"
      },
      {
        "id": 3,
        "description": "GROUT"
      },
      {
        "id": 4,
        "description": "HARDWOOD REMOVAL"
      },
      {
        "id": 5,
        "description": "INSTALL MOULDING"
      },
      {
        "id": 6,
        "description": "MOVE FURNITURE"
      },
      {
        "id": 7,
        "description": "RUN PUNCH LIST"
      },
      {
        "id": 8,
        "description": "SLAB REPAIR"
      },
      {
        "id": 9,
        "description": "TAKE KEY"
      },
      {
        "id": 10,
        "description": "TRIP CHARGE"
      },
      {
        "id": 11,
        "description": "WARRANTY - INSTALLER"
      },
      {
        "id": 12,
        "description": "WARRANTY - STORE"
      },
      {
        "id": 13,
        "description": "WARRANTY - VENDOR"
      },
      {
        "id": 14,
        "description": "WOOD REPAIR"
      }
    ],
    "track2Listings": [
      {
        "id": 1,
        "description": "ALTERNATE-APARTMENTS"
      },
      {
        "id": 2,
        "description": "ALTERNATE-COMMERCIAL"
      },
      {
        "id": 3,
        "description": "ALTERNATE-INSURANCE CLAIM"
      },
      {
        "id": 4,
        "description": "ALTERNATE-NEW RESIDENTIAL"
      },
      {
        "id": 5,
        "description": "ALTERNATE-RETAIL"
      },
      {
        "id": 6,
        "description": "ALTERNATE-WARRANTY"
      }
    ]
  }
}
```

---

### Get Job Status Ids

**GET** `https://api.rfms.online/v2/jobstatusids`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/jobstatusids'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/jobstatusids'
)

print(response.json())
```

#### Response Examples

**Get Job Status Ids** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `345`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "status": "success",
  "result": "OK",
  "detail": [
    {
      "id": 6,
      "description": "GROUT"
    },
    {
      "id": 7,
      "description": "FINISH"
    },
    {
      "id": 9,
      "description": "START"
    },
    {
      "id": 10,
      "description": "ONE DAY COMPLETE"
    },
    {
      "id": 11,
      "description": "DELIVER TO ACCLIMATE"
    },
    {
      "id": 15,
      "description": "TAKE UP ONLY"
    },
    {
      "id": 18,
      "description": "MOVE FURNITURE"
    },
    {
      "id": 19,
      "description": "CONTINUED"
    }
  ]
}
```

---

### Get Job Types

**GET** `https://api.rfms.online/v2/jobtypes`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/jobtypes'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/jobtypes'
)

print(response.json())
```

#### Response Examples

**Get Job Types** (OK - 200)

*Response Headers:*

- `Cache-Control`: `no-cache`
- `Pragma`: `no-cache`
- `Content-Length`: `196`
- `Content-Type`: `application/json; charset=utf-8`
- `Expires`: `-1`

```json
{
  "jobTypes": [
    "CARPET",
    "WOOD",
    "VINYL",
    "VCT",
    "LAMINATES",
    "CERAMIC",
    "TAKE UP CARPET",
    "TAKE UP WOOD",
    "DELIVERY",
    "SAND/FINISH",
    "MEASURE"
  ]
}
```

---

## Store Settings

*1 endpoints*

### Sync Settings

**GET** `https://api.rfms.online/v2/cacherefresh`

#### Code Examples

**cURL:**

```bash
curl -X GET 'https://api.rfms.online/v2/cacherefresh'
```

**Python:**

```python
import requests

response = requests.get(
    'https://api.rfms.online/v2/cacherefresh'
)

print(response.json())
```

---

