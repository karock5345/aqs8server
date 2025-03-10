# Mobile APP for Admin API specification version 1.0

### Version: 1.0
- Date: 2023-09-20

# Introduction to the Mobile APP API

This readme was built from the ground-up with a JSON API that data exchange and functionality between the mobile app and the server. The API is organized around REST. Our API has predictable resource-oriented URLs, accepts form-encoded request bodies, returns JSON-encoded responses, and uses standard HTTP response codes, authentication, and verbs.

## Use Cases

1. Check server status is online or offline
2. Functionality calls to the server

## Check server status

```http
GET [Server IP or DN]/api/?app=postman&version=8.2.0
```
*** Please note that, this API no need to authentication
| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be 'iOS' or "Android" |
| `version` | `string` | Your App version. It should be start from 8.2.0 |


### Response

```javascript
{
    "msg": "API is working!",
    "aqs_version": "8.2.0"
}
```
## Authorization

All API requests require the use of a generated JWT. 

To authenticate an API request, you should provide your JWT in the `Authorization` header.

Get your JWT from the server by calling the following API


```http
POST [Server IP or DN]/api/token/
```
*** Please note that, in Postman, select `Body` and you need to set the body type to "x-www-form-urlencoded"
| Key | Type | Description |
| :--- | :--- | :--- |
| `username` | `string` | **Required**. provided by TSVD |
| `password` | `string` | **Required**. provided by TSVD |

### Response
```javascript
{
    "refresh": "eyJhbG...NrLFilpU",
    "access":  "eyJhbG...enbnRfXk"
}
```

### Refreshing JWT Tokens
```http
POST [Server IP or DN]/api/token/refresh/
```
*** Please note that, in Postman, select `Body` and you need to set the body type to "x-www-form-urlencoded"
| Key | Type | Description |
| :--- | :--- | :--- |
| `refresh` | `string` | **Required**. from `/api/token/` |


### Response
```javascript
{
    "access": "eyJhbG...enbnRfXk"
}
```

## Status Codes

| Status Code | Description |
| :--- | :--- |
| 200 | `OK` |
| 201 | `CREATED` |
| 400 | `BAD REQUEST` |
| 404 | `NOT FOUND` |
| 500 | `INTERNAL SERVER ERROR` |

## Call API with JWT

- All API requests require the use of a generated JWT.
- The `access` token is placed in the `Authorization` header of every request.
- The type of token is `Bearer`.
- The `refresh` token is used to generate a new `access` token once the previous one has expired.
- The `access` token is valid for 5 minutes. The `refresh` token is valid for 24 hours.

# API List
## Admin APP API List
### 6. Admin login API
### 7. Member items List API (Similiar to 3. Member items list API)
### 8. Member items create API
### 9. Member items read API
### 10. Member items update API
### 11. Member items delete API
### 12. Member discount List API
### 13. Member discount create API
### 14. Member discount read API
### 15. Member discount update API
### 16. Member discount delete API
### 17. Products List API
### 18. Products create API
### 19. Products read API
### 20. Products update API
### 21. Products delete API
### 22. Quotation List API
### 23. Quotation read API
### 24. Quotation Confirm API
### 25. Invoice List API
### 26. Invoice read API
### 27. Invoice Confirm API
### 28. Admin logout API
---
### 29. Supplier List API
### 30. Products Status List API
### 31. Products Category List API



# 6. Admin login API (Admin APP)
All API requests require the use of a generated JWT. 

To authenticate an API request, you should provide your JWT in the `Authorization` header.

Get your JWT from the server by calling the following API


```http
POST [Server IP or DN]/api/token/
```
*** Please note that, in Postman, select `Body` and you need to set the body type to "x-www-form-urlencoded"
| Key | Type | Description |
| :--- | :--- | :--- |
| `username` | `string` | **Required**. provided by TSVD |
| `password` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "refresh": "eyJhbG...NrLFilpU",
    "access":  "eyJhbG...enbnRfXk"
}
```
### Refreshing JWT Tokens
```http
POST [Server IP or DN]/api/token/refresh/
```
*** Please note that, in Postman, select `Body` and you need to set the body type to "x-www-form-urlencoded"
| Key | Type | Description |
| :--- | :--- | :--- |
| `refresh` | `string` | **Required**. from `/api/token/` |


### Response
```javascript
{
    "access": "eyJhbG...enbnRfXk"
}
```
# 7. Member items List API (Admin APP)
### Request
```http
GET [Server IP or DN]/api/crm/admin_items?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
        {
        "id": 1,
        "pid": 1,
        "name": "Men's Dress Shirt",
        "des": "White, Slim Fit, Size M",
        "price": 49.9,
        "dis_price": 30,
        "mp": 0
		},
		{
        "id": 2,
        "pid": 2,
        "name": "Nike Air Max Running Shoes",
        "des": "Men's, Black/Red, Size 10",
        "price": 129.9,
        "dis_price": 99,
        "mp": 1000
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```
```javascript
{
    "detail": "Given token not valid for any token type",
    "code": "token_not_valid",
    "messages": [
        {
            "token_class": "AccessToken",
            "token_type": "access",
            "message": "Token is invalid or expired"
        }
    ]
}
```

# 8. Member item create API
*** Please note that, `pid`, `name`, `des`, `price` get from `Products List API` and `dis_price`, `mp` are input by admin


### Request
```http
POST [Server IP or DN]/api/crm/admin_item_create?app=postman&version=8.2.0&pid=xxx&name=xxx&des=xxx&price=200&dis_price=xxx&mp=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `pid` | `string` | **Required**. Product ID from `Products` table |
| `name` | `string` | **Required**. Item name |
| `des` | `string` | **Required**. Item description |
| `price` | `float` | **Required**. Item price should be positive |
| `dis_price` | `float` | **Required**. Item discount price should be positive |
| `mp` | `integer` | **Required**. Item member points should be positive integer |


### Response

```javascript
{
    "status": "success",
    "msg": "Member item create Successfully!"    
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```
# 9. Member items read API
### Request
```http
GET [Server IP or DN]/api/crm/admin_items_r?app=postman&version=8.2.0&item_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `item_id` | `integer` | **Required**. Item ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 2,
        "pid": 2,
        "name": "Nike Air Max Running Shoes",
        "des": "Men's, Black/Red, Size 10",
        "price": 129.9,
        "dis_price": 99,
        "mp": 1000
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Item ID does not exist"
}
```


# 10. Member item update API
*** Please note that, `item_id`, `pid`, `name`, `des`, `price` get from `Products List API` and `dis_price`, `mp` are input by admin


### Request
```http
POST [Server IP or DN]/api/crm/admin_item_update?app=postman&version=8.2.0&item_id=xxx&pid=xxx&name=xxx&des=xxx&price=200&dis_price=xxx&mp=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `item_id` | `integer` | **Required**. Item ID |
| `pid` | `integer` | **Required**. Product ID from `Products` table |
| `name` | `string` | **Required**. Item name |
| `des` | `string` | **Required**. Item description |
| `price` | `float` | **Required**. Item price should be positive |
| `dis_price` | `float` | **Required**. Item discount price should be positive |
| `mp` | `integer` | **Required**. Item member points should be positive integer |


### Response

```javascript
{
    "status": "success",
    "msg": "Member item update Successfully!"    
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 11. Member item delete API
### Request
```http
POST [Server IP or DN]/api/crm/admin_items_del?app=postman&version=8.2.0&item_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `item_id` | `integer` | **Required**. Item ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Member item delete successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Item ID does not exist"
}
```

# 12. Member Discount list API
### Request
```http
GET [Server IP or DN]/api/crm/admin_discounts?app=postman&version=8.2.0&member_no=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_no` | `string` | **Required**. Member number from `Member login API` |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
        {
        "id": 1,
        "name": "Sliver",
        "des": "Sliver Member",
        "discount": 10,
        "terms": 30,
        "mp": 1000
		},
		{
        "id": 2,
        "name": "Gold",
        "des": "Gold Member",
        "discount": 20,
        "terms": 60,
        "mp": 2000
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 13. Member Discount create API
### Request
```http
POST [Server IP or DN]/api/crm/admin_discount_create?app=postman&version=8.2.0&name=xxx&des=xxx&terms=10&mp=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `name` | `string` | **Required**. Member Discount name |
| `des` | `string` | **Required**. Member Discount description |
| `terms` | `integer` | **Required**. Member Discount Payment terms should be 0-100 |
| `mp` | `integer` | **Required**. Member Discount member points should be positive integer |


### Response

```javascript
{
    "status": "success",
    "msg": "Member Discount create successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```
# 14. Member Discount read API
### Request
```http
GET [Server IP or DN]/api/crm/admin_discount_r?app=postman&version=8.2.0&discount_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `discount_id` | `integer` | **Required**. Discount ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 2,
        "name": "Gold",
        "des": "Gold Member",
        "discount": 20,
        "terms": 60,
        "mp": 2000
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Item ID does not exist"
}
```


# 15. Member Discount update API
### Request
```http
POST [Server IP or DN]/api/crm/admin_discount_update?app=postman&version=8.2.0&discount_id=xxx&name=xxx&des=xxx&terms=xxx&mp=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `discount_id` | `integer` | **Required**. Member Discount ID |
| `name` | `string` | **Required**. Member Discount name |
| `des` | `string` | **Required**. Member Discount description |
| `terms` | `integer` | **Required**. Member Discount Payment terms should be 0-100 |
| `mp` | `integer` | **Required**. Member Discount member points should be positive integer |

### Response

```javascript
{
    "status": "success",
    "msg": "Member item update Successfully!"    
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 16. Member Discount delete API
### Request
```http
POST [Server IP or DN]/api/crm/admin_discount_del?app=postman&version=8.2.0&discount_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `discount_id` | `integer` | **Required**. Member Discount ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Member Discount delete successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Item ID does not exist"
}
```

# 17. Products List API
### Request
```http
GET [Server IP or DN]/api/crm/admin_products_list?app=postman&version=8.2.0
```
| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |


### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "products": [
        {
        "pid":"001",
        "name": "Men's Dress Shirt",
        "des": "White, Slim Fit, Size M",
        "price": 49.9
		},
		{
        "pid":"002",
        "name": "Nike Air Max Running Shoes",
        "des": "Men's, Black/Red, Size 10",
        "price": 129.9
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 18. Products create API
*** Please note that, `cat`, `supplier`, `status` get from `category list API`, `supplier list API` and `status list API`.

```http
POST [Server IP or DN]/api/crm/admin_products_create?app=postman&version=8.2.0&name=xxx&des=xxx&cat=xxx&barcode=xxx&price=xxx&cost=xxx&tax=xxx&supplier=xxx&qty=xxx&minqty=xxx&maxqty=xxx&reorder=xxx&discount=xxx&attr=xxx&status=xxx&usernotes=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `name` | `string` | **Required**. Products name |
| `des` | `string` | **Required**. Products description |
| `cat` | `string` | **Required**. Refer to category table. Products category name |
| `barcode` | `string` | Products barcode |
| `price` | `float` | **Required**. Products price |
| `cost` | `float` | Products cost |
| `tax` | `float` | Products tax |
| `supplier` | `string` | Refer to supplier table. Products supplier ID|
| `qty` | `integer` | Products quantity |
| `minqty` | `integer` | The minimum quantity at which the system should trigger a restocking alert. |
| `maxqty` | `integer` | The maximum quantity at which the system should stop ordering or producing the product |
| `reorder` | `integer` |  A threshold level at which the system should initiate the reordering of the product. |
| `discount` | `float` | Products discount |
| `attr` | `string` | Products attribute |
| `status` | `string` | **Required**. Refer to `status` table. Indicates whether the product is active, discontinued, or out of stock. |
| `usernotes` | `string` | A field for adding internal notes or comments about the product. |


### Response

```javascript
{
    "status": "success",
    "msg": "Products create successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```
# 19. Products read API
### Request
```http
GET [Server IP or DN]/api/crm/admin_products_r?app=postman&version=8.2.0&pid=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `pid` | `string` | **Required**. Products ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "pid": "002",
        "name": "Samsung 55 TV",
        "des": "Model:Q55F\nQLED Display\n HDR",
        "cat": "TV",
        "barcode": "123456789",
        "price": 1299.9,
        "cost": 1000,
        "tax": 0,
        "supplier": "Samsung",
        "qty": 100,
        "minqty": 10,
        "maxqty": 1000,
        "reorder": 20,
        "discount": 0,
        "attr": "55\" inch",
        "status": "Active",
        "usernotes": "This is a good TV"
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Item ID does not exist"
}
```


# 20. Products update API
### Request
```http
POST [Server IP or DN]/api/crm/admin_products_update?app=postman&version=8.2.0&pid=xxx&name=xxx&des=xxx&cat=xxx&barcode=xxx&price=xxx&cost=xxx&tax=xxx&supplier=xxx&qty=xxx&minqty=xxx&maxqty=xxx&reorder=xxx&discount=xxx&attr=xxx&status=xxx&usernotes=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `pid` | `string` | Products ID |
| `name` | `string` | **Required**. Products name |
| `des` | `string` | **Required**. Products description |
| `cat` | `string` | **Required**. Refer to category table. Products category name |
| `barcode` | `string` | Products barcode |
| `price` | `float` | **Required**. Products price |
| `cost` | `float` | Products cost |
| `tax` | `float` | Products tax |
| `supplier` | `string` | Refer to supplier table. Products supplier ID|
| `qty` | `integer` | Products quantity |
| `minqty` | `integer` | The minimum quantity at which the system should trigger a restocking alert. |
| `maxqty` | `integer` | The maximum quantity at which the system should stop ordering or producing the product |
| `reorder` | `integer` |  A threshold level at which the system should initiate the reordering of the product. |
| `discount` | `float` | Products discount |
| `attr` | `string` | Products attribute |
| `status` | `string` | **Required**. Refer to `status` table. Indicates whether the product is active, discontinued, or out of stock. |
| `usernotes` | `string` | A field for adding internal notes or comments about the product. |

### Response

```javascript
{
    "status": "success",
    "msg": "Products update Successfully!"    
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 21. Products delete API
### Request
```http
POST [Server IP or DN]/api/crm/admin_products_del?app=postman&version=8.2.0&pid=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `pid` | `string` | **Required**. Products ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Products delete successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Products ID does not exist"
}
```

# 22. Quotation List API
### Request
```http
GET [Server IP or DN]/api/crm/admin_quotations_list?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 2,
        "agent": "John",
        "amount": 1299.9,
        "date": "2021-01-01",
        "confirmed": "Elton",
		},
        {
        "id": 3,
        "agent": "May",
        "amount": 11400.9,
        "date": "2021-01-01",
        "confirmed": None,
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 23. Quotation read API
### Request
```http
GET [Server IP or DN]/api/crm/admin_quotation_r?app=postman&version=8.2.0&quotation_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `quotation_id` | `integer` | **Required**. Quotation ID |

### Response

```javascript
{
   "status":"success",
   "msg":"Successfully!",
   "items":[
      {
         "id": 2,
         "quotation_no":"Q20210101-002",
         "version":1,
         "agent":"John",
         "date":"2021-01-01",
         "confirmed":"Elton",
         "confirmed_date":"2021-01-02",
         "customer_id": 1,
         "customer_co":"ABC Company",
         "customer_tel":"12345678",
         "customer_name":"John",
         "customer_email":"john@email.com",
         "customer_mobile":"12345678",
         "customer_address":"Hong Kong",
         "customer_fax":"12348567",
         "quotation_vaild_start":"2021-01-31",
         "quotation_vaild_end":"2021-02-28",
         "quotation_payment_terms":"30 days",
         "quotation_delivery_terms":"FOB Hong Kong",
         "quotation_delivery_date":"2021-02-28",
         "quotation_delivery_address":"Hong Kong",
         "products":[
            {
               "row":1,
               "pid":"001",
               "name":"Samsung 55 TV",
               "des":"Samsung 55 TV Model:Q55F\nQLED Display\n HDR",
               "qty":1,
               "price":1299.9,
               "sub":1299.9
            },
            {
               "row":2,
               "pid":"002",
               "name":"Nike Air",
               "des":"Nike Air Max Running Shoes",
               "qty":2,
               "price":129.9,
               "sub":259.8
            }
         ],
         "subtotal":1559.7,
         "tax":0,
         "discount":0,
         "amount":1559.7,
         "terms_conditions":"Provide a link or reference to the full terms and conditions associated with the quotation.",
         "remark":"This is a good quotation",
         "quotation_status":"Draft",
         "quotation_status_date":"2021-01-02",
         "followup":"This is a good quotation"
      }
   ]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Quotation ID does not exist"
}
```
*** Please note that, "quotation_status": Track the status of the quotation, such as "Draft", "Sent", "Accepted" or "Rejected"

# 24. Quotation confirm API
### Request
```http
POST [Server IP or DN]/api/crm/admin_quotation_confirm?app=postman&version=8.2.0&quotation_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `quotation_id` | `integer` | **Required**. Quotation ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Quotation confirm successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Quotation ID does not exist"
}
```

# 25. Invoice List API
### Request
```http
GET [Server IP or DN]/api/crm/admin_invoice_list?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 2,
        "agent": "John",
        "amount": 1299.9,
        "date": "2021-01-01",
        "paid": "2022-02-02",
		},
        {
        "id": 3,
        "agent": "May",
        "amount": 11400.9,
        "date": "2021-01-01",
        "paid": None,
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 26. Invoice read API
### Request
```http
GET [Server IP or DN]/api/crm/admin_invoice_r?app=postman&version=8.2.0&invoice_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `invoice_id` | `integer` | **Required**. Invoice ID |

### Response

```javascript
{
   "status":"success",
   "msg":"Successfully!",
   "items":[
      {
         "id": 2,
         "invoice_no":"Q20210101-002",
         "quotation_id": 2,
         "agent":"John",
         "date":"2021-01-01",
         "confirmed":"Elton",
         "confirmed_date":"2021-01-02",
         "customer_id": 1,
         "customer_co":"ABC Company",
         "customer_tel":"12345678",
         "customer_name":"John",
         "customer_email":"john@email.com",
         "customer_mobile":"12345678",
         "customer_address":"Hong Kong",
         "customer_fax":"12348567",
         "invoice_payment_terms":"30 days",
         "invoice_delivery_terms":"FOB Hong Kong",
         "invoice_delivery_date":"2021-02-28",
         "invoice_delivery_address":"Hong Kong",
         "products":[
            {
               "row":1,
               "pid": 1,
               "name":"Samsung 55 TV",
               "des":"Samsung 55 TV Model:Q55F\nQLED Display\n HDR",
               "qty":1,
               "price":1299.9,
               "sub":1299.9
            },
            {
               "row":2,
               "pid": 2,
               "name":"Nike Air",
               "des":"Nike Air Max Running Shoes",
               "qty":2,
               "price":129.9,
               "sub":259.8
            }
         ],
         "subtotal":1559.7,
         "tax":0,
         "discount":0,
         "amount":1559.7,
         "terms_conditions":"Provide a link or reference to the full terms and conditions associated with the quotation.",
         "remark":"This is a good quotation",
         "invoice_status":"paid",
         "invoice_status_date":"2021-01-02",
         "followup":"This is a good quotation"
      }
   ]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Invoice ID does not exist"
}
```
*** Please note that, "invoice_status": Track the status of the invoice, such as "Unpaid" or "Paid"

# 27. Quotation confirm API
### Request
```http
POST [Server IP or DN]/api/crm/admin_invoice_confirm?app=postman&version=8.2.0&invoice_id=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `invoice_id` | `integer` | **Required**. Invoice ID |

### Response

```javascript
{
    "status": "success",
    "msg": "Invoice confirm successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Invoice ID does not exist"
}
```










# 29. Supplier List API
### Request
```http
GET [Server IP or DN]/api/crm/admin_supplier_list?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 2,
        "co": "ABC Company",
        "person": "Mary",
        "tel":"12345678",
        "email":"john@email.com",
        "mobile":"12345678",
        "address":"Hong Kong",
        "fax":"12348567"
		},
        {
        "id": 3,
        "co": "DEF Company",
        "person": "Kaith",
        "tel":"12345678",
        "email":"john@email.com",
        "mobile":"12345678",
        "address":"Hong Kong",
        "fax":"12348567"
		}
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 30. Products Status List API
```http
GET [Server IP or DN]/api/crm/admin_status_list?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 1,
        "name": "Active"        
		},
        {
        "id": 2,
        "name": "Discontinued"  
		},
        {
        "id": 3,
        "name": "Out of stock"  
		}        
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```

# 31. Products Category List API
```http
GET [Server IP or DN]/api/crm/admin_category_list?app=postman&version=8.2.0
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
		{
        "id": 1,
        "name": "electronics"        
		},
        {
        "id": 2,
        "name": "clothing"  
		},
        {
        "id": 3,
        "name": "groceries"  
		}        
	]
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "User does not exist"
}
```