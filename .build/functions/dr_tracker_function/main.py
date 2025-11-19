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
    req_data = request.get_json(silent=True) or {}
    frequency = req_data.get('Frequency')
    duration = req_data.get('Duration')
    special = req_data.get('SpecialInstruction')
    symptoms = req_data.get('CurrentSymptoms')
    patient_id = req_data.get('PatientId')

    # PatientId is required and must be unique (acts as primary key)
    if patient_id is None:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: PatientId'}), 400)

    # Convert numeric fields
    try:
        frequency = int(frequency) if frequency is not None and str(frequency) != '' else None
    except Exception:
        frequency = None
    try:
        duration = int(duration) if duration is not None and str(duration) != '' else None
    except Exception:
        duration = None

    # Ensure Patient exists (foreign key). PatientId is the PK of Patient table.
    try:
        zcql = app.zcql()
        safe_pid = str(patient_id).replace("'", "\\'")
        # Accept PatientId that matches either Patient.PatientId or Patient.Phonenumber
        patient_exists = zcql.execute_query(f"SELECT ROWID FROM Patient WHERE PatientId = '{safe_pid}' OR Phonenumber = '{safe_pid}'")
        # If not found, return 400
        if not patient_exists:
            return make_response(jsonify({'status': 'failure', 'error': 'Referenced Patient not found'}), 400)
    except Exception:
        logger.exception('Failed to verify referenced Patient')

    # Uniqueness check removed to allow multiple prescriptions per PatientId

    table = app.datastore().table('Prescription')
    row = table.insert_row({
        'Frequency': frequency,
        'Duration': duration,
        'SpecialInstruction': special,
        'CurrentSymptoms': symptoms,
        'PatientId': patient_id
    })

    # Prescription uses PatientId as its primary identifier; return that as the prescription id.
    resp = {'status': 'success', 'data': {'prescriptionId': patient_id}}
    return make_response(jsonify(resp), 200)


def _list_prescriptions(request: Request, app):
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
        query_result = zcql_service.execute_query(f"SELECT ROWID, Frequency, Duration, SpecialInstruction, CurrentSymptoms, PatientId FROM Prescription LIMIT {offset},{per_page}")
        items = []
        for item in query_result:
            if isinstance(item, dict) and len(item) == 1 and list(item.keys())[0] == 'Prescription':
                row = list(item.values())[0]
            else:
                row = item
            items.append({
                'id': row.get('ROWID') or row.get('id') or row.get('Id'),
                'Frequency': row.get('Frequency'),
                'Duration': row.get('Duration'),
                'SpecialInstruction': row.get('SpecialInstruction'),
                'CurrentSymptoms': row.get('CurrentSymptoms'),
                'PatientId': row.get('PatientId')
            })

        resp = {'status': 'success', 'data': {'prescriptions': items, 'hasMore': has_more, 'page': page, 'perPage': per_page, 'total': total}}
        return make_response(jsonify(resp), 200)
    except Exception:
        logger.exception('Failed to query Prescription')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescriptions'}), 500)


def _get_prescription_by_patient(request: Request, app):
    # Fetch by PatientId only. PatientId is the primary key for Prescription.
    pid = request.args.get('PatientId') or request.args.get('patientId') or request.args.get('Patient')
    if not pid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing PatientId query parameter'}), 400)
    try:
        zcql = app.zcql()
        safe_pid = str(pid).replace("'", "\\'")
        query_result = zcql.execute_query(f"SELECT * FROM Prescription WHERE PatientId = '{safe_pid}'")
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
        logger.exception('Failed to query Prescription by PatientId')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to fetch prescription'}), 500)


def _delete_prescription(request: Request, app):
    pid = request.args.get('PatientId') or request.args.get('patientId') or request.args.get('Patient')
    if not pid:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing PatientId query parameter'}), 400)
    try:
        # Find the prescription by PatientId and delete it. Prescription uses PatientId as primary key.
        zcql = app.zcql()
        safe_pid = str(pid).replace("'", "\\'")
        rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE PatientId = '{safe_pid}'")
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
            return make_response(jsonify({'status': 'failure', 'error': 'No prescription found for that PatientId'}), 404)
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
        logger.exception('Failed to delete Prescription by PatientId')
        return make_response(jsonify({'status': 'failure', 'error': 'Failed to delete prescription(s)'}), 500)


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


def _update_prescription(request: Request, app):
    """Update prescription fields by PatientId. Requires 'PatientId' in JSON body."""
    req_data = request.get_json(silent=True) or {}
    patient_id = req_data.get('PatientId') or req_data.get('patientId')
    if not patient_id:
        return make_response(jsonify({'status': 'failure', 'error': 'Missing required field: PatientId'}), 400)

    updates = {}
    for key in ('Frequency', 'Duration', 'SpecialInstruction', 'CurrentSymptoms'):
        if key in req_data:
            updates[key] = req_data.get(key)

    if 'Frequency' in updates:
        try:
            updates['Frequency'] = int(updates['Frequency']) if updates['Frequency'] is not None and str(updates['Frequency']) != '' else None
        except Exception:
            updates.pop('Frequency', None)
    if 'Duration' in updates:
        try:
            updates['Duration'] = int(updates['Duration']) if updates['Duration'] is not None and str(updates['Duration']) != '' else None
        except Exception:
            updates.pop('Duration', None)

    if not updates:
        return make_response(jsonify({'status': 'failure', 'error': 'No updatable fields provided'}), 400)

    try:
        zcql = app.zcql()
        safe_pid = str(patient_id).replace("'", "\\'")
        rows = zcql.execute_query(f"SELECT ROWID FROM Prescription WHERE PatientId = '{safe_pid}'")
        row_id = None
        if rows:
            first = rows[0]
            if isinstance(first, dict) and len(first) == 1 and list(first.keys())[0] == 'Prescription':
                inner = list(first.values())[0]
                row_id = inner.get('ROWID') or inner.get('id') or inner.get('Id')
            else:
                row_id = first.get('ROWID') if isinstance(first, dict) else None
        if not row_id:
            return make_response(jsonify({'status': 'failure', 'error': 'Prescription not found for PatientId'}), 404)

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

        return make_response(jsonify({'status': 'success', 'data': {'prescriptionId': patient_id}}), 200)
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
        if request.path == "/add" and request.method == 'POST':
            return _create_patient(request, app)
        if request.path == "/all" and request.method == 'GET':
            return _list_patients(request, app)
        if request.path == "/patient" and request.method == 'GET':
            return _get_patient_by_phone(request, app)
        if request.method == 'DELETE' and request.path.startswith('/patient'):
            return _delete_patient(request, app)

        # Prescription endpoints
        if request.path == "/prescription/add" and request.method == 'POST':
            return _create_prescription(request, app)
        if request.path == "/prescription/all" and request.method == 'GET':
            return _list_prescriptions(request, app)
        if request.path == "/prescription" and request.method == 'GET':
            return _get_prescription_by_patient(request, app)
        if request.path == "/prescription" and request.method == 'DELETE':
            return _delete_prescription(request, app)
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
        if request.path == "/patient" and request.method == 'PUT':
            return _update_patient(request, app)
        if request.path == "/prescription" and request.method == 'PUT':
            return _update_prescription(request, app)
        print('working')
    except Exception as err:
        logger.error(f"Exception in to_do_list_function :{err}")
        response = make_response(jsonify({
                 "error": "Internal server error occurred. Please try again in some time."
        }), 500)
        return response