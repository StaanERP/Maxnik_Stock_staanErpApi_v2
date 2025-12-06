from itemmaster.models import *
from itemmaster.serializer import *
from itemmaster.Utils.CommanUtils import *
from itemmaster.schema import *
from itemmaster2.Utils.ItemMasterComman import *
from decimal import Decimal, InvalidOperation


class DebitNoteSerivce:
    def __init__(self, data, status, info):
        self.status_text= status
        self.data = data
        self.status = None
        self.success = False
        self.errors = []
        self.info = info
        self.debit_note = None
        self.item_details_serializer = []
        self.other_income_serializer = []
        self.account_serializer = []
        self.new_item_details_instances = []
        self.new_other_income_instances = []
        self.new_account = []
        self.old_item_details_instances = []
        self.old_other_income_instances = []
        self.old_account = []
        self.gst_transaction = None
        self.updated_item_details = []
        self.updated_other_income = []
        self.updated_account = []
        self.tds = None
        self.tcs = None

    # Get or validate existing debit note
    def get_debit_note(self)-> bool:
        debit_note_id = self.data.get("id")
        if debit_note_id:
            self.debit_note =  DebitNote.objects.filter(id=debit_note_id).first()
            if not self.debit_note:
                self.errors.append("Debit note not found.")
                return False
            
            self.old_item_details_instances.extend(self.debit_note.debitnoteitemdetail_set.all())
            self.old_other_income_instances.extend(self.debit_note.debitnoteotherincomecharge_set.all())
            self.old_account.extend(self.debit_note.debitnoteaccount_set.all())

            if self.status_text == "Draft" and self.debit_note.status.name in ['Submit', "Canceled"]:
                self.errors.append(f"Already {self.debit_note.status.name} debit Note did'n make Draft again.")
            elif self.status_text == "Submit" and self.debit_note.status.name in ["Canceled","Submit" ]:
                self.errors.append(f"Already {self.debit_note.status.name} debit Note did'n make Submit again.")

            supplier = self.debit_note.supplier
            if supplier.tds and "P" in supplier.pan_no:
                self.tds =  "P"
            elif supplier.tds and "P" not in supplier.pan_no:
                self.tds = "O"
            if supplier.tcs in ['PURCHASE', "BOTH"]:
                if supplier.pan_no and "P" in supplier.pan_no:
                    self.tcs =  "WP"
                elif supplier.pan_no and "P" not in supplier.pan_no:
                    self.tcs =  "WO"
                else:
                    self.tcs =  "WOO"
        
        return_invoice_id = bool(self.data.get("return_invoice"))
        is_have_purchase_return_id = any(item.get("purchase_return_item") for item in self.data.get("item_detail"))

        if return_invoice_id and not is_have_purchase_return_id:
            self.errors.append("Purchase return invoice item id is missing in item details.")
        
        if not return_invoice_id and is_have_purchase_return_id:
            self.errors.append("Purchase return invoice id is missing.")

        if not self.data.get('item_detail', []) and not self.data.get('accounts', []):
            self.errors.append("At least one item detail or account is required.")
            return False

        if len(self.errors):
            return False
        
        return True

    # Validate mandatory fields
    def validate_required_fields(self)-> bool:
        REQUIRED_FIELDS = [
            "status", "debit_note_date", "supplier", "department","gstin_type",
            "exchange_rate", "gst_nature_transaction", "gst_nature_type",
            "contact", "address", "currency",    "place_of_supply",
            "item_total_befor_tax", "net_amount"]
         
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')

        return not self.errors

    # Validate and fetch status instance
    def update_status_instance(self)-> bool:
        self.status  = CommanStatus.objects.filter(name=self.status_text, table="Debit Note").first()
        
        if not self.status :
            self.errors.append(f"Ask developer to add status '{self.status_text}' in CommanStatus.")
            return False
        
        self.data["status"] = self.status.id
        return True
    
    # Validate numbering series
    def validate_numbering(self)-> bool:
        debit_note_id = self.data.get("id")
        if not debit_note_id:
            conditions = {'resource': 'Debit Note', 'default': True}
            numbering_series = NumberingSeries.objects.filter(**conditions).first()
            if not numbering_series:
                self.errors.append("No matching NumberingSeries found.")
                return False
        return True
    
    # Validate item details
    def validate_item_details(self)-> bool:
        instance_list = []
        item_details = self.data.get('item_detail', [])
        item_labels = []

        if not item_details:
            return True

        for item in item_details:
            purchase_return_challan_id = item.get("purchase_return_item")
            item_master  = ItemMaster.objects.filter(id=item.get("item_master")).first()
            if not item_master :
                self.errors.append(f"{item_master } not found in Item Master.")
                return False
            
            if purchase_return_challan_id:
                pr_item  = PurchaseReturnChallanItemDetails.objects.filter(id=purchase_return_challan_id).first()
                if not pr_item :
                    self.errors.append(f"{item_master} -> purchase return Challan item not found .")
            item_labels.append(str(item_master))
            
            if item_master.item_uom != item_master.purchase_uom:
                for field_ in ['po_qty',"po_uom", "po_rate", "conversion_factor","po_amount"]:
                    if item.get(field_) is None:
                        self.errors.append(f'{item_master} → {field_} is required.')
                        
                if not self.data.get('return_invoice' , None) and  item.get("po_amount") != item.get("amount"):
                    self.errors.append(f"{item_master} Purchase amount and base amount must be equal.")

            if  item.get("purchase_return_item"):
                for field in ["item_master", "qty", "uom",  "rate", "amount"]:
                    if item.get(field) is None:
                        self.errors.append(f'{item_master} → {field} is required.')

            if item.get('id'):
                instance = DebitNoteItemDetail.objects.filter(id=item.get("id")).first()

                if not instance:
                    self.errors.append(f'{item_master} → Debit Note Item instance not Found.')
                instance_list.append(instance)
            else:
                instance_list.append(None)
        
        if self.errors:
            return False
        
        item_result = validate_common_data_and_send_with_instance(
            item_details, instance_list,
            DebitNoteItemDetailSerializer,
            item_labels,
            self.info.context
        )
        
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.item_details_serializer.extend(item_result.get("instance"))
        return True
    
    # Validate other charges
    def validate_other_charges(self)-> bool:
        instance_list = []
        other_expence_charges = self.data.get('other_income_charge', [])
        item_labels = []

        if not other_expence_charges:
            return True
        
        for charge  in other_expence_charges:
            other_expence_id = charge .get("other_income_charges")
            other_income_charge = OtherIncomeCharges.objects.filter(id=other_expence_id)
            
            if not other_income_charge:
                self.errors.append(f"{other_expence_id} other income charges id is not found.")
                continue
            item_labels.append(other_income_charge)

            for field in ["other_income_charges", "amount"]:
                if charge .get(field) is None:
                    self.errors.append(f'{other_income_charge} → {field} is required.')
            
            if charge.get('id'):
                instance = DebitNoteOtherIncomeCharge.objects.filter(id=charge.get("id")).first()
                if not instance:
                    self.errors.append(f'{other_income_charge} → debit note other income charge {charge.get("id")} not Found.')
                instance_list.append(instance)
            else:
                instance_list.append(None)

        if self.errors:
            return False
        
        item_result = validate_common_data_and_send_with_instance(
                            other_expence_charges, instance_list,
                            DebitNoteOtherIncomeChargesSerializer,
                            item_labels,
                            self.info.context)
         
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.other_income_serializer.extend(item_result.get("instance"))
        return True

    # Validate account
    def validate_account(self)-> bool:
        instance_list = []
        accounts = self.data.get('accounts', [])
        item_labels = []
        
        if not accounts:
            return True

        for account in accounts:
            debit_note_acount_id = account.get("id")
            account_master_instance = AccountsMaster.objects.filter(id=account.get("account_master")).first()

            if not account_master_instance :
                self.errors.append(f"{account.get('account_master')} not found in Account Master.")
                continue
            
            item_labels.append(str(account_master_instance.accounts_name))

            for field in ["account_master",   "amount"]:
                if account.get(field) is None:
                    self.errors.append(f'{account_master_instance} → {field} is required.')
            
            if debit_note_acount_id:
                instance = DebitNoteAccount.objects.filter(id=debit_note_acount_id).first()

                if not instance:
                    self.errors.append(f'{account_master_instance.accounts_name} → Account instance not Found.')
                instance_list.append(instance)
            else:
                instance_list.append(None)
            
        if self.errors:
            return False
            
        item_result = validate_common_data_and_send_with_instance(
            accounts, instance_list,
            DebitNoteAccountSerializer,
            item_labels,
            self.info.context)
        
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.account_serializer.extend(item_result.get("instance"))
        return True

    # Save item details
    def save_item_details(self)-> bool:
        if not self.item_details_serializer:
            return True
        try:
            for serializer_item in self.item_details_serializer:
                if serializer_item:
                    serializer_item.save()
                    self.new_item_details_instances.append(serializer_item.instance)
            return True

        except Exception as e:
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False

    # Save other income charges
    def save_other_income_charges(self)-> bool:
        if not self.other_income_serializer:
            return True
        
        try:
            for serializer_other_income in self.other_income_serializer:
                if serializer_other_income:
                    serializer_other_income.save()
                    self.new_other_income_instances.append(serializer_other_income.instance)
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving other income: {str(e)}")
            return False
    
    def save_accout(self)-> bool:
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

    # Save debit note
    def save_debit_note(self)-> bool:
        try:
            serializer_class = DebitNoteSerializer
            if self.debit_note:
                serializer = serializer_class(self.debit_note, data=self.data, partial=True, context={'request': self.info.context})
            else:
                serializer = serializer_class(data=self.data, context={'request': self.info.context})

            if not serializer.is_valid():
                self.errors.extend(f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items())
                return False

            serializer.save()
            self.debit_note = serializer.instance

            for item in self.new_item_details_instances:
                item.debit_note = self.debit_note
                item.save()

            for income in self.new_other_income_instances:
                income.debit_note = self.debit_note
                income.save()
            
            for account in self.new_account:
                account.debit_note = self.debit_note
                account.save()
            
            deleteCommanLinkedTable([item.id for item in self.old_item_details_instances],  [item.id for item in self.new_item_details_instances], DebitNoteItemDetail)
            deleteCommanLinkedTable([charge.id for charge in self.old_other_income_instances], [charge.id for charge in self.new_other_income_instances], DebitNoteOtherIncomeCharge)
            deleteCommanLinkedTable([account.id for account in self.old_account], [acount.id for acount in self.new_account], DebitNoteAccount)
            return True
        except Exception as e:
            self.errors.append(f"Error saving Debit Note: {str(e)}")
            return False

    # validate item details on submit
    def validate_item_detail_on_submit(self)->bool:
        if self.debit_note and not self.debit_note.return_invoice:
            return True
        self.old_item_details_instances  = self.debit_note.debitnoteitemdetail_set.all()
        for item in self.old_item_details_instances:
            purchase_retun_item = item.purchase_return_item
            item_master = item.item_master
            lable = f"{item_master.item_part_code}-{item_master.item_name}"

            if not purchase_retun_item:
                self.errors.append(f"{lable} purchase return item is missing.")
                continue
            purchase_invoice_item = purchase_retun_item.purchase_invoice_item
            if not purchase_invoice_item:
                self.errors.append(f"{lable} purchase invoice item is missing.")
                continue

            if purchase_invoice_item.conversion_factor != item.conversion_factor:
                self.errors.append(f"{lable}  Conversion Factor is mismatch with purchase invoice.")
            if purchase_invoice_item.po_rate != item.po_rate:
                self.errors.append(f"{lable}  Po Rate is mismatch with purchase invoice.")
            if purchase_retun_item.po_return_qty != item.po_qty:
                self.errors.append(f"{lable}  Po QTY is mismatch with purchase return.")
        return not self.errors
    
    def to_decimal(self, value):
        """Safely convert strings/numbers to Decimal for accurate comparison."""
        if value is None:
            return Decimal('0')
        try:
            return Decimal(str(value)).quantize(Decimal('0.000'))
        except (InvalidOperation, TypeError):
            return Decimal('0')

    # validate tax flow
    def validate_tax(self)->bool:
        if self.debit_note and self.debit_note.return_invoice:
            return True
        
        self.gst_transaction = self.debit_note.gst_nature_transaction

        if self.old_item_details_instances:
            for item in self.old_item_details_instances:
                item_master = item.item_master
                
                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        
                        if (
                            self.to_decimal(item.sgst) != self.to_decimal(self.gst_transaction.sgst_rate) or
                            self.to_decimal(item.cgst) != self.to_decimal(self.gst_transaction.cgst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                           
                            
                            return False
                    elif self.gst_transaction.place_of_supply == "Interstate":
                        if (
                            self.to_decimal(item.igst) != self.to_decimal(self.gst_transaction.igst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False

                elif  self.gst_transaction.gst_nature_type == "As per HSN":
                    hsn = item.hsn
                    if ((self.to_decimal(item.sgst))  + self.to_decimal(item.cgst) + self.to_decimal(item.igst) ) != self.to_decimal(hsn.gst_rates.rate) or self.to_decimal(item.cess)  != self.to_decimal(hsn.cess_rate):
                        return False

                else:
                    # Fallback check — if all 4 rates are present, reject
                    if (self.to_decimal(item.sgst)) or self.to_decimal(item.cgst) or self.to_decimal(item.igst) or self.to_decimal(item.cess):
                        return False
                
                # TDS
                if self.tds == "P" and item_master.tds_link:
                    if item_master.tds_link.percent_individual_with_pan != item.tds_percentage:
                        
                        return False
                elif self.tds == "O" and item_master.tds_link:
                        if item_master.tds_link.percent_other_with_pan != item.tds_percentage:
                            
                            return False
                else:
                    if item.tds_percentage and  item.tds_percentage > 0:
                        
                        return False
                
                # TCS
                if self.tcs == "WP" and item_master.tcs_link:
                    
                    
                    if item_master.tcs_link.percent_individual_with_pan != item.tcs_percentage:
                        
                        return False
                    
                elif self.tcs == "WO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_with_pan != item.tcs_percentage:
                        
                        return False
                    
                elif self.tcs == "WOO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_without_pan != item.tcs_percentage:
                        
                        return False
                    
                else:
                    if item.tcs_percentage and item.tcs_percentage > 0:
                        
                        return False
        
        if self.old_account:
            for item in self.old_account:
                account_master = item.account_master
                if not item.hsn:
                    continue

                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        if (
                            self.to_decimal(item.sgst) != self.to_decimal(self.gst_transaction.sgst_rate) or
                            self.to_decimal(item.cgst) != self.to_decimal(self.gst_transaction.cgst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False
                    elif self.gst_transaction.place_of_supply == "Interstate":
                        if (
                            self.to_decimal(item.igst) != self.to_decimal(self.gst_transaction.igst_rate) or
                            self.to_decimal(item.cess) != self.to_decimal(self.gst_transaction.cess_rate)
                        ):
                            return False

                elif  self.gst_transaction.gst_nature_type == "As per HSN":
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
        
        return True
    
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
        company = company_info()

        if company is None:
            self.errors.append("Company Not Found.")
            return False
        item_details = self.data.get('item_detail', [])
        other_charge = self.data.get('other_income_charge', [])
        accounts = self.data.get('accounts', [])
        other_income_instance = self.old_other_income_instances
        account_instance = self.old_account
        supplier_state =  self.debit_note.address.state
        updated_item_details = []
        updated_accounts = []
         
        
        if item_details:
            for item, instance_item in zip(item_details, self.old_item_details_instances):
                item['sgst'] = "0"
                item['cgst'] = "0"
                item['cess'] = "0"
                item['tax'] = "0"
                item['igst'] = "0"
                item['tds_percentage'] = "0"
                item['tds_value'] = "0"
                item['tcs_percentage'] = "0"
                item['tcs_value'] = "0"
                

                item_master = instance_item.item_master  
                if self.tds == "P" and item_master.tds_link:
                    item['tds_percentage'] = str(item_master.tds_link.percent_individual_with_pan)
                    item['tds_value'] = str((item.po_amount*item_master.tds_link.percent_individual_with_pan)/100)
                elif self.tds == "O" and item_master.tds_link:
                    item['tds_percentage'] = str(item_master.tds_link.percent_other_with_pan)
                    item['tds_value'] = str((item.po_amount*item_master.tds_link.percent_other_with_pan)/100)
                
                if self.tcs == "WP" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_individual_with_pan)
                    item['tcs_value'] = str((item.po_amount*item_master.tcs_link.percent_individual_with_pan)/100)
                elif self.tcs == "WO" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_other_with_pan)
                    item['tcs_value'] = str((item.po_amount*item_master.tcs_link.percent_other_with_pan)/100)
                elif self.tcs == "WOO" and item_master.tcs_link:
                    item['tcs_percentage'] = str(item_master.tcs_link.percent_other_without_pan)
                    item['tcs_value'] = str((item.po_amount*item_master.tcs_link.percent_other_without_pan)/100)



                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        item['sgst'] = str(self.gst_transaction.sgst_rate)
                        item['cgst'] = str(self.gst_transaction.cgst_rate)
                        item['cess'] = str(self.gst_transaction.cess_rate)
                        item['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        item['igst'] = str(self.gst_transaction.igst_rate)
                        item['cess'] = str(self.gst_transaction.cess_rate)
                        item['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)
                    
                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(supplier_state).lower() == str(company.address.state).lower():
                        rate_half = instance_item.hsn.gst_rates.rate / 2
                        item['sgst'] =str(rate_half or 0)
                        item['cgst'] =str(rate_half or 0)
                        item['cess'] =str(instance_item.hsn.cess_rate or 0)
                        item['tax'] = str(instance_item.hsn.gst_rates.rate or 0)
                    else: 
                        item['igst'] =str(instance_item.hsn.gst_rates.rate or 0)
                        item['cess'] =str(instance_item.hsn.cess_rate or 0)
                        item['tax'] = str(instance_item.hsn.gst_rates.rate or 0)
                updated_item_details.append(item)
                
        
        if other_charge:
            for charge, instance_charge in zip(other_charge, other_income_instance):
                 
                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        charge['sgst'] = str(self.gst_transaction.sgst_rate)
                        charge['cgst'] = str(self.gst_transaction.cgst_rate)
                        charge['cess'] = str(self.gst_transaction.cess_rate)
                        charge['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        charge['igst'] = str(self.gst_transaction.igst_rate)
                        charge['cess'] = str(self.gst_transaction.cess_rate)
                        charge['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)

                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(supplier_state).lower() == str(company.address.state).lower():
                        hsn = instance_charge.other_income_charges.hsn
                        rate_half = hsn.gst_rates.rate / 2
                        charge['sgst'] =str(rate_half or 0)
                        charge['cgst'] =str(rate_half or 0)
                        charge['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        charge['tax'] = str(hsn.gst_rates.rate or 0)
                    else: 
                        charge['igst'] =str(hsn.gst_rates.rate or 0)
                        charge['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        charge['tax'] = str(hsn.gst_rates.rate or 0)
                self.updated_other_income.append(charge)
         
        if accounts:
            
            for account, instance_acount in zip(accounts, account_instance):
                account['sgst'] = "0"
                account['cgst'] = "0"
                account['cess'] = "0"
                account['tax'] = "0"
                account['igst'] = "0"
                account_master = instance_acount.account_master

                if not instance_acount.hsn:
                    continue
                
                
                # amount = account.amount 
                if  self.tds == "P" and account_master.tds_link:
                    account['tds_percentage'] = str(account_master.tds_link.percent_individual_with_pan)
                    # account['tdsValue'] = str((amount*account_master.tds_link.percent_individual_with_pan)/100)
                elif self.tds == "O" and account_master.tds_link:
                    account['tds_percentage'] = str(account_master.tds_link.percent_other_with_pan)
                    # account['tds_value'] = str((amount*account_master.tds_link.percent_other_with_pan)/100)
                
                # TCS
                if self.tcs == "WP" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_individual_with_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_individual_with_pan)/100)
                elif self.tcs == "WO" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_other_with_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_other_with_pan)/100)
                elif self.tcs == "WOO" and account_master.tcs_link:
                    account['tcs_percentage'] = str(account_master.tcs_link.percent_other_without_pan)
                    # account['tcsValue'] = str((amount*account_master.tcs_link.percent_other_without_pan)/100)

                if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
                    if self.gst_transaction.place_of_supply == "Intrastate":
                        account['sgst'] = str(self.gst_transaction.sgst_rate)
                        account['cgst'] = str(self.gst_transaction.cgst_rate)
                        account['cess'] = str(self.gst_transaction.cess_rate)
                        account['tax'] = str(self.gst_transaction.sgst_rate+self.gst_transaction.cgst_rate+self.gst_transaction.cess_rate)
                    else:
                        account['igst'] = str(self.gst_transaction.igst_rate)
                        account['cess'] = str(self.gst_transaction.cess_rate)
                        account['tax'] =  str(self.gst_transaction.igst_rate+self.gst_transaction.cess_rate)
                
                elif self.gst_transaction.gst_nature_type == "As per HSN":
                    if str(supplier_state).lower() == str(company.address.state).lower():
                        hsn = instance_acount.hsn
                        rate_half = hsn.gst_rates.rate / 2
                        account['sgst'] =str(rate_half or 0)
                        account['cgst'] =str(rate_half or 0)
                        account['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        account['tax'] = str(hsn.gst_rates.rate or 0)
                    else:
                        account['igst'] =str(hsn.gst_rates.rate or 0)
                        account['cess'] =str(hsn.gst_rates.cess_rate or 0)
                        account['tax'] = str(hsn.gst_rates.rate or 0)
                updated_accounts.append(account)
         
        

        combined_list = updated_item_details+updated_accounts
        item_detail_and_account_list = sorted(combined_list, key=lambda x: int(x["index"]))
        
        self.updated_item_details.extend(item_detail_and_account_list)
        
        return True

    # Main process flows
    def process(self)-> dict:
        with transaction.atomic():
            if self.status_text == "Draft":
                if not self.get_debit_note():
                    return self.response()
                
                if not self.validate_required_fields():
                    return self.response()
                
                if not self.update_status_instance():
                    return self.response()
                
                if not self.validate_numbering():
                    return self.response()
                
                if not self.validate_item_details():
                    return self.response()
                
                if not self.validate_other_charges():
                    return self.response()
                
                if not self.validate_account():
                    return self.response()
                
                if not self.save_item_details():
                    return self.response()
                
                if not self.save_other_income_charges():
                    return self.response()
                
                if not self.save_accout():
                    return self.response()
                
                if not self.save_debit_note():
                    return self.response()
                
                self.success = True
            elif self.status_text == "Submit":
                if not self.get_debit_note():
                    return self.response()
                if not self.validate_required_fields():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                if not self.validate_item_detail_on_submit():
                    return self.response()
                
                if not self.validate_tax():
                    
                    self.update_tax_item_details()
                    
                    return self.response()
                self.debit_note.status = self.status
                self.debit_note.save()
                self.success = True
            else:
                self.errors.append(f"{self.status_text} Unexpected status.")
        return self.response()
            
    #  Response structure
    def response(self)-> dict:
        
        
        return {
            "debit_note": self.debit_note,
            "success": self.success,
            "errors": self.errors,
            "item_detail" :  self.convert_decimals_to_str(self.updated_item_details) if self.updated_item_details else None ,
            "other_income_charges" :  self.convert_decimals_to_str(self.updated_other_income) if self.updated_other_income else None 
        }



def debit_note_general_update(data): 
    valid_serializers = []
    errors = []
    credits = data.get("credits", [])
    debit = data.get("debit", {})

    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "debit_note", "account", "created_by"]

    # Process credits
    for idx, credit in enumerate(credits):
        for field in REQUIRED_FIELDS + ["credit"]:
            if credit.get(field) in [None, ""]:
                errors.append(f"credit [{idx}] → '{field}' is required.")
        
        credits_amount += credit.get("credit", 0)
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
    debit_amount = Decimal(str(debit.get("debit", 0)))
    if credits_amount != debit_amount:
        errors.append(f"Debit amount ({debit_amount}) and credit amount ({credits_amount}) do not match.----")

    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}


