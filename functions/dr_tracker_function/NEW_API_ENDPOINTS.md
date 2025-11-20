# Updated API Endpoints Documentation

## Overview
This document describes the newly implemented UUID-based CRUD operations for the **Prescription** and **PrescribedMedicine** tables in the DRTracker backend.

---

## 🔹 Prescription APIs (UUID-based)

### 1. Save Prescription (Atomic - CREATE or UPDATE)
**Endpoint:** `POST /prescription/save`

**Description:**  
Atomically saves a prescription with its medicines in a single operation. Supports both creating new prescriptions and updating existing ones.

**Request Body:**
```json
{
  "UUID": "optional-prescription-uuid-if-editing",
  "PatientUUID": "patient-uuid-here (required)",
  "OutsideMedicines": "Vitamin supplements",
  "CurrentSymptoms": "Fever, cough",
  "fees": "500",
  "medicines": [
    {
      "ROWID": "optional-rowid-if-editing-existing-medicine",
      "MedicineName": "Paracetamol 500mg",
      "frequency": "Twice daily",
      "Duration": "5 days",
      "timing": "After food"
    },
    {
      "ROWID": null,
      "MedicineName": "Cough syrup",
      "frequency": "Thrice daily",
      "Duration": "7 days",
      "timing": "Before food"
    }
  ],
  "deletedMedicineRowIds": [12345, 67890]
}
```

**Request Fields:**
- `UUID` (optional): If provided, updates existing prescription; if null/missing, creates new one
- `PatientUUID` (required): Reference to patient
- `OutsideMedicines` (optional): External medicines not in stock
- `CurrentSymptoms` (optional): Patient's symptoms
- `fees` (optional): Consultation/prescription fees
- `medicines` (required): Array of medicine objects
  - `ROWID` (optional): If provided, updates existing medicine; if null, creates new one
  - `MedicineName`, `frequency`, `Duration`, `timing`: Medicine details
- `deletedMedicineRowIds` (optional): Array of medicine ROWIDs to delete

**Response (Success):**
```json
{
  "status": "success",
  "data": {
    "UUID": "prescription-uuid",
    "PatientUUID": "patient-uuid-here",
    "OutsideMedicines": "Vitamin supplements",
    "CurrentSymptoms": "Fever, cough",
    "fees": "500",
    "medicines": [
      {
        "ROWID": "1234567890",
        "MedicineName": "Paracetamol 500mg",
        "frequency": "Twice daily",
        "Duration": "5 days",
        "timing": "After food"
      },
      {
        "ROWID": "1234567891",
        "MedicineName": "Cough syrup",
        "frequency": "Thrice daily",
        "Duration": "7 days",
        "timing": "Before food"
      }
    ]
  }
}
```

**Response (Failure):**
```json
{
  "status": "failure",
  "error": "Human readable error message",
  "details": "Additional error details"
}
```

**Atomicity Guarantee:**
- **CREATE mode**: If any medicine insert fails, the entire prescription and all medicines are rolled back
- **UPDATE mode**: All updates are applied; if any fails, appropriate error is returned
- No partial data will be left in the database on failure

**Notes:**
- Validates that PatientUUID exists before creating/updating
- Generates UUID server-side for new prescriptions
- `medicines` must be an array (can be empty)
- Returns 400 if PatientUUID is missing or patient not found
- Returns 404 if updating and prescription UUID not found

---

### 2. Create Prescription
**Endpoint:** `POST /prescription/add`

**Request Body:**
```json
{
  "PatientUUID": "string (required)",
  "OutsideMedicines": "text (optional)",
  "CurrentSymptoms": "text (optional)",
  "fees": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "UUID": "generated-uuid-string"
  }
}
```

**Notes:**
- Generates a new UUID for the prescription
- Validates that the referenced Patient exists by UUID
- Returns 400 if PatientUUID is missing or patient not found

---

### 3. Get All Prescriptions
**Endpoint:** `GET /prescription/all`

**Query Parameters:**
- `page` (optional, default: 1)
- `perPage` (optional, default: 50)

**Response:**
```json
{
  "status": "success",
  "data": {
    "prescriptions": [
      {
        "ROWID": "number",
        "UUID": "string",
        "PatientUUID": "string",
        "OutsideMedicines": "text",
        "CurrentSymptoms": "text",
        "fees": "string",
        "CREATEDTIME": "timestamp"
      }
    ],
    "hasMore": boolean,
    "page": number,
    "perPage": number,
    "total": number
  }
}
```

---

### 4. Get Single Prescription by UUID
**Endpoint:** `GET /prescription/get/:uuid`

**Path Parameters:**
- `uuid` - The prescription UUID

**Response:**
```json
{
  "status": "success",
  "data": {
    "prescription": {
      "ROWID": "number",
      "UUID": "string",
      "PatientUUID": "string",
      "OutsideMedicines": "text",
      "CurrentSymptoms": "text",
      "fees": "string",
      "CREATEDTIME": "timestamp"
    }
  }
}
```

**Notes:**
- Returns `prescription: null` if not found
- 400 error if UUID is missing

---

### 5. Update Prescription
**Endpoint:** `PUT /prescription/update/:uuid`

**Path Parameters:**
- `uuid` - The prescription UUID

**Request Body:**
```json
{
  "PatientUUID": "string (optional)",
  "OutsideMedicines": "text (optional)",
  "CurrentSymptoms": "text (optional)",
  "fees": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "UUID": "uuid-string"
  }
}
```

**Notes:**
- Only updates fields that are provided in the request body
- Returns 404 if prescription not found
- Returns 400 if no updatable fields provided

---

### 6. Delete Prescription (with Cascade Delete)
**Endpoint:** `DELETE /prescription/delete/:uuid`

**Path Parameters:**
- `uuid` - The prescription UUID

**Response:**
```json
{
  "status": "success",
  "data": {
    "deletedRowIds": [row_id1, row_id2, ...]
  }
}
```

**Notes:**
- **Automatically deletes all linked PrescribedMedicine entries** (cascade delete)
- Returns 404 if prescription not found
- Returns 400 if UUID is missing

---

## 🔹 PrescribedMedicine APIs

### 1. Create PrescribedMedicine
**Endpoint:** `POST /prescribedmedicine/add`

**Request Body:**
```json
{
  "PrescriptionUUID": "string (required)",
  "MedicineName": "text (optional)",
  "frequency": "string (optional)",
  "Duration": "string (optional)",
  "timing": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "ROWID": "number",
    "PrescriptionUUID": "string"
  }
}
```

**Notes:**
- Validates that the referenced Prescription exists by UUID
- Returns 400 if PrescriptionUUID is missing or prescription not found

---

### 2. Get All Medicines for a Prescription
**Endpoint:** `GET /prescribedmedicine/all/:prescriptionUUID`

**Path Parameters:**
- `prescriptionUUID` - The prescription UUID

**Response:**
```json
{
  "status": "success",
  "data": {
    "prescribedMedicines": [
      {
        "ROWID": "number",
        "PrescriptionUUID": "string",
        "MedicineName": "text",
        "frequency": "string",
        "Duration": "string",
        "timing": "string",
        "CREATEDTIME": "timestamp"
      }
    ]
  }
}
```

**Notes:**
- Returns empty array if no medicines found for the prescription
- 400 error if PrescriptionUUID is missing

---

### 3. Get Single PrescribedMedicine by ROWID
**Endpoint:** `GET /prescribedmedicine/get/:rowid`

**Path Parameters:**
- `rowid` - The PrescribedMedicine ROWID

**Response:**
```json
{
  "status": "success",
  "data": {
    "prescribedMedicine": {
      "ROWID": "number",
      "PrescriptionUUID": "string",
      "MedicineName": "text",
      "frequency": "string",
      "Duration": "string",
      "timing": "string",
      "CREATEDTIME": "timestamp"
    }
  }
}
```

**Notes:**
- Returns `prescribedMedicine: null` if not found
- 400 error if ROWID is missing

---

### 4. Update PrescribedMedicine
**Endpoint:** `PUT /prescribedmedicine/update/:rowid`

**Path Parameters:**
- `rowid` - The PrescribedMedicine ROWID

**Request Body:**
```json
{
  "MedicineName": "text (optional)",
  "frequency": "string (optional)",
  "Duration": "string (optional)",
  "timing": "string (optional)"
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "ROWID": "number"
  }
}
```

**Notes:**
- Only updates fields that are provided in the request body
- Returns 400 if no updatable fields provided or ROWID is missing

---

### 5. Delete PrescribedMedicine
**Endpoint:** `DELETE /prescribedmedicine/delete/:rowid`

**Path Parameters:**
- `rowid` - The PrescribedMedicine ROWID

**Response:**
```json
{
  "status": "success",
  "data": {
    "deletedRowId": "number"
  }
}
```

**Notes:**
- Returns 400 if ROWID is missing

---

## 📋 Database Schema

### Prescription Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| UUID | varchar | Unique, Server-generated |
| PatientUUID | varchar | Foreign Key → Patient.UUID |
| OutsideMedicines | text | Optional |
| CurrentSymptoms | text | Optional |
| fees | varchar | Optional |
| CREATEDTIME | timestamp | Auto-generated |

### PrescribedMedicine Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| PrescriptionUUID | varchar | Foreign Key → Prescription.UUID |
| MedicineName | text | Optional |
| frequency | varchar | Optional |
| Duration | varchar | Optional |
| timing | varchar | Optional |
| CREATEDTIME | timestamp | Auto-generated |

---

## 🔐 Error Handling

All endpoints follow consistent error response format:

**Error Response:**
```json
{
  "status": "failure",
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing required fields, invalid data)
- `404` - Not Found (resource not found by UUID/ROWID)
- `409` - Conflict (duplicate entry)
- `500` - Internal Server Error

---

## 🔑 Key Features Summary

### ✅ New Atomic Save Endpoint Benefits:
1. **Single API Call** - Create/update prescription + medicines in one request
2. **True Atomicity** - All-or-nothing guarantee with automatic rollback
3. **Simplified Frontend** - No need to manage multiple sequential API calls
4. **Better UX** - Faster response time, reduced network overhead
5. **Data Consistency** - No partial saves or orphaned records
6. **Flexible Updates** - Add, update, delete medicines in single operation

### ✅ Implementation Highlights:

1. ✅ **UUID-based primary keys** for Prescription
2. ✅ **ROWID-based operations** for PrescribedMedicine (update/delete)
3. ✅ **Cascade delete** - Deleting a prescription automatically removes all linked medicines
4. ✅ **Foreign key validation** - Validates PatientUUID and PrescriptionUUID references
5. ✅ **Input sanitization** - SQL injection protection on all queries
6. ✅ **Consistent JSON responses** - Standard success/failure format
7. ✅ **Proper error codes** - HTTP status codes for different error scenarios
8. ✅ **Complete CRUD operations** - Create, Read, Update, Delete for both tables

---

## 🚀 Testing the APIs

### Example 1: Using Atomic Save (Recommended)

**Create a Complete Prescription with Medicines in ONE API Call**
```bash
curl -X POST http://localhost:3000/server/dr_tracker_function/prescription/save \
  -H "Content-Type: application/json" \
  -d '{
    "PatientUUID": "existing-patient-uuid",
    "CurrentSymptoms": "Fever, headache, body pain",
    "OutsideMedicines": "Vitamin C tablets",
    "fees": "500",
    "medicines": [
      {
        "MedicineName": "Paracetamol 500mg",
        "frequency": "Twice daily",
        "Duration": "5 days",
        "timing": "After meals"
      },
      {
        "MedicineName": "Amoxicillin 250mg",
        "frequency": "Thrice daily",
        "Duration": "7 days",
        "timing": "Before meals"
      },
      {
        "MedicineName": "Cough syrup",
        "frequency": "Twice daily",
        "Duration": "5 days",
        "timing": "After dinner"
      }
    ]
  }'
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "UUID": "abc-123-def-456",
    "PatientUUID": "existing-patient-uuid",
    "CurrentSymptoms": "Fever, headache, body pain",
    "OutsideMedicines": "Vitamin C tablets",
    "fees": "500",
    "medicines": [
      {
        "ROWID": "1234567890",
        "MedicineName": "Paracetamol 500mg",
        "frequency": "Twice daily",
        "Duration": "5 days",
        "timing": "After meals"
      },
      {
        "ROWID": "1234567891",
        "MedicineName": "Amoxicillin 250mg",
        "frequency": "Thrice daily",
        "Duration": "7 days",
        "timing": "Before meals"
      },
      {
        "ROWID": "1234567892",
        "MedicineName": "Cough syrup",
        "frequency": "Twice daily",
        "Duration": "5 days",
        "timing": "After dinner"
      }
    ]
  }
}
```

---

### Example 2: Updating an Existing Prescription

**Update prescription, modify some medicines, add new ones, and delete others**
```bash
curl -X POST http://localhost:3000/server/dr_tracker_function/prescription/save \
  -H "Content-Type: application/json" \
  -d '{
    "UUID": "abc-123-def-456",
    "PatientUUID": "existing-patient-uuid",
    "CurrentSymptoms": "Fever reduced, still coughing",
    "OutsideMedicines": "Vitamin C tablets, Steam inhalation",
    "fees": "500",
    "medicines": [
      {
        "ROWID": "1234567890",
        "MedicineName": "Paracetamol 500mg",
        "frequency": "Once daily",
        "Duration": "3 days",
        "timing": "After meals"
      },
      {
        "ROWID": "1234567892",
        "MedicineName": "Cough syrup",
        "frequency": "Twice daily",
        "Duration": "7 days",
        "timing": "After dinner"
      },
      {
        "MedicineName": "Antihistamine",
        "frequency": "Once at night",
        "Duration": "5 days",
        "timing": "Before sleep"
      }
    ],
    "deletedMedicineRowIds": ["1234567891"]
  }'
```

**What happens:**
1. Updates prescription UUID `abc-123-def-456`
2. Updates medicine ROWID `1234567890` (reduces frequency and duration)
3. Keeps medicine ROWID `1234567892` unchanged
4. Adds new medicine "Antihistamine" (no ROWID provided)
5. Deletes medicine ROWID `1234567891` (Amoxicillin)

---

### Example 3: Creating a Prescription with Medicines (Step-by-Step - Legacy Method)

**Step 1: Create a Prescription**
```bash
POST /prescription/add
{
  "PatientUUID": "existing-patient-uuid",
  "CurrentSymptoms": "Fever, headache",
  "fees": "500"
}
# Returns: {"status": "success", "data": {"UUID": "new-prescription-uuid"}}
```

**Step 2: Add Medicines to the Prescription**
```bash
POST /prescribedmedicine/add
{
  "PrescriptionUUID": "new-prescription-uuid",
  "MedicineName": "Paracetamol",
  "frequency": "Twice daily",
  "Duration": "5 days",
  "timing": "After meals"
}
# Returns: {"status": "success", "data": {"ROWID": 123, "PrescriptionUUID": "..."}}
```

**Step 3: Get All Medicines for the Prescription**
```bash
GET /prescribedmedicine/all/new-prescription-uuid
# Returns list of all medicines
```

**Step 4: Delete the Prescription (Cascade)**
```bash
DELETE /prescription/delete/new-prescription-uuid
# Deletes prescription AND all linked medicines automatically
```

---

## 📝 Migration Notes

### Changes from Old Schema:

**OLD Prescription Table:**
- Used `PatientId` as identifier
- Had `Frequency`, `Duration`, `SpecialInstruction` fields

**NEW Prescription Table:**
- Uses `UUID` as primary identifier
- Uses `PatientUUID` instead of `PatientId`
- Has `OutsideMedicines`, `CurrentSymptoms`, `fees` fields
- Removed `Frequency`, `Duration`, `SpecialInstruction` (moved to PrescribedMedicine)

**NEW PrescribedMedicine Table:**
- Separate table for medicine details
- Linked via `PrescriptionUUID`
- Contains `MedicineName`, `frequency`, `Duration`, `timing`

---

**Document Version:** 1.0  
**Last Updated:** November 2024  
**Author:** Backend Implementation Team
