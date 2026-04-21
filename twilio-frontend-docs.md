# Twilio API Connection Guide

This document provides instructions for frontend developers on how to connect to and interact with the Twilio-related endpoints of the `Borderless-Network` backend API.

## Base URL

All API endpoints are relative to a base URL.

*   **Development:** `http://127.0.0.1:8001/api/twilio`
*   **Production:** `https://api.yourdomain.com/api/twilio`

For convenience in API clients like Postman, you can set a `baseURL` variable:
`{{baseURL}} = http://127.0.0.1:8001/api/twilio`

---

## Authentication

All Twilio endpoints require authentication. To access these endpoints, you must first log in to receive a JWT `access` token. This token must be included in the `Authorization` header for all subsequent protected requests.

**Header Format:**
```
Authorization: Bearer <your_access_token>
```

--- 

## Call History Endpoint

### Get Call History

Retrieves the call history for the authenticated user.

- **Endpoint:** `/calls/`
- **Method:** `GET`
- **Headers:**
  - `Authorization: Bearer <access_token>`

**Success Response (200 OK):**

```json
[
    {
        "id": 1,
        "user": 1,
        "twilio_number": "+1234567890",
        "from_number": "+0987654321",
        "to_number": "+1122334455",
        "sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "status": "completed",
        "duration": 60,
        "timestamp": "2023-10-27T10:00:00Z"
    }
]
```

---

## Twilio Virtual Number Endpoints

### 1. List Countries

Retrieves a list of all supported countries where Twilio numbers can be provisioned.

*   **Endpoint:** `GET {{baseURL}}/countries/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    [
        {
            "name": "United States",
            "code": "US"
        },
        {
            "name": "Canada",
            "code": "CA"
        }
    ]
    ```

### 2. Search for Available Numbers

Searches for available mobile numbers in a specific country that can be purchased. The country is specified with a two-letter ISO country code.

*   **Endpoint:** `GET {{baseURL}}/search/?country_code=<country_code>`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Query Parameters:**
    *   `country_code` (optional, default: `US`): The two-letter ISO code of the country to search in (e.g., `US`, `CA`, `GB`).
*   **Success Response (200 OK):** A list of available numbers with their price.

    ```json
    [
        {
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "locality": "Elgin",
            "price": 1000.00
        },
        {
            "phone_number": "+15005550007",
            "friendly_name": "(500) 555-0007",
            "locality": "Elgin",
            "price": 1000.00
        }
    ]
    ```

*   **Error Response (500 Internal Server Error):** If there's an issue communicating with Twilio.

### 3. Purchase a Number (Subscription)

Purchases a specific phone number from the available list and subscribes for a chosen duration. The total price is calculated based on the monthly price and the subscription duration.

*   **Endpoint:** `POST {{baseURL}}/purchase/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "phone_number": "+15005550006",
        "months": 3
    }
    ```

    *   `months` (optional, default: `1`): The subscription duration in months. Valid options are `1`, `3`, `6`, or `12`.

*   **Success Response (201 Created):** The details of the purchased number, including the subscription end date.

    ```json
    {
        "id": 1,
        "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "phone_number": "+15005550006",
        "friendly_name": "(500) 555-0006",
        "price": "3000.00",
        "subscription_status": "active",
        "subscription_end_date": "2024-01-27T10:00:00Z",
        "purchased_at": "2023-10-27T10:00:00Z"
    }
    ```

*   **Error Response (400 Bad Request):** If the number is not available, invalid, if there's a billing issue, or if the user has insufficient balance.

### 4. List User's Numbers

Retrieves a list of all Twilio numbers owned by the authenticated user.

*   **Endpoint:** `GET {{baseURL}}/my-numbers/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    [
        {
            "id": 1,
            "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "price": "3000.00",
            "subscription_status": "active",
            "subscription_end_date": "2024-01-27T10:00:00Z",
            "purchased_at": "2023-10-27T10:00:00Z"
        }
    ]
    ```

### 5. Resubscribe to a Number

Allows a user to resubscribe to an expired or inactive number for a chosen duration. The cost of the subscription is deducted from the user's wallet.

*   **Endpoint:** `POST {{baseURL}}/resubscribe/<number_id>/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "months": 6
    }
    ```

    *   `months` (optional, default: `1`): The subscription duration in months. Valid options are `1`, `3`, `6`, or `12`.

*   **Success Response (200 OK):**

    ```json
    {
        "success": "Number resubscribed successfully."
    }
    ```

*   **Error Response (400 Bad Request):** If the number is already active or if there's insufficient balance in the user's wallet.
*   **Error Response (404 Not Found):** If the number does not exist.

### 6. Make a Call

Initiates a call between a user-owned Twilio number and a destination number. The user must own the `from_number` and have an active subscription.

*   **Endpoint:** `POST {{baseURL}}/make-call/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "from_number": "+15005550006",
        "to_number": "+11234567890"
    }
    ```

*   **Success Response (201 Created):**

    ```json
    {
        "sid": "CAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "status": "Call initiated successfully."
    }
    ```

*   **Error Response (400 Bad Request):** If `from_number` or `to_number` are missing, or if the user has insufficient balance.
*   **Error Response (403 Forbidden):** If the user does not own the `from_number` or if the subscription is inactive.
*   **Error Response (500 Internal Server Error):** If there is an issue with the Twilio API, the calling service rate is not configured, or the call fails to initiate.


### 7. Send SMS

Sends an SMS message from a user-owned Twilio number to a destination number.

*   **Endpoint:** `POST {{baseURL}}/send-sms/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "from_number": "+15005550006",
        "to_number": "+11234567890",
        "body": "Hello from your Twilio number!"
    }
    ```

*   **Success Response (201 Created):**

    ```json
    {
        "sid": "SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "status": "SMS sent successfully."
    }
    ```

*   **Error Response (400 Bad Request):** If `from_number`, `to_number`, or `body` are missing, or if the user has insufficient balance.
*   **Error Response (403 Forbidden):** If the user does not own the `from_number` or if the subscription is inactive.
*   **Error Response (500 Internal Server Error):** If there is an issue with the Twilio API, the SMS service rate is not configured, or the SMS fails to send.