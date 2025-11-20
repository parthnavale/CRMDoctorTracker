# DRTracker API Endpoints

This document lists all REST API endpoints available in the DRTracker backend (`main.py`).

---

## Patient APIs

| Endpoint         | Method | Description                                 |
|------------------|--------|---------------------------------------------|
| `/add`           | POST   | Create a new patient                        |
| `/all`           | GET    | List all patients (with pagination)         |
| `/patient`       | GET    | Get patient by phone number                 |
| `/patient`       | PUT    | Update patient by phone number              |
| `/patient`       | DELETE | Delete patient by phone number or ROWID     |

**Sample Request:**
```
POST /add
Content-Type: application/json
{
  "Name": "John Doe",
  "Gender": "Male",
  "Age": 35,
  "Profession": "Engineer",
  "Weight": 75,
  "Height": 180,
  "Phonenumber": "9876543210",
  "MedicialHistory": "None"
}
```

---

## Prescription APIs

| Endpoint                | Method | Description                                         |
|-------------------------|--------|-----------------------------------------------------|
| `/prescription/add`     | POST   | Create a new prescription for a patient (legacy)    |
| `/prescription/save`    | POST   | **Atomically save prescription with stock deduction** |
| `/prescription/all`     | GET    | List all prescriptions (with pagination)            |
| `/prescription/get/:uuid` | GET  | Get prescription by UUID                            |
| `/prescription/update/:uuid` | PUT | Update prescription by UUID                      |
| `/prescription/delete/:uuid` | DELETE | Delete prescription by UUID                   |
| `/prescription/patient/:uuid` | GET | Get all prescriptions for a patient           |

**RECOMMENDED: Use `/prescription/save` for all prescription creation/updates**

### `/prescription/save` - Atomic Prescription with Stock Deduction

This endpoint atomically creates or updates a prescription and automatically deducts medicine stock.

**Key Features:**
- ✅ Validates stock availability BEFORE saving
- ✅ Automatically calculates required quantity from frequency × duration
- ✅ Deducts stock atomically with prescription creation
- ✅ Complete rollback on failure
- ✅ Prevents negative stock

**Sample Request (CREATE):**
```json
POST /prescription/save
Content-Type: application/json
{
  "PatientUUID": "patient-uuid-here",
  "CurrentSymptoms": "Fever, headache",
  "OutsideMedicines": "Vitamin C",
  "fees": "500",
  "medicines": [
    {
      "MedicineName": "Paracetamol",
      "frequency": "Twice daily",
      "Duration": "7",
      "timing": "After food"
    },
    {
      "MedicineName": "Ibuprofen",
      "frequency": "Thrice daily",
      "Duration": "5",
      "timing": "Before food"
    }
  ]
}
```

**Sample Request (UPDATE):**
```json
POST /prescription/save
Content-Type: application/json
{
  "UUID": "existing-prescription-uuid",
  "PatientUUID": "patient-uuid-here",
  "CurrentSymptoms": "Updated symptoms",
  "OutsideMedicines": "Vitamin D",
  "fees": "600",
  "deletedMedicineRowIds": [123, 456],
  "medicines": [
    {
      "ROWID": 789,
      "MedicineName": "Paracetamol",
      "frequency": "Once daily",
      "Duration": "3",
      "timing": "After food"
    }
  ]
}
```

**Stock Calculation:**
- `Total Quantity = Duration × Frequency Multiplier`
- Frequency mappings: "Once daily" = 1, "Twice daily" = 2, "Thrice daily" = 3, etc.
- Example: 7 days × Twice daily = 14 tablets required

**Success Response (200):**
```json
{
  "status": "success",
  "data": {
    "UUID": "prescription-uuid",
    "PatientUUID": "patient-uuid",
    "CurrentSymptoms": "Fever, headache",
    "OutsideMedicines": "Vitamin C",
    "fees": "500",
    "medicines": [
      {
        "ROWID": 101,
        "MedicineName": "Paracetamol",
        "frequency": "Twice daily",
        "Duration": "7",
        "timing": "After food"
      }
    ],
    "updatedMedicineStock": [
      {
        "Name": "Paracetamol",
        "Quantity": 86
      }
    ]
  }
}
```

**Error Response - Insufficient Stock (409):**
```json
{
  "status": "failure",
  "error": "Insufficient stock for: Paracetamol (required 14, available 6)"
}
```

**Error Response - Medicine Not Found (409):**
```json
{
  "status": "failure",
  "error": "Medicine not found in stock: NonExistentMedicine"
}
```

### `/prescription/add` (Legacy)

**Sample Request:**
```
POST /prescription/add
Content-Type: application/json
{
  "PatientUUID": "patient-uuid-here",
  "CurrentSymptoms": "Fever",
  "OutsideMedicines": "Aspirin",
  "fees": "300"
}
```

**Note:** This endpoint does NOT manage PrescribedMedicine or stock deduction.

---

## Medicine Stock APIs

| Endpoint                | Method | Description                                         |
|-------------------------|--------|-----------------------------------------------------|
| `/medicinestock/add`    | POST   | Add a new medicine to stock                         |
| `/medicinestock/all`    | GET    | List all medicines (with pagination)                |
| `/medicinestock`        | GET    | Get medicine by name                                |
| `/medicinestock`        | PUT    | Update medicine by name                             |
| `/medicinestock`        | DELETE | Delete medicine by name or ROWID                    |

**Sample Request:**
```
POST /medicinestock/add
Content-Type: application/json
{
  "Name": "Paracetamol",
  "Dosage": 500,
  "Quantity": 100,
  "Category": "Tablet",
  "Price": 50,
  "ManufacturerName": "ABC Pharma"
}
```

---

All endpoints expect and return JSON. For list endpoints, use `page` and `perPage` query parameters for pagination.
