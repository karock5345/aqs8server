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



# Member login API

### Request
```http
POST [Server IP or DN]/api/crm/login?app=postman&version=8.2.0&username=xxx&password=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be 'iOS' or "Android" |
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

# Member info API
### Request
```http
GET [Server IP or DN]/api/crm/info?app=postman&version=8.2.0&member_id=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be 'iOS' or "Android" |
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

# Member items API
### Request
```http
GET [Server IP or DN]/api/crm/items?app=postman&version=8.2.0&member_id=xxx&member_token=xxx
```

| Key | Type | Description |
| :--- | :--- | :--- |
| `app` | `string` | If called by mobile App it can be 'iOS' or "Android" |
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