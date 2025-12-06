import pandas as pd
from itemmaster.models import *
from itemmaster.serializer import *

def validate_supplier_data(index, data):
    errors = []
    try:
        # Unique checks
        if data.get('company_name') and SupplierFormData.objects.exclude(pk=data['id']).filter(company_name__iexact=data['company_name']).exists():
            errors.append("Company Name must be unique.")
        if data.get('gstin') and data['gstin'] != 'URP':
            if SupplierFormData.objects.filter(gstin=data['gstin']).exists():
                errors.append("GSTIN must be unique.")
            if len(data['gstin']) != 15:
                errors.append("Enter a valid GSTIN.")
                
        # if data.get('pan_no') and SupplierFormData.objects.filter(pan_no=data['pan_no']).exists():
        #     errors.append("PAN No must be unique.")
        
        # # GSTIN type check
        if data.get('gstin') == "URP" and (data.get('gstin_type') != 'UNREGISTERED/CONSUMER' and data.get('gstin_type') != 'Export/Import'):
            errors.append("GSTIN is URP -> GST Type must be UNREGISTERED/CONSUMER")
        try:
            Gst__Type =  GstType.objects.filter(gst_type=data.get('gstin_type')).first()
            if Gst__Type:
                data['gstin_type'] = Gst__Type.id
            else:
                errors.append("Gstin Type not Found")
        except Exception as e: 
            errors.append("Gstin Type not Found")
        

        # # Role flags
        if not data.get('customer') and not data.get('supplier'):
            errors.append("Supplier or Customer must be enabled")
            # # Supplier validations
        if data.get('supplier'):
            if data.get('supplier_group'):
                try:
                    sg = SupplierGroups.objects.get(name=data.get('supplier_group'))
                    data['supplier_group'] = sg.id
                except SupplierGroups.DoesNotExist:
                    errors.append(f"{data.get('supplier_group')} Not Found.")
                except Exception as e:
                    errors.append(f"supplier_group {e}.")
            else:
                errors.append("supplier_group is required.")
            if not isinstance(data.get('supplier_credited_period'), int):
                errors.append("Check the Supplier Credit Period.")
            # Customer validations
        if data.get('customer'):
            if not isinstance(data.get('customer_group'), int):
                errors.append("Check the Customer Group.")
            if not isinstance(data.get('sales_person'), int):
                errors.append("Check Sales Person.")
            if not isinstance(data.get('customer_credited_period'), int):
                errors.append("Check Customer Credit Period.")
            if not isinstance(data.get('credited_limit'), int):
                errors.append("Check Credited Limit.")
            # # Contact validation
        contacts = data.get('contact', [])
        if contacts:
            for contact in contacts:
                if not contact.get('contact_person_name'):
                    errors.append("Contact person name is required.")
                # if not contact.get('phone_number'):
                #     errors.append("Phone number is required.")
                if contact['salutation'] not in ['MR','MS','MRS','DR',"MS_"]:
                    errors.append("salutation is required.")
                if contact.get('phone_number'):
                    contact_details_item = ContactDetalis.objects.filter(phone_number=contact.get('phone_number')).first()
                    if contact_details_item:
                        contact['id'] = contact_details_item.id
        else:
            errors.append("Contact is required.")
        # Address validation
        addresses = data.get('address', [])
        if addresses:
            for address in addresses:
                if address['address_type'] not in ['Billing Address', "Shipping Address","Others"]:
                    errors.append("address_type is required.")
                for field in ['address_line_1', 'state', 'country', 'city', 'pincode']:
                    if not address.get(field):
                        errors.append(f"{field.replace('_', ' ')} is required.")
                if len(address.get('address_line_1')) >= 100:
                    errors.append("Address line 1 must be leas than 100 chartest")
                if len(address.get('address_line_2')) >= 100:
                    errors.append("Address line 2 must be leas than 100 chartest")
        else:
            errors.append("Address is required.")
    except Exception as e:
        print(e,"bs")

    return {"success": not errors, "error": errors}

def Save_To_DB(index, data):
    from itemmaster.mutations.Item_master_mutations import SaveContact, SaveAddress
    
    # save contact
    contact_result = SaveContact(data['contact'])
    if not contact_result['success']: 
        error_message = f"Row {index} ({data['Company Name']}): {contact_result['error']}"
        print("Validation errors:", error_message)
        log_error(error_message)
        return
    data['contact'] = contact_result['ids']

    # save address
    address_result = SaveAddress(data['address'])
    if not address_result['success']:
        error_message = f"Row {index} ({data['Company Name']}): {address_result['error']}"
        print("Validation errors:", error_message)
        log_error(error_message)
        return
    data['address'] = address_result['ids']

    serializers = ItemSupplierSerializer(data=data)

    if serializers.is_valid():
        print("saved index", index)
        serializers.save()
    else:
        error_message = f"Row--- {index} ({data['Company Name']}): {serializers.errors}"
        print("Validation errors:", error_message)
        log_error(error_message) 
        print()
    
def update_supplier_in_db(index, data):
    required_fields = ["company_name", "legal_name", "gstin_type", "gstin", "created_by"]
    missing = [f"{f.replace('_', ' ').title()} is required" for f in required_fields if not data.get(f)]

    if missing:
        return {"success": False, "error": missing, "index": index}
    validation = validate_supplier_data(index, data)
    if validation['success']:
        Save_To_DB(index, data)
        return validation
    else:

        return validation

def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

LOG_FILE = r"C:\Users\Jegathish.E.STDOMAIN\Downloads\supplier_update_errors.txt"

def log_error(message):
    with open(LOG_FILE, "a") as f:
        f.write(message + "\n")
def bulk_update_supplier_from_csv(csv_path):
    print("csv_path", csv_path)
    try:
        df = pd.read_csv(
            csv_path,
            dtype={'GSTIN': str},
        )
        df.columns = df.columns.str.strip()
        df = df.fillna('')  # Safe because we handle Int64 safely below
        for _, row in df.iterrows():
            if _  in [212, 215, 237, 358, 462, 475, 495, 512, 540, 541, 637,
                      845, 847, 999, 1082, 1083, 1128]:
                result = update_supplier_in_db(_, {
                    "id": None,
                    "company_name": row.get('Company Name'),
                    "legal_name": row.get('Legal Name'),
                    "customer": False,
                    "supplier": True,
                    "transporter": False,
                    "transporter_id": '',
                    "gstin_type": row.get('GSTIN Type'),
                    "gstin": row.get('GSTIN'),
                    "tcs": "",
                    "pan_no": row.get('PAN No') if row.get('PAN No') else None,
                    "contact": [{
                        "id":None,
                        "contact_person_name": row.get('Contact Person'),
                        "email": row.get('Email'),
                        "phone_number": row.get('Mobile'),
                        "default": True,
                        "salutation": row.get('Salutation'),
                        "other_no": row.get('Other Phone'),
                        "whatsapp_no": row.get('Whatspp')
                    }],
                    "address": [{
                        "id":None,
                        "address_line_1": row.get('First Line (Primary Address)'),
                        "address_line_2": row.get('Second Line (Primary Address)'),
                        "Default": True,
                        "state": row.get('State'),
                        "country": row.get('Country (Primary Address)'),
                        "address_type": row.get("Address Type"),
                        "city": row.get('City'),
                        "pincode": row.get('Pincode'),
                    }],
                    "supplier_group": row.get('Supplier Group'),
                    "supplier_credited_period": safe_int(row.get('Credit Period')),
                    "customer_group": None,
                    "sales_person": None,
                    "customer_credited_period": None,
                    "credited_limit": None,
                    "created_by": "3"
                })
                if not result['success']:
                    error_message = f"Row {_} ({row.get('Company Name')}): {result['error']}"
                    print("Validation errors:", error_message)
                    log_error(error_message)
    except Exception as e:
        error_message = f"Row {_} ({row.get('Company Name')}): {e}"
        print("Validation errors:", error_message)
        log_error(error_message)
        print(e,"final")