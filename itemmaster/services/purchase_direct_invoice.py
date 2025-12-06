from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from itemmaster.Utils.stockAddtinons import *
from django.db.models import Max
import copy


class DirectPurchaseInvoiceService:
    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status_text = status
        self.status = None
        self.errors = []
        self.info = info
        self.success = False
        self.direct_purchase_invoice = None
        self.item_details_instances = []
        self.item_details_serializer = []
        self.account_serializer = []
        self.new_account = []
        self.account_instance = []
        self.gst_transaction = None
        self.company = None
        self.currency = None
        self.tds = None
        self.tcs = None
        self.item_details = None
        self.other_expense = []
        self.other_expense_serializer = []
        self.other_expense_instance = []

    def process(self) ->bool:
        with transaction.atomic():
            if self.status_text == "Draft": 
                if not self.validate_required_fields(): 
                    return self.response()
                
                if not self.update_status():
                    return self.response()
                
                if not self.get_direct_invoice():
                    return self.response() 
                
                if not self.validate_numbering_serial():
                    return self.response() 
                
                if not self.validate_invoice_itemdetails():
                    return self.response() 
                
                if not self.validate_expense():
                    return self.response() 
                if not self.validate_account():
                    return self.response() 
                
                
                if not self.save_item_details():
                    return self.response() 
                
                if not self.save_expences():
                    return self.response() 
                if not self.save_account():
                    return self.response() 
                
                if not self.save_purchase_direct_invoice():
                    return self.response()
                 
                self.success = True
            elif self.status_text == "Submit":
                self.company_obj = company_info()
                if self.company_obj is None:
                    self.errors.append("Company data not found.")
                    return self.response()
                
                if not self.validate_required_fields():
                    return self.response()
                
                if not self.update_status():
                    return self.response()
                
                if not self.get_direct_invoice():
                    return self.response()
                
                if not self.validate_tax():
                    self.update_tax_item_details() 
                    return self.response()
                
                self.direct_purchase_invoice.status = self.status
                self.direct_purchase_invoice.save()
                self.success = True
            else:
                self.errors.append(f"{self.status_text} Unexpected status.")
            return self.response()
    
    def validate_required_fields(self) ->bool:
        try:
            REQUIRED_FIELDS  = ['status','gst_nature_transaction' ,"direct_purchase_invoice_date", 'due_date', 'supplier',
                                'supplier_address','supplier_contact_person','supplier_gstin_type',"supplier_gstin",
                                "exchange_rate", "supplier_state","supplier_place_of_supply", "creadit_period","creadit_date",
                                "department",'terms_conditions', 'terms_conditions_text', "taxable_value", "net_amount"]
            for field in REQUIRED_FIELDS:
                if self.kwargs[field] is None:
                    self.errors.append(f'{field} is required')
            
            if not self.kwargs.get("item_detail",[]) and not self.kwargs.get('accounts', []):
                self.errors.append(f'At least one item detail or account is required.')
            return len(self.errors) == 0
        except Exception as e :
            self.errors.append(f"Error in validate_required_fields-{e}")
    
    def update_status(self) ->bool: 
        try:
            if self.status_text:
                statusObjects = CommanStatus.objects.filter(name=self.status_text
                                                            , table="Sales Invoice").first()
                if statusObjects:
                    self.kwargs["status"] = statusObjects.id
                    self.status = statusObjects
                    return True
                else:
                    status = self.kwargs.get("status", "default_status")
                    self.kwargs["status"]
                    self.errors.append(f"Status '{status}' is not configured. Please contact support to add it.")
                    return False
        except Exception as e:
            self.errors.append(f"Error in update_status {str(e)}")  
    
    def get_direct_invoice(self) ->bool:
        
        if not self.kwargs.get('item_detail', []) and not self.kwargs.get('accounts', []):
            self.errors.append("Item Details or account any one must be enter.")
            return False

        try:
            if "id" in self.kwargs and self.kwargs['id']:
                try:
                    self.direct_purchase_invoice = DirectPurchaseinvoice.objects.get(id=self.kwargs['id']) 
                    self.gst_transaction = self.direct_purchase_invoice.gst_nature_transaction 
                    self.currency = self.direct_purchase_invoice.currency
                    supplier = self.direct_purchase_invoice.supplier
                    
                    if supplier.tds and "P" in supplier.pan_no:
                        self.tds =  "P"
                    elif supplier.tds and "P" not in supplier.pan_no:
                            self.tds =  "O"
                    if supplier.tcs in ['PURCHASE', "BOTH"]:
                        if supplier.pan_no and "P" in supplier.pan_no:
                            self.tcs =  "WP"
                        elif supplier.pan_no and "P" not in supplier.pan_no:
                            self.tcs =  "WO"
                        elif supplier.pan_no and "P" not in supplier.pan_no:
                            self.tcs =  "WOO"
                    
                    self.item_details_instances = list(self.direct_purchase_invoice.item_detail.values_list("id",flat=True)) 
                    self.account_instance = list(self.direct_purchase_invoice.directpurchaseinvoiceaccount_set.values_list("id",flat=True))
                    self.other_expense_instance = list(self.direct_purchase_invoice.other_expence_charge.values_list("id",flat=True))

                    return True
                except ObjectDoesNotExist:
                    self.errors.append("Direct Sales invoice not Found.")
                    return False
                except Exception as e:
                    self.errors.append(f"An exception occurred {e}")
                    return False
            else:
                self.direct_purchase_invoice = None
                return True
        except Exception as e:
            self.errors.append(f"Error in get_direct_invoice {str(e)}")  
    
    def validate_numbering_serial(self) ->bool:
        conditions = {
            'resource': 'Direct Purchase Invoice',
            'default': True,
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
    
    def validate_invoice_itemdetails(self) ->bool:
        try:
            item_details = self.kwargs.get("item_detail",[])
            if not item_details:
                
                return True
            
            if len(item_details) > 0:
                item_lables = []
                instance_list = []
                
                for item in item_details: 
                    part_code = ItemMaster.objects.filter(id=item.get("itemmaster")).first()
                    item_lables.append(part_code) 
                    if not part_code:
                        self.errors.append(f"Item Master instance Not found.")
                        return False
                    for field in ['itemmaster',"description","uom","qty","rate","hsn","tax","amount"]: 
                        if item.get(field) is None:
                            self.errors.append(f'{part_code} → {field} is required.')
                    
                    if item.get('id'):
                        instance = DirectPurchaseInvoiceItemDetails.objects.filter(id=item.get("id")).first()
                        if not instance:
                            self.errors.append(f"{part_code} Direct Purchase Invoice Item Details instance Not found.")
                            return False
                        instance_list.append(instance)
                    else:
                        instance_list.append(None) 
                if len(self.errors) != 0:
                    return False 
     
                item_result = validate_common_data_and_send_with_instance(
                    item_details, instance_list, DirectPurchaseInvoiceItemDetailsSerializer,
                    item_lables, self.info.context)
                 
                if item_result.get("error"): 
                    self.errors.extend(item_result["error"])
                    return False
                
                self.item_details_serializer = item_result.get("instance")
                return True
        except Exception as e:
            self.errors.append(f"An exception occurred while validate item details: {str(e)}")
            return False
    
    def validate_account(self)-> bool:
        instance_list = []
        accounts = self.kwargs.get('accounts', [])
        item_labels = []

        if not accounts:
            return True
        
        for account in accounts:
            acount_id = account.get("id")
            account_master_instance = AccountsMaster.objects.filter(id=account.get("account_master")).first()

            if not account_master_instance :
                self.errors.append(f"{account.get('account_master')} not found in Account Master.")
                continue

            item_labels.append(str(account_master_instance.accounts_name))

            for field in ["account_master",   "amount"]:
                if account.get(field) is None:
                    self.errors.append(f'{account_master_instance} → {field} is required.')
            
            if acount_id:
                instance = DirectPurchaseInvoiceAccount.objects.filter(id=acount_id).first()

                if not instance:
                    self.errors.append(f'{account_master_instance.accounts_name} → Account instance not Found.')
                instance_list.append(instance)
            else:
                instance_list.append(None)
        
        if self.errors:
            return False
        
        item_result = validate_common_data_and_send_with_instance(
                accounts, instance_list,
                DirectPurchaseInvoiceAccountSerializer,
                item_labels,
                self.info.context)
        if item_result.get("error"): 
            self.errors.extend(item_result["error"])
            return False 
        self.account_serializer.extend(item_result.get("instance"))
        return True
    
    def validate_expense(self) ->bool:
        instance_list = []
        item_labels = [] 
        other_expences = self.kwargs.get('other_expence_charge', [])
        if len(other_expences) == 0:
            return True
        
        try:
            for expences in other_expences: 
                
                charge = OtherExpenses.objects.filter(id=expences.get("other_expenses_id")).first()
                
                if not charge:
                    self.errors.append("Other Expense charge not found.")
                    continue

                item_labels.append(charge.name)
                

                for field in ["other_expenses_id","hsn",  "amount"]:
                    if expences.get(field) is None:
                        self.errors.append(f'{charge.name} → {field} is required.')
                if len(self.errors) > 0:
                    continue
                instance = None
                if expences.get("id"):
                    instance = OtherExpensespurchaseOrder.objects.filter(id=expences.get("id")).first()
                    if not instance:
                        self.errors.append("Other Expense instance not found.")
                        continue
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                
        
            if len(self.errors) > 0:
                return False
            
            expense_result = validate_common_data_and_send_with_instance(
                other_expences, instance_list,
                OtherExpensespurchaseOrderSerializer,
                item_labels,
                self.info.context
            ) 
            if expense_result.get("error"):
                self.errors.extend(expense_result["error"])
                return False
            
            self.other_expense_serializer.extend(expense_result.get("instance"))
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred while saving other expence: {str(e)}")
            return False

    def save_item_details(self) ->bool:
        item_detail_ids = []
        try:
            for serializer in self.item_details_serializer:
                if serializer: 
                    serializer.save()
                    item_detail_ids.append(serializer.instance.id)

            self.kwargs['item_detail'] = item_detail_ids
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False
    
    def save_expences(self) ->bool:
        other_expence_ids = []
        try:
            for serializer in self.other_expense_serializer:
                if serializer:
                    serializer.save()
                    other_expence_ids.append(serializer.instance.id)

            self.kwargs['other_expence_charge'] = other_expence_ids
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving expenses: {e}")
            return False
    
    def save_account(self)-> bool:
       
        if not self.account_serializer:
            return True
        
        try:
            for serializer_account in self.account_serializer:
                if serializer_account:
                    serializer_account.save()
                    self.new_account.append(serializer_account.instance)
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred while saving account : {str(e)}")
            return False

    def save_purchase_direct_invoice(self) ->bool:
        try:
            serializer = None
            if self.direct_purchase_invoice:
                serializer = DirectPurchaseinvoiceSerializer(self.direct_purchase_invoice,
                                                    data=self.kwargs, partial=True,
                                                    context={'request': self.info.context})
            else:
                serializer = DirectPurchaseinvoiceSerializer(data=self.kwargs, partial=True,
                                                    context={'request': self.info.context})
            
            if serializer and serializer.is_valid():
                serializer.save()
                self.direct_purchase_invoice = serializer.instance
                

                for account in self.new_account:
                    account.direct_purchase_invoice = self.direct_purchase_invoice
                    account.save()
                
                deleteCommanLinkedTable(self.item_details_instances, list(self.direct_purchase_invoice.item_detail.values_list("id", flat=True)), DirectPurchaseInvoiceItemDetails)
                deleteCommanLinkedTable(self.account_instance, list(self.direct_purchase_invoice.directpurchaseinvoiceaccount_set.values_list("id",flat=True)), DirectPurchaseInvoiceAccount)
                deleteCommanLinkedTable(self.other_expense_instance, list(self.direct_purchase_invoice.other_expence_charge.values_list("id",flat=True)), OtherExpensespurchaseOrder)
                
                return True
            
            else:
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                            for field, error in serializer.errors.items()])
                return False
        except Exception as e:
            self.errors.append(f"An exception error occurred while saving purchase invoice {str(e)}")
            return False

    def validate_tax(self) ->bool:
        try:
            gst_type = self.gst_transaction.gst_nature_type
            specify_type = self.gst_transaction.specify_type
            pos = self.gst_transaction.place_of_supply
            # if not item_details:
            #     self.errors.append("Item details not found in tax validation.")
            #     return False  # No item details to validate, considered valid
            if self.item_details_instances and self.direct_purchase_invoice.item_detail.exists(): 
                
                for item_data in self.direct_purchase_invoice.item_detail.all():
                     
                    item_master = item_data.itemmaster 
                    # --- TDS Validation ---
                    tds_percentage = (item_data.tds_percentage or 0)
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
                    tcs_percentage = (item_data.tcs_percentage or 0)
    
                    if self.tcs == "WP" and item_master and item_master.tcs_link:
                        if item_master.tcs_link.percent_individual_with_pan != tcs_percentage:
                            return False
                    elif self.tcs == "WO" and item_master and item_master.tcs_link:
                        if item_master.tcs_link.percent_other_with_pan != tcs_percentage:
                            return False
                    elif self.tcs == "WOO" and item_master and item_master.tcs_link:
                        if item_master.tcs_link.percent_other_without_pan != tcs_percentage:
                            return False
                    # else:
                    #     if tcs_percentage and tcs_percentage > 0:
                    #         return False 
                    # --- GST Validation ---
                   

                    if gst_type == "Specify" and specify_type == "taxable":
                        if pos == "Intrastate": 
                            if (
                                (item_data.sgst or 0) != (self.gst_transaction.sgst_rate or 0) or
                                (item_data.cgst or 0) != (self.gst_transaction.cgst_rate or 0) or
                                (item_data.cess or 0) != (self.gst_transaction.cess_rate or 0)
                            ): 
                                return False
                        elif pos == "Interstate":
                            if (
                                (item_data.igst or 0) != self.gst_transaction.igst_rate or
                                (item_data.cess or 0) != self.gst_transaction.cess_rate
                            ):
                                return False
                    elif gst_type == "As per HSN":
                        hsn_id = getattr(item_data, "hsn_id", None) 
                        hsn = Hsn.objects.filter(id=hsn_id).first() 
                        if hsn:
                            total_tax = (item_data.sgst or 0) + (item_data.cgst or 0) + (item_data.igst or 0)
                            if total_tax != hsn.gst_rates.rate or (item_data.cess or 0) != (hsn.cess_rate or 0):
                                return False
                    else:
                        if item_data.sgst or item_data.cgst or item_data.igst or item_data.cess:
                            return False
                    return True
   
            if self.account_instance:
                for item in self.direct_purchase_invoice.directpurchaseinvoiceaccount_set.all():
                    account_master = item.account_master
                    if not item.hsn:
                        continue
                    if gst_type == "Specify" and specify_type == "taxable":
                        if pos == "Intrastate":
                            if (
                                item.sgst != self.gst_transaction.sgst_rate or
                                item.cgst != self.gst_transaction.cgst_rate or
                                item.cess != self.gst_transaction.cess_rate
                            ):
                                return False
                        elif pos == "Interstate":
                            if (
                                item.igst != self.gst_transaction.igst_rate or
                                item.cess != self.gst_transaction.cess_rate
                            ):
                                return False

                    elif gst_type == "As per HSN":
                        hsn = item.hsn
                        if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != hsn.gst_rates.rate or (item.cess or 0) !=(hsn.cess_rate or 0):
                            return False

                    else:
                        # Fallback check — if all 4 rates are present, reject
                        if item.sgst or item.cgst or item.igst or item.cess:
                            return False
                    
                    # TDS
                    if self.tds == "P" and account_master.tds_link:
                        if account_master.tds_link.percent_individual_with_pan != item.tds_percentage:
                            return False
                    elif self.tds == "O" and account_master.tds_link:
                            if account_master.tds_link.percent_other_with_pan != item.tds_percentage:
                                return False
                    else:
                        if item.tds_percentage and  item.tds_percentage > 0:
                            return False
                    
                    # TCS
                    if self.tcs == "WP" and account_master.tcs_link:
                        if account_master.tcs_link.percent_individual_with_pan != item.tcs_percentage:
                            return False
                        
                    elif self.tcs == "WO" and account_master.tcs_link:
                        if account_master.tcs_link.percent_other_with_pan != item.tcs_percentage:
                            return False
                        
                    elif self.tcs == "WOO" and account_master.tcs_link:
                        if account_master.tcs_link.percent_other_without_pan != item.tcs_percentage:
                            return False
                        
                    else:
                        if item.tcs_percentage and item.tcs_percentage > 0:
                            return False

      
            if self.direct_purchase_invoice.other_expence_charge.exists():
                for charges in self.direct_purchase_invoice.other_expence_charge.all():
                    if gst_type == "Specify" and specify_type == "taxable":
                        if pos == "Intrastate": 
                            if (
                                (charges.sgst or 0) != (self.gst_transaction.sgst_rate or 0) or
                                (charges.cgst or 0) != (self.gst_transaction.cgst_rate or 0) or
                                (charges.cess or 0) != (self.gst_transaction.cess_rate or 0)
                            ): 
                                return False
                        elif pos == "Interstate":
                            if (
                                (charges.igst or 0) != self.gst_transaction.igst_rate or
                                (charges.cess or 0) != self.gst_transaction.cess_rate
                            ):
                                return False
                    elif gst_type == "As per HSN":
                        hsn =charges.hsn
                        
                        if hsn:
                            total_tax = (charges.sgst or 0) + (charges.cgst or 0) + (charges.igst or 0)
                            if total_tax != hsn.gst_rates.rate or (charges.cess or 0) != (hsn.cess_rate or 0):
                                return False
                    else:
                        if charges.sgst or charges.cgst or charges.igst or charges.cess:
                            return False
                    return True
 



            return True
        except Exception as e:
            self.errors.append(f"error in validate_tax {str(e)}")  
            
    def convert_decimals_to_str(self, data):
        if isinstance(data, list):
            return [self.convert_decimals_to_str(item) for item in data]
        elif isinstance(data, dict):
            return {
                key: self.convert_decimals_to_str(value)
                for key, value in data.items()
            }
        elif isinstance(data, Decimal):
            return str(data)
        else:
            return data
        
    def update_tax_item_details(self):
        try:
            updated_item_details = []
            updated_accounts = []
            company_state= str(self.company_obj.address.state).lower()
            supplier_status = str(self.kwargs.get("supplier_state", "")).lower()
            item_details = self.direct_purchase_invoice.item_detail.all()
            other_expence_charge = self.kwargs.get('other_expence_charge', [])
            if not item_details:
                self.errors.append("Item details not found in update tax.")
                return False  # No item details to validate, considered valid
            
            gst = self.gst_transaction
            gst_type = self.gst_transaction.gst_nature_type
            specify_type = self.gst_transaction.specify_type
            if self.company_obj and self.company_obj.address.state and  gst.place_of_supply == "Intrastate":
                if self.company_obj.address.state != self.kwargs.get("supplier_state"):
                    self.errors.append("Company state is in intrastate but gst place of supply is interstate please check gst nature of transaction.")
                    return False
            elif self.company_obj and self.company_obj.address.state and  gst.place_of_supply == "Interstate":
                if self.company_obj.address.state == self.kwargs.get("supplier_state"):
                    self.errors.append("Company state is in intrastate but gst place of supply is interstate please check gst nature of transaction.")
                    return False

            for item in item_details:
                itemaster = item.itemmaster
                qty = item.qty
                rate = item.rate
                amount = qty*rate
                data = {
                    "index" : item.index,
                    "id" : item.id,
                    "tds_percentage":"",
                    "tds_value" :"",
                    "tcs_percentage" :"",
                    "tcs_value" :"",
                    "after_discount_value_for_per_item" : "",
                    "discount_percentage" :"",
                    "discount_value" :"",
                    "final_value" : "",
                    'sgst': "0",
                    'cgst': "0",
                    'igst': "0",
                    'cess': "0",
                    'tax' : "0",
                    'cgst_value': "0",
                    'sgst_value': "0",
                    'igst_value': "0",
                    'cess_value': "0",
                    'amount': f"{amount:.2f}",
                }
                
                # TDS
                if self.tds == "P" and itemaster.tds_link:
                    data['tds_percentage'] = itemaster.tds_link.percent_individual_with_pan
                    data['tds_value'] = (amount*itemaster.tds_link.percent_individual_with_pan)/100
                elif self.tds == "O" and itemaster.tds_link:
                    data['tds_percentage'] = itemaster.tds_link.percent_other_with_pan
                    data['tds_value'] = (amount*itemaster.tds_link.percent_other_with_pan)/100

                # TCS
                if self.tcs == "WP" and itemaster.tcs_link:
                    data['tcs_percentage'] = itemaster.tcs_link.percent_individual_with_pan
                    data['tcs_value'] = (amount*itemaster.tcs_link.percent_individual_with_pan)/100
                elif self.tcs == "WO" and itemaster.tcs_link:
                    data['tcs_percentage'] = itemaster.tcs_link.percent_other_with_pan
                    data['tcs_value'] = (amount*itemaster.tcs_link.percent_other_with_pan)/100
                elif self.tcs == "WOO" and itemaster.tcs_link:
                    data['tcs_percentage'] = itemaster.tcs_link.percent_other_without_pan
                    data['tcs_value'] = (amount*itemaster.tcs_link.percent_other_without_pan)/100

                is_specify_taxable = gst.gst_nature_type == "Specify" and gst.specify_type == "taxable"
                if is_specify_taxable:
                    if gst.place_of_supply == "Intrastate":
                        cgst_rate = Decimal(gst.cgst_rate or 0)
                        sgst_rate = Decimal(gst.sgst_rate or 0)
                        cess_rate = Decimal(gst.cess_rate or 0)
                        data['cgst'] = cgst_rate
                        data['sgst'] = sgst_rate
                        data['cess'] = cess_rate
                        data['tax'] = cgst_rate + sgst_rate
                        data['cgst_value'] = f"{(amount * cgst_rate) / 100:.2f}"
                        data['sgst_value'] = f"{(amount * sgst_rate) / 100:.2f}"
                        data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                        data['igst'] = 0
                        data['igst_value'] = 0
                    else:
                        igst_rate = Decimal(gst.igst_rate or 0)
                        cess_rate = Decimal(gst.cess_rate or 0)
                        data['igst'] = igst_rate
                        data['cgst'] = 0
                        data['sgst'] = 0
                        data['cess'] = cess_rate
                        data['tax'] = igst_rate
                        data['cgst_value'] = 0
                        data['sgst_value'] = 0
                        data['igst_value'] = f"{(amount * igst_rate) / 100:.2f}"
                        data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                elif gst.gst_nature_type == "As per HSN":
                    hsn = item.hsn
                    
                    tax_rate = Decimal(hsn.gst_rates.rate or 0)
                    cess_rate = Decimal(hsn.cess_rate or 0) 
                    if supplier_status == company_state:
                        rate_tax_half = tax_rate / 2
                        data['cgst'] = rate_tax_half
                        data['sgst'] = rate_tax_half
                        data['igst'] = 0
                        data['cess'] = cess_rate
                        data['tax'] = tax_rate
                        data['cgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        data['sgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        data['igst_value'] = 0
                        data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}" 
                    else:
                        data['igst'] = tax_rate
                        data['cgst'] = 0
                        data['sgst'] = 0
                        data['cess'] = cess_rate
                        data['tax'] = tax_rate
                        data['cgst_value'] = 0
                        data['sgst_value'] = 0
                        data['igst_value'] = f"{(amount * tax_rate) / 100:.2f}"
                        data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                else:
                    pass
                updated_item_details.append(data)

            for account in self.direct_purchase_invoice.directpurchaseinvoiceaccount_set.all():
                amount = account.amount
                account_master = account.account_master
                account_data = {
                    "index" : account.index,
                    "id" : account.id,
                    "tds_percentage": "0",
                    "tds_value" : "0",
                    "tcs_percentage" :"0",
                    "tcs_value" : "0",
                    'sgst': "0",
                    'cgst': "0",
                    'igst': "0",
                    'cess': "0",
                    'tax' : "0",
                    'cgst_value': "0",
                    'sgst_value': "0",
                    'igst_value': "0",
                    'cess_value': "0",
                    'amount': f"{amount:.2f}",
                }
                if  self.tds == "P" and account_master.tds_link:
                    account_data['tdsPercentage'] = str(account_master.tds_link.percent_individual_with_pan)
                    account_data['tdsValue'] = str((amount*account_master.tds_link.percent_individual_with_pan)/100)
                elif self.tds == "O" and account_master.tds_link:
                    account_data['tdsPercentage'] = str(account_master.tds_link.percent_other_with_pan)
                    account_data['tdsValue'] = str((amount*account_master.tds_link.percent_other_with_pan)/100)
                
                # TCS
                if self.tcs == "WP" and account_master.tcs_link:
                    account_data['tcsPercentage'] = str(account_master.tcs_link.percent_individual_with_pan)
                    account_data['tcsValue'] = str((amount*account_master.tcs_link.percent_individual_with_pan)/100)
                elif self.tcs == "WO" and account_master.tcs_link:
                    account_data['tcsPercentage'] = str(account_master.tcs_link.percent_other_with_pan)
                    account_data['tcsValue'] = str((amount*account_master.tcs_link.percent_other_with_pan)/100)
                elif self.tcs == "WOO" and account_master.tcs_link:
                    account_data['tcsPercentage'] = str(account_master.tcs_link.percent_other_without_pan)
                    account_data['tcsValue'] = str((amount*account_master.tcs_link.percent_other_without_pan)/100)

                is_specify_taxable = gst.gst_nature_type == "Specify" and gst.specify_type == "taxable"
                if is_specify_taxable:
                    if gst.place_of_supply == "Intrastate":
                        cgst_rate = Decimal(gst.cgst_rate or 0)
                        sgst_rate = Decimal(gst.sgst_rate or 0)
                        cess_rate = Decimal(gst.cess_rate or 0)
                        account_data['cgst'] = cgst_rate
                        account_data['sgst'] = sgst_rate
                        account_data['cess'] = cess_rate
                        account_data['tax'] = cgst_rate + sgst_rate
                        account_data['cgst_value'] = f"{(amount * cgst_rate) / 100:.2f}"
                        account_data['sgst_value'] = f"{(amount * sgst_rate) / 100:.2f}"
                        account_data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                        account_data['igst'] = 0
                        account_data['igst_value'] = 0
                    else:
                        igst_rate = Decimal(gst.igst_rate or 0)
                        cess_rate = Decimal(gst.cess_rate or 0)
                        account_data['igst'] = igst_rate
                        account_data['cgst'] = 0
                        account_data['sgst'] = 0
                        account_data['cess'] = cess_rate
                        account_data['tax'] = igst_rate
                        account_data['cgst_value'] = 0
                        account_data['sgst_value'] = 0
                        account_data['igst_value'] = f"{(amount * igst_rate) / 100:.2f}"
                        account_data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                elif gst.gst_nature_type == "As per HSN":
                    hsn = item.hsn
                    company_state= str(self.company_obj.address.state).lower()
                    supplier_status = str(self.kwargs.get("supplier_state", "")).lower()
                    tax_rate = Decimal(hsn.gst_rates.rate or 0)
                    cess_rate = Decimal(hsn.cess_rate or 0)
                    if supplier_status == company_state:
                        rate_tax_half = tax_rate / 2
                        account_data['cgst'] = rate_tax_half
                        account_data['sgst'] = rate_tax_half
                        account_data['igst'] = 0
                        account_data['cess'] = cess_rate
                        account_data['tax'] = tax_rate
                        account_data['cgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        account_data['sgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        account_data['igst_value'] = 0
                        account_data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}" 
                    else:
                        account_data['igst'] = tax_rate
                        account_data['cgst'] = 0
                        account_data['sgst'] = 0
                        account_data['cess'] = cess_rate
                        account_data['tax'] = tax_rate
                        account_data['cgst_value'] = 0
                        account_data['sgst_value'] = 0
                        account_data['igst_value'] = f"{(amount * tax_rate) / 100:.2f}"
                        account_data['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                else:
                    pass
                updated_accounts.append(account_data)

            combined_list = updated_item_details + updated_accounts


            for expences , instance_expences in zip(other_expence_charge, self.direct_purchase_invoice.other_expence_charge.all()):
                if gst_type == "Specify" and specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate": 
                        expences['sgst'] = str(self.gst_transaction.sgst_rate)
                        expences['cgst'] = str(self.gst_transaction.cgst_rate)
                        expences['cess'] = str(self.gst_transaction.cess_rate)
                        expences['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    elif self.gst_transaction.place_of_supply == "Interstate":
                        expences['igst'] = str(self.gst_transaction.igst_rate)
                        expences['cess'] = str(self.gst_transaction.cess_rate)
                        expences['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)

                elif gst_type == "As per HSN":
                    hsn =instance_expences.hsn
                    amount  = instance_expences.amount
                    tax_rate = Decimal(hsn.gst_rates.rate or 0)
                    cess_rate = Decimal(hsn.cess_rate or 0) 
                    if supplier_status == company_state:
                        rate_tax_half = tax_rate / 2
                        expences['cgst'] = rate_tax_half
                        expences['sgst'] = rate_tax_half
                        expences['igst'] = 0
                        expences['cess'] = cess_rate
                        expences['tax'] = tax_rate
                        expences['cgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        expences['sgst_value'] = f"{(amount * rate_tax_half) / 100:.2f}"
                        expences['igst_value'] = 0
                        expences['cess_value'] = f"{(amount * cess_rate) / 100:.2f}" 
                    else:
                        expences['igst'] = tax_rate
                        expences['cgst'] = 0
                        expences['sgst'] = 0
                        expences['cess'] = cess_rate
                        expences['tax'] = tax_rate
                        expences['cgst_value'] = 0
                        expences['sgst_value'] = 0
                        expences['igst_value'] = f"{(amount * tax_rate) / 100:.2f}"
                        expences['cess_value'] = f"{(amount * cess_rate) / 100:.2f}"
                else:
                    expences['igst'] = "0"
                    expences['cgst'] = "0"
                    expences['sgst'] = "0"
                    expences['cess'] = "0"
                    expences['tax'] = "0"
                    expences['cgst_value'] = "0"
                    expences['sgst_value'] = "0"
                    expences['igst_value'] = "0"
                    expences['cess_value'] = "0" 
                self.other_expense.append(expences)





            

            self.errors.append("Tax details for items have been updated.") 
            self.item_details = sorted(combined_list, key=lambda x: int(x["index"]))
            

            return True
        except Exception as e:
            self.errors.append(f"Unexpeted error occurred in update_tax_item_details-- {str(e)}")
            return False
        
    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "direct_purchase_invoice": self.direct_purchase_invoice,
            "item_details" : self.convert_decimals_to_str(self.item_details) if self.item_details else None,
            "other_expence" : self.convert_decimals_to_str(self.other_expense) if self.other_expense else None
        }
    


def purchase_direct_invoice_general_update(data): 
    valid_serializers = []
    errors = []
    credit = data.get("credit", {})
    debits = data.get("debits", [])

    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "direct_purchase_invoice", "account", "created_by"]

    # Process debits
    for idx, debit in enumerate(debits):
        for field in REQUIRED_FIELDS + ["debit"]:
            if debit.get(field) in [None, ""]:
                errors.append(f"debit [{idx}] → '{field}' is required.")
        
        debit_amount = debit.get("debit", 0) 
        debits_amount += debit_amount

        serializer = AccountsGeneralLedgerSerializer(data=debit)
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"debit [{idx}] → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)

    # Process debit
    for field in REQUIRED_FIELDS + ["credit"]:
        if credit.get(field) in [None, ""]:
            errors.append(f"credit → '{field}' is required.")

    serializer = AccountsGeneralLedgerSerializer(data=credit)
    if not serializer.is_valid():
        for field, error in serializer.errors.items():
            errors.append(f"credit → {field}: {'; '.join(map(str, error))}")
    else:
        valid_serializers.append(serializer)

    # Compare debit and credit amounts
    credit_amount = Decimal(str(credit.get("credit", 0)))
    if credit_amount != debits_amount:
        errors.append(f"Debit amount ({debits_amount}) and credit amount ({credit_amount}) do not match.----")

    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}


