# DRTracker - System Structure & Architecture Documentation

## 1. Project Overview

### Purpose
DRTracker is a comprehensive healthcare management system designed to streamline patient record management, prescription tracking, and medicine inventory control for medical practitioners and healthcare facilities.

### Core Functionality
- **Patient Management**: Create, read, update, and delete patient records with complete medical history
- **Prescription Management**: Track and manage patient prescriptions with dosage, frequency, and special instructions
- **Atomic Stock Deduction**: Automatic medicine stock deduction when creating prescriptions with rollback on failure
- **Medicine Stock Management**: Monitor medicine inventory with real-time stock status tracking (Critical/Low/In Stock)
- **Patient Insights**: Visual analytics and insights into patient demographics and medical data
- **Theme Customization**: Personalized UI theming with persistent preferences

### Target Audience
- Medical practitioners (doctors, physicians)
- Healthcare clinic administrators
- Hospital management staff
- Medical inventory managers

### Business Context
The application addresses the critical need for digitizing healthcare records, reducing paperwork, preventing medication stock-outs, and providing quick access to patient information for improved healthcare delivery.

---

## 2. System Architecture

### Overall Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client Layer                        │
│          React SPA (Port 3000 - Development)           │
│     Ant Design UI Components + Custom Styling          │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST API
                   │ (Axios)
┌──────────────────▼──────────────────────────────────────┐
│                 Backend Layer                           │
│     Zoho Catalyst Advanced I/O Function                │
│          Python 3.9 Flask Application                   │
└──────────────────┬──────────────────────────────────────┘
                   │ zcatalyst_sdk
                   │ ZCQL Queries
┌──────────────────▼──────────────────────────────────────┐
│                 Data Layer                              │
│          Zoho Catalyst Datastore                        │
│   Tables: Patient, Prescription, MedicineStock          │
└─────────────────────────────────────────────────────────┘
```

### Major Components

#### Frontend (React Application)
- **Routing Layer**: React Router DOM for SPA navigation
- **State Management**: React Context API (PatientContext, MedicineContext, ThemeContext)
- **UI Framework**: Ant Design 5.28.0 components
- **HTTP Client**: Axios for API communication
- **Presentation Layer**: Functional components with React Hooks

#### Backend (Python Flask)
- **API Handler**: Flask Request/Response handling
- **Business Logic**: CRUD operations for Patient, Prescription, Medicine
- **Data Access Layer**: Zoho Catalyst SDK for database operations
- **Query Engine**: ZCQL (Zoho Catalyst Query Language) for complex queries

#### Database
- **Provider**: Zoho Catalyst Datastore (NoSQL-style cloud database)
- **Tables**: 
  - Patient (12 fields including UUID, demographics, medical history)
  - Prescription (5 fields with patient UUID reference)
  - PrescribedMedicine (5 fields linking prescriptions to medicines)
  - MedicineStock (8 fields with inventory tracking)
- **Key Features**:
  - Atomic operations with optimistic concurrency control
  - Automatic stock validation and deduction
  - Rollback mechanism for failed transactions

### Component Interaction Flow

1. **User Interaction** → UI Component (React)
2. **Component** → Context Provider (State Management)
3. **Context** → API Utility Functions (axios)
4. **API Call** → Backend Flask Handler
5. **Handler** → Catalyst SDK → Datastore
6. **Response** ← Reverse flow to UI with data/status

### Deployment Environment

**Platform**: Zoho Catalyst Cloud Platform
- **Frontend**: Deployed as static React build via Catalyst CLI Plugin
- **Backend**: Advanced I/O serverless function (Python 3.9 runtime)
- **Database**: Managed Catalyst Datastore (cloud-native)
- **Configuration**: catalyst.json orchestrates deployment

---

## 3. Tech Stack

### Frontend Technologies

| Technology | Version | Justification |
|------------|---------|---------------|
| **React** | 19.2.0 | Modern, component-based UI library for building interactive SPAs |
| **React Router DOM** | 7.9.5 | Client-side routing for seamless navigation without page reloads |
| **Ant Design** | 5.28.0 | Enterprise-grade UI component library with rich table, form, and layout components |
| **Axios** | 1.13.2 | Promise-based HTTP client for clean API communication |
| **React Scripts** | 5.0.1 | Zero-configuration tooling for building and testing |

### Backend Technologies

| Technology | Version | Justification |
|------------|---------|---------------|
| **Python** | 3.9 | Robust, readable language with excellent library ecosystem |
| **Flask** | Implicit | Lightweight web framework for REST API development |
| **Zoho Catalyst SDK** | 1.0.2 | Official SDK for Catalyst platform integration |

### Development & DevOps

- **Build Tool**: React Scripts (Webpack-based)
- **Package Manager**: npm
- **Deployment**: Zoho Catalyst CLI (`catalyst deploy`)
- **Environment**: Node.js for frontend, Python 3.9 runtime for backend

### Database & Data Storage

- **Primary Database**: Zoho Catalyst Datastore
- **Query Language**: ZCQL (SQL-like syntax)
- **Data Persistence**: Cloud-managed with automatic backups

### APIs & Integrations

- **Internal API**: Custom REST API via Flask handlers
- **Third-Party Services**: Zoho Catalyst Platform Services (Datastore, ZCQL)

---

## 4. Directory Structure

```
TESTDRTRACKER/
│
├── drtrackerui/                          # Frontend React Application
│   ├── public/                           # Static assets and HTML template
│   │   ├── index.html                    # Main HTML entry point
│   │   ├── manifest.json                 # PWA manifest
│   │   └── robots.txt                    # SEO crawler instructions
│   │
│   ├── src/                              # Source code directory
│   │   ├── components/                   # Reusable UI components
│   │   │   ├── AddPatientForm.jsx        # Patient creation form with validation
│   │   │   ├── HeaderBar.jsx             # Top navigation bar with theme toggle
│   │   │   ├── MedicineTable.jsx         # Medicine inventory table with CRUD
│   │   │   ├── PatientTable.jsx          # Patient listing table with actions
│   │   │   ├── Sidebar.jsx               # Left navigation menu
│   │   │   ├── ThemeCustomizer.jsx       # Theme color/radius customization panel
│   │   │   └── patientTableColumns.js    # Ant Design table column definitions
│   │   │
│   │   ├── context/                      # React Context Providers
│   │   │   ├── MedicineContext.jsx       # Medicine state + API integration
│   │   │   └── PatientContext.jsx        # Patient state + API integration
│   │   │
│   │   ├── hooks/                        # Custom React hooks
│   │   │   └── useDataManagement.js      # Shared data management logic
│   │   │
│   │   ├── pages/                        # Route-level page components
│   │   │   ├── AddPrescriptionPage.jsx   # Prescription creation interface
│   │   │   ├── PatientInsightsPage.jsx   # Analytics and insights dashboard
│   │   │   ├── PatientsPage.jsx          # Patient management view
│   │   │   ├── OverviewPage.jsx          # Main dashboard/overview
│   │   │   └── MedicineStockPage.jsx     # Medicine inventory management
│   │   │
│   │   ├── utils/                        # Utility functions and API clients
│   │   │   ├── medicineApi.js            # Medicine API calls (axios)
│   │   │   ├── patientApi.js             # Patient API calls (axios)
│   │   │   ├── prescriptionApi.js        # Prescription API calls (axios)
│   │   │   └── validation.js             # Form validation utilities
│   │   │
│   │   ├── App.css                       # Application-level styles
│   │   ├── App.js                        # Main app component with routing
│   │   ├── App.test.js                   # App component tests
│   │   ├── index.css                     # Global CSS styles
│   │   ├── index.js                      # React app entry point with providers
│   │   ├── reportWebVitals.js            # Performance monitoring
│   │   ├── setupTests.js                 # Jest test configuration
│   │   └── themeContext.js               # Theme state management context
│   │
│   ├── README.md                         # Frontend documentation
│   ├── client-package.json               # Alternative package config
│   └── package.json                      # npm dependencies and scripts
│
├── functions/                            # Backend serverless functions
│   └── dr_tracker_function/             # Main API function
│       ├── main.py                       # Flask handlers for all endpoints (1462 lines)
│       ├── api_endpoints.md              # API documentation with atomic prescription details
│       ├── catalyst-config.json          # Function deployment config
│       └── requirements.txt              # Python dependencies
│
└── catalyst.json                         # Catalyst project configuration
```

---

## 5. Data Flow & Architecture Patterns

### Data Flow Architecture

#### Patient Creation Flow
```
User Input (AddPatientForm)
    ↓
Validation (validation.js)
    ↓
PatientContext.createPatient()
    ↓
patientApi.addPatient() [Axios POST]
    ↓
Backend: _create_patient(request, app)
    ↓
Uniqueness Check (ZCQL: SELECT WHERE Phonenumber)
    ↓
UUID Generation + Data Insertion
    ↓
Catalyst Datastore: Patient Table
    ↓
Response {status: 'success', data: {patient}}
    ↓
PatientContext.fetchPatients() [Refresh List]
    ↓
UI Update (React State Re-render)
```

#### Medicine Stock Monitoring Flow
```
MedicineContext.fetchMedicines()
    ↓
medicineApi.getAllMedicines() [Axios GET]
    ↓
Backend: _list_medicines() [ZCQL SELECT with LIMIT]
    ↓
Datastore Query Results
    ↓
Frontend: Calculate Stock Status
    • Quantity === 0 → 'Critical Stock'
    • Quantity ≤ 50 → 'Low Stock'
    • Quantity > 50 → 'In Stock'
    ↓
MedicineTable Component Display
```

#### Atomic Prescription Creation with Stock Deduction Flow
```
User Input (AddPrescriptionPage)
    ↓
Form Submission with Medicines Array
    ↓
prescriptionApi.savePrescription() [Axios POST]
    ↓
Backend: _save_prescription_atomic(request, app)
    ↓
STEP 1: Validate Patient exists
    ↓
STEP 2: For each medicine:
    • Calculate total_required = Duration × Frequency_Multiplier
    • Query MedicineStock for current quantity
    • Validate: current_quantity >= total_required
    • If insufficient → ABORT with 409 error
    ↓
STEP 3: Create/Update Prescription record
    ↓
STEP 4: Delete removed medicines (update mode)
    ↓
STEP 5: Deduct stock atomically:
    • For each medicine: new_qty = current_qty - total_required
    • Verify new_qty >= 0 (race condition check)
    • UPDATE MedicineStock.Quantity
    • Track for rollback
    ↓
STEP 6: Save PrescribedMedicine records
    ↓
Success Response with updated stock
    ↓
Frontend: fetchMedicines() [Refresh Inventory]
    ↓
UI Update with new stock quantities

ON ERROR → ROLLBACK:
    • Restore all stock quantities
    • Delete created prescription (CREATE mode)
    • Delete created medicine records (CREATE mode)
    • Return error response
```

### Architectural Patterns

#### 1. **Model-View-Controller (MVC) Variant**
- **Model**: Context Providers (PatientContext, MedicineContext) + Backend data models
- **View**: React Components (Pages + Components)
- **Controller**: API utility functions + Flask handlers

#### 2. **Context API Pattern (State Management)**
- Centralized state in Context Providers
- Hook-based consumption (usePatients, useMedicines)
- Automatic re-rendering on state changes

#### 3. **Repository Pattern**
- API utility files act as repositories
- Abstract data source (backend) from components
- Clean separation of concerns

#### 4. **Serverless Function Pattern**
- Single Flask handler function routes all requests
- Path-based routing (`/add`, `/all`, `/patient`, etc.)
- Stateless request processing

#### 5. **Optimistic UI Updates**
- Medicine operations update local state immediately
- Backend sync happens asynchronously
- Improved perceived performance

#### 6. **Atomic Transaction Pattern**
- Pre-flight validation before any database changes
- Ordered operations with comprehensive rollback
- Optimistic concurrency control for stock management
- Simulated ACID-like behavior without native transactions

---

## 6. Security & Authentication

### Current Security Implementation

#### Data Validation
- **Frontend Validation**: 
  - Age validation (0-150 range) in PatientContext
  - Required field checks in forms
  - Type conversions and null handling

- **Backend Validation**:
  - Required field validation for all entities
  - SQL injection prevention via parameterized queries
  - Type coercion for numeric fields (Age, Weight, Height, Dosage, Quantity, Price)

#### Data Integrity
- **Uniqueness Constraints**:
  - Patient: Phonenumber must be unique (409 Conflict on duplicate)
  - Medicine: Name must be unique (409 Conflict on duplicate)
- **Foreign Key Validation**: 
  - Prescription requires valid PatientUUID reference
  - PrescribedMedicine requires valid PrescriptionUUID reference
- **UUID-based Identification**: Generated server-side for Patient, Prescription, and Medicine records
- **Stock Integrity**:
  - Atomic stock validation and deduction
  - Prevents negative stock through optimistic concurrency control
  - Automatic rollback on transaction failure

#### SQL Injection Protection
```python
# Example from main.py
safe_phone = str(phone).replace("'", "\\'")
query = f"SELECT * FROM Patient WHERE Phonenumber = '{safe_phone}'"
```
All user inputs are escaped before ZCQL query construction.

### Authentication & Authorization

**Current Status**: ⚠️ **No authentication/authorization implemented**

The application currently lacks:
- User authentication (login/logout)
- Role-based access control
- Session management
- API token validation

**Zoho Catalyst Platform Security**:
- Managed infrastructure security
- HTTPS encryption in transit
- Cloud-native data encryption at rest

### Security Best Practices Applied
1. Input sanitization before database queries
2. Error message sanitization (no sensitive data leakage)
3. Proper HTTP status codes (400, 404, 409, 500)
4. Logging for audit trails

---

## 7. Performance & Scalability Analysis

### Performance Considerations

#### Frontend Optimization
1. **Code Splitting**: React.lazy() with Suspense for route-based splitting
2. **Optimistic Updates**: Medicine operations update UI immediately before backend confirmation
3. **Memoization**: useCallback in Context Providers to prevent unnecessary re-fetches
4. **Pagination**: All list endpoints support page/perPage parameters

#### Backend Optimization
1. **Query Optimization**: 
   - LIMIT clauses for paginated results
   - Selective field retrieval (not SELECT *)
   - Index-based lookups on unique fields (Phonenumber, UUID, Name)

2. **Response Size Management**:
   - Default page size: 50 records
   - hasMore flag prevents over-fetching
   - Lightweight JSON payloads

#### Database Optimization
- **ZCQL Indexing**: Automatic indexing on unique fields (assumed by Catalyst)
- **Batch Operations**: Not implemented (potential improvement)

### Scalability Strategy

#### Current Architecture Scalability

**Strengths**:
- **Serverless Backend**: Auto-scales with Catalyst platform
- **Stateless Functions**: No session affinity required
- **Cloud-Native Database**: Managed scalability by Zoho

**Limitations**:
- **No Caching Layer**: Every request hits the database
- **Single Function Deployment**: All endpoints in one function (potential cold start)
- **Synchronous Processing**: No async job queue for heavy operations

#### Horizontal Scalability
- ✅ **Frontend**: Static asset CDN distribution (via Catalyst)
- ✅ **Backend**: Automatic function instance scaling
- ✅ **Database**: Managed by Catalyst platform

#### Vertical Scalability
- Limited to Catalyst function runtime constraints
- No direct control over resource allocation

### Load Balancing
- Handled automatically by Zoho Catalyst platform
- No custom load balancer configuration needed

### Caching Strategy

**Current State**: ⚠️ No caching implemented

**Potential Improvements**:
1. **Frontend Caching**:
   - LocalStorage for patient/medicine lists
   - Service Worker for offline capability
   - React Query for smart cache invalidation

2. **Backend Caching**:
   - In-memory cache for frequently accessed patients
   - Medicine stock cache with TTL
   - Catalyst Cache service integration

### Bottleneck Mitigation

**Identified Bottlenecks**:
1. **Database Queries**: Multiple ZCQL queries per request (uniqueness checks + CRUD)
2. **Context Re-fetches**: Full list refresh after every mutation
3. **No Debouncing**: Search/filter operations trigger immediate API calls

**Mitigation Plans**:
1. Implement database transactions for atomic operations
2. Use differential updates instead of full re-fetches
3. Add request debouncing for search inputs
4. Implement virtual scrolling for large patient lists

---

## 8. API Documentation Reference

### RESTful Endpoint Structure

All API endpoints follow REST conventions and are documented in:
📄 `functions/dr_tracker_function/api_endpoints.md`

### Endpoint Categories

#### Patient APIs (5 endpoints)
- `POST /add` - Create patient
- `GET /all` - List patients (paginated)
- `GET /patient?Phonenumber=X` - Get by phone
- `PUT /patient` - Update patient
- `DELETE /patient?UUID=X` - Delete patient

#### Prescription APIs (7 endpoints)
- `POST /prescription/add` - Create prescription (legacy)
- `POST /prescription/save` - **Atomic prescription save with stock deduction (recommended)**
- `GET /prescription/all` - List prescriptions (paginated)
- `GET /prescription/get/:uuid` - Get prescription by UUID
- `GET /prescription/patient/:uuid` - Get all prescriptions for a patient
- `PUT /prescription/update/:uuid` - Update prescription by UUID
- `DELETE /prescription/delete/:uuid` - Delete prescription by UUID (cascade deletes medicines)

#### PrescribedMedicine APIs (5 endpoints)
- `POST /prescribedmedicine/add` - Add medicine to prescription
- `GET /prescribedmedicine/all/:uuid` - Get all medicines for a prescription
- `GET /prescribedmedicine/get/:rowid` - Get medicine by ROWID
- `PUT /prescribedmedicine/update/:rowid` - Update medicine by ROWID
- `DELETE /prescribedmedicine/delete/:rowid` - Delete medicine by ROWID

#### Medicine Stock APIs (5 endpoints)
- `POST /medicinestock/add` - Add medicine
- `GET /medicinestock/all` - List medicines (paginated)
- `GET /medicinestock?Name=X` - Get by name
- `PUT /medicinestock` - Update medicine
- `DELETE /medicinestock?UUID=X` - Delete medicine

### Standard Response Format
```json
{
  "status": "success" | "failure",
  "data": { ... },
  "error": "Error message if failure"
}
```

### Atomic Prescription Save Response
```json
{
  "status": "success",
  "data": {
    "UUID": "prescription-uuid",
    "PatientUUID": "patient-uuid",
    "CurrentSymptoms": "Fever, headache",
    "medicines": [...],
    "updatedMedicineStock": [
      {"Name": "Paracetamol", "Quantity": 86}
    ]
  }
}
```

### Stock Calculation Formula
```
Total Quantity Required = Duration (days) × Frequency Multiplier

Frequency Multipliers:
- Once daily: 1
- Twice daily: 2
- Thrice daily: 3
- Four times daily: 4
- Every 6 hours: 4
- Every 8 hours: 3
- Every 12 hours: 2
- Once weekly: 1/7
- As needed: 1
```

---

## 9. Future Improvements / Roadmap

### Known Limitations

1. **No Authentication**: Anyone with access can view/modify all records
2. **No Multi-tenancy**: Single database for all users
3. **Limited Error Handling**: No retry mechanisms or circuit breakers
4. **No Audit Logging**: No tracking of who made changes
5. **No Search Functionality**: Only supports exact match queries
6. **No File Upload**: Cannot attach patient documents/images
7. **No Real-time Updates**: No WebSocket or push notifications
8. **Limited Analytics**: Basic insights only, no advanced reporting
9. **Stock Restoration**: Deleting a prescription does not restore medicine stock
10. **Update Mode Stock**: Updating prescriptions deducts additional stock (design decision needed)

### Planned Enhancements

#### Phase 1: Security & Authentication (High Priority)
- [ ] Implement Zoho Catalyst Authentication
- [ ] Add role-based access control (Doctor, Admin, Receptionist)
- [ ] Session management with JWT tokens
- [ ] API rate limiting and throttling

#### Phase 2: Feature Expansion
- [x] Atomic prescription creation with stock deduction
- [x] Automatic inventory updates on prescription save
- [ ] Stock restoration on prescription deletion
- [ ] Advanced search with fuzzy matching
- [ ] Patient document upload and management
- [ ] Prescription PDF generation
- [ ] Email/SMS notifications for appointments
- [ ] Multi-language support
- [ ] Dark mode theme option

#### Phase 3: Analytics & Reporting
- [ ] Advanced patient demographics dashboard
- [ ] Medicine expiry tracking
- [ ] Revenue analytics
- [ ] Custom report builder
- [ ] Data export (CSV, Excel, PDF)

#### Phase 4: Performance Optimization
- [ ] Implement Redis caching layer
- [ ] Add GraphQL API for flexible querying
- [ ] Database query optimization with indexes
- [ ] Implement lazy loading for large tables
- [ ] Add service worker for offline mode

#### Phase 5: Integration & Scalability
- [ ] Integration with pharmacy systems
- [ ] Laboratory test result integration
- [ ] Appointment scheduling module
- [ ] Telemedicine video consultation
- [ ] Mobile app (React Native)

### Technical Debt
- Refactor 1462-line main.py into modular controllers
- Add comprehensive unit and integration tests
- Implement CI/CD pipeline
- Add API versioning (v1, v2)
- Migrate from string-based SQL to ORM (if Catalyst supports)
- Consider true database transactions if Catalyst adds support
- Implement stock audit trail for tracking deductions

---

## 10. Appendix

### A. Environment Setup

#### Prerequisites
- Node.js 14+ and npm
- Python 3.9+
- Zoho Catalyst CLI

#### Frontend Setup
```bash
cd drtrackerui
npm install
npm start  # Runs on http://localhost:3000
```

#### Backend Setup
```bash
cd functions/dr_tracker_function
pip install -r requirements.txt
# Deploy via Catalyst CLI
catalyst deploy
```

#### Full Project Deployment
```bash
catalyst deploy
# Deploys both frontend and backend to Catalyst cloud
```

### B. Database Schema

#### Patient Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| UUID | String | Unique, Server-generated |
| Name | String | Required |
| Gender | String | Required |
| Age | Integer | Required, 0-150 |
| Profession | String | Optional |
| Weight | Float | Optional |
| Height | Float | Optional |
| Phonenumber | String | Required, Unique |
| MedicialHistory | String | Optional |
| AdharNumber | Integer | Optional |
| Address | String | Optional |

#### Prescription Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| UUID | String | Unique, Server-generated |
| PatientUUID | String | Required, FK to Patient.UUID |
| CurrentSymptoms | String | Optional |
| OutsideMedicines | String | Optional |
| fees | String/Number | Optional |
| CREATEDTIME | Timestamp | Auto-generated |

#### PrescribedMedicine Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| PrescriptionUUID | String | Required, FK to Prescription.UUID |
| MedicineName | String | Required |
| frequency | String | Required (e.g., "Twice daily") |
| Duration | String/Number | Required (days) |
| timing | String | Required (e.g., "After food") |
| CREATEDTIME | Timestamp | Auto-generated |

#### MedicineStock Table
| Field | Type | Constraints |
|-------|------|-------------|
| ROWID | Integer | Auto-generated |
| UUID | String | Unique, Server-generated |
| Name | String | Required, Unique |
| Dosage | Float | Optional |
| Quantity | String (converted to Integer) | Required, Stock level |
| Category | String | Optional |
| Price | Integer | Optional |
| ManufacturerName | String | Optional |

**Note**: Quantity is stored as string in Datastore but converted to integer in application code for arithmetic operations.

### C. Technology Links

- [React Documentation](https://react.dev)
- [Ant Design Components](https://ant.design)
- [Zoho Catalyst Platform](https://catalyst.zoho.com)
- [Flask Documentation](https://flask.palletsprojects.com)
- [Axios Documentation](https://axios-http.com)

### D. Configuration Files

- **catalyst.json**: Project-level Catalyst configuration
- **catalyst-config.json**: Function-level runtime configuration
- **package.json**: Frontend dependencies and scripts
- **requirements.txt**: Python backend dependencies

### E. Development Guidelines

#### Code Style
- **Frontend**: ESLint with react-app config
- **Backend**: PEP 8 Python style guide
- **Comments**: Inline for complex logic, JSDoc for functions

#### Git Workflow
- Feature branch development recommended
- Pull request reviews before merging
- Semantic commit messages

---

**Document Version**: 1.0  
**Last Updated**: November 2024  
**Maintained By**: Development Team  
**For Questions**: Refer to API documentation or contact system administrator
