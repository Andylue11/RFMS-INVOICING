# RFMS API 2 - Quick Reference Guide

Access your RFMS Business Management System data within your own application using a standard REST API.

> **Total Endpoints:** 88  
> **Categories:** 10

---

## Quick Navigation

- [API Data Pass Through](#api-data-pass-through) (1)
- [Accounts Payable](#accounts-payable) (1)
- [Authentication](#authentication) (2)
- [Customers](#customers) (10)
- [Order Entry](#order-entry) (51)
- [Order History](#order-history) (1)
- [Other](#other) (2)
- [Reports](#reports) (2)
- [Schedule Pro](#schedule-pro) (17)
- [Store Settings](#store-settings) (1)

---

## All Endpoints Summary

| Method | Endpoint | Category | Auth | Body | Description |
|--------|----------|----------|------|------|-------------|
| `GET` | `https:///` | Other |  |  |  |
| `GET` | `https:///` | Other |  |  |  |
| `POST` | `https://api.rfms.online/v2/passthrough` | API Data Pass Through |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/payables` | Accounts Payable |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/session/begin` | Authentication | ✓ | ✓ |  |
| `POST` | `https://api.rfms.online/v2/session/request` | Authentication |  | ✓ |  |
| `GET` | `https://api.rfms.online/v2/opportunities` | Customers |  |  |  |
| `GET` | `https://api.rfms.online/v2/opportunities/:stage` | Customers |  |  |  |
| `GET` | `https://api.rfms.online/v2/customer/{customerId}` | Customers |  | ✓ |  |
| `GET` | `https://api.rfms.online/v2/customers` | Customers |  |  |  |
| `GET` | `https://api.rfms.online/v2/opportunity/:id` | Customers |  |  |  |
| `GET` | `https://api.rfms.online/v2/opportunities/lastmodified` | Customers |  |  |  |
| `POST` | `https://api.rfms.online/v2/customers/find/advanced` | Customers |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/opportunity` | Customers |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/customer/` | Customers |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/customers/find` | Customers |  | ✓ |  |
| `DELETE` | `https://api.rfms.online/v2/attachment/:id` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/attachment/:id` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/estimate/:number` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/order/:number?locked=false&inc...` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/order/grossprofit/CG003607` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/payments` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/personnel` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/product/get/productcodes` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/product/etaggs` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/product/templates/:id` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/quote/:number?locked=false&inc...` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/quote/grossprofit/ES803033` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/orders/jobcosted` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/remark/types` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/suppliers` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/stores/:id` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/order` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/order/payments/:number` | Order Entry |  |  |  |
| `GET` | `https://api.rfms.online/v2/unlock/:id` | Order Entry |  |  |  |
| `POST` | `https://api.rfms.online/v2/attachment` | Order Entry |  |  |  |
| `POST` | `https://api.rfms.online/v2/claim/notes` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/notes` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/find/advanced` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/calculatetaxes` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/product/inventorycheck` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/claim/create` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/estimate/create` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/create` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/quote/create` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/remark` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/cut` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/deliver` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/quote/ES903214/export` | Order Entry |  |  |  |
| `POST` | `https://api.rfms.online/v2/estimate/find` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/find` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/product/find` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/purchaseorder/find` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/quote/find` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/attachment/paperless/doctype` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/product/get/productbundle` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/product/get` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/attachments` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/provider` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/payment` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/reserve` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/inventory/location` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/stage` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order/save/linestatus` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/estimate` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/order` | Order Entry |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/quote` | Order Entry |  | ✓ |  |
| `GET` | `https://api.rfms.online/v2/order/history/:number` | Order History |  |  |  |
| `GET` | `https://api.rfms.online/v2/report/terms` | Reports |  |  |  |
| `POST` | `https://api.rfms.online/v2/quote/report/generate` | Reports |  | ✓ |  |
| `GET` | `https://api.rfms.online/v2/statuses` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/order/jobs/:number` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/crews` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/job/:id` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/jobstatusids` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/job/tracklist` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/jobtypes` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/jobs/:crew` | Schedule Pro |  |  |  |
| `GET` | `https://api.rfms.online/v2/timeslots` | Schedule Pro |  |  |  |
| `POST` | `https://api.rfms.online/v2/job/notes` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/job/status` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/job` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/job/create` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/jobs/find` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/jobs/crew` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/job/provider` | Schedule Pro |  | ✓ |  |
| `POST` | `https://api.rfms.online/v2/job` | Schedule Pro |  | ✓ |  |
| `GET` | `https://api.rfms.online/v2/cacherefresh` | Store Settings |  |  |  |

---

## API Data Pass Through

*1 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `https://api.rfms.online/v2/passthrough` |  |

### API Pass Through

**POST** `https://api.rfms.online/v2/passthrough`

*Requires Request Body*

---

## Accounts Payable

*1 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `https://api.rfms.online/v2/payables` |  |

### Record Payables

**POST** `https://api.rfms.online/v2/payables`

*Requires Request Body*

---

## Authentication

*2 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `https://api.rfms.online/v2/session/begin` |  |
| `POST` | `https://api.rfms.online/v2/session/request` |  |

### Begin a new session

**POST** `https://api.rfms.online/v2/session/begin`

*Requires Authentication, Requires Request Body*

---

### Request Bus ID

**POST** `https://api.rfms.online/v2/session/request`

*Requires Request Body*

---

## Customers

*10 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https://api.rfms.online/v2/opportunities` |  |
| `GET` | `https://api.rfms.online/v2/opportunities/:stage` |  |
| `GET` | `https://api.rfms.online/v2/customer/{customerId}` |  |
| `GET` | `https://api.rfms.online/v2/customers` |  |
| `GET` | `https://api.rfms.online/v2/opportunity/:id` |  |
| `GET` | `https://api.rfms.online/v2/opportunities/lastmodified` |  |
| `POST` | `https://api.rfms.online/v2/customers/find/advanced` |  |
| `POST` | `https://api.rfms.online/v2/opportunity` |  |
| `POST` | `https://api.rfms.online/v2/customer/` |  |
| `POST` | `https://api.rfms.online/v2/customers/find` |  |

### Get CRM Opportunities

**GET** `https://api.rfms.online/v2/opportunities`

---

### Get CRM Opportunities  By Stage

**GET** `https://api.rfms.online/v2/opportunities/:stage`

---

### Get Customer

**GET** `https://api.rfms.online/v2/customer/{customerId}`

*Requires Request Body*

---

### Get Customer Values

**GET** `https://api.rfms.online/v2/customers`

---

### Get Opportunity

**GET** `https://api.rfms.online/v2/opportunity/:id`

---

### Get Opportunity Change Logs

**GET** `https://api.rfms.online/v2/opportunities/lastmodified`

---

### Advanced Customers Find

**POST** `https://api.rfms.online/v2/customers/find/advanced`

*Requires Request Body*

---

### Create an Opportunity

**POST** `https://api.rfms.online/v2/opportunity`

*Requires Request Body*

---

### Create or Update a Customer

**POST** `https://api.rfms.online/v2/customer/`

*Requires Request Body*

---

### Find Customers

**POST** `https://api.rfms.online/v2/customers/find`

*Requires Request Body*

---

## Order Entry

*51 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `DELETE` | `https://api.rfms.online/v2/attachment/:id` |  |
| `GET` | `https://api.rfms.online/v2/attachment/:id` |  |
| `GET` | `https://api.rfms.online/v2/estimate/:number` |  |
| `GET` | `https://api.rfms.online/v2/order/:number?locked=false&includeAttach...` |  |
| `GET` | `https://api.rfms.online/v2/order/grossprofit/CG003607` |  |
| `GET` | `https://api.rfms.online/v2/payments` |  |
| `GET` | `https://api.rfms.online/v2/personnel` |  |
| `GET` | `https://api.rfms.online/v2/product/get/productcodes` |  |
| `GET` | `https://api.rfms.online/v2/product/etaggs` |  |
| `GET` | `https://api.rfms.online/v2/product/templates/:id` |  |
| `GET` | `https://api.rfms.online/v2/quote/:number?locked=false&includeAttach...` |  |
| `GET` | `https://api.rfms.online/v2/quote/grossprofit/ES803033` |  |
| `GET` | `https://api.rfms.online/v2/orders/jobcosted` |  |
| `GET` | `https://api.rfms.online/v2/remark/types` |  |
| `GET` | `https://api.rfms.online/v2/suppliers` |  |
| `GET` | `https://api.rfms.online/v2/stores/:id` |  |
| `GET` | `https://api.rfms.online/v2/order` |  |
| `GET` | `https://api.rfms.online/v2/order/payments/:number` |  |
| `GET` | `https://api.rfms.online/v2/unlock/:id` |  |
| `POST` | `https://api.rfms.online/v2/attachment` |  |
| `POST` | `https://api.rfms.online/v2/claim/notes` |  |
| `POST` | `https://api.rfms.online/v2/order/notes` |  |
| `POST` | `https://api.rfms.online/v2/order/find/advanced` |  |
| `POST` | `https://api.rfms.online/v2/calculatetaxes` |  |
| `POST` | `https://api.rfms.online/v2/product/inventorycheck` |  |
| `POST` | `https://api.rfms.online/v2/claim/create` |  |
| `POST` | `https://api.rfms.online/v2/estimate/create` |  |
| `POST` | `https://api.rfms.online/v2/order/create` |  |
| `POST` | `https://api.rfms.online/v2/quote/create` |  |
| `POST` | `https://api.rfms.online/v2/remark` |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/cut` |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/deliver` |  |
| `POST` | `https://api.rfms.online/v2/quote/ES903214/export` |  |
| `POST` | `https://api.rfms.online/v2/estimate/find` |  |
| `POST` | `https://api.rfms.online/v2/order/find` |  |
| `POST` | `https://api.rfms.online/v2/product/find` |  |
| `POST` | `https://api.rfms.online/v2/order/purchaseorder/find` |  |
| `POST` | `https://api.rfms.online/v2/quote/find` |  |
| `POST` | `https://api.rfms.online/v2/attachment/paperless/doctype` |  |
| `POST` | `https://api.rfms.online/v2/product/get/productbundle` |  |
| `POST` | `https://api.rfms.online/v2/product/get` |  |
| `POST` | `https://api.rfms.online/v2/attachments` |  |
| `POST` | `https://api.rfms.online/v2/order/provider` |  |
| `POST` | `https://api.rfms.online/v2/payment` |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/reserve` |  |
| `POST` | `https://api.rfms.online/v2/inventory/location` |  |
| `POST` | `https://api.rfms.online/v2/order/inventory/stage` |  |
| `POST` | `https://api.rfms.online/v2/order/save/linestatus` |  |
| `POST` | `https://api.rfms.online/v2/estimate` |  |
| `POST` | `https://api.rfms.online/v2/order` |  |
| `POST` | `https://api.rfms.online/v2/quote` |  |

### Delete Attachment

**DELETE** `https://api.rfms.online/v2/attachment/:id`

---

### Get Attachment

**GET** `https://api.rfms.online/v2/attachment/:id`

---

### Get Estimate

**GET** `https://api.rfms.online/v2/estimate/:number`

---

### Get Order

**GET** `https://api.rfms.online/v2/order/:number?locked=false&includeAttachments=true`

---

### Get Order Gross Profit

**GET** `https://api.rfms.online/v2/order/grossprofit/CG003607`

---

### Get Payment Values

**GET** `https://api.rfms.online/v2/payments`

---

### Get Personnel

**GET** `https://api.rfms.online/v2/personnel`

---

### Get Product Codes

**GET** `https://api.rfms.online/v2/product/get/productcodes`

---

### Get Product ETaggs

**GET** `https://api.rfms.online/v2/product/etaggs`

---

### Get Product Templates

**GET** `https://api.rfms.online/v2/product/templates/:id`

---

### Get Quote

**GET** `https://api.rfms.online/v2/quote/:number?locked=false&includeAttachments=true`

---

### Get Quote Gross Profit

**GET** `https://api.rfms.online/v2/quote/grossprofit/ES803033`

---

### Get Recently Jobcosted Orders

**GET** `https://api.rfms.online/v2/orders/jobcosted`

---

### Get Remark Types

**GET** `https://api.rfms.online/v2/remark/types`

---

### Get Suppliers

**GET** `https://api.rfms.online/v2/suppliers`

---

### Get Visible Stores To Salesperson

**GET** `https://api.rfms.online/v2/stores/:id`

---

### Get order values

**GET** `https://api.rfms.online/v2/order`

---

### List Payments

**GET** `https://api.rfms.online/v2/order/payments/:number`

---

### Unlock Document

**GET** `https://api.rfms.online/v2/unlock/:id`

---

### Add Attachment

**POST** `https://api.rfms.online/v2/attachment`

---

### Add Notes to Claim

**POST** `https://api.rfms.online/v2/claim/notes`

*Requires Request Body*

---

### Add Notes to Order

**POST** `https://api.rfms.online/v2/order/notes`

*Requires Request Body*

---

### Advanced Order Search

**POST** `https://api.rfms.online/v2/order/find/advanced`

*Requires Request Body*

---

### Calculate Taxes

**POST** `https://api.rfms.online/v2/calculatetaxes`

*Requires Request Body*

---

### Check Available Inventory

**POST** `https://api.rfms.online/v2/product/inventorycheck`

*Requires Request Body*

---

### Create Claim

**POST** `https://api.rfms.online/v2/claim/create`

*Requires Request Body*

---

### Create Estimate

**POST** `https://api.rfms.online/v2/estimate/create`

*Requires Request Body*

---

### Create Order

**POST** `https://api.rfms.online/v2/order/create`

*Requires Request Body*

---

### Create Quote

**POST** `https://api.rfms.online/v2/quote/create`

*Requires Request Body*

---

### Create Remark

**POST** `https://api.rfms.online/v2/remark`

*Requires Request Body*

---

### Cut Inventory

**POST** `https://api.rfms.online/v2/order/inventory/cut`

*Requires Request Body*

---

### Deliver Lines

**POST** `https://api.rfms.online/v2/order/inventory/deliver`

*Requires Request Body*

---

### Export Quote to Order

**POST** `https://api.rfms.online/v2/quote/ES903214/export`

---

### Find Estimate

**POST** `https://api.rfms.online/v2/estimate/find`

*Requires Request Body*

---

### Find Orders

**POST** `https://api.rfms.online/v2/order/find`

*Requires Request Body*

---

### Find Products

**POST** `https://api.rfms.online/v2/product/find`

*Requires Request Body*

---

### Find Purchase Orders

**POST** `https://api.rfms.online/v2/order/purchaseorder/find`

*Requires Request Body*

---

### Find Quotes

**POST** `https://api.rfms.online/v2/quote/find`

*Requires Request Body*

---

### Get Paperless Document Types

**POST** `https://api.rfms.online/v2/attachment/paperless/doctype`

*Requires Request Body*

---

### Get Product Bundles

**POST** `https://api.rfms.online/v2/product/get/productbundle`

*Requires Request Body*

---

### Get Products

**POST** `https://api.rfms.online/v2/product/get`

*Requires Request Body*

---

### List Attachments

**POST** `https://api.rfms.online/v2/attachments`

*Requires Request Body*

---

### Post Provider Record From Order

**POST** `https://api.rfms.online/v2/order/provider`

*Requires Request Body*

---

### Record Payment

**POST** `https://api.rfms.online/v2/payment`

*Requires Request Body*

---

### Reserve Inventory

**POST** `https://api.rfms.online/v2/order/inventory/reserve`

*Requires Request Body*

---

### Set Inventory Location

**POST** `https://api.rfms.online/v2/inventory/location`

*Requires Request Body*

---

### Stage Lines

**POST** `https://api.rfms.online/v2/order/inventory/stage`

*Requires Request Body*

---

### Switch Line Status None To GenPO

**POST** `https://api.rfms.online/v2/order/save/linestatus`

*Requires Request Body*

---

### Update Estimate

**POST** `https://api.rfms.online/v2/estimate`

*Requires Request Body*

---

### Update Order

**POST** `https://api.rfms.online/v2/order`

*Requires Request Body*

---

### Update Quote

**POST** `https://api.rfms.online/v2/quote`

*Requires Request Body*

---

## Order History

*1 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https://api.rfms.online/v2/order/history/:number` |  |

### Get Order History

**GET** `https://api.rfms.online/v2/order/history/:number`

---

## Other

*2 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https:///` |  |
| `GET` | `https:///` |  |

### Get Jobs Scheduled for Tomorrow

**GET** `https:///`

---

### New Request

**GET** `https:///`

---

## Reports

*2 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https://api.rfms.online/v2/report/terms` |  |
| `POST` | `https://api.rfms.online/v2/quote/report/generate` |  |

### Get Terms

**GET** `https://api.rfms.online/v2/report/terms`

---

### Generate Report

**POST** `https://api.rfms.online/v2/quote/report/generate`

*Requires Request Body*

---

## Schedule Pro

*17 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https://api.rfms.online/v2/statuses` |  |
| `GET` | `https://api.rfms.online/v2/order/jobs/:number` |  |
| `GET` | `https://api.rfms.online/v2/crews` |  |
| `GET` | `https://api.rfms.online/v2/job/:id` |  |
| `GET` | `https://api.rfms.online/v2/jobstatusids` |  |
| `GET` | `https://api.rfms.online/v2/job/tracklist` |  |
| `GET` | `https://api.rfms.online/v2/jobtypes` |  |
| `GET` | `https://api.rfms.online/v2/jobs/:crew` |  |
| `GET` | `https://api.rfms.online/v2/timeslots` |  |
| `POST` | `https://api.rfms.online/v2/job/notes` |  |
| `POST` | `https://api.rfms.online/v2/job/status` |  |
| `POST` | `https://api.rfms.online/v2/job` |  |
| `POST` | `https://api.rfms.online/v2/job/create` |  |
| `POST` | `https://api.rfms.online/v2/jobs/find` |  |
| `POST` | `https://api.rfms.online/v2/jobs/crew` |  |
| `POST` | `https://api.rfms.online/v2/job/provider` |  |
| `POST` | `https://api.rfms.online/v2/job` |  |

### Get Active Job Statuses

**GET** `https://api.rfms.online/v2/statuses`

---

### Get All Scheduled Jobs

**GET** `https://api.rfms.online/v2/order/jobs/:number`

---

### Get Crews

**GET** `https://api.rfms.online/v2/crews`

---

### Get Job

**GET** `https://api.rfms.online/v2/job/:id`

---

### Get Job Status Ids

**GET** `https://api.rfms.online/v2/jobstatusids`

---

### Get Job Track Listings

**GET** `https://api.rfms.online/v2/job/tracklist`

---

### Get Job Types

**GET** `https://api.rfms.online/v2/jobtypes`

---

### Get Scheduled Jobs for Crews

**GET** `https://api.rfms.online/v2/jobs/:crew`

---

### Get Time Slots

**GET** `https://api.rfms.online/v2/timeslots`

---

### Add Notes To Job

**POST** `https://api.rfms.online/v2/job/notes`

*Requires Request Body*

---

### Change Job Status

**POST** `https://api.rfms.online/v2/job/status`

*Requires Request Body*

---

### Create Job

**POST** `https://api.rfms.online/v2/job`

*Requires Request Body*

---

### Create Job From Order

**POST** `https://api.rfms.online/v2/job/create`

*Requires Request Body*

---

### Find Jobs

**POST** `https://api.rfms.online/v2/jobs/find`

*Requires Request Body*

---

### Get Jobs For Crew - POST

**POST** `https://api.rfms.online/v2/jobs/crew`

*Requires Request Body*

---

### Post Provider Record From Job

**POST** `https://api.rfms.online/v2/job/provider`

*Requires Request Body*

---

### Update Job

**POST** `https://api.rfms.online/v2/job`

*Requires Request Body*

---

## Store Settings

*1 endpoints*

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `https://api.rfms.online/v2/cacherefresh` |  |

### Sync Settings

**GET** `https://api.rfms.online/v2/cacherefresh`

---

## Authentication

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
