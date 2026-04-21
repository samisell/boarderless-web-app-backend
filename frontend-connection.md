# Frontend API Connection Guide

This document provides instructions for frontend developers on how to connect to and interact with the `Borderless-Network` backend API.

## Base URL

All API endpoints are relative to a base URL.

*   **Development:** `http://127.0.0.1:8000/api`

For convenience in API clients like Postman, you can set a `baseURL` variable:
`{{baseURL}} = http://127.0.0.1:8000/api`

---

## Authentication

Many endpoints require authentication. To access these endpoints, you must first log in to receive a JWT `access` token. This token must be included in the `Authorization` header for all subsequent protected requests.

**Header Format:**
---

## Twilio Virtual Number Endpoints

These endpoints require authentication. See the Authentication section.

### 1. Search for Available Numbers

Searches for available U.S. mobile numbers that can be purchased.

*   **Endpoint:** `GET {{baseURL}}/twilio/search/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):** A list of available numbers.

    ```json
    [
        {
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "locality": "Elgin"
        },
        {
            "phone_number": "+15005550007",
            "friendly_name": "(500) 555-0007",
            "locality": "Elgin"
        }
    ]
    ```

---

## Wallet and Payment Endpoints

These endpoints require authentication. See the Authentication section.

### 1. Get User Wallet

Retrieves the wallet for the authenticated user.

*   **Endpoint:** `GET {{baseURL}}/payments/wallet/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    {
        "id": 1,
        "user": 1,
        "balance": "10000.00"
    }
    ```

### 2. List User Transactions

Retrieves a list of all transactions for the authenticated user.

*   **Endpoint:** `GET {{baseURL}}/payments/transactions/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    [
        {
            "id": 1,
            "wallet": 1,
            "transaction_type": "credit",
            "amount": "5000.00",
            "status": "completed",
            "payment_method": "paystack",
            "reference": "ref_xxxxxxxxxxxx",
            "created_at": "2023-10-27T12:00:00Z"
        }
    ]
    ```

### 3. Initialize Paystack Payment

Initializes a payment with Paystack to fund the user's wallet.

*   **Endpoint:** `POST {{baseURL}}/payments/paystack/initialize/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "amount": 5000
    }
    ```

*   **Success Response (200 OK):** The response from Paystack, including the authorization URL.

    ```json
    {
        "status": true,
        "message": "Authorization URL created",
        "data": {
            "authorization_url": "https://checkout.paystack.com/xxxxxxxxxxxx",
            "access_code": "xxxxxxxxxxxx",
            "reference": "ref_xxxxxxxxxxxx"
        }
    }
    ```

### 4. Verify Paystack Payment

Verifies a Paystack payment after the user has completed the transaction.

*   **Endpoint:** `GET {{baseURL}}/payments/paystack/verify/?reference=<reference>`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    {
        "message": "Payment successful",
        "balance": "15000.00"
    }
    ```

*   **Error Response (400 Bad Request):** If the payment failed or the reference is invalid.

### 5. Initialize Flutterwave Payment

Initializes a payment with Flutterwave to fund the user's wallet.

*   **Endpoint:** `POST {{baseURL}}/payments/flutterwave/initialize/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "amount": 5000,
        "redirect_url": "http://localhost:3000/wallet"
    }
    ```

*   **Success Response (200 OK):** The response from Flutterwave, including the payment link and transaction reference (`tx_ref`).

    ```json
    {
        "status": "success",
        "message": "Hosted Link",
        "data": {
            "link": "https://ravemodal.flutterwave.com/v3/hosted/pay/xxxxxxxxxxxx"
        },
        "tx_ref": "hustle-1-123"
    }
    ```

    **Note for Frontend:** If the payment link expires, you can use the `tx_ref` to re-initialize the payment without creating a new transaction. Simply make the same `POST` request to this endpoint with the original `amount` and `redirect_url`, and the backend will return a new payment link.

### 6. Verify Flutterwave Payment

Verifies a Flutterwave payment after the user has completed the transaction.

*   **Endpoint:** `GET {{baseURL}}/payments/flutterwave/verify/?transaction_id=<transaction_id>`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    {
        "message": "Payment successful",
        "balance": "20000.00"
    }
    ```

*   **Error Response (400 Bad Request):** If the payment failed or the transaction ID is invalid.

    **Note for Frontend:** If you are seeing `[object Object]` being sent as the `transaction_id`, please ensure you are correctly extracting the `transaction_id` from the redirect URL. The backend now has stricter validation and will return a `400 Bad Request` with the message `{"error": "Transaction ID is missing or invalid."}` if the `transaction_id` is not a valid integer.

*   **Error Response (500 Internal Server Error):** If there's an issue communicating with Twilio.

### 2. Purchase a Number

Purchases a specific phone number from the available list.

*   **Endpoint:** `POST {{baseURL}}/twilio/purchase/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "phone_number": "+15005550006",
        "bundle_sid": "BUxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    ```

    **Note:** The `bundle_sid` is an **optional** parameter. If not provided in the request, the system will automatically use the `bundle_sid` from the user's profile. This is required for purchasing numbers in certain countries (e.g., UK) due to regulatory requirements. It represents a "Regulatory Bundle" that verifies your identity. You can create and manage these bundles in your Twilio account console and save the SID to your profile.

*   **Success Response (201 Created):** The details of the purchased number.

    ```json
    {
        "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "phone_number": "+15005550006",
        "friendly_name": "(500) 555-0006",
        "purchased_at": "2023-10-27T10:00:00Z"
    }
    ```

*   **Error Response (400 Bad Request):** If the number is not available, invalid, or if there's a billing issue.

### 3. List User's Numbers

Retrieves a list of all Twilio numbers owned by the authenticated user.

*   **Endpoint:** `GET {{baseURL}}/twilio/my-numbers/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    [
        {
            "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "purchased_at": "2023-10-27T10:00:00Z"
        }
    ]
    ```
    ```
Authorization: Bearer <your_access_token>
```

---

## User Authentication Endpoints

### 1. Register User

Creates a new user account. The account remains inactive until the email is verified with the OTP sent to the user's email address.

*   **Endpoint:** `POST {{baseURL}}/users/register/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "a-strong-password",
        "password2": "a-strong-password"
    }
    ```

*   **Success Response (201 Created):**

    ```json
    {
        "username": "newuser",
        "email": "newuser@example.com"
    }
    ```

*   **Error Response (400 Bad Request):**

    ```json
    {
        "password": [
            "Password fields didn't match."
        ]
    }
    ```

### 2. Verify Email

Activates a user's account using the OTP sent during registration.

*   **Endpoint:** `POST {{baseURL}}/users/verify-email/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "email": "newuser@example.com",
        "otp": "123456"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "message": "Email verified successfully."
    }
    ```

*   **Error Response (400 Bad Request):**

    ```json
    {
        "error": "Invalid or expired OTP."
    }
    ```

### 3. Resend Verification OTP

Resends the One-Time Password (OTP) to a user's email if their account is not yet active.

*   **Endpoint:** `POST {{baseURL}}/users/resend-otp/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "email": "newuser@example.com"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "message": "A new OTP has been sent to your email."
    }
    ```

*   **Error Response (400 Bad Request):** If the account is already active.
*   **Error Response (404 Not Found):** If no user with that email exists.

### 3. Login User

Authenticates a user and returns JWT `access` and `refresh` tokens. The `access` token is used for authenticating subsequent requests.

*   **Endpoint:** `POST {{baseURL}}/users/login/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "email": "verifieduser@example.com",
        "password": "a-strong-password"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

*   **Error Response (401 Unauthorized):**

    ```json
    {
        "error": "Invalid credentials."
    }
    ```

### 4. Refresh Access Token

Uses a `refresh` token to obtain a new `access` token. This is used when the original access token has expired.

*   **Endpoint:** `POST {{baseURL}}/users/token/refresh/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

*   **Error Response (401 Unauthorized):** If the refresh token is invalid or expired.

### 5. Request Password Reset

Initiates the password reset process by sending an OTP to the user's registered email.

*   **Endpoint:** `POST {{baseURL}}/users/password-reset/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "email": "existinguser@example.com"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "message": "If an account with this email exists, an OTP has been sent."
    }
    ```

### 6. Confirm Password Reset

Sets a new password for the user using the OTP from the password reset request.

*   **Endpoint:** `POST {{baseURL}}/users/password-reset/confirm/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "email": "existinguser@example.com",
        "otp": "654321",
        "new_password": "a-brand-new-password"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "message": "Password has been reset successfully."
    }
    ```

### 7. Logout User

Logs out a user by blacklisting their refresh token. The user will no longer be able to use this token to get new access tokens.

*   **Endpoint:** `POST {{baseURL}}/users/logout/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

*   **Success Response (205 Reset Content):** An empty response indicating success.
*   **Error Response (400 Bad Request):** If the refresh token is invalid or missing.

### 8. Verify Token

Checks if a given token is valid. This endpoint can be used to verify an access token on the frontend before making a protected API call.

*   **Endpoint:** `POST {{baseURL}}/users/token/verify/`
*   **Headers:** `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {}
    ```

*   **Error Response (401 Unauthorized):**

    ```json
    {
        "detail": "Token is invalid or expired",
        "code": "token_not_valid"
    }
    ```

---

## Dashboard

### 1. Get User Activity

*   **Endpoint:** `GET {{baseURL}}/users/activities/`
*   **Description:** Retrieves a summary of the user's activities, including wallet balance, recent transactions, and Twilio usage.
*   **Authentication:** Required (Token-based).
*   **Permissions:** User must be authenticated.
*   **Success Response (200 OK):**

    ```json
    {
        "wallet_balance": "100.00",
        "recent_transactions": [
            {
                "id": 1,
                "transaction_type": "credit",
                "amount": "50.00",
                "status": "completed",
                "created_at": "2023-10-27T10:00:00Z"
            }
        ],
        "active_numbers": 2,
        "total_calls": 10,
        "unread_messages": 5
    }
    ```

---

## User Profile Endpoints

These endpoints require authentication. See the Authentication section.

### 1. Get User Profile

Retrieves the profile information for the currently logged-in user.

*   **Endpoint:** `GET {{baseURL}}/users/profile/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    {
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "profile_picture": "/media/profile_pics/avatar.jpg",
        "country": "Nigeria",
        "bio": "Software developer."
    }
    ```

### 2. Update User Profile

Updates the profile information for the currently logged-in user. Use `multipart/form-data` to handle file uploads.

*   **Endpoint:** `PATCH {{baseURL}}/users/profile/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: multipart/form-data`
*   **Request Body (form-data):**
    *   `first_name`: (Text) `John`
    *   `last_name`: (Text) `Doe`
    *   `country`: (Text) `Canada`
    *   `bio`: (Text) `Updated bio here.`
    *   `profile_picture`: (File) `[select a file]`
*   **Success Response (200 OK):** The response will contain the fully updated user profile object.

### 7. Update User Profile

Updates the authenticated user's profile information, including their forwarding phone number, address, gender, and date of birth.

*   **Endpoint:** `PUT {{baseURL}}/users/profile/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "phone_number": "+11234567890",
        "full_address": "123 Main St, Anytown, USA",
        "gender": "M",
        "date_of_birth": "YYYY-MM-DD",
        "bundle_sid": "BUxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "username": "testuser",
        "email": "testuser@example.com",
        "profile_picture": null,
        "country": "",
        "bio": "",
        "phone_number": "+11234567890",
        "full_address": "123 Main St, Anytown, USA",
        "gender": "M",
        "date_of_birth": "YYYY-MM-DD"
    }
    ```

*   **Error Response (400 Bad Request):** If the request body is invalid.


### 9. Send OTP

Sends a One-Time Password (OTP) to the user's registered phone number.

*   **Endpoint:** `POST {{baseURL}}/users/send-otp/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    {
        "message": "OTP sent successfully."
    }
    ```

*   **Error Response (400 Bad Request):** If the user does not have a verified phone number or an active Twilio number.
*   **Error Response (500 Internal Server Error):** If there is an issue with the Twilio API.


Allows an authenticated user to change their password by providing their old password and a new one.

*   **Endpoint:** `PUT {{baseURL}}/users/change-password/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "old_password": "current-strong-password",
        "new_password": "a-new-strong-password",
        "new_password2": "a-new-strong-password"
    }
    ```

*   **Success Response (200 OK):**

    ```json
    {
        "message": "Password updated successfully"
    }
    ```

*   **Error Response (400 Bad Request):**

    ```json
    {
        "old_password": [
            "Wrong password."
        ]
    }
    ```

---

## Twilio Virtual Number Endpoints

These endpoints require authentication. See the Authentication section.

### 1. Search for Available Numbers

Searches for available U.S. mobile numbers that can be purchased.

*   **Endpoint:** `GET {{baseURL}}/twilio/search/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):** A list of available numbers.

    ```json
    [
        {
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "locality": "Elgin"
        },
        {
            "phone_number": "+15005550007",
            "friendly_name": "(500) 555-0007",
            "locality": "Elgin"
        }
    ]
    ```

*   **Error Response (500 Internal Server Error):** If there's an issue communicating with Twilio.

### 2. Purchase a Number

Purchases a specific phone number from the available list.

*   **Endpoint:** `POST {{baseURL}}/twilio/purchase/`
*   **Headers:**
    *   `Authorization: Bearer <access_token>`
    *   `Content-Type: application/json`
*   **Request Body:**

    ```json
    {
        "phone_number": "+15005550006",
        "bundle_sid": "BUxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
    ```

    **Note:** The `bundle_sid` is an **optional** parameter. If not provided in the request, the system will automatically use the `bundle_sid` from the user's profile. This is required for purchasing numbers in certain countries (e.g., UK) due to regulatory requirements. It represents a "Regulatory Bundle" that verifies your identity. You can create and manage these bundles in your Twilio account console and save the SID to your profile.

*   **Success Response (201 Created):** The details of the purchased number.

    ```json
    {
        "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "phone_number": "+15005550006",
        "friendly_name": "(500) 555-0006",
        "purchased_at": "2023-10-27T10:00:00Z"
    }
    ```

*   **Error Response (400 Bad Request):** If the number is not available, invalid, or if there's a billing issue.

### 3. List User's Numbers

Retrieves a list of all Twilio numbers owned by the authenticated user.

*   **Endpoint:** `GET {{baseURL}}/twilio/my-numbers/`
*   **Headers:** `Authorization: Bearer <access_token>`
*   **Success Response (200 OK):**

    ```json
    [
        {
            "sid": "PNxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "phone_number": "+15005550006",
            "friendly_name": "(500) 555-0006",
            "purchased_at": "2023-10-27T10:00:00Z"
        }
    ]
    ```
    ```