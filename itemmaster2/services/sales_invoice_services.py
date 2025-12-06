from itemmaster2.models import *
from itemmaster2.Serializer import *
from itemmaster.mutations.Item_master_mutations import *
from django.db import transaction
import copy

class SalesInvoiceService:
    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status = status
        self.errors = [] 
        self.info = info
        self.success = False
        self.sales_invoice_obj = None
        self.gst_transaction = None
        self.allow_rate_change = False
        self.allow_due_date_change = False
        self.sales_order_exchange_rate = None
        self.tds = None
        self.tcs = None
        self.state_of_company = None
        self.item_details = None
        self.other_income_charges = None
        self.account_list = None

    def process(self):
        try:
            # Start a database transaction
            with transaction.atomic():
                self.getPermission()

                # 1. Run all validations
                if not self.run_validations():
                    return self.response()
                
                # 2. Save item details
                if not self.save_item_details():
                    return self.response()
                
                # 3. Save other income charges
                if not self.save_other_income():
                    return self.response()
                
                # 4. Save or update SalesInvoice
                if not self.save_sales_invoice():
                    return self.response()
                
                # All done
                self.success = True

        except Exception as e:
            self.errors.append(f"Unexpected error occurred: {str(e)}")
            self.success = False

        return self.response()
    
    def calculate_item_combo(self, item_combo_list, amount, qty):
        item_combo_data = []

        # Calculate total value of all items
        total_value = sum(float(item['rate']) * float(item['qty']) for item in item_combo_list)

        if total_value == 0:
            return item_combo_list

        rounded_final_total = round(float(amount) / float(qty), 2)
        total_discount_needed = total_value - rounded_final_total

        # Calculate contributions and ratios
        item_contributions = [float(item['rate']) * float(item['qty']) for item in item_combo_list]
        ratios = [contribution / total_value for contribution in item_contributions]
        discounts = [total_discount_needed * ratio for ratio in ratios]

        for index, item in enumerate(item_combo_list):
            qty = float(item['qty'])
            rate = float(item['rate'])
            original_price = qty * rate

            discount = discounts[index]
            discounted_amount = original_price - discount
            final_discounted_amount = round(max(discounted_amount, 0), 3)
            after_discount_value_per_item = round(final_discounted_amount / qty, 3)

            item["afterDiscountValueForPerItem"] = str(after_discount_value_per_item)
            item["amount"] = str(final_discounted_amount)

            item_combo_data.append(item)

        return item_combo_data
    
    def update_tax_item_details(self):
        updated_item_details = []
        updated_other_income = []
        item_details = self.kwargs.get("item_detail", [])
       
        if item_details:
            for item in item_details:
                dc_item = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id__in=item.get("item")).first()
                if not dc_item:
                    self.errors.append(f'{item.get("item")} not Found in DC Item Details.')
                    return False

                item_master = dc_item.sales_order_item_detail.itemmaster
                qty = item.get("qty", 0)
                rate = item.get("rate", 0)
                amount = qty * rate
                item['tds_percentage'] = 0
                item['tds_value'] = 0
                item['tcs_percentage'] = 0
                item['tcs_value'] = 0

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
                
                
                updated_item_details.append(item)
            self.item_details = updated_item_details
            self.errors.append("Tax Is updated.")
            return self.response()

    def validate_tax(self):
        dc_item_list = []
        item_details = self.kwargs.get("item_detail", [])
        gst = self.gst_transaction

        # --- Handle ITEM DETAILS (DC Items) ---
        if item_details:
            for item in item_details: 
                dc_item = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id=item.get("item")).first()
                item_instance = self.sales_invoice_obj.item_detail.filter(id=item.get("id"))
            
                if not dc_item:
                    self.errors.append(f'{item.get("item")} not Found in DC Item Details.')
                    return False
                if not item_instance:
                    self.errors.append(f'{item.get("item")} not Found in Sales invoice Item Details.')
                    return False
                
                item_master = dc_item.sales_order_item_detail.itemmaster
                
                
                # TDS
                if self.tds == "P" and item_master.tds_link:
                    if item_master.tds_link.percent_individual_with_pan != item.get("tds_percentage"):
                        return False
                elif self.tds == "O" and item_master.tds_link:
                    if item_master.tds_link.percent_other_with_pan != item.get("tds_percentage"):
                        return False
                else:
                    if item.get("tds_percentage") and  item.get("tds_percentage") > 0:
                        return False

                # TCS
                if self.tcs == "WP" and item_master.tcs_link:
                    if item_master.tcs_link.percent_individual_with_pan != item.get("tcs_percentage"):
                        return False
                elif self.tcs == "WO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_with_pan != item.get("tcs_percentage"):
                        return False
                elif self.tcs == "WOO" and item_master.tcs_link:
                    if item_master.tcs_link.percent_other_without_pan != item.get("tcs_percentage"):
                        return False
                else:
                    if item.get("tcs_percentage") and item.get("tcs_percentage") > 0:
                        return False
                
            return True

    def run_validations(self):
        self.state_of_company = CompanyMaster.objects.all().values("address__state").first()
        self.validate_required_fields()
        self.update_status_id()
        self.validate_sales_invoice()
        self.validate_numbering_serial()
        self.validate_foreign_keys()
        self.validate_dc()
        self.validate_invoice_itemdetails()
        self.validate_other_income_charges()
        
        if self.status == "Submit":
            
            if not self.validate_tax():
                self.update_tax_item_details()
        return len(self.errors) == 0
    
    def validate_sales_invoice(self):
        if "id" in self.kwargs and self.kwargs['id']:
            try:
                self.sales_invoice_obj = SalesInvoice.objects.get(id=self.kwargs['id'])
                if self.sales_invoice_obj is None:
                    self.errors.append("Sales invoice not Found.")
                supplier = self.sales_invoice_obj.buyer
                if supplier.tds and "P" in supplier.pan_no:
                    self.tds =  "P"
                elif supplier.tds and "P" not in supplier.pan_no:
                    self.tds = "O"
                if supplier.tcs in ['SALES', "BOTH"]:
                    if supplier.pan_no and "P" in supplier.pan_no:
                        self.tcs =  "WP"
                    elif supplier.pan_no and "P" not in supplier.pan_no:
                        self.tcs =  "WO"
                    else:
                        self.tcs =  "WOO"
                         
            except ObjectDoesNotExist:
                self.errors.append("Sales invoice not Found.")
            except Exception as e:
                self.errors.append(f"11An exception occurred {e}")
            

    def validate_required_fields(self):
        REQUIRED_FIELDS  = ['status',"sales_invoice_date", 'due_date', 'buyer','buyer_address','buyer_contact_person'
                    ,'buyer_gstin_type',"buyer_gstin","buyer_state","buyer_place_of_supply","consignee","consignee_address",
                    "consignee_contact_person", "consignee_gstin_type", "consignee_gstin", "consignee_state", "consignee_place_of_supply",
                    "creadit_period","sales_person", "payment_term", "customer_po","customer_po_date", "department",
                    'terms_conditions', 'terms_conditions_text',"taxable_value" , "net_amount"]
        for field in REQUIRED_FIELDS :
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required')
    
    def check_rate_range(self, item_master_instance, rate, exchange_rate):
        
        if exchange_rate>1:
            min_price = item_master_instance.item_min_price/exchange_rate
        else:
            min_price = item_master_instance.item_min_price
        if min_price > rate:
            self.errors.append(f"{item_master_instance.item_part_code} amount is  less then allow value please check item master minimum amount.")

    def getPermission(self):
        user_management = UserManagement.objects.filter(user=self.info.context.user).first()
        if user_management and user_management.profile:
            allowed_perms = user_management.profile.allowed_permission.filter(model_name="Sales Invoice")
            for perm in allowed_perms: 
                if perm.permission_options.filter(options_name="DueDate Change").exists():
                        self.allow_due_date_change =  True
                if perm.permission_options.filter(options_name="Rate Change").exists():
                        self.allow_rate_change =  True

    def update_status_id(self):
        if self.status:
            statusObjects = CommanStatus.objects.filter(name=self.kwargs["status"]
                                                        , table="Sales Invoice").first()
            if statusObjects:
                self.kwargs["status"] = statusObjects.id
            else:
                status = self.kwargs.get("status", "default_status")
                self.errors.append(f"Status '{status}' is not configured. Please contact support to add it.")

    def validate_foreign_keys(self):
        # reuse your existing ValidationForeignKeys helper
        fk_definitions = [
            {'field': 'terms_conditions', 'model_name': 'TermsConditions', 'appname': 'itemmaster'}]
        for fk in fk_definitions:
            if self.kwargs.get(fk['field']):
                result = ValidationForeignKeys(fk['appname'], fk['model_name'], self.kwargs[fk['field']])
                if not result['success']:
                    self.errors.append(result['error'])
    
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
        except Exception as e:
            self.errors.append(str(e))

    def validate_dc(self):
        if "sales_dc" in self.kwargs and len(self.kwargs['sales_dc']) > 0:
            for dc in self.kwargs['sales_dc']:
                result = ValidationForeignKeys("itemmaster2", "SalesOrder_2_DeliveryChallan", dc)
                
                if not result['success']:
                    self.errors.append(result['error'])
                elif result['instance']:
                    
                    if result['instance'].status.name not in ['Submit', "Dispatch"]:
                        self.errors.append(f"{result['instance'].status.name} Are not allowed")
                     
                    if self.sales_order_exchange_rate == None:
                        self.sales_order_exchange_rate = (result['instance'].sales_order.exchange_rate or 1)
        else:
            self.errors.append(f"Sales Dc is required.")

    def validate_invoice_itemdetails(self):
        item_details = self.kwargs.get("item_detail",[])
        exceeds_qty_item = []

        if len(item_details) > 0:
            for itemdetails in item_details:
                try:
                    dc_item_details = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id=itemdetails.get("item")).first()
                    if not dc_item_details:
                        self.errors.append(f'{itemdetails.get("item")}Parent DC Item Detail Is Missing.')
                        continue 
                    
                    part_code = dc_item_details.sales_order_item_detail.itemmaster.item_part_code
                    item_master= dc_item_details.sales_order_item_detail.itemmaster
                    dc_item_detail_qty =  dc_item_details.qty
                    
                    if dc_item_detail_qty < itemdetails.get("qty"):
                        self.errors.append(f"Quantity for {part_code}  more then Sales DC item quantity.")
                        continue

                    required_fields = ["qty", "rate", "amount"]
                    for field in required_fields:
                        if itemdetails.get(field) is None:
                            self.errors.append(f'{part_code} - {field} is required')
                    if len(self.errors) > 0:
                        continue
                    item_id = itemdetails.get("id")
                    new_rate = itemdetails.get("after_discount_value_for_per_item") if itemdetails.get("after_discount_value_for_per_item") else itemdetails.get("rate")

                    if self.status == "Submit":
                        dc_item_detail_allow_qty = (dc_item_details.qty or 0) - (dc_item_details.return_submit_count or 0) - (dc_item_details.invoice_submit_count or 0)
                        if dc_item_detail_allow_qty < itemdetails.get("qty"):
                            exceeds_qty_item.append(part_code)
                        
                        self.check_rate_range(item_master, new_rate, self.sales_order_exchange_rate)
                    
                    if item_id:
                        existing_instance = SalesInvoiceItemDetail.objects.filter(id=item_id).first()
                        if not existing_instance:
                            self.errors.append(f"{part_code} sales invoice item did not Found.")
                        existing_rate = existing_instance.after_discount_value_for_per_item  if existing_instance.after_discount_value_for_per_item else existing_instance.rate
                        if existing_rate != new_rate and not self.allow_rate_change:
                            self.errors.append(f"User does not have permission to change the rate for {part_code}.")
                    else:
                        dc_rate = dc_item_details.sales_order_item_detail.rate
                        if dc_rate != new_rate and not self.allow_rate_change:
                            self.errors.append(f"Rate in sales order differs for {part_code}, but user lacks permission.")
                    
                    # Handle item combo
                    if dc_item_details.sales_order_item_detail.item_combo:
                        combo_list = itemdetails.get("item_combo")
                        
                        if isinstance(combo_list, list) and len(combo_list) > 0:
                            for combo in combo_list:
                                try: 
                                    item_combo_obj = SalesOrder_2_DeliverChallanItemCombo.objects.filter(id=combo.get("item_combo")).first()
                                    if not item_combo_obj:
                                        self.errors.append(f'Parent Combo not in {part_code} item detail is not found.')
                                    
                                    combo_part = item_combo_obj.item_combo.itemmaster.item_part_code
                                    combo_item_master = item_combo_obj.item_combo.itemmaster 

                                    dc_item_combo_qty = item_combo_obj.qty
                                    if dc_item_combo_qty < combo.get("qty"):
                                        self.errors.append(f"{part_code}->{combo_item_master} QTY is more then DC item combo QTY.")
                                        continue

                                    for field in ["item_combo", "qty", "rate"]:
                                        if combo.get(field) is None:
                                            self.errors.append(f'{part_code} — {combo_part} — {field} is required')

                                    if len(self.errors) > 0:
                                        continue

                                    combo_item_id = combo.get("id")
                                    combo_rate = combo.get("after_discount_value_for_per_item") if combo.get("after_discount_value_for_per_item") else combo.get("rate")
                                    if self.status == "Submit":
                                        dc_item_combo_allow_qty =  (item_combo_obj.qty or 0) - (item_combo_obj.return_submit_count or 0) -(item_combo_obj.invoice_submit_count or 0)
                                        # dc_item_detail_allow_qty = (dc_item_details.qty or 0) - (dc_item_details.return_submit_count or 0) - (dc_item_details.invoice_submit_count or 0)
                              
                                        if dc_item_combo_allow_qty < combo.get("qty"):
                                            exceeds_qty_item.append(f"{part_code}->{combo_part}")
                                        # self.check_rate_range(combo_item_master, combo_rate, self.sales_order_exchange_rate)
                                    if combo_item_id:
                                        existing_combo_instance = SalesInvoiceItemCombo.objects.get(id=combo_item_id)
                                        existing_combo_rate = existing_combo_instance.after_discount_value_for_per_item if existing_combo_instance.after_discount_value_for_per_item else existing_combo_instance.rate
                                        if existing_combo_rate != combo_rate and not self.allow_rate_change:
                                            self.errors.append(f"Rate changed for combo {part_code} — {combo_part}, but user lacks permission.")
                                            continue
                                    else:
                                        base_rate = item_combo_obj.item_combo.rate
                                        if base_rate != combo_rate and not self.allow_rate_change:
                                            self.errors.append(f"Sales order rate mismatch for combo {part_code} — {combo_part}, but user lacks permission.")
                                            continue

                                    combo_serializer = SalesInvoiceItemComboSerialzer(data=combo)
                                    if not combo_serializer.is_valid():
                                        for field, errors in combo_serializer.errors.items():
                                            self.errors.append(f"{part_code} — {combo_part} — {field}: {', '.join(errors)}")
                                            continue
                                    # Optional submission check
                                    if self.status == "Submit":
                                        submit_count =  item_combo_obj.invoice_submit_count or 0
                                        item_combo_qty = item_combo_obj.qty or 0
                                        qty = combo.get("qty") or 0
                                        if item_combo_qty < (submit_count + qty):
                                            self.errors.append(f"{part_code}--- Entered quantity for {combo_part} exceeds available Sales DC quantity.")
                                            continue
                                except ObjectDoesNotExist:
                                    self.errors.append(f'Combo item {combo.get("item_combo")} not found.')
                                    continue
                        else:
                            self.errors.append(f'Item combo is required for part {part_code}.')
                            continue
                    # Validate item detail serializer
                    copy_item_detail = copy.deepcopy(itemdetails)
                    copy_item_detail['item_combo'] = []

                    item_serializer = SalesInvoiceItemDetailSerialzer(data=copy_item_detail)
                    if not item_serializer.is_valid():
                        for field, errors in item_serializer.errors.items():
                            self.errors.append(f"{part_code} — {field}: {', '.join(errors)}")
                    if len(self.errors) > 0:
                        continue

                    # Optional submission check
                    if self.status == "Submit":
                        submit_count =  dc_item_details.invoice_submit_count or 0
                        dc_itemdetails_qty = dc_item_details.qty
                        qty = itemdetails.get("qty") or 0
                        if dc_itemdetails_qty < (submit_count + qty):
                            self.erors.append(f"Entered quantity for {part_code} exceeds available Sales DC quantity.")
                            continue

                    if len(exceeds_qty_item) > 0:
                        self.errors.append(f"The following item(s) exceed the quantity allowed for invoicing: {', '.join(exceeds_qty_item)}")
                        continue
                    
                except ObjectDoesNotExist:
                    self.errors.append(f'Item {itemdetails.get("item")} not found.')
                    continue
                
                except Exception as e: 
                    self.errors.append(f'Exception occurred: {e}')
                    continue
        else:
            self.errors.append(f'Item Details and Sales Account Ledger not found.')

    def validate_other_income_charges(self):
        try:
            other_incomes = self.kwargs.get('other_income_charge', [])

            for other_income in other_incomes:
                if other_income.get("parent"):
                    parent = SalesOrder_2_otherIncomeCharges.objects.filter(id=other_income.get("parent")).first()
                    if parent:
                        siblings = SalesOrder_2_otherIncomeCharges.objects.filter(parent=other_income.parent).exclude(id=other_income.id)
                    
                        if siblings.exists():
                            self.errors.append(f"{parent.other_income_charges_id.name} already exists in Sales Invoice and cannot be saved again.")

            if not self.errors and other_incomes:
                validation_errors = validate_with_serializer(
                    other_incomes,
                    SalesOrder_2_otherIncomeCharges,
                    SalesOrder_2_otherIncomeChargesSerializer,
                    OtherIncomeCharges,
                    'other_income_charges_id',
                    'Other Income charges',
                    'name'
                )
                self.errors.extend(validation_errors)

        except Exception as e:
            self.errors.append(f"An exception occurred: {e}")

    def save_sales_invoice_item_details(self):
        try:
            ItemDetails_id = []
            errors = []
            item_data = self.kwargs['item_detail']
            for item in item_data: 
                combo_items = item.get("item_combo") or []
                combo_ids = []
                if combo_items is not None and len(combo_items) > 0:
                    for combo in combo_items:
                        if 'id' in combo and combo.get("id"):
                            combo_instance = SalesInvoiceItemCombo.objects.get(id=combo['id'])
                            serialize_combo = SalesInvoiceItemComboSerialzer(combo_instance , data=combo, partial=True,context={'request': self.info.context})
                        else:
                            serialize_combo = SalesInvoiceItemComboSerialzer(data=combo, context={'request': self.info.context})
                        if serialize_combo.is_valid():
                            serialize_combo.save()
                            combo_ids.append(serialize_combo.instance.id)
                        else:
                            error_list = [f"{field}: {', '.join(errs)}" for field, errs in serialize_combo.errors.items()]
                            return {"ids": [], "success": False, "error": error_list}
                item['item_combo'] = combo_ids
                if 'id' in item and item['id']: 
                    sales_invoice_itemdetail = SalesInvoiceItemDetail.objects.get(id=item['id'])
                    serialize_itemdetils = SalesInvoiceItemDetailSerialzer(sales_invoice_itemdetail,
                                                                        data=item, partial=True, context={'request': self.info.context})
                else:
                    serialize_itemdetils = SalesInvoiceItemDetailSerialzer(data=item, context={'request': self.info.context})
                if serialize_itemdetils.is_valid(): 
                    serialize_itemdetils.save()
                    ItemDetails_id.append(serialize_itemdetils.instance.id)
                else:
                    for field, errs in serialize_itemdetils.errors.items():
                        errors.append(f"{field}: {', '.join(errs)}")
        except Exception as e:
            errors.append(f"An exception occurred -- {e}")
        

        return {"ids": ItemDetails_id, "success": len(errors) == 0, "error": errors}

    def save_item_details(self):
        item_details = self.kwargs.get("item_detail",[])
        if len(item_details) > 0:
            result = self.save_sales_invoice_item_details()
            if not result['success']:
                self.errors.extend(result['error'])
                self.success = False
                return False
            self.kwargs['item_detail'] = result['ids']
            return True
        
        else:
            self.errors.append(f'Item Details and Sales Account Ledger not found.')
            return False
    
    def save_other_income_charges(self):
        charges = self.kwargs['other_income_charge']
        return save_items(charges, SalesOrder_2_otherIncomeCharges, SalesOrder_2_otherIncomeChargesSerializer_qs,
                        "Other Income charges")
    
    def save_other_income(self):
        sales_account_ledger = self.kwargs.get("sales_account_ledger",[])
        other_income = self.kwargs.get("other_income_charge", [])
        if len(other_income) > 0 and len(sales_account_ledger)>0:
            self.errors.extend("Do not allowed to add both Other Income and sales account ledger.")
            return False


        if len(other_income) > 0:
            result = self.save_other_income_charges()
            
            if not result['success']:
                self.errors.extend(result['error'])
                self.success = False
                return False
            self.kwargs['other_income_charge'] = result['ids']
        return True
    
    def save_sales_invoice(self):
        other_income_old_id = []
        item_details_old_id = []
        itemdetails_id_qty = []
        prev_status = None
        if self.sales_invoice_obj:
            item_details_old_id = set(self.sales_invoice_obj.item_detail.values_list('id', flat=True))
            other_income_old_id = set(self.sales_invoice_obj.other_income_charge.values_list('id', flat=True))
            # prev_status  = self.sales_invoice_obj.status.name
            # for old_item in self.sales_invoice_obj.item_detail.all():
            #     if not old_item.item_combo.exists():
            #         itemdetails_id_qty.append({
            #             "id": old_item.id,
            #             "qty": old_item.qty
            #         })
            #     elif old_item.item_combo.exists():
            #         itemcombo_list = [
            #             {"id": combo.id, "qty": combo.qty}
            #             for combo in old_item.item_combo.all()
            #         ]
            #         itemdetails_id_qty.append({
            #             "id": old_item.id,
            #             "qty": old_item.qty,
            #             "itemcombo": itemcombo_list
            #         })

            serializer = SalesInvoiceSerializer(self.sales_invoice_obj,
                                                data=self.kwargs, partial=True, context={'request': self.info.context})
        else:
            serializer = SalesInvoiceSerializer(data=self.kwargs, context={'request': self.info.context})
        if serializer.is_valid():
            
            try: 
                serializer.save() 
                self.sales_invoice_obj = serializer.instance
                if "id" in self.kwargs and  self.kwargs['id']:
                    self.cleanup_old_income(item_details_old_id, other_income_old_id ) 
                # if self.status == "Draft" :
                #     self.update_invoice_draft_count(itemdetails_id_qty) 
                if self.status == "Submit":
                    self.update_invoice_submit_count()
                # if self.status == "Canceled":
                #     self.update_invoice_draft_submit_count(prev_status)
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
    
    def safe_decimal(self , val):
        return val if val is not None else Decimal('0')

    def cleanup_old_income(self, item_details_old_id, other_income_old_id):
        
        other_income_new_ids = set(self.sales_invoice_obj.other_income_charge.values_list('id', flat=True))
        other_income_delete_ids = list(other_income_old_id - other_income_new_ids)
        if other_income_delete_ids:
            SalesOrder_2_otherIncomeCharges.objects.filter(id__in=other_income_delete_ids).delete()
        
        item_details_new_id = set(self.sales_invoice_obj.item_detail.values_list('id', flat=True))
        item_detail_delete_ids = list(item_details_old_id - item_details_new_id)
        if item_detail_delete_ids:
            SalesInvoiceItemDetail.objects.filter(id__in=item_detail_delete_ids).delete()
        
    def update_sales_dc_links(self):
        if self.sales_invoice_obj:
            for sales_dc in self.sales_invoice_obj.sales_dc.all():
                sales_dc.sales_invoice = self.sales_invoice_obj
                sales_dc.save()

    # def update_invoice_draft_count(self, itemdetails_id_qty):
    #     for itemdetail in self.sales_invoice_obj.item_detail.all(): 
    #         old_id_qty = next((entry for entry in itemdetails_id_qty if entry['id'] == itemdetail.id), None)
    #         dc_item_details = itemdetail.item
    #         item_main_qty = Decimal(itemdetail.qty)
    #         if dc_item_details:
    #             # Remove old qty
    #             if old_id_qty:
    #                 dc_item_details.invoice_draft_count  = (dc_item_details.invoice_draft_count or 0) - Decimal(old_id_qty.get('qty', 0))
                
    #             # Add new qty
    #             dc_item_details.invoice_draft_count += Decimal(itemdetail.qty)
    #             dc_item_details.save()

    #             if dc_item_details.sales_order_item_detail.item_combo:
    #                 for itemCombo in itemdetail.item_combo.all():
    #                     combo_instance = itemCombo.item_combo

    #                     for dc_combo in itemCombo.item_combo.all():
    #                         dc_combo.invoice_draft_count = self.safe_decimal(dc_combo.invoice_draft_count)

    #                         if old_id_qty and "itemcombo" in old_id_qty:
    #                             old_combo_qty = next((combo for combo in old_id_qty['itemcombo']
    #                                                 if combo['id'] == itemCombo.id), None)
    #                             if old_combo_qty:
    #                                 dc_combo.invoice_draft_count -= Decimal(old_combo_qty.get('qty', 0))

    #                         dc_combo.invoice_draft_count += Decimal(itemCombo.qty)
    #                         dc_combo.save()


 

    def update_invoice_submit_count(self):
        for itemdetail in self.sales_invoice_obj.item_detail.all():
            dc_item_detail = itemdetail.item

            if itemdetail.item_combo.exists():
                for combo in itemdetail.item_combo.all():
                    sales_dc = combo.item_combo
                    sales_dc.invoice_submit_count = (sales_dc.invoice_submit_count or 0) + combo.qty
                    # if sales_dc.invoice_draft_count >= combo.qty:
                    #         sales_dc.invoice_draft_count = (sales_dc.invoice_draft_count or 0) - combo.qty
                    sales_dc.save()

            dc_item_detail.invoice_submit_count = (dc_item_detail.invoice_submit_count or 0) + itemdetail.qty

            dc_item_detail.save()

    def response(self): 
        return {"SalesInvoice":self.sales_invoice_obj,
            "success":self.success,
            "errors":self.errors,
            "item_detail":self.item_details,
            "other_income_charges":self.other_income_charges,
            "sales_account_ledger":self.account_list,
            }




from decimal import Decimal

def sales_invoice_general_update(data): 
    valid_serializers = []
    errors = []
    credits = data.get("credits", [])
    debit = data.get("debit", {})

    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "sales_invoice_voucher_no", "account", "created_by"]

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

