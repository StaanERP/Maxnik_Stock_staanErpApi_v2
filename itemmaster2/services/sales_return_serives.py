from itemmaster2.models import *
from itemmaster2.Serializer import *
from django.db import transaction
from itemmaster2.services.salesorder_delivery_challan_service import *
from decimal import Decimal

class SalesReturnService:

    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status_text = status
        self.status = None
        self.errors = [] 
        self.info = info
        self.success = False
        self.tds = None
        self.tcs = None
        self.combo_batch = {} # ex : {parent_index: [{combo_index: ['AA145']}]}
        self.item_batch = {}  # ex : {item_index: batch_list]}
        self.combo_serializer  = {}
        self.item_serializer = []
        self.other_charges_serializer = []
        self.other_charges_instance = []
        self.item_instance= [] 
        self.sales_return = None
        self.sales_order = None
        self.item_old_instance = [] 
    
    def process(self):
        try:
            # Start a database transaction 
            with transaction.atomic():
                if self.status_text == "Draft":
                    if not self.validate_required_fields():
                        return self.response()
                    print("----01")
                    if not self.validate_sales_invoice():
                        return self.response()
                    print("----02")
                    if not self.update_status_id():
                        return self.response()
                    print("----03")
                    if not self.validate_numbering_serial():
                        return self.response()
                    print("----04")
                    if not self.validate_item_details():
                        return self.response()
                    print("----05")
                    # if not self.validate_other_charges():
                    #     return self.response()
                    if not self.save_item_details():
                        return self.response()
                    print("----06")
                    # if not self.save_other_income_charges():
                        # return self.response()
                    if not self.save_sales_return():
                        return self.response()
                    
                    self.success = True
                    return self.response()
                elif self.status_text == "Submit": 
                    if not self.validate_required_fields():
                        return self.response()
                    print("---1")
                    if not self.validate_sales_invoice():
                        return self.response()
                    print("---2")
                    if not self.update_status_id():
                        return self.response()
                    print("---3")
                    if not self.check_item_befor_submit():
                        return self.response()
                    print("---4")
                    if not self.stock_additions():
                        return self.response()
                    print("---5")
                    print(self.status)
                    self.sales_return.status = self.status
                    self.sales_return.save()
                    self.success = True
                    return self.response()
                    
                else:
                    self.errors.append(f"{self.status_text} Unexpected status.")
                    return self.response()
        except Exception as e:
            self.errors.append(f"Unexpected error occurred {repr(e)}.")
            return self.response()
    
    def validate_required_fields(self) -> bool:
        REQUIRED_FIELDS = ["sr_date", "sales_order",  
                          "reason", "taxable_value", 'net_amount', "terms_conditions",
                        "terms_conditions_text"]
        
        for field in REQUIRED_FIELDS : 
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required')
                return False 
        if not self.kwargs.get("sales_invoice_ids") and not self.kwargs.get("sales_dc_ids"):
            self.errors.append(f'Sales invoice or Sales dc  ids is required')
            return False
        return True
    
    def update_status_id(self) -> bool:
        if self.status_text: 
            statusObjects = CommanStatus.objects.filter(name=self.kwargs["status"], table="Sales Return").first() 
            if statusObjects:
                self.status = statusObjects
                self.kwargs["status"] = statusObjects.id
                return True
            else:
                status = self.kwargs.get("status", "default_status")
                self.errors.append(f"Status {status} is not configured. Please contact support to add it.")
                return False
        else:
            self.errors.append("Status is required.")
            return False
    
    def validate_sales_invoice(self) -> bool:
        if "id" in self.kwargs and self.kwargs['id']:
            try:
                self.sales_return = SalesReturn.objects.filter(id=self.kwargs['id']).first()

                if not self.sales_return:
                    self.errors.append("Sales Return Not Found.")
                    return False
                if self.status_text == "Draft" and self.sales_return.status.name in ['Submit', "Canceled"]:
                    self.errors.append(f"Already {self.sales_return.status.name} Sales return did'n make Draft again.")
                elif self.status_text == "Submit" and self.sales_return.status.name in ["Canceled","Submit" ]:
                    self.errors.append(f"Already {self.sales_return.status.name} Sales return did'n make Submit again.")
                
                if len(self.errors):
                    return False
                
                self.item_old_instance = list(self.sales_return.salesreturnitemdetails_set.values_list('id', flat=True)) 

                self.sales_order = self.sales_return.sales_order

                if not self.sales_order:
                    self.errors.append("Sales Order Not Found.")
                    return False
            except ObjectDoesNotExist:
                self.errors.append("Sales invoice not Found.")
                return False
            except Exception as e:
                self.errors.append(f"An exception occurred {repr(e)}")
                return False
        else:
            self.sales_order = SalesOrder_2.objects.filter(id=self.kwargs.get("sales_order")).first()
            if not self.sales_order:
                self.errors.append("Sales order not Found.")
                return False
        return True
    
    def validate_numbering_serial(self) -> bool:
        if self.sales_return:
            return True
        conditions = {
            'resource': 'Sales Return',
            'default': True,
            "department": self.sales_order.department
        }
        try:
            series = NumberingSeries.objects.filter(**conditions).first()
            if not series:
                self.errors.append("Numbering Serial not found.")
                return False
            return True
        except Exception as e:
            self.errors.append(repr(e))
            return False
    
    def validate_item_combo(self, itemdetail, main_item_master, parent_index):
        combo_list = itemdetail.get("item_combo",[])
        if len(combo_list) > 0:
            instance_combo_list = []
            item_combo_labels = []
            try:
                for index, combo in enumerate(combo_list):
                    itemmaster = ItemMaster.objects.filter(id=combo.get("itemmaster", None)).first()
                    
                    if not itemmaster:
                        self.errors.append(f"{combo.get('itemmaster_name',None)} not found in item master.")
                        continue
                    item_combo_labels.append(itemmaster.item_part_code)

                    for field in [ "qty", "amount", "store"]:
                        if combo.get(field) is None:
                            self.errors.append(f'{main_item_master.item_part_code} --> {itemmaster.item_part_code} - {field} is required')
                    
                    if not combo.get("dc_item_combo") and  not combo.get("sales_invoice_item_combo"):
                        self.errors.append(f"{main_item_master.item_part_code} {itemmaster.item_part_code}  sales dc item combo and sales invoice item combo not found.")
                        continue

                    if combo.get("dc_item_combo"):
                        sales_dc_item_combo = SalesOrder_2_DeliverChallanItemCombo.objects.filter(id=combo.get("dc_item_combo")).first()
                        if not sales_dc_item_combo:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} sales dc item combo not found.")
                            continue

                        sales_order_item_combo = sales_dc_item_combo.item_combo
                        if not sales_order_item_combo:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} sales order item combo not found.")
                            continue

                        if sales_order_item_combo.itemmaster != itemmaster:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} item master  mismatch.")
                            continue
                        
                    if combo.get("sales_invoice_item_combo"):
                        sales_invoice_item_combo = SalesInvoiceItemCombo.objects.filter(id=combo.get("sales_invoice_item_combo")).first()
                        if not sales_invoice_item_combo:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} sales invoice item not found.")
                            continue
                        print("sales_invoice_item_combo", sales_invoice_item_combo)
                        sales_dc_combo = sales_invoice_item_combo.item_combo
                        print("sales_dc_combo", sales_dc_combo)
                        if not sales_dc_combo:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} sales dc item item not found.")
                            continue 
                        
                        sales_order_item_combo = sales_dc_combo.item_combo
                        if not sales_order_item_combo:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} sales order item item not found.")
                            continue

                        if sales_order_item_combo.itemmaster != itemmaster:
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} item master mismatch.")
                            continue
                    
                    if itemmaster.batch_number:
                        current_combo_batch = {}
                        if not combo.get("batch_link"):
                            self.errors.append(f"{main_item_master.item_part_code} --> {itemmaster.item_part_code} batch is required.")
                        
                        for combo_batch in combo.get("batch_link"):
                            batch_instance = None
                            combo_batch['item_detail'] = None

                            if combo_batch.get("id"):
                                batch_instance = SalesReturnBatch_item.objects.filter(id=combo_batch.get("id")).first()
                                
                                if not batch_instance:
                                    self.errors.append(f"{main_item_master.item_part_code}--> {itemmaster.item_part_code} -> batch serial id  {combo_batch.get('batch_str') or combo_batch.get('id')} not found.")
                                    continue
                            
                            for batch_field in ['batch', "qty" ]:
                                if not combo_batch.get(batch_field):
                                    self.errors.append(f"{itemmaster.item_part_code} -> {combo_batch.get('batch_str') or  ''} {batch_field} field is required'.")
                            
                            if self.errors:
                                continue

                            sales_return_combo_batch = SalesReturnBatch_itemSerialzer(batch_instance, data=combo_batch, partial=True)
                            if not sales_return_combo_batch.is_valid():
                                for field, field_errors in sales_return_combo_batch.errors.items():
                                    for err in field_errors:
                                        self.errors.append(f"{itemmaster.item_part_code} {combo_batch.get('batch_str') or  ''} - {field}: {err}")
                                continue
                            else:
                                current_combo_batch.setdefault(index, []).append(sales_return_combo_batch)

                        self.combo_batch.setdefault(parent_index, []).append(current_combo_batch)
                    elif itemmaster.serial:
                        if len(combo.get("serial")) != combo.get("qty"):
                            self.errors.append(f"{itemmaster.item_part_code} Total batch qty and item qty is mismatch.")
                            continue
                        combo['batch_link'] = []
                    else:
                        combo['batch_link'] = []
                        combo['serial'] = []
                    
                    combo_id = combo.get("id") 
                    if combo_id:
                        existing_combo_instance = SalesReturnItemCombo.objects.filter(id=combo_id).first()
                        if not existing_combo_instance:
                            self.errors.append(f"Item ID {combo_id} not found.")

                        instance_combo_list.append(existing_combo_instance)
                    else:
                        instance_combo_list.append(None)

                if len(self.errors) > 0:
                    return
                    
                item_result = validate_common_data_and_send_with_instance(
                    combo_list, instance_combo_list,
                    SalesReturnItemComboSerialzer,
                    item_combo_labels, self.info.context)
                
                if item_result.get("error"):
                    self.errors.extend(item_result["error"])
                    return {"sucess" : False, "error": self.errors, "instance" : []}
                self.combo_serializer[parent_index] =  item_result['instance']
                return
            except Exception as e:
                self.errors.append( f'An exception error occurred in item combo : {repr(e)}')
                return
        else:
            self.errors.append(f'For {main_item_master.item_part_code} Combo is required.')
            return
    
    def validate_item_details(self) -> bool:
        try:
            item_details = self.kwargs.get("item_details", [])
            instance__list = []
            item_labels = []
            if len(item_details)<=0:
                self.errors.append("At lease one item details required.")
                return False
            for index, item_detail in enumerate(item_details):

                itemmaster = ItemMaster.objects.filter(id=item_detail.get("itemmaster", None)).first() 
                if not itemmaster:
                    self.errors.append(f"{item_detail.get('itemmaster_name',None)} not found in item master.")
                    continue

                if item_detail.get("amount") is None:
                        self.errors.append(f'{itemmaster.item_part_code} - amount is required')

                item_labels.append(itemmaster.item_part_code)
                if not item_detail.get("dc_item_detail") and  not item_detail.get("sales_invoice_item_detail"):
                    self.errors.append(f"{itemmaster.item_part_code}  sales dc item and sales invoice item not found.")
                    continue
                
                if item_detail.get("dc_item_detail"):
                     
                    sales_dc_item = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id=item_detail.get("dc_item_detail")).first()
                    if not sales_dc_item:
                        self.errors.append(f"{itemmaster.item_part_code} sales dc item not found.")
                        continue

                    sales_order_item = sales_dc_item.sales_order_item_detail
                    if not sales_order_item:
                        self.errors.append(f"{itemmaster.item_part_code} sales order item item not found.")
                        continue

                    if sales_order_item.itemmaster != itemmaster:
                        self.errors.append(f"{itemmaster.item_part_code} item master mismatch.")
                        continue
                    
                if item_detail.get("sales_invoice_item_detail"):
                    print("=====>")
                    sales_invoice_item = SalesInvoiceItemDetail.objects.filter(id=item_detail.get("sales_invoice_item_detail")).first()
                    if not sales_invoice_item:
                        self.errors.append(f"{itemmaster.item_part_code} sales invoice item not found.")
                        continue
                    sales_dc = sales_invoice_item.item
                    print("=====>", sales_dc)
                    if not sales_dc:
                        self.errors.append(f"{itemmaster.item_part_code} sales dc item item not found.")
                        continue

                    sales_order_item = sales_invoice_item.item.sales_order_item_detail
                    if not sales_order_item:
                        self.errors.append(f"{itemmaster.item_part_code} sales order item item not found.")
                        continue

                    if sales_order_item.itemmaster != itemmaster:
                        self.errors.append(f"{itemmaster.item_part_code} item master mismatch.")
                        continue
                print("======>>>000")
                if not itemmaster.item_combo_bool:
                    required_fields = ["qty", "amount","store"]
                    for field in required_fields:
                        if item_detail.get(field) is None:
                            self.errors.append(f'{itemmaster.item_part_code} - {field} is required')

                    if itemmaster.batch_number:
                        if not item_detail.get("batch_link"):
                            self.errors.append(f"{itemmaster.item_part_code} batch is required.")
                            continue
                        
                        for batch_data in item_detail.get("batch_link"):
                            batch_instance = None
                            batch_data['item_combo'] = None
                            if batch_data.get("id"):
                                batch_instance = SalesReturnBatch_item.objects.filter(id=batch_data.get("id")).first()
                                
                                if not batch_instance:
                                    self.errors.append(f"{itemmaster.item_part_code} -> batch id  {batch_data.get('batch_str') or batch_data.get('id')} not found.")
                                    continue

                            for batch_field in ['batch', "qty" ]:
                                if not batch_data.get(batch_field):
                                    self.errors.append(f"{itemmaster.item_part_code} -> {batch_data.get('batch_str') or  ''} {batch_field} field is required'.")
                            
                            if self.errors:
                                continue

                            sales_return_item_batch = SalesReturnBatch_itemSerialzer(batch_instance, data=batch_data, partial=True)
                            if not sales_return_item_batch.is_valid():
                                for field, field_errors in sales_return_item_batch.errors.items():
                                    for err in field_errors:
                                        self.errors.append(f"{itemmaster.item_part_code} {batch_data.get('batch_str') or  ''} - {field}: {err}")
                                continue
                            else:
                                self.item_batch.setdefault(index, []).append(sales_return_item_batch)
                        
                        total_batch = sum(batch_data.get("qty", 0) for batch_data in item_detail.get("batch_link"))

                        if item_detail.get("qty", 0) != total_batch:
                            self.errors.append(f"{itemmaster.item_part_code} Total batch qty and item qty is mismatch.")
                            continue
                        item_detail['batch_link'] = []
                        item_detail['serial'] = []
                    elif itemmaster.serial:
                        if len(item_detail.get("serial")) != item_detail.get("qty"):
                            self.errors.append(f"{itemmaster.item_part_code} Total batch qty and item qty is mismatch.")
                            continue
                        item_detail['batch_link'] = []
                    else:
                        item_detail['batch_link'] = []
                        item_detail['serial'] = []
                
                elif itemmaster.item_combo_bool:
                    self.validate_item_combo(item_detail, itemmaster, index) 
                if item_detail.get("id"):
                    sales_return_item_instance = SalesReturnItemDetails.objects.filter(id=item_detail.get("id")).first()
                    if not sales_return_item_instance:
                        self.errors.append(f'{itemmaster.item_part_code} - id not found in sales return item details.')
                    instance__list.append(sales_return_item_instance)
                else:
                    instance__list.append(None)

            if not self.errors:
                item_result = validate_common_data_and_send_with_instance(
                        item_details, instance__list,
                        SalesReturnItemDetailsSerialzer,
                        item_labels, self.info.context)
                    
                if item_result.get("error"):
                    self.errors.extend(item_result["error"])
                    return False
                    
                self.item_serializer.extend(item_result.get("instance"))
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"An exception error occurred in item detail validations {repr(e)}")
            return False
    
    def validate_other_charges(self) ->bool:
        try:
            other_income_charges = self.kwargs.get("other_income_charge",[])
            charges_instance_list = []
            charges_labels = []
            if not other_income_charges:
                return True
            
            for other_income_charge in  other_income_charges:
                oid = other_income_charge.get("other_income_charges_id")
                other_income_charge_obj = OtherIncomeCharges.objects.filter(id=oid).first()

                if not other_income_charge_obj:
                    self.errors.append(f"{other_income_charge.get('other_income_charges_name',None)} not found in other charges.")
                    continue

                charges_labels.append(other_income_charge_obj)
                for field in ["parent","amount"]:
                    if other_income_charge.get(field) is None:
                        self.errors.append(f'{other_income_charge_obj} - {field} is required')
                
                # existing instance check
                if other_income_charge.get("id"):
                    sales_return_other_income = SalesReturnOtherIncomeCharges.objects.filter(id=other_income_charge.get("id")).first()

                    if not  sales_return_other_income:
                        self.errors.append(f"{other_income_charge_obj} not found in  Sales Return Other Income Charges.")
                    
                    charges_instance_list.append(sales_return_other_income)
                else:
                    charges_instance_list.append(None)
            
            if not self.errors:
                item_result = validate_common_data_and_send_with_instance(
                        other_income_charges, charges_instance_list,
                        SalesReturnOtherIncomeChargesSerializer,
                        charges_labels, self.info.context)
                    
                if item_result.get("error"):
                    self.errors.extend(item_result["error"])
                    return False
                    
                self.other_charges_serializer.extend(item_result.get("instance"))
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"An exception error occurred in other income chages validations {repr(e)}")
            return False
    
    def save_item_combo(self,parent_index, parent_instance) -> bool:
        """save item combo after validations"""
        try:
            for combo_index , combo in enumerate(self.combo_serializer.get(parent_index, [])):
                if not combo:
                    continue
                validated_data = combo.validated_data
                validated_data["item_detail"] = parent_instance
                combo.save()

                combo_batches = self.combo_batch.get(parent_index, [])
                for current_combo_batch in combo_batches:
                    if combo_index in current_combo_batch:
                        for item_combo_batch in current_combo_batch[combo_index]:
                            vd_combo = item_combo_batch.validated_data
                            vd_combo["item_combo"] = combo.instance
                            item_combo_batch.save(**vd_combo)


                dc_item_combo_instance = None
                if combo.instance.dc_item_combo:
                    dc_item_combo_instance = combo.instance.dc_item_combo

                elif combo.instance.sales_invoice_item_combo:
                    sales_invoice_item = combo.instance.sales_invoice_item_combo
                    
                    if sales_invoice_item:
                        dc_item_combo_instance = sales_invoice_item.item_combo
                
                if dc_item_combo_instance is None:
                    self.errors.append(f"index {combo_index+1} -> {combo.instance.itemmaster.item_part_code} dc link not found.")
                    continue
                
                dc_item_combo_instance.return_draft_count = (dc_item_combo_instance.return_draft_count or 0) + (combo.instance.qty or 0)
                dc_item_combo_instance.save()
            return len(self.errors) == 0

        except Exception as e:
            self.errors.append(f"Unexpeted error occurred in item combo - Save {repr(e)}")
            return len(self.errors) == 0
    
    def save_item_details(self) -> bool:
        """Save item details after validation"""
        try:
            item_details = self.kwargs.get('item_details', [])
            if len(self.item_serializer) != len(item_details):
                self.errors.append("Item serializer count mismatch.")
                return False

            for index, serializer in enumerate(self.item_serializer):
                if not serializer:
                    continue
                serializer.save()
                self.item_instance.append(serializer.instance)

                # safe check for item_batch for this index
                batches_for_index = self.item_batch.get(index, [])
                for item_batch in batches_for_index:
                    try:
                        vd = item_batch.validated_data
                        vd["item_detail"] = serializer.instance
                        item_batch.save(**vd)
                    except Exception as e:
                        
                        self.errors.append(f"Unexpected error occurred in batch serial - Save {repr(e)}")
                        continue
                        # continue saving other items but mark rollback
                        
                if self.errors:
                    transaction.set_rollback(True)
                    break
                
                dc_item_instance = None
                if serializer.instance.dc_item_detail:
                    dc_item_instance = serializer.instance.dc_item_detail
                elif serializer.instance.sales_invoice_item_detail:
                    sales_invoice_item = serializer.instance.sales_invoice_item_detail
                    if sales_invoice_item:
                        dc_item_instance = sales_invoice_item.item
                
                if dc_item_instance is None:
                    self.errors.append(f"index {index+1} -> {serializer.instance.itemmaster.item_part_code} dc link not found.")
                    continue
                
                dc_item_instance.return_draft_count = (dc_item_instance.return_draft_count or 0) + (serializer.instance.qty or 0)
                dc_item_instance.save()


                # save combos if any
                if index in self.combo_serializer:
                    if not self.save_item_combo(index, serializer.instance):
                        # errors appended inside save_item_combo
                        transaction.set_rollback(True)
                        break

            if self.errors:
                transaction.set_rollback(True)
            return len(self.errors) == 0

        except Exception as e:
            transaction.set_rollback(True)
            self.errors.append(f"Unexpected error occurred in item - Save {repr(e)}")
            return False
    
    def save_sales_return(self) -> bool:
        try:
            if "id" in self.kwargs and self.kwargs['id'] and self.sales_return:
                serializer = SalesReturnSerializer(self.sales_return, data=self.kwargs,
                                                partial=True, context={'request': self.info.context})
            else:
                serializer = SalesReturnSerializer(data=self.kwargs, partial=True,
                                                context={'request': self.info.context})

            if serializer is None:
                self.errors.append("Serializer initialization failed.")
                return False

            if serializer.is_valid():
                instance = serializer.save()
                self.sales_return = instance
                # attach saved sales_return to item instances 

                for item in self.item_instance:
                    item.sales_return = instance
                    item.save()
                
                for charge in self.other_charges_instance:
                    charge.sales_return = instance
                    charge.save()
                
                if self.kwargs.get("sales_dc_ids"): 
                    sales_dc_list = SalesOrder_2_DeliveryChallan.objects.filter(id__in=self.kwargs.get("sales_dc_ids"))
                    if not sales_dc_list:
                        transaction.set_rollback(True)
                        self.errors.append("Sales Dc not found. refresh the page and try again")
                        return False 
                    if len(sales_dc_list) != len(self.kwargs.get("sales_dc_ids", [])):
                        self.errors.append("Some Sales Dc ids is not found. refer the page and try again")
                        transaction.set_rollback(True)
                        return False
                    
                    for sales_dc in sales_dc_list:
                        sales_dc.sales_return.add(self.sales_return)
                 
                if self.kwargs.get("sales_invoice_ids"):
                    sales_invoice_list = SalesInvoice.objects.filter(id__in=self.kwargs.get("sales_invoice_ids"))
                    
                    if not sales_invoice_list:
                        transaction.set_rollback(True)
                        self.errors.append("Sales Invoice not found. refer the page and try again")
                        return False

                    if len(sales_invoice_list) != len(self.kwargs.get("sales_invoice_ids", [])):
                        self.errors.append("Some Sales Invoice ids is not found. refer the page and try again")
                        transaction.set_rollback(True)
                        return False
                    
                    for sales_invoice in sales_invoice_list:
                        sales_invoice.sales_return.add(self.sales_return)

                deleteCommanLinkedTable(self.item_old_instance, [item.id for item in self.item_instance], SalesReturnItemDetails)
                

                return True
            else:
                for field, error in serializer.errors.items():
                    self.errors.append(f"{field}: {'; '.join(repr(e) for e in error)}")
                transaction.set_rollback(True)
                return False

        except Exception as e:
            transaction.set_rollback(True)
            self.errors.append(f"Unexpected error occurred in sales return - Save {repr(e)}")
            return False
    
    def response(self) -> dict:
        return {
            "sales_return":self.sales_return,
            "success":self.success,
            "errors":self.errors
            }
    
    def check_item_befor_submit(self) -> bool:
        self.item_instance = self.sales_return.salesreturnitemdetails_set.all()

        for item in self.item_instance:

            if item.is_stock_added:
                continue

            # SIMPLE ITEM
            if not item.itemmaster.item_combo_bool:

                dc_item = item.dc_item_detail
                print("main", item.itemmaster)
                # 1. DC ITEM FLOW
                if dc_item:
                    old_return = dc_item.return_submit_count or 0
                    old_invoice = dc_item.invoice_submit_count or 0

                    new_qty = (item.qty or 0) + old_return + old_invoice

                    if new_qty > dc_item.qty:
                        self.errors.append(
                            f" {item.itemmaster.item_part_code} Exceeds total Qty!"
                        )

                    # Serial validation
                    if item.itemmaster.serial:
                         
                        existing_serial_ids = list(
                            dc_item.dc_item_sales_return
                            .filter(is_stock_added=True)
                            .values_list("serial__id", flat=True)
                        )

                        used_serials = [
                            s.serial_number
                            for s in item.serial.all()
                            if s.id in existing_serial_ids
                        ]

                        if used_serials:
                            self.errors.append(
                                f"{item.itemmaster.item_part_code}-> "
                                f"{','.join(used_serials)} These Serial Nos has already been returned!"
                            )

                # -----------------------------
                # 2. INVOICE COMBO FLOW
                # -----------------------------
                elif item.sales_invoice_item_detail:
                    sales_invoice = item.sales_invoice_item_detail
                    dc_items = item.sales_invoice_item_detail.item

                    # sum_return =  (dc_items.return_submit_count or 0)
                    # sum_invoice = (dc_items.invoice_submit_count or 0)
              
                    sum_return = sales_invoice.salesreturnitemdetails_set.filter(sales_return__status__name="Submit").aggregate(
                                                                    total=Sum('qty'))['total'] or 0
                    sum_invoice = dc_items.salesinvoiceitemdetail_set.filter(salesinvoice__status__name="Submit").exclude(id=sales_invoice.id).aggregate(
                                                                    total=Sum('qty'))['total'] or 0

                    new_qty = (item.qty or 0) + sum_return + sum_invoice

                    total_dc_qty =  dc_items.qty 
                    if new_qty > total_dc_qty:
                        self.errors.append(
                            f" {item.itemmaster.item_part_code} Exceeds total Qty.!"
                        )

                    # Serial validations for combo
                    if item.itemmaster.serial:
                        all_used_serial_ids =  dc_items.dc_item_sales_return\
                                                    .filter(is_stock_added=True)\
                                                    .values_list("serial__id", flat=True)

                        duplicate_serials = [
                            s.serial_number for s in item.serial.all()
                            if s.id in all_used_serial_ids
                        ]

                        if duplicate_serials:
                            self.errors.append(
                                f"{item.itemmaster.item_part_code}-> "
                                f"{','.join(duplicate_serials)} These Serial Nos has already been returned!"
                            )

                # -----------------------------
                # 3. BATCH VALIDATION
                # -----------------------------
                if item.itemmaster.batch_number:

                    # Each SalesReturnBatch tied to this item
                    for batch_item in item.salesreturnbatch_item_set.all():
                        batch_instance = batch_item.batch
                        dc_batch_qty = batch_instance.qty or 0

                        # Total returned for that batch from all sales returns
                        batch_total_return = (
                            batch_instance.salesreturnbatch_item_set
                            .filter(is_stock_added=True)
                            .aggregate(total=Sum("qty"))["total"] or 0
                        )

                        new_total = (batch_item.qty or 0) + batch_total_return

                        if new_total > dc_batch_qty:
                            self.errors.append(
                                f"{item.itemmaster.item_part_code} -> Exceeds the Batch Qty {batch_instance.batch.batch_number_name} !"
                                f"Returned Qty: {batch_total_return}"
                                f"Current: {batch_item.qty}, Batch Qty: {dc_batch_qty}"
                            )

            # COMBO ITEM OUTSIDE NORMAL FLOW
            else:
                for combo_item in item.salesreturnitemcombo_set.all():
                    if combo_item.is_stock_added:
                        continue
                    dc_item_combo = combo_item.dc_item_combo

                    # -----------------------------
                    # 1. DC ITEM FLOW
                    # -----------------------------
                    if dc_item_combo:
                        old_return_combo = dc_item_combo.return_submit_count or 0
                        old_invoice_combo = dc_item_combo.invoice_submit_count or 0

                        new_combo_qty = (combo_item.qty or 0) + old_return_combo + old_invoice_combo

                        if new_combo_qty > combo_item.qty:
                            self.errors.append(
                                f"{combo_item.itemmaster.item_part_code} Exceeds total Qty!"
                            )

                        # Serial validation
                        if combo_item.itemmaster.serial:
                            existing_combo_serial_ids = list(
                                dc_item_combo.salesreturnitemcombo_set
                                .filter(is_stock_added=True)
                                .values_list("serial__id", flat=True)
                            )

                            combo_used_serials = [
                                s.serial_number
                                for s in combo_item.serial.all()
                                if s.id in existing_combo_serial_ids
                            ]

                            if combo_used_serials:
                                self.errors.append(
                                    f"{combo_item.itemmaster.item_part_code}-> "
                                    f"{','.join(combo_used_serials)} These Serial Nos has already been returned!"
                                )
                    
                    # -----------------------------
                    # 2. INVOICE COMBO FLOW
                    # -----------------------------
                    elif combo_item.sales_invoice_item_combo:
                        dc_item_combos = combo_item.sales_invoice_item_combo.item_combo
                        sales_invoice_combo = combo_item.sales_invoice_item_combo
                        
                        # sum_return = (dc_item_combos.return_submit_count or 0)
                        # sum_invoice = (dc_item_combos.invoice_submit_count or 0)
                        sum_return = sales_invoice_combo.salesreturnitemcombo_set.filter(item_detail__sales_return__status__name="Submit").aggregate(
                                                                    total=Sum('qty'))['total'] or 0
                        sum_invoice = dc_item_combos.salesinvoiceitemcombo_set.filter(salesinvoiceitemdetail__salesinvoice__status__name="Submit").exclude(id=sales_invoice_combo.id).aggregate(
                                                                    total=Sum('qty'))['total'] or 0
                        
                        new_qty = (combo_item.qty or 0) + sum_return + sum_invoice

                        total_dc_qty = dc_item_combos.qty

                        if new_qty > total_dc_qty:
                            self.errors.append(
                                f"{item.itemmaster.item_part_code} Exceeds total Qty!"
                            )

                        # Serial validations for combo
                        if combo_item.itemmaster.serial:
                            all_used_serial_ids =  dc_item_combos.salesreturnitemcombo_set \
                                                    .filter(is_stock_added=True) \
                                                    .values_list("serial__id", flat=True) \


                            combo_duplicate_serials = [
                                s.serial_number for s in combo_item.serial.all()
                                if s.id in all_used_serial_ids
                            ]

                            if combo_duplicate_serials:
                                self.errors.append(
                                    f"{combo_item.itemmaster.item_part_code}-> "
                                    f"{','.join(combo_duplicate_serials)} These Serial Nos has already been returned!"
                                )

                    # -----------------------------
                    # 3. BATCH VALIDATION
                    # -----------------------------
                    if combo_item.itemmaster.batch_number:

                        # Each SalesReturnBatch tied to this item
                        for batch_item in combo_item.salesreturnbatch_item_set.all():
                            batch_instance = batch_item.batch
                            dc_batch_qty = batch_instance.qty or 0

                            # Total returned for that batch from all sales returns
                            batch_total_return = (
                                batch_instance.salesreturnbatch_item_set
                                .filter(is_stock_added=True)
                                .aggregate(total=Sum("qty"))["total"] or 0
                            )

                            new_total = (batch_item.qty or 0) + batch_total_return

                            if new_total > dc_batch_qty:
                                self.errors.append(
                                f"{combo_item.itemmaster.item_part_code} -> Exceeds the Batch Qty {batch_instance.batch.batch_number_name} !"
                                f"Returned Qty: {batch_total_return}"
                                f"Current: {batch_item.qty}, Batch Qty: {dc_batch_qty}"
                            )

        return not self.errors

    def addBatchStockIn(self, itemmaster, batchs, store, qty, transaction_model, transaction_id, saveing_user, display_id, display_name):
 
        try:
            for batch in batchs:
                if batch.is_stock_added:
                    continue
   
                batch_addtions =  AddStockDataService(part_code=itemmaster, 
                                                    store=store,
                                                    batch=batch.batch.batch,
                                                    qty=batch.qty,
                                                    unit=itemmaster.item_uom,
                                                    transaction_model=transaction_model,
                                                    transaction_id= transaction_id,
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = None,
                                                    conference = None)
                batch_addtions.add_batch_stock()
                if batch_addtions.success:
                    batch.is_stock_added = True
                    batch.save()
                    return None
                else:
                    return  batch.errors
                
        except Exception as e:
            return [f"{itemmaster} -- {e}"]
    
    def addSerialStockIn(self, itemmaster, serials, store, qty, transaction_model, transaction_id, saveing_user, display_id, display_name):
        serial = AddStockDataService(part_code=itemmaster,
                                        store=store,
                                        serials=serials,
                                        qty=len(serials),
                                        unit=itemmaster.item_uom,
                                        transaction_model=transaction_model,
                                        transaction_id= transaction_id,
                                        saved_by = saveing_user,
                                        display_id= display_id,
                                        display_name= display_name,
                                        rate = None,
                                        conference = None)
   
        serial.add_serial_stock()

        if serial.success:
            return None
        else:
            self.errors.extend(serial.errors)
            return False
    
    def addNoBatchSerialStockIn(self, itemmaster,   store, qty, transaction_model, transaction_id, saveing_user, display_id, display_name):
        nobatch_noserial = AddStockDataService(part_code=itemmaster,
                                        store=store, 
                                        qty=qty,
                                        unit=itemmaster.item_uom,
                                        transaction_model=transaction_model,
                                        transaction_id= transaction_id,
                                        saved_by = saveing_user,
                                        display_id= display_id,
                                        display_name= display_name,
                                        rate = None,
                                        conference = None)
        nobatch_noserial.add_non_tracked_stock()
        if nobatch_noserial.success:
            return None
        else:
            self.errors.extend(nobatch_noserial.errors)
            return False

    def stock_additions(self) -> bool:
        transaction_model = "Sales Return"
        transaction_id = self.sales_return.id
        saveing_user = self.info.context.user
        display_id = self.sales_return.sr_no.linked_model_id
        display_name = "Sales Return"
        try:
            for item in self.sales_return.salesreturnitemdetails_set.all():
                if item.is_stock_added:
                    continue
                itemmaster_item = item.itemmaster
                print("itemmaster_item", itemmaster_item)
                if not itemmaster_item.item_combo_bool:
                    if itemmaster_item.batch_number:
                        
                        batch_list = item.salesreturnbatch_item_set.all()
                        if batch_list:
                            error = self.addBatchStockIn(itemmaster_item, batch_list, item.store, item.qty,
                                                        transaction_model, transaction_id, saveing_user,
                                                        display_id, display_name)

                            if error:
                                self.errors.extend(error)
                                transaction.set_rollback(True)
                                return False
                    
                    elif itemmaster_item.serial:
                        print("serial")
                        error = self.addSerialStockIn(itemmaster_item, item.serial.all(), item.store, item.qty,
                                                    transaction_model, transaction_id, saveing_user,
                                                    display_id, display_name)
                        print("error", error)
                        if error:
                            self.errors.extend(error)
                            transaction.set_rollback(True)
                            return False
                    
                    else: 
                        error = self.addNoBatchSerialStockIn(itemmaster_item, dc_item.store, item.qty,
                                                            transaction_model, transaction_id, saveing_user,
                                                            display_id, display_name)
                        if error:
                            self.errors.extend(error)
                            transaction.set_rollback(True)
                            return False
                    dc_item = None

                    if item.dc_item_detail:
                        dc_item = item.dc_item_detail

                    elif item.sales_invoice_item_detail.item:
                        dc_item = item.sales_invoice_item_detail.item

                    if dc_item:
                        item.is_stock_added = True
                        item.save()
                        dc_item.return_submit_count = (dc_item.return_submit_count or 0) + item.qty
                        dc_item.save()

                elif item.itemmaster.item_combo_bool:
                    for combo_item in item.salesreturnitemcombo_set.all():
                        if combo_item.itemmaster.batch_number:
                            combo_batch_list = combo_item.salesreturnbatch_item_set.all()
                            if combo_batch_list:

                                error = self.addBatchStockIn(combo_item.itemmaster, combo_batch_list, combo_item.store, combo_item.qty,
                                                        transaction_model, transaction_id, saveing_user,
                                                        display_id, display_name)
                                if error:
                                    self.errors.extend(error)
                                    transaction.set_rollback(True)
                                    return False
                                
                        elif combo_item.itemmaster.serial:
                            error = self.addSerialStockIn(combo_item.itemmaster, combo_item.serial.all(), combo_item.store, combo_item.qty,
                                                    transaction_model, transaction_id, saveing_user,
                                                    display_id, display_name)
                            if error:
                                self.errors.extend(error)
                                transaction.set_rollback(True)
                                return False
                            
                        else: 
                            error = self.addNoBatchSerialStockIn(combo_item.itemmaster, combo_item.store, combo_item.qty,
                                                            transaction_model, transaction_id, saveing_user,
                                                            display_id, display_name)
                            
                            if error:
                                self.errors.extend(error)
                                transaction.set_rollback(True)
                                return False
                        
                        dc_item_combo = None

                        if combo_item.dc_item_combo:
                            dc_item_combo = combo_item.dc_item_combo

                        elif combo_item.sales_invoice_item_combo.item_combo:
                            dc_item_combo = combo_item.sales_invoice_item_combo.item_combo

                        if dc_item_combo:
                            combo_item.is_stock_added = True
                            combo_item.save()
                            dc_item_combo.return_submit_count = (dc_item_combo.return_submit_count or 0) + item.qty
                            dc_item_combo.save()
                            
                    item.is_stock_added = True
                    item.save()
            return len(self.errors) == 0
        except Exception as e:
                self.errors.append(f"unexpeted error occurred: {str(e)}")
                return False
        

class SalesReturnCancelService:

    def __init__(self, id ):
        self.id = id 
        self.sales_return = None
        self.errors = []
        self.needStock = []
        self.success = False
        self.status = None
    
    def process(self) ->dict:
        with transaction.atomic():
            try:
                if not self.get_sales_return():
                    return self.response()
                print("----1")
                if not self.check_the_stock():
                    return self.response()
                print("----2")
                if not self.stock_reduce():
                    return self.response()
                print("----3")
                if not self.update_status_id():
                    return self.response()
                print("----4")
                self.sales_return.status = self.status
                self.sales_return.save()
                self.success = True
                return self.response()
            except Exception as e:
                self.errors.append(f"An exception occurred {str(e)}")
                transaction.rollback(True)
                return self.response()
            

    def update_status_id(self) -> bool:
        statusObjects = CommanStatus.objects.filter(name="Canceled", table="Sales Return").first() 
        if statusObjects:
            self.status = statusObjects
            return True
        else: 
            self.errors.append(f"Canceled status is not configured. Please contact support to add it.")
            return False

    def get_sales_return(self) -> bool:
        try:
            self.sales_return = SalesReturn.objects.filter(id=self.id).first()
            if not self.sales_return:
                    self.errors.append("Sales Return Not Found.")
                    return False
            
            if  self.sales_return.status.name in [ "Canceled"]:
                self.errors.append("Sales return is already canceled!")

            
            return not self.errors
        except Exception as e:
            self.errors.append(f"Unexpeted error: {str(e)}")
            return not self.errors
    
    def check_batch_stock(self, batchs, item_master, store_id) -> bool:
        needStock = []
        for batch in batchs:
            if not batch.is_stock_added:
                required_stock= (batch.qty or 0)
                stock_data_existing = ItemStock.objects.filter(
                            part_number=item_master.id,
                            store=store_id,
                            batch_number=batch.batch.id
                        ).first()
                if stock_data_existing:
                    current_stock = Decimal(stock_data_existing.current_stock)
                    
                    if (current_stock - required_stock) < 0:
                        batch_lable = batch.batch.batch_number_name 
                        needStock.append({
                                        "partcode": item_master.item_part_code,
                                        "batch": batch_lable,
                                        "needStock": abs(current_stock - required_stock)
                                    })
                        
                else:
                    batch_lable = batch.batch.batch_number_name
                    needStock.append({
                        "partcode": item_master.item_part_code,
                        "batch": batch_lable,
                        "needStock": required_stock
                    })
        
        self.needStock.extend(needStock)

        return len(needStock) == 0

    def check_serial_stock(self, serials, item_master, store_id)  -> bool:
        needStock = []
        serial_ids = [serial.id for serial in serials]
        stock_data_existing = ItemStock.objects.filter(
                        part_number=item_master.id,
                        store=store_id,
                    ).first()
        if not stock_data_existing:
            missing_serial_str = [serial.serial_number for serial in serials]
            needStock.append({
                    "partcode": item_master.item_part_code,
                    "Serial": ", ".join(missing_serial_str),
                    "needStock": len(serial_ids)
                })
            return False
        
        # Fetch the serial numbers associated with this stock
        serial_list = [serial.id for serial in stock_data_existing.serial_number.all()]
        
        # Check if all serial_ids are in serial_list
        missing_serial_ids = [serial_id for serial_id in serial_ids if serial_id not in serial_list]
        # Fetch the missing serial numbers
        missing_serials = SerialNumbers.objects.filter(id__in=missing_serial_ids)
        
        if missing_serial_ids:
            needSerial = [serial.serial_number for serial in missing_serials]
            needStock.append({
                "partcode": item_master.item_part_code,
                "Serial": needSerial,
                "needStock": len(needSerial)
            })
        
        self.needStock.extend(needStock)

        return len(needStock) == 0

    def check_no_batch_serial(self, item_master, store_id, required_stock)  -> bool:
        needStock = []
        stock_data_existing = ItemStock.objects.filter(part_number=item_master.id,
                                            store=store_id).first()
        if not stock_data_existing:
            needStock.append({
                "partcode": item_master.item_part_code,
                "needStock": required_stock
            })
            return False
        
        current_stock = Decimal(stock_data_existing.current_stock)
        required_stock = Decimal(required_stock)

        if (current_stock - required_stock) < 0:
            needStock.append({
                "partcode": item_master.item_part_code,
                "needStock": abs(current_stock - required_stock)
            })
        self.needStock.extend(needStock)

        return len(needStock) == 0

    def check_the_stock(self)  -> bool:
        for item in self.sales_return.salesreturnitemdetails_set.all():
            if not item.is_stock_added:
                continue

            if not item.itemmaster.item_combo_bool:
                # SIMPLE ITEM
                if item.itemmaster.batch_number:
                    ok = self.check_batch_stock(
                        item.salesreturnbatch_item_set.all(),
                        item.itemmaster,
                        item.store.id
                    )
                
                elif item.itemmaster.serial:
                    ok = self.check_serial_stock(
                        item.serial.all(),
                        item.itemmaster,
                        item.store.id
                    )
                
                else:
                    ok = self.check_no_batch_serial(
                        item.itemmaster,
                        item.store.id,
                        item.qty
                    )

                if not ok:
                    continue
            
            else:
                # COMBO ITEM
                for combo_item in item.salesreturnitemcombo_set.all():
                    if not combo_item.is_stock_added:
                        continue

                    if combo_item.itemmaster.batch_number:
                        ok = self.check_batch_stock(
                            combo_item.salesreturnbatch_item_set.all(),
                            combo_item.itemmaster,
                            combo_item.store.id
                        )
                    elif combo_item.itemmaster.serial:
                        ok = self.check_serial_stock(
                            combo_item.serial.all(),
                            combo_item.itemmaster,
                            combo_item.store.id
                        )
                    else:
                        ok = self.check_no_batch_serial(
                            combo_item.itemmaster,
                            combo_item.store.id,
                            combo_item.qty
                        )

                    if not ok:
                        continue

        return len(self.needStock) == 0

    def reduce_batch_stock(self, item, itemmaster, store_id, is_combo) -> bool:
        try:
            total_qty = 0
            for batch in item.salesreturnbatch_item_set.all():
                qty = batch.qty or 0

                stock_reduce = StockReduce(
                    partCode_id=itemmaster.id,
                    Store_id=store_id,
                    batch_id=batch.batch.batch.id,
                    serial_id_list=[],
                    qty=qty,
                    partCode=itemmaster,
                    batch=batch.batch.batch.batch_number_name
                )

                batch_result = stock_reduce.reduceBatchNumber()

                if batch_result.get("success"):
                    total_qty += qty
                    batch.is_stock_reduce = False
                    batch.save()
                else:
                    self.errors.extend(batch_result.get("error"))
                    continue

            if self.errors:
                return False
            if is_combo:
                if item.dc_item_combo:
                    item.dc_item_combo.return_submit_count = (item.dc_item_combo.return_submit_count or 0) - total_qty
                else:
                    item.sales_invoice_item_combo.item_combo.return_submit_count = (item.sales_invoice_item_combo.item_combo.return_submit_count or 0) - total_qty
            else:
                if item.dc_item_detail:
                    item.dc_item_detail.return_submit_count = (item.dc_item_detail.return_submit_count or 0) - total_qty
                else:
                    item.sales_invoice_item_detail.item.return_submit_count = (item.sales_invoice_item_detail.item.return_submit_count or 0) - total_qty

            item.is_stock_reduce = False
            item.save()
            return True

        except Exception as e:
            self.errors.append(f"Unexpected error: {str(e)}")
            return False

    
    def reduce_serial_stock(self, item, itemmaster, store_id, is_combo) ->bool:
        serial_id = [serial.id for serial in item.serial.all()]
                    
        stock_reduce = StockReduce(
                            partCode_id= itemmaster.id,
                            Store_id= store_id,
                            batch_id= None,
                            serial_id_list= serial_id,
                            qty= item.qty,
                            partCode = itemmaster,
                            batch =  None)
        
        serial_result = stock_reduce.reduceSerialNumber()
        if serial_result.get("success"):
            if is_combo:
                if item.dc_item_combo:
                    item.dc_item_combo.return_submit_count = (item.dc_item_combo.return_submit_count or 0) - item.qty
                else:
                    item.sales_invoice_item_combo.item_combo.return_submit_count = (item.sales_invoice_item_combo.item_combo.return_submit_count or 0) - item.qty
            else:
                if item.dc_item_detail:
                    item.dc_item_detail.return_submit_count = (item.dc_item_detail.return_submit_count or 0) - item.qty
                else:
                    item.sales_invoice_item_detail.item.return_submit_count = (item.sales_invoice_item_detail.item.return_submit_count or 0) - item.qty

            item.is_stock_reduce = False
            item.save()

        else:
            self.errors.extend(serial_result.get("error"))
        return len(self.errors) == 0

    def reduce_no_batch_serial_stock(self, item, itemmaster, store_id, is_combo) ->bool:
                
        stock_reduce = StockReduce(
                            partCode_id= itemmaster.id,
                            Store_id= store_id,
                            batch_id= None,
                            serial_id_list= [],
                            qty= item.qty,
                            partCode = itemmaster,
                            batch =  None)
        
        no_batch_serial_result = stock_reduce.reduceNoBatchNoSerial()
        if no_batch_serial_result.get("success"):
            if is_combo:
                if item.dc_item_combo:
                    item.dc_item_combo.return_submit_count = (item.dc_item_combo.return_submit_count or 0) - item.qty
                else:
                    item.sales_invoice_item_combo.item_combo.return_submit_count = (item.sales_invoice_item_combo.item_combo.return_submit_count or 0) - item.qty
            else:
                if item.dc_item_detail:
                    item.dc_item_detail.return_submit_count = (item.dc_item_detail.return_submit_count or 0) - item.qty
                else:
                    item.sales_invoice_item_detail.item.return_submit_count = (item.sales_invoice_item_detail.item.return_submit_count or 0) - item.qty
            item.is_stock_reduce = False
            item.save()
            return True
        else:
            self.errors.extend(no_batch_serial_result.get("error"))
        return len(self.errors) == 0

    def stock_reduce(self) -> bool:
        try:
            for item in self.sales_return.salesreturnitemdetails_set.all():
                if not item.is_stock_added:
                    continue
                
                if not item.itemmaster.item_combo_bool:
                    itemmaster = item.itemmaster 
                    store_id = item.store.id

                    if itemmaster.batch_number:
                        ok = self.reduce_batch_stock(item, itemmaster, store_id , False)
                    elif itemmaster.serial:
                        ok = self.reduce_serial_stock(item, itemmaster, store_id , False)
                    else:
                        ok = self.reduce_no_batch_serial_stock(item, itemmaster, store_id , False)

                    if not ok:
                        transaction.set_rollback(True)
                        return False

                else:
                    for combo_item in item.salesreturnitemcombo_set.all():
                        if not combo_item.is_stock_added:
                            continue

                        im = combo_item.itemmaster
                        sid = combo_item.store.id

                        if im.batch_number:
                            ok = self.reduce_batch_stock(combo_item, im, sid , True)
                        elif im.serial:
                            ok = self.reduce_serial_stock(combo_item, im, sid , True)
                        else:
                            ok = self.reduce_no_batch_serial_stock(combo_item, im, sid , True)

                        if not ok:
                            transaction.set_rollback(True)
                            return False
                    item.is_stock_reduce = False
                    item.save()

            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Unexpeted error {e}.")
            transaction.rollback(True)
            return False

        

    def response(self) -> dict:
        return {
            "sales_return":self.sales_return,
            "need_stock" : self.needStock,
            "success":self.success,
            "errors":self.errors
            }


def sales_return_general_update(data):
    valid_serializers = []
    errors = []
    credit = data.get("credit", {})
    debits = data.get("debits", [])

    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type","sales_return_voucher_no", "account", "created_by"]

    # Process debits
    for idx, debit in enumerate(debits):
        for field in REQUIRED_FIELDS + ["debit"]:
            if debit.get(field) in [None, ""]:
                errors.append(f"credit [{idx}] → '{field}' is required.")
        
        debit_amount = debit.get("debit", 0) 
        debits_amount += debit_amount

        serializer = AccountsGeneralLedgerSerializer(data=debit)
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"debit [{idx}] → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)
    
    # Process credit
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

