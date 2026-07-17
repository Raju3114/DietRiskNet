# DietRiskNet API Reference Manual

This document details the REST API specifications for the **DietRiskNet** backend service.

---

## 1. Authentication System

All private endpoints require JWT authentication.
To make requests, include the `Authorization` header with a valid bearer token:
```http
Authorization: Bearer <JWT_ACCESS_TOKEN>
```
Tokens can be generated using the `/api/auth/login` or `/api/auth/register` routes. Access tokens expire after 24 hours under development presets, and refresh tokens last 7 days.

---

## 2. Authentication Endpoints

### A. Register New Patient
* **Route**: `/api/auth/register`
* **Method**: `POST`
* **Request Body** (`application/json`):
  ```json
  {
    "email": "patient@dietrisknet.org",
    "password": "securepassword123",
    "full_name": "Dr. Naveen Kumar"
  }
  ```
* **Response Payload** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user_id": 1,
    "email": "patient@dietrisknet.org",
    "full_name": "Dr. Naveen Kumar"
  }
  ```

### B. Authenticate / Sign In
* **Route**: `/api/auth/login`
* **Method**: `POST`
* **Request Body** (`application/json`):
  ```json
  {
    "email": "patient@dietrisknet.org",
    "password": "securepassword123"
  }
  ```
* **Response Payload** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user_id": 1,
    "email": "patient@dietrisknet.org",
    "full_name": "Dr. Naveen Kumar"
  }
  ```

### C. Refresh Access Token
* **Route**: `/api/auth/refresh`
* **Method**: `POST`
* **Request Body** (`application/json`):
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn..."
  }
  ```
* **Response Payload** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "user_id": 1,
    "email": "patient@dietrisknet.org",
    "full_name": "Dr. Naveen Kumar"
  }
  ```

---

## 3. Meal Diagnostics & Analytics Endpoints

### A. Upload and Analyze Food Photo
* **Route**: `/api/meals/analyze-meal`
* **Method**: `POST`
* **Authentication**: Required (Bearer Token)
* **Request Body** (`multipart/form-data`):
  * `file`: (Binary image file, e.g. `.png`, `.jpg`)
  * `notes`: (String, optional description of the meal)
* **Response Payload** (`200 OK`):
  ```json
  {
    "meal_id": 4,
    "notes": "Verification scan",
    "image_path": "/static/d7e415fb-e848-4cb5-b44c-3a3f5a11c1e5.png",
    "items": [
      {
        "name": "Sambar",
        "confidence": 0.3225,
        "x1": 10.0,
        "y1": 10.0,
        "x2": 200.0,
        "y2": 200.0,
        "weight_g": 150.0,
        "calories": 145.0,
        "carbs": 24.5,
        "protein": 6.2,
        "fats": 2.1
      }
    ],
    "nutrition": {
      "calories": 145.0,
      "carbs": 24.5,
      "protein": 6.2,
      "fats": 2.1,
      "sodium": 320.0
    },
    "dci": 0.8855,
    "dci_level": "High Consistency",
    "nis": 0.9022,
    "nis_level": "Severe Imbalance",
    "predictions": {
      "diabetes_risk": 0.0,
      "obesity_risk": 0.952,
      "hypertension_risk": 0.0,
      "deficiency_risk": 0.003
    },
    "fusion": {
      "fused_score": 0.402,
      "risk_level": "Moderate"
    },
    "recommendations": [
      {
        "category": "General Nutrition",
        "content": "Diversify your ingredients with fresh fruits, lean proteins, and leafy greens.",
        "explanation": "To balance the Severe Imbalance (NIS = 0.90), incorporate micro-nutrient dense ingredients."
      },
      {
        "category": "Obesity",
        "content": "Control your portion sizes and practice mindful eating. Increase dietary fiber to feel full longer.",
        "explanation": "Due to a forecasted Obesity Risk of 95.2%, focus on high-volume low-calorie vegetables."
      }
    ]
  }
  ```

### B. Retrieve Patient Dashboard
* **Route**: `/api/meals/dashboard`
* **Method**: `GET`
* **Authentication**: Required (Bearer Token)
* **Response Payload** (`200 OK`):
  ```json
  {
    "daily_aggregated": {
      "calories": 145.0,
      "carbs": 24.5,
      "protein": 6.2,
      "fats": 2.1
    },
    "daily_percentage_rdi": {
      "calories": 0.0725,
      "carbs": 0.0816,
      "protein": 0.1127,
      "fats": 0.0323
    },
    "dci": 0.8855,
    "dci_level": "High Consistency",
    "nis": 0.9022,
    "nis_level": "Severe Imbalance",
    "fused_risk_score": 0.402,
    "fused_risk_level": "Moderate",
    "recent_meals": [
      {
        "id": 4,
        "created_at": "2026-07-17T11:20:42.128459",
        "items_count": 1,
        "calories": 145.0,
        "risk_score": 0.402
      }
    ],
    "recommendations": [
      {
        "category": "General Nutrition",
        "content": "Diversify your ingredients with fresh fruits, lean proteins, and leafy greens.",
        "explanation": "To balance the Severe Imbalance (NIS = 0.90), incorporate micro-nutrient dense ingredients."
      }
    ]
  }
  ```

### C. Retrieve Meal History
* **Route**: `/api/meals/history`
* **Method**: `GET`
* **Authentication**: Required (Bearer Token)
* **Response Payload** (`200 OK`):
  ```json
  [
    {
      "id": 4,
      "created_at": "2026-07-17T11:20:42.128459",
      "items": [
        {
          "name": "Sambar"
        }
      ],
      "risk_score": 0.402,
      "risk_level": "Moderate",
      "calories": 145.0,
      "protein": 6.2,
      "carbs": 24.5,
      "fats": 2.1,
      "dci": 0.8855,
      "nis": 0.9022
    }
  ]
  ```

### D. Retrieve Historical Trends
* **Route**: `/api/meals/trends`
* **Method**: `GET`
* **Query Parameters**:
  * `days`: (Integer, default 30, window of tracking)
* **Authentication**: Required (Bearer Token)
* **Response Payload** (`200 OK`):
  ```json
  [
    {
      "date": "07/17",
      "calories": 145.0,
      "carbs": 24.5,
      "protein": 6.2,
      "fats": 2.1,
      "dci": 0.8855,
      "nis": 0.9022,
      "diabetes_risk": 0.0,
      "obesity_risk": 0.952,
      "hypertension_risk": 0.0,
      "deficiency_risk": 0.003
    }
  ]
  ```

---

## 4. User Profile & Settings Endpoints

### A. Retrieve Patient Demographics
* **Route**: `/api/users/profile`
* **Method**: `GET`
* **Authentication**: Required (Bearer Token)
* **Response Payload** (`200 OK`):
  ```json
  {
    "full_name": "Dr. Naveen Kumar",
    "email": "patient@dietrisknet.org",
    "settings": {
      "age": 45,
      "gender": "Male",
      "height": 175.0,
      "weight": 82.0,
      "activity_level": "Moderately Active",
      "existing_conditions": ["hypertension"]
    }
  }
  ```

### B. Update Profile Name
* **Route**: `/api/users/profile`
* **Method**: `PUT`
* **Authentication**: Required (Bearer Token)
* **Request Body** (`application/json`):
  ```json
  {
    "full_name": "Dr. Naveen Kumar"
  }
  ```
* **Response Payload** (`200 OK`):
  ```json
  {
    "full_name": "Dr. Naveen Kumar",
    "email": "patient@dietrisknet.org"
  }
  ```

### C. Update Clinical Demographics Vector
* **Route**: `/api/users/settings`
* **Method**: `PUT`
* **Authentication**: Required (Bearer Token)
* **Request Body** (`application/json`):
  ```json
  {
    "age": 45,
    "gender": "Male",
    "height": 175.0,
    "weight": 82.0,
    "activity_level": "Moderately Active",
    "existing_conditions": ["hypertension"]
  }
  ```
* **Response Payload** (`200 OK`):
  ```json
  {
    "id": 1,
    "user_id": 1,
    "age": 45,
    "gender": "Male",
    "height": 175.0,
    "weight": 82.0,
    "activity_level": "Moderately Active",
    "existing_conditions": ["hypertension"]
  }
  ```
