import logging
from flask import Request, make_response, jsonify
import zcatalyst_sdk
import uuid
 
logger = logging.getLogger()

def _create_patient(request: Request, app):
    req_data = request.get_json(silent=True) or {}
    logger.info(f"[main.py] Received add patient request: {req_data}")
    name = req_data.get("Name")
    gender = req_data.get("Gender")
    age = req_data.get("Age")
    profession = req_data.get("Profession")
    weight = req_data.get("Weight")
    height = req_data.get("Height")
    medical_history = req_data.get("MedicialHistory")
    phone = req_data.get("Phonenumber")
    adhar_number = req_data.get("AdharNumber")
    address = req_data.get("Address")
    # current_symptoms field removed from Patient schema

    if not name:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Name'}), 400)
    if not phone:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Phonenumber'}), 400)
    if not gender:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Gender'}), 400)
    if not age:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Age'}), 400)

    try:
        age = int(age) if age is not None and str(age) != '' else None
    except Exception:
        age = None
    try:
        weight = float(weight) if weight is not None and str(weight) != '' else None
    except Exception:
        weight = None
    try:
        height = float(height) if height is not None and str(height) != '' else None
    except Exception:
        height = None

    try:
        zcql = app.zcql()
        safe_phone = str(phone).replace("'", "\\'")
        existing = zcql.execute_query(f"SELECT * FROM Patient WHERE Phonenumber = '{safe_phone}'")
        if existing and len(existing) > 0:
            return make_response(jsonify({'status': 'failure', 'error': 'Phonenumber already exists'}), 409)
    except Exception:
        logger.exception('Failed to check Phonenumber uniqueness')

    table = app.datastore().table('Patient')
    logger.info(f"[main.py] Inserting patient row: Name={name}, Gender={gender}, Age={age}, Profession={profession}, Weight={weight}, Height={height}, Phonenumber={phone}, MedicialHistory={medical_history}")
    patient_uuid = generate_uuid()
    patient_data = {
        'Name': name,
        'Gender': gender,
        'Age': age,
        'Profession': profession,
        'Weight': weight,
        'Height': height,
        'Phonenumber': phone,
        'MedicialHistory': medical_history,
        'UUID': patient_uuid,
        'Address': address
    }
    # Only add AdharNumber if it is a valid integer
    try:
        if adhar_number is not None and str(adhar_number).strip() != '':
            patient_data['AdharNumber'] = int(adhar_number)
    except Exception:
        pass
    row = table.insert_row(patient_data)

    row_id = None
    if isinstance(row, dict):
        row_id = row.get('ROWID') or row.get('id') or row.get('Id') or row.get('ROW_ID')
    patient = {'patientId': row_id or phone, 'Name': name, 'uuid': patient_uuid}
    response_data = {
        'status': 'success',
        'data': {
            'patient': patient
        }
    }
    logger.info(f"[main.py] Patient created: {response_data}")
    return make_response(jsonify(response_data), 200)


def _list_patients(request: Request, app):
    page = request.args.get('page')
    per_page = request.args.get('perPage')
    try:
        page = int(page) if page is not None else 1
    except Exception:
        page = 1
    try:
        per_page = int(per_page) if per_page is not None else 50
    except Exception:
        per_page = 50

    zcql_service = app.zcql()
    total = 0
    try:
        row_count = zcql_service.execute_query(f"SELECT COUNT(ROWID) FROM Patient")
        if row_count:
            first = row_count[0]
            if isinstance(first, dict):
                for v in first.values():
                    if isinstance(v, dict):
                        for vv in v.values():
                            try:
                                total = int(vv)
                                break
                            except Exception:
                                continue
                if total == 0:
                    for k, vv in first.items():
                        try:
                            total = int(vv)
                            break
                        except Exception:
                            continue
        has_more = total > (page) * (per_page)
    except Exception:
        logger.exception('Failed to fetch total count')
        has_more = False

    try:
        offset = (page - 1) * per_page
        query_result = zcql_service.execute_query(f"SELECT ROWID, Name, Gender, Age, Profession, Weight, Height, Phonenumber, MedicialHistory, UUID, AdharNumber, Address FROM Patient LIMIT {offset},{per_page}")
        todo_items = []
        for item in query_result:
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'Patient':
                row = list(item.values())[0]
            else:
                row = item
            todo_items.append({
                'id': row.get('ROWID') or row.get('id') or row.get('Id'),
                'Name': row.get('Name'),
                'Gender': row.get('Gender'),
                'Age': row.get('Age'),
                'Profession': row.get('Profession'),
                'Weight': row.get('Weight'),
                'Height': row.get('Height'),
                'Phonenumber': row.get('Phonenumber'),
                'MedicialHistory': row.get('MedicialHistory'),
                'UUID': row.get('UUID'),
                'AdharNumber': row.get('AdharNumber'),
                'Address': row.get('Address')
            })

        get_resp = {
            'status': 'success',
            'data': {
                'patients': todo_items,
                'hasMore': has_more,
                'page': page,
                'perPage': per_page,
                'total': total
            }
        }
        return make_response(jsonify(get_resp), 200)
    except Exception:
        logger.exception('Failed to query patients')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch patients'}), 500)


def _get_patient_by_phone(request: Request, app):
    phone = request.args.get('Phonenumber') or request.args.get('phone')
    if not phone:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing phone query parameter'}), 400)
    try:
        zcql_service = app.zcql()
        safe_phone = str(phone).replace("'", "\\'")
        query_result = zcql_service.execute_query(f"SELECT * FROM Patient WHERE Phonenumber = '{safe_phone}'")
        if query_result:
            item = query_result[0]
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'Patient':
                row = list(item.values())[0]
            else:
                row = item
            resp = {'status': 'success', 'data': {'patient': row}}
        else:
            resp = {'status': 'success', 'data': {'patient': None}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query patient by phone')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch patient'}), 500)


def _delete_patient(request: Request, app):
    uuid = request.args.get('UUID') or request.args.get('uuid')
    datastore_service = app.datastore()
    table_service = datastore_service.table("Patient")
    if uuid:
        try:
            zcql = app.zcql()
            safe_uuid = str(uuid).replace("'", "\\'")
            rows = zcql.execute_query(f"SELECT ROWID FROM Patient WHERE UUID = '{safe_uuid}'")
            row_ids = []
            for r in rows or []:
                if isinstance(r, dict) and len(r) == 1 and list(r.keys())[0] == 'Patient':
                    inner = list(r.values())[0]
                    rid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
                else:
                    rid = r.get('ROWID') if isinstance(r, dict) else None
                if rid:
                    row_ids.append(rid)
            if not row_ids:
                return make_response(jsonify({'status': 'failure', 'error': 'No patient found with that UUID'}), 404)
            deleted = []
            for rid in row_ids:
                try:
                    table_service.delete_row(rid)
                    deleted.append(rid)
                except Exception:
                    logger.exception('Failed to delete row %s', rid)
            resp = {'status': 'success', 'data': {'deletedRowIds': deleted}}
            return make_response(jsonify(resp), 200)
        except Exception:
            logger.exception('Failed to delete by UUID')
            return make_response(jsonify({'status': 'failure', 'error': 'Failed to delete patient(s)'}), 500)
    else:
        message = {
            'status': 'failure',
            'error': 'Please provide UUID query param to delete patient.'
        }
        return make_response(jsonify(message), 400)


def _create_prescription(request: Request, app):
    """Create a new prescription with UUID as primary identifier."""
    req_data = request.get_json(silent=True) or {}
    patient_uuid = req_data.get('PatientUUID')
    outside_medicines = req_data.get('OutsideMedicines')
    current_symptoms = req_data.get('CurrentSymptoms')
    fees = req_data.get('fees')

    # PatientUUID is required
    if not patient_uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: PatientUUID'}), 400)

    # Verify Patient exists by UUID
    try:
        zcql = app.zcql()
        safe_uuid = str(patient_uuid).replace("'", "\\'")
        patient_exists = zcql.execute_query(f"SELECT ROWID FROM Patient WHERE UUID = '{safe_uuid}'")
        if not patient_exists:
            return make_response(jsonify({'status': 'failure', 'error': 'Referenced Patient not found'}), 400)
    except Exception:
        logger.exception('Failed to verify referenced Patient')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to verify patient'}), 500)

    # Generate UUID for prescription
    prescription_uuid = generate_uuid()

    table = app.datastore().table('Prescription')
    try:
        row = table.insert_row({
            'UUID': prescription_uuid,
            'PatientUUID': patient_uuid,
            'OutsideMedicines': outside_medicines,
            'CurrentSymptoms': current_symptoms,
            'fees': fees
        })

        resp = {'status': 'success', 'data': {'UUID': prescription_uuid}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to create Prescription')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to create prescription'}), 500)


def _list_prescriptions(request: Request, app):
    """Get all prescriptions."""
    page = request.args.get('page')
    per_page = request.args.get('perPage')
    try:
        page = int(page) if page is not None else 1
    except Exception:
        page = 1
    try:
        per_page = int(per_page) if per_page is not None else 50
    except Exception:
        per_page = 50

    zcql_service = app.zcql()
    total = 0
    try:
        row_count = zcql_service.execute_query(f"SELECT COUNT(ROWID) FROM Prescription")
        if row_count:
            first = row_count[0]
            if isinstance(first, dict):
                for v in first.values():
                    if isinstance(v, dict):
                        for vv in v.values():
                            try:
                                total = int(vv)
                                break
                            except Exception:
                                continue
                if total == 0:
                    for k, vv in first.items():
                        try:
                            total = int(vv)
                            break
                        except Exception:
                            continue
        has_more = total > (page) * (per_page)
    except Exception:
        logger.exception('Failed to fetch Prescription total count')
        has_more = False

    try:
        offset = (page - 1) * per_page
        query_result = zcql_service.execute_query(f"SELECT ROWID, UUID, PatientUUID, OutsideMedicines, CurrentSymptoms, fees, CREATEDTIME FROM Prescription LIMIT {offset},{per_page}")
        items = []
        for item in query_result:
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'Prescription':
                row = list(item.values())[0]
            else:
                row = item
            items.append({
                'ROWID': row.get('ROWID') or row.get('id') or row.get('Id'),
                'UUID': row.get('UUID'),
                'PatientUUID': row.get('PatientUUID'),
                'OutsideMedicines': row.get('OutsideMedicines'),
                'CurrentSymptoms': row.get('CurrentSymptoms'),
                'fees': row.get('fees'),
                'CREATEDTIME': row.get('CREATEDTIME')
            })

        resp = {'status': 'success', 'data': {'prescriptions': items, 'hasMore': has_more, 'page': page, 'perPage': per_page, 'total': total}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query Prescription')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescriptions'}), 500)


def _get_prescription_by_uuid(request: Request, app, uuid):
    """Get a single prescription by UUID."""
    if not uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing UUID parameter'}), 400)
    try:
        zcql = app.zcql()
        safe_uuid = str(uuid).replace("'", "\\'")
        query_result = zcql.execute_query(f"SELECT * FROM Prescription WHERE UUID = '{safe_uuid}'")
        if query_result:
            item = query_result[0]
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'Prescription':
                row = list(item.values())[0]
            else:
                row = item
            resp = {'status': 'success', 'data': {'prescription': row}}
        else:
            resp = {'status': 'success', 'data': {'prescription': None}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query Prescription by UUID')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescription'}), 500)


def _delete_prescription(request: Request, app, uuid):
    """Delete prescription by UUID and cascade delete all linked PrescribedMedicine entries."""
    if not uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing UUID parameter'}), 400)
    try:
        zcql = app.zcql()
        safe_uuid = str(uuid).replace("'", "\\'")
        
        # Find the prescription ROWID
        rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE UUID = '{safe_uuid}'")
        row_ids = []
        for r in rows or []:
            if isinstance(r, dict) and len(r) == 1 and list(r.keys())[0] == 'Prescription':
                inner = list(r.values())[0]
                rid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
            else:
                rid = r.get('ROWID') if isinstance(r, dict) else None
            if rid:
                row_ids.append(rid)
        
        if not row_ids:
            return make_response(jsonify({'status': 'failure', 'error': 'No prescription found with that UUID'}), 404)
        
        # Cascade delete: First delete all PrescribedMedicine entries linked to this prescription
        try:
            prescribed_meds = zcql.execute_query(f"SELECT ROWID FROM PrescribedMedicine WHERE PrescriptionUUID = '{safe_uuid}'")
            prescribed_med_table = app.datastore().table('PrescribedMedicine')
            deleted_meds = []
            for pm in prescribed_meds or []:
                if isinstance(pm, dict) and len(pm) == 1 and list(pm.keys())[0] == 'PrescribedMedicine':
                    inner = list(pm.values())[0]
                    pm_rid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
                else:
                    pm_rid = pm.get('ROWID') if isinstance(pm, dict) else None
                if pm_rid:
                    try:
                        prescribed_med_table.delete_row(pm_rid)
                        deleted_meds.append(pm_rid)
                    except Exception:
                        logger.exception('Failed to delete PrescribedMedicine %s', pm_rid)
        except Exception:
            logger.exception('Failed to cascade delete PrescribedMedicine entries')
        
        # Now delete the prescription itself
        datastore_service = app.datastore()
        table_service = datastore_service.table('Prescription')
        deleted = []
        for rid in row_ids:
            try:
                table_service.delete_row(rid)
                deleted.append(rid)
            except Exception:
                logger.exception('Failed to delete prescription %s', rid)
        
        return make_response(jsonify({'status': 'success', 'data': {'deletedRowIds': deleted}}), 200)
    except Exception:
        logger.exception('Failed to delete Prescription by UUID')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to delete prescription'}), 500)


def _update_patient(request: Request, app):
    """Update patient fields by Phonenumber. Requires 'Phonenumber' (or 'phone') in JSON body."""
    req_data = request.get_json(silent=True) or {}
    phone = req_data.get('Phonenumber') or req_data.get('phone')
    if not phone:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Phonenumber'}), 400)

    # Collect updatable fields if present
    updates = {}
    for key in ('Name', 'Gender', 'Age', 'Profession', 'Weight', 'Height', 'Phonenumber', 'MedicialHistory'):
        if key in req_data:
            updates[key] = req_data.get(key)

    # Type conversions
    if 'Age' in updates:
        try:
            updates['Age'] = int(updates['Age']) if updates['Age'] is not None and str(updates['Age']) != '' else None
        except Exception:
            updates.pop('Age', None)
    if 'Weight' in updates:
        try:
            updates['Weight'] = float(updates['Weight']) if updates['Weight'] is not None and str(updates['Weight']) != '' else None
        except Exception:
            updates.pop('Weight', None)
    if 'Height' in updates:
        try:
            updates['Height'] = float(updates['Height']) if updates['Height'] is not None and str(updates['Height']) != '' else None
        except Exception:
            updates.pop('Height', None)

    if not updates:
        return make_response(jsonify({'status': 'failure', 'error': 'No updatable fields provided'}), 400)

    try:
        zcql = app.zcql()
        safe_phone = str(phone).replace("'", "\\'")
        rows = zcql.execute_query(f"SELECT ROWID FROM Patient WHERE Phonenumber = '{safe_phone}'")
        row_id = None
        if rows:
            first = rows[0]
            if isinstance(first, dict) and len(first) == 1 and list(first.keys())[0] == 'Patient':
                inner = list(first.values())[0]
                row_id = inner.get('ROWID') or inner.get('id') or inner.get('Id')
            else:
                row_id = first.get('ROWID') if isinstance(first, dict) else None
        if not row_id:
            return make_response(jsonify({'status': 'failure', 'error': 'Patient not found'}), 404)

        table = app.datastore().table('Patient')
        try:
            table.update_row(row_id, updates)
        except Exception:
            # Fallback to ZCQL UPDATE if SDK doesn't support update_row
            set_clauses = []
            for k, v in updates.items():
                if v is None:
                    set_clauses.append(f"{k}=NULL")
                elif isinstance(v, (int, float)):
                    set_clauses.append(f"{k}={v}")
                else:
                    safe_v = str(v).replace("'", "\\'")
                    set_clauses.append(f"{k}='{safe_v}'")
            zcql.execute_query(f"UPDATE Patient SET {', '.join(set_clauses)} WHERE ROWID = '{row_id}'")

        return make_response(jsonify({'status': 'success', 'data': {'Phonenumber': phone}}), 200)
    except Exception:
        logger.exception('Failed to update Patient')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to update patient'}), 500)


def _update_prescription(request: Request, app, uuid):
    """Update prescription fields by UUID."""
    req_data = request.get_json(silent=True) or {}
    
    if not uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing UUID parameter'}), 400)

    updates = {}
    for key in ('PatientUUID', 'OutsideMedicines', 'CurrentSymptoms', 'fees'):
        if key in req_data:
            updates[key] = req_data.get(key)

    if not updates:
        return make_response(jsonify({'status': 'failure', 'error': 'No updatable fields provided'}), 400)

    try:
        zcql = app.zcql()
        safe_uuid = str(uuid).replace("'", "\\'")
        rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE UUID = '{safe_uuid}'")
        row_id = None
        if rows:
            first = rows[0]
            if isinstance(first, dict) and len(first) == 1 and list(first.keys())[0] == 'Prescription':
                inner = list(first.values())[0]
                row_id = inner.get('ROWID') or inner.get('id') or inner.get('Id')
            else:
                row_id = first.get('ROWID') if isinstance(first, dict) else None
        if not row_id:
            return make_response(jsonify({'status': 'failure', 'error': 'Prescription not found for UUID'}), 404)

        table = app.datastore().table('Prescription')
        try:
            table.update_row(row_id, updates)
        except Exception:
            set_clauses = []
            for k, v in updates.items():
                if v is None:
                    set_clauses.append(f"{k}=NULL")
                elif isinstance(v, (int, float)):
                    set_clauses.append(f"{k}={v}")
                else:
                    safe_v = str(v).replace("'", "\\'")
                    set_clauses.append(f"{k}='{safe_v}'")
            zcql.execute_query(f"UPDATE Prescription SET {', '.join(set_clauses)} WHERE ROWID = '{row_id}'")

        return make_response(jsonify({'status': 'success', 'data': {'UUID': uuid}}), 200)
    except Exception:
        logger.exception('Failed to update Prescription')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to update prescription'}), 500)


def _create_medicine(request: Request, app):
    req_data = request.get_json(silent=True) or {}
    name = req_data.get('Name')
    dosage = req_data.get('Dosage')
    quantity = req_data.get('Quantity')
    category = req_data.get('Category')
    price = req_data.get('Price')
    manufacturer = req_data.get('ManufacturerName')

    if not name:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: Name'}), 400)

    # convert numeric fields
    try:
        dosage = float(dosage) if dosage is not None and str(dosage) != '' else None
    except Exception:
        dosage = None
    try:
        quantity = int(quantity) if quantity is not None and str(quantity) != '' else None
    except Exception:
        quantity = None
    try:
        price = int(price) if price is not None and str(price) != '' else None
    except Exception:
        price = None

    try:
        zcql = app.zcql()
        safe_name = str(name).replace("'", "\\'")
        existing = zcql.execute_query(f"SELECT * FROM MedicineStock WHERE Name = '{safe_name}'")
        if existing and len(existing) > 0:
            return make_response(jsonify({'status': 'failure', 'error': 'Medicine with this Name already exists'}), 409)
    except Exception:
        logger.exception('Failed to check MedicineStock uniqueness')

    table = app.datastore().table('MedicineStock')
    medicine_uuid = generate_uuid()
    row = table.insert_row({
        'Name': name,
        'Dosage': dosage,
        'Quantity': quantity,
        'Category': category,
        'Price': price,
        'ManufacturerName': manufacturer,
        'UUID': medicine_uuid
    })

    row_id = None
    if isinstance(row, dict):
        row_id = row.get('ROWID') or row.get('id') or row.get('Id') or row.get('ROW_ID')
    medicine = {'medicineId': row_id or name, 'Name': name}
    return make_response(jsonify({'status': 'success', 'data': {'medicine': medicine}}), 200)


def _create_prescribed_medicine(request: Request, app):
    """Create a new PrescribedMedicine entry."""
    req_data = request.get_json(silent=True) or {}
    prescription_uuid = req_data.get('PrescriptionUUID')
    medicine_name = req_data.get('MedicineName')
    frequency = req_data.get('frequency')
    duration = req_data.get('Duration')
    timing = req_data.get('timing')

    # PrescriptionUUID is required
    if not prescription_uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: PrescriptionUUID'}), 400)

    # Verify Prescription exists by UUID
    try:
        zcql = app.zcql()
        safe_uuid = str(prescription_uuid).replace("'", "\\'")
        prescription_exists = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE UUID = '{safe_uuid}'")
        if not prescription_exists:
            return make_response(jsonify({'status': 'failure', 'error': 'Referenced Prescription not found'}), 400)
    except Exception:
        logger.exception('Failed to verify referenced Prescription')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to verify prescription'}), 500)

    table = app.datastore().table('PrescribedMedicine')
    try:
        row = table.insert_row({
            'PrescriptionUUID': prescription_uuid,
            'MedicineName': medicine_name,
            'frequency': frequency,
            'Duration': duration,
            'timing': timing
        })

        row_id = None
        if isinstance(row, dict):
            row_id = row.get('ROWID') or row.get('id') or row.get('Id') or row.get('ROW_ID')
        
        resp = {'status': 'success', 'data': {'ROWID': row_id, 'PrescriptionUUID': prescription_uuid}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to create PrescribedMedicine')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to create prescribed medicine'}), 500)


def _get_prescribed_medicines_by_prescription(request: Request, app, prescription_uuid):
    """Get all PrescribedMedicine entries for a prescription by PrescriptionUUID."""
    if not prescription_uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing PrescriptionUUID parameter'}), 400)
    
    try:
        zcql = app.zcql()
        safe_uuid = str(prescription_uuid).replace("'", "\\'")
        query_result = zcql.execute_query(f"SELECT * FROM PrescribedMedicine WHERE PrescriptionUUID = '{safe_uuid}'")
        
        items = []
        for item in query_result or []:
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'PrescribedMedicine':
                row = list(item.values())[0]
            else:
                row = item
            items.append({
                'ROWID': row.get('ROWID') or row.get('id') or row.get('Id'),
                'PrescriptionUUID': row.get('PrescriptionUUID'),
                'MedicineName': row.get('MedicineName'),
                'frequency': row.get('frequency'),
                'Duration': row.get('Duration'),
                'timing': row.get('timing'),
                'CREATEDTIME': row.get('CREATEDTIME')
            })
        
        resp = {'status': 'success', 'data': {'prescribedMedicines': items}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query PrescribedMedicine by PrescriptionUUID')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescribed medicines'}), 500)


def _get_prescribed_medicine_by_rowid(request: Request, app, rowid):
    """Get a single PrescribedMedicine entry by ROWID."""
    if not rowid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing ROWID parameter'}), 400)
    
    try:
        zcql = app.zcql()
        safe_rowid = str(rowid).replace("'", "\\'")
        query_result = zcql.execute_query(f"SELECT * FROM PrescribedMedicine WHERE ROWID = '{safe_rowid}'")
        
        if query_result:
            item = query_result[0]
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'PrescribedMedicine':
                row = list(item.values())[0]
            else:
                row = item
            resp = {'status': 'success', 'data': {'prescribedMedicine': row}}
        else:
            resp = {'status': 'success', 'data': {'prescribedMedicine': None}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query PrescribedMedicine by ROWID')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescribed medicine'}), 500)


def _update_prescribed_medicine(request: Request, app, rowid):
    """Update a PrescribedMedicine entry by ROWID."""
    req_data = request.get_json(silent=True) or {}
    
    if not rowid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing ROWID parameter'}), 400)

    updates = {}
    for key in ('MedicineName', 'frequency', 'Duration', 'timing'):
        if key in req_data:
            updates[key] = req_data.get(key)

    if not updates:
        return make_response(jsonify({'status': 'failure', 'error': 'No updatable fields provided'}), 400)

    try:
        table = app.datastore().table('PrescribedMedicine')
        try:
            table.update_row(rowid, updates)
        except Exception:
            zcql = app.zcql()
            set_clauses = []
            for k, v in updates.items():
                if v is None:
                    set_clauses.append(f"{k}=NULL")
                elif isinstance(v, (int, float)):
                    set_clauses.append(f"{k}={v}")
                else:
                    safe_v = str(v).replace("'", "\\'")
                    set_clauses.append(f"{k}='{safe_v}'")
            safe_rowid = str(rowid).replace("'", "\\'")
            zcql.execute_query(f"UPDATE PrescribedMedicine SET {', '.join(set_clauses)} WHERE ROWID = '{safe_rowid}'")

        return make_response(jsonify({'status': 'success', 'data': {'ROWID': rowid}}), 200)
    except Exception:
        logger.exception('Failed to update PrescribedMedicine')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to update prescribed medicine'}), 500)


def _delete_prescribed_medicine(request: Request, app, rowid):
    """Delete a PrescribedMedicine entry by ROWID."""
    if not rowid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing ROWID parameter'}), 400)
    
    try:
        datastore_service = app.datastore()
        table_service = datastore_service.table('PrescribedMedicine')
        
        table_service.delete_row(rowid)
        
        return make_response(jsonify({'status': 'success', 'data': {'deletedRowId': rowid}}), 200)
    except Exception:
        logger.exception('Failed to delete PrescribedMedicine by ROWID')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to delete prescribed medicine'}), 500)


def _save_prescription_atomic(request: Request, app):
    """Atomically save a prescription with its medicines (CREATE or UPDATE)."""
    req_data = request.get_json(silent=True) or {}
    prescription_uuid = req_data.get('UUID')
    patient_uuid = req_data.get('PatientUUID')
    outside_medicines = req_data.get('OutsideMedicines')
    current_symptoms = req_data.get('CurrentSymptoms')
    fees = req_data.get('fees')
    medicines = req_data.get('medicines', [])
    deleted_medicine_rowids = req_data.get('deletedMedicineRowIds', [])

    # Validation
    if not patient_uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: PatientUUID'}), 400)
    
    if not isinstance(medicines, list):
        return make_response(jsonify({'status': 'failure', 'error': 'medicines must be an array'}), 400)

    # Verify Patient exists by UUID
    try:
        zcql = app.zcql()
        safe_patient_uuid = str(patient_uuid).replace("'", "\\'")
        patient_exists = zcql.execute_query(f"SELECT ROWID FROM Patient WHERE UUID = '{safe_patient_uuid}'")
        if not patient_exists:
            return make_response(jsonify({'status': 'failure', 'error': 'Referenced Patient not found'}), 400)
    except Exception:
        logger.exception('Failed to verify referenced Patient')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to verify patient'}), 500)

    is_update = prescription_uuid is not None and prescription_uuid != ''
    created_prescription_uuid = None
    created_medicine_rowids = []
    prescription_table = app.datastore().table('Prescription')
    medicine_table = app.datastore().table('PrescribedMedicine')

    try:
        # Step 1: CREATE or UPDATE Prescription
        if is_update:
            # UPDATE mode
            safe_uuid = str(prescription_uuid).replace("'", "\\'")
            rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE UUID = '{safe_uuid}'")
            prescription_rowid = None
            if rows:
                first = rows[0]
                if isinstance(first, dict) and len(first) == 1 and list(first.keys())[0] == 'Prescription':
                    inner = list(first.values())[0]
                    prescription_rowid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
                else:
                    prescription_rowid = first.get('ROWID') if isinstance(first, dict) else None
            
            if not prescription_rowid:
                return make_response(jsonify({'status': 'failure', 'error': 'Prescription not found for UUID'}), 404)
            
            # Update prescription fields
            updates = {
                'PatientUUID': patient_uuid,
                'OutsideMedicines': outside_medicines,
                'CurrentSymptoms': current_symptoms,
                'fees': fees
            }
            try:
                prescription_table.update_row(prescription_rowid, updates)
            except Exception:
                set_clauses = []
                for k, v in updates.items():
                    if v is None:
                        set_clauses.append(f"{k}=NULL")
                    elif isinstance(v, (int, float)):
                        set_clauses.append(f"{k}={v}")
                    else:
                        safe_v = str(v).replace("'", "\\'")
                        set_clauses.append(f"{k}='{safe_v}'")
                zcql.execute_query(f"UPDATE Prescription SET {', '.join(set_clauses)} WHERE ROWID = '{prescription_rowid}'")
            
            created_prescription_uuid = prescription_uuid
        else:
            # CREATE mode
            created_prescription_uuid = generate_uuid()
            row = prescription_table.insert_row({
                'UUID': created_prescription_uuid,
                'PatientUUID': patient_uuid,
                'OutsideMedicines': outside_medicines,
                'CurrentSymptoms': current_symptoms,
                'fees': fees
            })

        # Step 2: Delete removed medicines (if provided in UPDATE mode)
        if is_update and deleted_medicine_rowids:
            for rowid in deleted_medicine_rowids:
                try:
                    medicine_table.delete_row(rowid)
                except Exception:
                    logger.exception('Failed to delete medicine ROWID %s during atomic save', rowid)
                    # Continue with other deletions

        # Step 3: INSERT or UPDATE medicines
        saved_medicines = []
        for med in medicines:
            med_rowid = med.get('ROWID')
            medicine_name = med.get('MedicineName')
            frequency = med.get('frequency')
            duration = med.get('Duration')
            timing = med.get('timing')

            if med_rowid:
                # UPDATE existing medicine
                med_updates = {
                    'MedicineName': medicine_name,
                    'frequency': frequency,
                    'Duration': duration,
                    'timing': timing
                }
                try:
                    medicine_table.update_row(med_rowid, med_updates)
                    saved_medicines.append({
                        'ROWID': med_rowid,
                        'MedicineName': medicine_name,
                        'frequency': frequency,
                        'Duration': duration,
                        'timing': timing
                    })
                except Exception:
                    # Fallback to ZCQL
                    set_clauses = []
                    for k, v in med_updates.items():
                        if v is None:
                            set_clauses.append(f"{k}=NULL")
                        elif isinstance(v, (int, float)):
                            set_clauses.append(f"{k}={v}")
                        else:
                            safe_v = str(v).replace("'", "\\'")
                            set_clauses.append(f"{k}='{safe_v}'")
                    safe_rowid = str(med_rowid).replace("'", "\\'")
                    zcql.execute_query(f"UPDATE PrescribedMedicine SET {', '.join(set_clauses)} WHERE ROWID = '{safe_rowid}'")
                    saved_medicines.append({
                        'ROWID': med_rowid,
                        'MedicineName': medicine_name,
                        'frequency': frequency,
                        'Duration': duration,
                        'timing': timing
                    })
            else:
                # INSERT new medicine
                row = medicine_table.insert_row({
                    'PrescriptionUUID': created_prescription_uuid,
                    'MedicineName': medicine_name,
                    'frequency': frequency,
                    'Duration': duration,
                    'timing': timing
                })
                
                new_rowid = None
                if isinstance(row, dict):
                    new_rowid = row.get('ROWID') or row.get('id') or row.get('Id') or row.get('ROW_ID')
                
                created_medicine_rowids.append(new_rowid)
                saved_medicines.append({
                    'ROWID': new_rowid,
                    'MedicineName': medicine_name,
                    'frequency': frequency,
                    'Duration': duration,
                    'timing': timing
                })

        # Success response
        return make_response(jsonify({
            'status': 'success',
            'data': {
                'UUID': created_prescription_uuid,
                'PatientUUID': patient_uuid,
                'OutsideMedicines': outside_medicines,
                'CurrentSymptoms': current_symptoms,
                'fees': fees,
                'medicines': saved_medicines
            }
        }), 200)

    except Exception as e:
        logger.exception('Failed to save prescription atomically')
        
        # Rollback logic for CREATE mode
        if not is_update and created_prescription_uuid:
            try:
                # Delete created medicines
                for rowid in created_medicine_rowids:
                    if rowid:
                        try:
                            medicine_table.delete_row(rowid)
                        except Exception:
                            logger.exception('Failed to rollback medicine ROWID %s', rowid)
                
                # Delete created prescription
                safe_uuid = str(created_prescription_uuid).replace("'", "\\'")
                prescription_rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE UUID = '{safe_uuid}'")
                if prescription_rows:
                    first = prescription_rows[0]
                    if isinstance(first, dict) and len(first) == 1 and list(first.keys())[0] == 'Prescription':
                        inner = list(first.values())[0]
                        p_rowid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
                    else:
                        p_rowid = first.get('ROWID') if isinstance(first, dict) else None
                    if p_rowid:
                        prescription_table.delete_row(p_rowid)
            except Exception:
                logger.exception('Failed to rollback prescription creation')
        
        return make_response(jsonify({
            'status': 'failure',
            'error': 'Failed to save prescription',
            'details': str(e)
        }), 500)


def _list_medicines(request: Request, app):
    page = request.args.get('page')
    per_page = request.args.get('perPage')
    try:
        page = int(page) if page is not None else 1
    except Exception:
        page = 1
    try:
        per_page = int(per_page) if per_page is not None else 50
    except Exception:
        per_page = 50

    zcql_service = app.zcql()
    total = 0
    try:
        row_count = zcql_service.execute_query(f"SELECT COUNT(ROWID) FROM MedicineStock")
        if row_count:
            first = row_count[0]
            if isinstance(first, dict):
                for v in first.values():
                    if isinstance(v, dict):
                        for vv in v.values():
                            try:
                                total = int(vv)
                                break
                            except Exception:
                                continue
                if total == 0:
                    for k, vv in first.items():
                        try:
                            total = int(vv)
                            break
                        except Exception:
                            continue
        has_more = total > (page) * (per_page)
    except Exception:
        logger.exception('Failed to fetch MedicineStock total count')
        has_more = False

    try:
        offset = (page - 1) * per_page
        query_result = zcql_service.execute_query(f"SELECT ROWID, Name, Dosage, Quantity, Category, Price, ManufacturerName, UUID FROM MedicineStock LIMIT {offset},{per_page}")
        items = []
        for item in query_result:
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'MedicineStock':
                row = list(item.values())[0]
            else:
                row = item
            items.append({
                'medicineId': row.get('ROWID') or row.get('id') or row.get('Id'),
                'UUID': row.get('UUID'),
                'Name': row.get('Name'),
                'Dosage': row.get('Dosage'),
                'Quantity': row.get('Quantity'),
                'Category': row.get('Category'),
                'Price': row.get('Price'),
                'ManufacturerName': row.get('ManufacturerName')
            })
        return make_response(jsonify({'status': 'success', 'data': {'medicines': items, 'hasMore': has_more, 'page': page, 'perPage': per_page, 'total': total}}), 200)
    except Exception:
        logger.exception('Failed to query MedicineStock')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch medicines'}), 500)


def _get_medicine_by_name(request: Request, app):
    name = request.args.get('Name') or request.args.get('name')
    if not name:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing Name query parameter'}), 400)
    try:
        zcql = app.zcql()
        safe_name = str(name).replace("'", "\\'")
        query_result = zcql.execute_query(f"SELECT * FROM MedicineStock WHERE Name = '{safe_name}'")
        if query_result:
            item = query_result[0]
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'MedicineStock':
                row = list(item.values())[0]
            else:
                row = item
            return make_response(jsonify({'status': 'success', 'data': {'medicine': row}}), 200)
        else:
            return make_response(jsonify({'status': 'success', 'data': {'medicine': None}}), 200)
    except Exception:
        logger.exception('Failed to query MedicineStock by Name')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch medicine'}), 500)


def _delete_medicine(request: Request, app):
    uuid = request.args.get('UUID') or request.args.get('uuid')
    datastore_service = app.datastore()
    table_service = datastore_service.table('MedicineStock')
    if uuid:
        try:
            zcql = app.zcql()
            safe_uuid = str(uuid).replace("'", "\\'")
            rows = zcql.execute_query(f"SELECT ROWID FROM MedicineStock WHERE UUID = '{safe_uuid}'")
            row_ids = []
            for r in rows or []:
                if isinstance(r, dict) and len(r) == 1 and list(r.keys())[0] == 'MedicineStock':
                    inner = list(r.values())[0]
                    rid = inner.get('ROWID') or inner.get('id') or inner.get('Id')
                else:
                    rid = r.get('ROWID') if isinstance(r, dict) else None
                if rid:
                    row_ids.append(rid)
            if not row_ids:
                return make_response(jsonify({'status': 'failure', 'error': 'No medicine found with that UUID'}), 404)
            deleted = []
            for rid in row_ids:
                try:
                    table_service.delete_row(rid)
                    deleted.append(rid)
                except Exception:
                    logger.exception('Failed to delete medicine %s', rid)
            return make_response(jsonify({'status': 'success', 'data': {'deletedRowIds': deleted}}), 200)
        except Exception:
            logger.exception('Failed to delete MedicineStock by UUID')
            return make_response(jsonify({'status': 'failure', 'error': 'Failed to delete medicine(s)'}), 500)
    else:
        return make_response(jsonify({'status': 'failure', 'error': 'Please provide UUID query param to delete medicine.'}), 400)


def _update_medicine(request: Request, app):
    req_data = request.get_json(silent=True) or {}
    uuid = req_data.get('UUID') or req_data.get('uuid')
    if not uuid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: UUID'}), 400)

    updates = {}
    for key in ('Dosage', 'Quantity', 'Category', 'Price', 'ManufacturerName', 'Name'):
        if key in req_data:
            updates[key] = req_data.get(key)

    if 'Dosage' in updates:
        try:
            updates['Dosage'] = float(updates['Dosage']) if updates['Dosage'] is not None and str(updates['Dosage']) != '' else None
        except Exception:
            updates.pop('Dosage', None)
    if 'Quantity' in updates:
        try:
            updates['Quantity'] = int(updates['Quantity']) if updates['Quantity'] is not None and str(updates['Quantity']) != '' else None
        except Exception:
            updates.pop('Quantity', None)
    if 'Price' in updates:
        try:
            updates['Price'] = int(updates['Price']) if updates['Price'] is not None and str(updates['Price']) != '' else None
        except Exception:
            updates.pop('Price', None)

    if not updates:
        return make_response(jsonify({'status': 'failure', 'error': 'No updatable fields provided'}), 400)

    try:
        zcql = app.zcql()
        safe_uuid = str(uuid).replace("'", "\\'")
        rows = zcql.execute_query(f"SELECT ROWID FROM MedicineStock WHERE UUID = '{safe_uuid}'")
        row_id = None
        if rows:
            first = rows[0]
            if isinstance(first, dict) and len(first.keys()) == 1 and list(first.keys())[0] == 'MedicineStock':
                inner = list(first.values())[0]
                row_id = inner.get('ROWID') or inner.get('id') or inner.get('Id')
            else:
                row_id = first.get('ROWID') if isinstance(first, dict) else None
        if not row_id:
            return make_response(jsonify({'status': 'failure', 'error': 'Medicine not found for UUID'}), 404)

        table = app.datastore().table('MedicineStock')
        try:
            table.update_row(row_id, updates)
        except Exception:
            set_clauses = []
            for k, v in updates.items():
                if v is None:
                    set_clauses.append(f"{k}=NULL")
                elif isinstance(v, (int, float)):
                    set_clauses.append(f"{k}={v}")
                else:
                    safe_v = str(v).replace("'", "\\'")
                    set_clauses.append(f"{k}='{safe_v}'")
            zcql.execute_query(f"UPDATE MedicineStock SET {', '.join(set_clauses)} WHERE ROWID = '{row_id}'")

        return make_response(jsonify({'status': 'success', 'data': {'medicineId': uuid}}), 200)
    except Exception:
        logger.exception('Failed to update MedicineStock')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to update medicine'}), 500)


def generate_uuid():
    """Generate and return a new UUID string."""
    return str(uuid.uuid4())


def handler(request: Request):
    try:
        app = zcatalyst_sdk.initialize()
        logger = logging.getLogger()
        
        # Patient endpoints
        if request.path == "/add" and request.method == 'POST':
            return _create_patient(request, app)
        if request.path == "/all" and request.method == 'GET':
            return _list_patients(request, app)
        if request.path == "/patient" and request.method == 'GET':
            return _get_patient_by_phone(request, app)
        if request.method == 'DELETE' and request.path.startswith('/patient'):
            return _delete_patient(request, app)
        if request.path == "/patient" and request.method == 'PUT':
            return _update_patient(request, app)

        # Prescription endpoints (UUID-based)
        if request.path == "/prescription/add" and request.method == 'POST':
            return _create_prescription(request, app)
        if request.path == "/prescription/save" and request.method == 'POST':
            return _save_prescription_atomic(request, app)
        if request.path == "/prescription/all" and request.method == 'GET':
            return _list_prescriptions(request, app)
        if request.path.startswith("/prescription/get/") and request.method == 'GET':
            uuid = request.path.split("/prescription/get/")[1]
            return _get_prescription_by_uuid(request, app, uuid)
        if request.path.startswith("/prescription/update/") and request.method == 'PUT':
            uuid = request.path.split("/prescription/update/")[1]
            return _update_prescription(request, app, uuid)
        if request.path.startswith("/prescription/delete/") and request.method == 'DELETE':
            uuid = request.path.split("/prescription/delete/")[1]
            return _delete_prescription(request, app, uuid)
        
        # PrescribedMedicine endpoints
        if request.path == "/prescribedmedicine/add" and request.method == 'POST':
            return _create_prescribed_medicine(request, app)
        if request.path.startswith("/prescribedmedicine/all/") and request.method == 'GET':
            prescription_uuid = request.path.split("/prescribedmedicine/all/")[1]
            return _get_prescribed_medicines_by_prescription(request, app, prescription_uuid)
        if request.path.startswith("/prescribedmedicine/get/") and request.method == 'GET':
            rowid = request.path.split("/prescribedmedicine/get/")[1]
            return _get_prescribed_medicine_by_rowid(request, app, rowid)
        if request.path.startswith("/prescribedmedicine/update/") and request.method == 'PUT':
            rowid = request.path.split("/prescribedmedicine/update/")[1]
            return _update_prescribed_medicine(request, app, rowid)
        if request.path.startswith("/prescribedmedicine/delete/") and request.method == 'DELETE':
            rowid = request.path.split("/prescribedmedicine/delete/")[1]
            return _delete_prescribed_medicine(request, app, rowid)
        
        # MedicineStock endpoints
        if request.path == "/medicinestock/add" and request.method == 'POST':
            return _create_medicine(request, app)
        if request.path == "/medicinestock/all" and request.method == 'GET':
            return _list_medicines(request, app)
        if request.path == "/medicinestock" and request.method == 'GET':
            return _get_medicine_by_name(request, app)
        if request.path == "/medicinestock" and request.method == 'DELETE':
            return _delete_medicine(request, app)
        if request.path == "/medicinestock" and request.method == 'PUT':
            return _update_medicine(request, app)
        
        print('working')
    except Exception as err:
        logger.error(f"Exception in to_do_list_function :{err}")
        response = make_response(jsonify({
                 "error": "Internal server error occurred. Please try again in some time."
        }), 500)
        return response