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
| `/prescription/add`     | POST   | Create a new prescription for a patient             |
| `/prescription/all`     | GET    | List all prescriptions (with pagination)            |
| `/prescription`         | GET    | Get prescription by PatientId                       |
| `/prescription`         | PUT    | Update prescription by PatientId                    |
| `/prescription`         | DELETE | Delete prescription by PatientId                    |

**Sample Request:**
```
POST /prescription/add
Content-Type: application/json
{
  "PatientId": "9876543210",
  "Frequency": 2,
  "Duration": 7,
  "SpecialInstruction": "Take after meals",
  "CurrentSymptoms": "Fever"
}
```

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
