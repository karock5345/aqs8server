# Mobile APP for Member API specification version 1.0
### Version: 1.1
- Updated: 2024-06-13
- API 2. Member info API (Member APP), added 'member_qr' field return

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
### 6. Member verify API (backend auto send email to member email address with the link to activate the member account)
### 7. Member del API (Testing only)

# 1. Member login API (Member APP)

### Request
```http
POST [Server IP or DN]/crm/api/login/?app=postman&version=8.2.0&username=xxx&password=xxx&ccode=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `username` | `string` | **Required**. Member username provided by TSVD |
| `password` | `string` | **Required**. provided by TSVD |
| `ccode` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "status": "success",
    "msg": "Login successfully!",
    "member_no": "20000SEDOIT",
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
GET [Server IP or DN]/crm/api/info/?app=postman&version=8.2.0&member_no=xxx&member_token=xxx&ccode=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_no` | `string` | **Required**. Member number from `Member login API` |
| `member_token` | `string` | **Required**. Member Token from `Member login API` |
| `ccode` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "nickname": "Hello Kitty",
    "member_level": "Gold",
    "member_points": 1000,
    "member_qr": "http://192.168.1.22:8000/static/qr/TSVD/MEM2024002/TSVD_MEM2024002_qyHb.png"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Username or password does not exist"
}
```

# 3. Member item list API (Member APP)
### Request
```http
GET [Server IP or DN]/crm/api/items/?app=postman&version=8.2.0&member_no=xxx&member_token=xxx&member_token=xxx&ccode=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_no` | `string` | **Required**. Member number from `Member login API` |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |
| `ccode` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!",
    "items": [
        {
            "id": 1,
            "name": "Men's Dress Shirt",
            "des": "White, Slim Fit, Size M",
            "price": 49.9,
            "dis_price": 30,
            "mp": 0
		},
		{
            "id": 2,
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
POST [Server IP or DN]/crm/api/logout/?app=postman&version=8.2.0&member_no=xxx&member_token=xxx&ccode=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `member_no` | `string` | **Required**. Member number from `Member login API` |
| `member_token` | `string` | **Required**. Member ID from `Member login API` |
| `ccode` | `string` | **Required**. provided by TSVD |

### Response

```javascript
{
    "status": "success",
    "msg": "Logout successfully!",
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
POST [Server IP or DN]/crm/api/reg/?app=postman&version=8.2.0&ccode=xxx&username=xxx&password=xxx&email=xxx&mobile=xxx&nickname=xxx&gender=xxx&dob=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `version` | `string` | Your App version. It should be start from 8.2.0 |
| `ccode` | `string` | **Required**. provided by TSVD |
| `username` | `string` | **Required**. Min. 3 char |
| `password` | `string` | **Required**. Min. 8 char |
| `email` | `string` | **Required**. Valid email address |
| `mobile` | `string` | **Required**. Valid mobile number 8-digit or 8-digit with "%2B852"(+852) country code e.g. "91234567", "%2B85291234567" Hong Kong mobile phone number start digit is "9", "6", "8", "5"|
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

# 6. Member verify API (backend auto send email to member email address with the link to activate the member account) 

### When the registration is successful, the system will send an email to the member's email address. The email contains a link to activate the member's account. In development mode the verify code is 1234. 


### Request (no need jwt token, this API link is in the member email)
```http
GET [Server IP or DN]/crm/api/verify/?app=email&username=xxx&ccode=xxx&verifycode=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be `iOS` or `Android` |
| `ccode` | `string` | **Required**. provided by TSVD |
| `username` | `string` | **Required**. Min. 3 char |
| `verifycode` | `string` | **Required**. random by the system |

### Response
HTML page


# 7. Member del API (Testing only)

### Remove member from the system, this API is for testing only


### Request (no need jwt token)
```http
DELETE [Server IP or DN]/crm/api/remove/?ccode=xxx&username=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `ccode` | `string` | **Required**. provided by TSVD |
| `username` | `string` | **Required**. Min. 3 char |



### Response

```javascript
{
    "status": "success",
    "msg": "Successfully!"
}
```
Or if failed
```javascript
{
    "status": "failed",
    "msg": "Username is existing"
}
```