# Mobile APP API specification version 1.0

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
## Member APP API List
### 1. Member login API
### 2. Member info API
### 3. Member items list API
### 4. Member logout API
### 5. Member register API

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

# 1. Member login API (Member APP)

### Request
```http
POST [Server IP or DN]/api/crm/login?app=postman&version=8.2.0&username=xxx&password=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `username` | `string` | **Required**. Member username provided by TSVD |
| `password` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "status": "success",
    "msg": "Login successfully!",
    "member_id": 2,
    "member_token": "eyJhbGc...4NrLFilpU"
}
```
Or if login failed
```javascript
{
    "status": "failed",
    "msg": "Username or password does not exist"
}
```
### Notes
- The `member_token` token is valid for 24 hours. Once the token is expired, you need to call the login API again to get a new token.

# 2. Member info API (Member APP)
### Request
```http
GET [Server IP or DN]/api/crm/info?app=postman&version=8.2.0&member_id=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_id` | `string` | **Required**. Member ID from `Member login API` |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |
### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "nickname": "Hello Kitty",
    "member_level": "Gold",
    "member_points": 1000
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Username or password does not exist"
}
```

# 3. Member items API (Member APP)
### Request
```http
GET [Server IP or DN]/api/crm/items?app=postman&version=8.2.0&member_id=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_id` | `string` | **Required**. Member ID from `Member login API` |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |
### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
        {
        "name": "Men's Dress Shirt",
        "des": "White, Slim Fit, Size M",
        "price": 49.9,
        "dis_price": 30,
        "mp": 0
		},
		{
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
    "msg": "Username or password does not exist"
}
```

# 4. Member logout API (Member APP)

### Request
```http
POST [Server IP or DN]/api/crm/logout?app=postman&version=8.2.0&username=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `username` | `string` | **Required**. Member username provided by TSVD |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |

### Response

```javascript
{
    "status": "success",
    "msg": "Logout successfully!",
    "member_id": 2
}
```
Or if login failed
```javascript
{
    "status": "failed",
    "msg": "Username does not exist"
}
```
# 5. Member register API (Member APP)
### Request
```http
GET [Server IP or DN]/api/crm/info?app=postman&version=8.2.0&username=xxx&password=xxx&password2=xxx&email=xxx&mobile=xxx&nickname=xxx&gender=xxx&dob=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `username` | `string` | **Required**. Min. 4 char |
| `password` | `string` | **Required**. Min. 8 char |
| `email` | `string` | **Required**. Valid email address |
| `mobile` | `string` | **Required**. Valid mobile number |
| `nickname` | `string` | **Required**. Min. 4 char |
| `gender` | `string` | **Required**. `M` or `F` |
| `dob` | `string` | **Required**. Date of birth in `YYYY_MM_DD` format |



### Response

```javascript
{
    "status": "success",
    "msg": "Successfully! Please check your email to activate your account."
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Username is existing"
}
```

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
        "name": "Men's Dress Shirt",
        "des": "White, Slim Fit, Size M",
        "price": 49.9,
        "dis_price": 30,
        "mp": 0
		},
		{
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

# 8. Member items create API
*** Please note that, `pid`, `name`, `des`, `price` get from `Products List API` and `dis_price`, `mp` are input by admin


### Request
```http
POST [Server IP or DN]/api/crm/admin_item_create?app=postman&version=8.2.0&pid=xxx&name=xxx&des=xxx&price=200&dis_price=100&mp=1000
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `pid` | `string` | **Required**. Product ID from `Products` table |
| `name` | `string` | **Required**. Item name |
| `des` | `string` | **Required**. Item description |
| `price` | `string` | **Required**. Item price should be positive |
| `dis_price` | `string` | **Required**. Item discount price should be positive |
| `mp` | `string` | **Required**. Item member points should be positive integer |


### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
        {
        "name": "Men's Dress Shirt",
        "des": "White, Slim Fit, Size M",
        "price": 49.9,
        "dis_price": 30,
        "mp": 0
		},
		{
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
# 9. Member items read API



























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