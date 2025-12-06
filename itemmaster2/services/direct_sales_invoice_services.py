from itemmaster2.models import *
from itemmaster2.Serializer import *
from itemmaster.mutations.Item_master_mutations import *
from django.db import transaction
import copy

class DirectSalesInvoiceService:
    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status = status
        self.errors = [] 
        self.info = info
        self.success = False
        self.direct_sales_invoice_obj = None
        self.gst_transaction = None
        self.currency = None
        self.tds = None
        self.tcs = None
        self.state_of_company = None
        self.item_details = None

    def process(self):
        
            # Start a database transaction
            with transaction.atomic():
                # 1. Run all validations
                if not self.run_validations():
                    return self.response()
                # 2. Save item details
                if not self.save_item_details():
                    return self.response()
                # 4. Save or update SalesInvoice
                if not self.save_sales_invoice():
                    return self.response()
                
                # All done
                self.success = True
                return self.response()
    
    
    def update_tax_item_details(self):
        updated_item_details = []
        item_details = self.kwargs.get("item_detail", [])
        # sales_account_ledger = self.kwargs.get("sales_account_ledger", [])
        gst = self.gst_transaction

        if gst.place_of_supply and  gst.place_of_supply == "Intrastate":
            if self.state_of_company.get("address__state", "") != self.kwargs.get("buyer_state"):
                self.errors.append("Company state is in intrastate but gst place of supply is interstate please check gst nature of transaction.")
                return self.response()
            
        elif gst.place_of_supply and gst.place_of_supply == "Interstate":
            if self.state_of_company.get("address__state", "") == self.kwargs.get("buyer_state"):
                self.errors.append("Company state is in interstate but gst place of supply is intrastate please check gst nature of transaction.")
                return self.response()
        
        if item_details:
            for item in item_details:
                item_ = DirectSalesInvoiceItemDetails.objects.filter(id=item.get("id")).first()
            
                item_master = item_.itemmaster
                qty = getattr(item, "qty", 0)
                rate = item.get("rate", 0)
                amount = qty * rate
                item['tds_percentage'] = ""
                item['tds_value'] = ""
                item['tcs_percentage'] = ""
                item['tcs_value'] = ""
                # TDS
                if self.tds == "P" and item_master.tds_link:
                    
                    item['tds_percentage'] = item_master.tds_link.percent_individual_with_pan
                    item['tds_value'] = (amount*item_master.tds_link.percent_individual_with_pan)/100
                elif self.tds == "O" and item_master.tds_link:
                    item['tds_percentage'] = item_master.tds_link.percent_other_with_pan
                    item['tds_value'] = (amount*item_master.tds_link.percent_other_with_pan)/100

                # TCS
                if self.tcs == "WP" and item_master.tcs_link:
                    item['tcs_percentage'] = item_master.tcs_link.percent_individual_with_pan
                    item['tcs_value'] = (amount*item_master.tcs_link.percent_individual_with_pan)/100
                elif self.tcs == "WO" and item_master.tcs_link:
                    item['tcs_percentage'] = item_master.tcs_link.percent_other_with_pan
                    item['tcs_value'] = (amount*item_master.tcs_link.percent_other_with_pan)/100
                elif self.tcs == "WOO" and item_master.tcs_link:
                    item['tcs_percentage'] = item_master.tcs_link.percent_other_without_pan
                    item['tcs_value'] = (amount*item_master.tcs_link.percent_other_without_pan)/100
                

                try:
                    is_specify_taxable = gst.gst_nature_type == "Specify" and gst.specify_type == "taxable"
                    if is_specify_taxable:
                        item.update({
                            'after_discount_value_for_per_item': "0",
                            'discount_percentage': "0",
                            'discount_value': "0",
                            'final_value': "0",
                            'amount': str(amount),
                        })

                        if gst.place_of_supply == "Intrastate":
                            cgst_rate = Decimal(gst.cgst_rate)
                            sgst_rate = Decimal(gst.sgst_rate)
                            cess_rate = Decimal(gst.cess_rate)

                            item['cgst'] = cgst_rate
                            item['sgst'] = sgst_rate
                            item['cess'] = cess_rate
                            item['tax'] = cgst_rate + sgst_rate
                            item['cgst_value'] = f"{(amount * cgst_rate) / 100:.2f}"
                            item['sgst_value'] = f"{(amount * sgst_rate) / 100:.2f}"
                            item['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                            item['igst'] = 0
                            item['igst_value'] = 0
                        else:
                            igst_rate = Decimal(gst.igst_rate)
                            cess_rate = Decimal(gst.cess_rate)

                            item['igst'] = igst_rate
                            item['cgst'] = 0
                            item['sgst'] = 0
                            item['cess'] = cess_rate
                            item['tax'] = igst_rate
                            item['cgst_value'] = 0
                            item['sgst_value'] = 0
                            item['igst_value'] = f"{(amount * igst_rate) / 100:.2f}"
                            item['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                        
                    elif gst.gst_nature_type == "As per HSN":
                        hsn = Hsn.objects.filter(id=item.get("hsn")).first()
                        item.update({
                            'after_discount_value_for_per_item': "0",
                            'discount_percentage': "0",
                            'discount_value': "0",
                            'final_value': "0",
                            'amount': f"{amount:.2f}",
                        })

                        company_state = str(self.state_of_company.get("address__state", "")).lower()
                        buyer_state = str(self.kwargs.get("buyer_state", "")).lower()
                        rate = Decimal(hsn.gst_rates.rate)
                        cess_rate = Decimal(hsn.cess_rate)

                        if buyer_state == company_state:
                            rate_half = rate / 2
                            item['cgst'] = rate_half
                            item['sgst'] = rate_half
                            item['igst'] = 0
                            item['cess'] = cess_rate
                            item['tax'] = rate
                            item['cgst_value'] = f"{(amount * rate_half) / 100:.2f}"
                            item['sgst_value'] = f"{(amount * rate_half) / 100:.2f}"
                            item['igst_value'] = 0
                            item['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                        else:
                            item['igst'] = rate
                            item['cgst'] = 0
                            item['sgst'] = 0
                            item['cess'] = cess_rate
                            item['tax'] = rate
                            item['cgst_value'] = 0
                            item['sgst_value'] = 0
                            item['igst_value'] = f"{(amount * rate) / 100:.2f}"
                            item['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"

                    else:  # Exempted or other nature types
                        item.update({
                            'after_discount_value_for_per_item': "0",
                            'discount_percentage': "",
                            'discount_value': "0",
                            'final_value': "0",
                            'sgst': "0",
                            'cgst': "0",
                            'igst': "0",
                            'cess': "0",
                            'tax': "0",
                            'cgst_value': "0",
                            'sgst_value': "0",
                            'igst_value': "0",
                            'cess_value': "0",
                            'amount': f"{amount:.2f}",
                        })

                    updated_item_details.append(item)

                except Exception as e:
                    self.errors.append(f"An exception occurred-- {str(e)}")

        self.item_details = updated_item_details
        self.errors.append("Tax details for items have been updated.")
        return self.response()

    def validate_tax(self):
        item_details = self.kwargs.get("item_detail", [])

        if not item_details:
            return True  # No item details to validate, considered valid

        for item_data in item_details:
            item_id = item_data.get("id")
            if not item_id:
                self.errors.append("Item ID is missing.")
                return False

            item_instance = DirectSalesInvoiceItemDetails.objects.filter(id=item_id).first()
            if not item_instance:
                self.errors.append(f'{item_id} not found in Direct Sales Invoice Item Details.')
                return False

            item_master = item_instance.itemmaster

            # --- TDS Validation ---
            tds_percentage = item_data.get("tds_percentage", 0)
            if self.tds == "P" and item_master and item_master.tds_link:
                if item_master.tds_link.percent_individual_with_pan != tds_percentage:
                    return False
            elif self.tds == "O" and item_master and item_master.tds_link:
                if item_master.tds_link.percent_other_with_pan != tds_percentage:
                    return False
            else:
                if tds_percentage and tds_percentage > 0:
                    return False

            # --- TCS Validation ---
            tcs_percentage = item_data.get("tcs_percentage", 0)
            if self.tcs == "WP" and item_master and item_master.tcs_link:
                if item_master.tcs_link.percent_individual_with_pan != tcs_percentage:
                    return False
            elif self.tcs == "WO" and item_master and item_master.tcs_link:
                if item_master.tcs_link.percent_other_with_pan != tcs_percentage:
                    return False
            elif self.tcs == "WOO" and item_master and item_master.tcs_link:
                if item_master.tcs_link.percent_other_without_pan != tcs_percentage:
                    return False
            else:
                if tcs_percentage and tcs_percentage > 0:
                    return False

            # --- GST Validation ---
            gst_type = self.gst_transaction.gst_nature_type
            specify_type = self.gst_transaction.specify_type
            pos = self.gst_transaction.place_of_supply

            if gst_type == "Specify" and specify_type == "taxable":
                if pos == "Intrastate":
                    if (
                        item_data.get("sgst") != self.gst_transaction.sgst_rate or
                        item_data.get("cgst") != self.gst_transaction.cgst_rate or
                        item_data.get("cess") != self.gst_transaction.cess_rate
                    ):
                        return False
                elif pos == "Interstate":
                    if (
                        item_data.get("igst") != self.gst_transaction.igst_rate or
                        item_data.get("cess") != self.gst_transaction.cess_rate
                    ):
                        return False
            elif gst_type == "As per HSN":
                hsn = Hsn.objects.filter(id=item_data.get("hsn")).first()
                if hsn:
                    total_tax = (item_data.get("sgst") or 0) + (item_data.get("cgst") or 0) + (item_data.get("igst") or 0)
                    if total_tax != hsn.gst_rates.rate or (item_data.get("cess") or 0) != (hsn.cess_rate or 0):
                        return False
            else:
                if item_data.get("sgst") or item_data.get("cgst") or item_data.get("igst") or item_data.get("cess"):
                    return False

        return True

    def run_validations(self):
        self.state_of_company = CompanyMaster.objects.all().values("address__state").first()
        if not self.validate_required_fields():
            return False
        if not self.update_status_id():
            return False
        if not self.validate_direct_sales_invoice():
            return False
        if not self.validate_numbering_serial():
            return False
        if not self.validate_foreign_keys():
            return False
        if not self.validate_invoice_itemdetails():
            return False
        if self.status == "Submit":
            if not self.validate_tax():
                
                self.update_tax_item_details()
                
        return len(self.errors) == 0
    
    def validate_direct_sales_invoice(self):
        if "id" in self.kwargs and self.kwargs['id']:
            try:
                self.direct_sales_invoice_obj = DirectSalesInvoice.objects.filter(id=self.kwargs['id']).first()
                self.gst_transaction = self.direct_sales_invoice_obj.gst_nature_transaction
                self.currency = self.direct_sales_invoice_obj.currency
                supplier = self.direct_sales_invoice_obj.buyer
                
                if supplier.tds and "P" in supplier.pan_no:
                    self.tds =  "P"
                elif supplier.tds and "P" not in supplier.pan_no:
                        self.tds =  "O"
                if supplier.tcs in ['SALES', "BOTH"]:
                    if supplier.pan_no and "P" in supplier.pan_no:
                        self.tcs =  "WP"
                    elif supplier.pan_no and "P" not in supplier.pan_no:
                        self.tcs =  "WO"
                    elif supplier.pan_no and "P" not in supplier.pan_no:
                        self.tcs =  "WOO"
                    
                return True
            except ObjectDoesNotExist:
                self.errors.append("Direct Sales invoice not Found.")
                return False
            except Exception as e:
                self.errors.append(f"An exception occurred {e}")
                return False
        else:
            self.direct_sales_invoice_obj = None
            return True

    def validate_required_fields(self):
        REQUIRED_FIELDS  = ['status','gst_nature_transaction' ,"direct_sales_invoice_date", 'due_date', 'buyer','buyer_address','buyer_contact_person'
                    ,'buyer_gstin_type',"buyer_gstin","buyer_state","buyer_place_of_supply","consignee","consignee_address",
                    "consignee_contact_person", "consignee_gstin_type", "consignee_gstin", "consignee_state", "consignee_place_of_supply",
                    "creadit_period","sales_person", "payment_term", "customer_po","customer_po_date", "department",
                    'terms_conditions', 'terms_conditions_text',"taxable_value" , "net_amount"]
        for field in REQUIRED_FIELDS :
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required')
        return len(self.errors) == 0
    
    def check_rate_range(self, item_master_instance, rate, currency=None):
        current_currency = None
        if currency:
            try:
                current_currency = CurrencyExchange.objects.get(id=currency)
            except Exception as e:
                print(e)
        if current_currency and current_currency.Currency.name != "Rupee":
            min_price = item_master_instance.item_min_price/current_currency.rate
        else:
            min_price = item_master_instance.item_min_price
        if min_price > rate:
            self.errors.append(f"{item_master_instance.item_part_code} amount is  less then allow value.")

    def update_status_id(self):
        if self.status:
            statusObjects = CommanStatus.objects.filter(name=self.kwargs["status"]
                                                        , table="Sales Invoice").first()
            if statusObjects:
                self.kwargs["status"] = statusObjects.id
                return True
            else:
                status = self.kwargs.get("status", "default_status")
                self.errors.append(f"Status '{status}' is not configured. Please contact support to add it.")
                return False

    def validate_foreign_keys(self):
        # reuse your existing ValidationForeignKeys helper
        fk_definitions = [
            {'field': 'terms_conditions', 'model_name': 'TermsConditions', 'appname': 'itemmaster'}]
        for fk in fk_definitions:
            if self.kwargs.get(fk['field']):
                result = ValidationForeignKeys(fk['appname'], fk['model_name'], self.kwargs[fk['field']])
                if not result['success']:
                    self.errors.append(result['error'])
                    return False
        return True
    
    def validate_numbering_serial(self):
        conditions = {
            'resource': 'Sales Invoice',
            'default': True,
            "department": self.kwargs["department"]
        }
        try:
            series = NumberingSeries.objects.filter(**conditions).first()
            if not series:
                self.errors.append("Numbering Serial not found.")
                return False
            else:
                return True
        except Exception as e:
            self.errors.append(str(e))
            return False

    def validate_invoice_itemdetails(self):
        item_details = self.kwargs.get("item_detail",[])
        sales_account_ledger = self.kwargs.get("sales_account_ledger",[])

        if len(item_details) == 0 and  len(sales_account_ledger) == 0:
            self.errors.append(f'Item Details and Sales account ledger not found.')
            return False


        if len(item_details) > 0:
            item_lable = []
            instance_list = []
            REQUIRED_FIELDS = ['itemmaster',"description","uom","qty","rate","hsn","tax","amount"]
            for item in item_details:
                part_code = ItemMaster.objects.filter(id=item.get("itemmaster")).first()
                item_lable.append(part_code)
                if not part_code:
                    self.errors.append(f"Item Master instance Not found.")
                    return False
                for field in REQUIRED_FIELDS:
                    if item.get(field) is None:
                        self.errors.append(f'{part_code} → {field} is required.')

                if item.get('id'):
                    instance = DirectSalesInvoiceItemDetails.objects.filter(id=item.get("id")).first()
                    if not instance:
                        self.errors.append(f"{part_code} Direct SalesInvoice Item Details instance Not found.")
                        return False
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
            
            if len(self.errors) != 0:
                return False
            
            Item_error = validate_common_data(item_details,instance_list,
                                            DirectSalesInvoiceItemDetailsSerialzer,item_lable, self.info.context)
                    
            if len(Item_error) > 0:
                self.errors.extend(Item_error)
                return False
         
        return True

    def save_item_details(self):
        try:
            item_details = self.kwargs.get("item_detail",[])

            if len(item_details) > 0:
                item_lable = []
                instance_list = []
                for item in item_details:
                    part_code = ItemMaster.objects.filter(id=item.get("itemmaster")).first()
                    item_lable.append(part_code)
                    if item.get('id'):
                        instance = DirectSalesInvoiceItemDetails.objects.filter(id=item.get("id")).first()
                        instance_list.append(instance)
                    else:
                        instance_list.append(None)
                
                itemDetails_result = save_common_data(item_details,instance_list,
                                                DirectSalesInvoiceItemDetailsSerialzer,item_lable, self.info.context)
                        
                if not itemDetails_result.get("success"):
                    self.errors.extend(itemDetails_result.get("error"))
                    return False
                else:
                    self.kwargs['item_detail'] = itemDetails_result.get("ids")
            return True
        except Exception as e :
            print(e,"eeeee")

    def save_sales_invoice(self):
        item_details_old_id = []
        if self.direct_sales_invoice_obj:
            item_details_old_id = set(self.direct_sales_invoice_obj.item_detail.values_list('id', flat=True))
            
            serializer = DirectSalesInvoiceSerialzer(self.direct_sales_invoice_obj,
                                                data=self.kwargs, partial=True, context={'request': self.info.context})
        else:
            serializer = DirectSalesInvoiceSerialzer(data=self.kwargs, context={'request': self.info.context})

        if serializer.is_valid():
            try: 
                serializer.save() 
                self.direct_sales_invoice_obj = serializer.instance
                new_itemdetails_ids = list(serializer.instance.item_detail.values_list('id', flat=True))

                deleteCommanLinkedTable(item_details_old_id,
                                        new_itemdetails_ids,
                                        DirectSalesInvoiceItemDetails)
                
                self.success = True
                return True
            except Exception as e: 
                self.errors.append(str(e))
                self.success = False
                return False
        else:
            for field, msgs in serializer.errors.items():
                self.errors.append(f"{field}: {', '.join(msgs)}")
            self.success = False
            return False

    def response(self):
        return {"direct_sales_invoice_obj":self.direct_sales_invoice_obj,
            "success":self.success,
            "errors":self.errors,
            "item_detail":self.item_details,
            # "other_income_charges":self.other_income_charges,
        
            }



from decimal import Decimal

def sales_invoice_general_update(data):
    valid_serializers = []
    errors = []
    credits = data.get("credits", [])
    debit = data.get("debit", {})

    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "direct_sales_voucher_no", "account", "created_by"]

    # Process credits
    for idx, credit in enumerate(credits):
        for field in REQUIRED_FIELDS + ["credit"]:
            if credit.get(field) in [None, ""]:
                errors.append(f"credit [{idx}] → '{field}' is required.")
        
        credit_amount = credit.get("credit", 0)
        credits_amount += credit_amount

        serializer = AccountsGeneralLedgerSerializer(data=credit)
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"credit [{idx}] → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)

    # Process debit
    for field in REQUIRED_FIELDS + ["debit"]:
        if debit.get(field) in [None, ""]:
            errors.append(f"debit → '{field}' is required.")

    serializer = AccountsGeneralLedgerSerializer(data=debit)
    if not serializer.is_valid():
        for field, error in serializer.errors.items():
            errors.append(f"debit → {field}: {'; '.join(map(str, error))}")
    else:
        valid_serializers.append(serializer)

    # Compare debit and credit amounts
    debit_amount = Decimal(debit.get("debit", 0))
    if credits_amount != debit_amount:
        errors.append(f"Debit amount ({debit_amount}) and credit amount ({credits_amount}) do not match.")

    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}
