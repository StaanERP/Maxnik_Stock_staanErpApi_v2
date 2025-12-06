from itemmaster.models import *
from itemmaster.serializer import *
from itemmaster.Utils.CommanUtils import *
from itemmaster.schema import *
from itemmaster2.Utils.ItemMasterComman import *

class PurchaseService:
    def __init__(self, data, status, info):
        self.data = data
        self.status = status
        self.success = False
        self.errors = []
        self.info = info
        self.purchase_obj = None
        self.item_details_instances = []
        self.other_expence_instances = []
        self.parent = None
        self.gst_transaction = None
        self.company_obj = None
        self.item_details = None
        self.version = []
        self.other_expence_charges = None
        self.old_item_details_ids = []
        self.old_other_expence_ids = []
        self.parent_item_details_ids = []
        self.parent_other_expence_ids = []
        

    def get_purchase_field(self):
        self.company_obj = company_info()
        if self.company_obj is None:
            self.errors.append("Company Not Found.")
            return False 
        if 'parent_order' in self.data and self.data['parent_order'] is not None:
            parent = purchaseOrder.objects.get(id=self.data['parent_order'])

            if parent:
                if self.data.get("id") is None and self.status == 'Submit':
                    self.parent_item_details_ids = parent.item_details.filter(received__gt=0).all()
                    self.parent_other_expence_ids = []
                    for other_expence in parent.other_expenses.all():
                        if OtherExpensespurchaseOrder.objects.filter(parent=other_expence).exists():
                            self.parent_other_expence_ids.append(other_expence)
                gin_instance = list(parent.gin.values_list("id", flat=True))
                if gin_instance: 
                    if parent.supplier_id.id != self.data.get("supplier_id"):
                        self.errors.append("Did'n allow to change supplier.")
                        return False
                self.parent= parent
                self.data['gin'] = gin_instance

            else:
                self.errors.append("Parent Purchase Order Not Found.")
                return False
        
        if 'id' in self.data and self.data.get("id"):
            self.purchase_obj = purchaseOrder.objects.filter(id=self.data.get("id")).first()
            
            if not self.purchase_obj:
                self.errors.append("Purchase not found.")
                return False
            else:
                self.old_item_details_ids = list(self.purchase_obj.item_details.values_list("id",flat=True))
                self.old_other_expence_ids = list(self.purchase_obj.other_expenses.values_list("id", flat=True))
                self.gst_transaction = self.purchase_obj.gst_nature_transaction
                if not self.gst_transaction:
                    self.errors.append("GST Nature Transaction is missing.")
                    return False
                if self.parent is None and self.status in ['Submit', "Draft"]:
                    self.data['gst_nature_type']= self.gst_transaction.gst_nature_type
        else:
            self.gst_transaction = GSTNatureTransaction.objects.filter(id=self.data.get("gst_nature_transaction")).first()
            if not self.gst_transaction:
                self.errors.append("GST Nature Transaction is missing.")
                return False 
            if self.parent is None and self.status in ['Submit', "Draft"]:
                self.data['gst_nature_type']= self.gst_transaction.gst_nature_type
            else:
                self.data['gst_nature_type']= self.parent.gst_nature_type
        return True

    def validate_required_fields(self):
        REQUIRED_FIELDS = [
            "po_date", "gst_nature_transaction", "gst_nature_type", "due_date","currency",
            "receiving_store_id", "exchange_rate",
            "supplier_id", "credit_period",
            "address", "contact", "gstin_type",   "place_of_supply",
            "item_total_befor_tax", "terms_conditions", "terms_conditions_text", "net_amount"
        ]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
        if len(self.errors) > 0:
            return False
        
        receving_store = self.data.get("receiving_store_id")
        # scrap_reject_store = self.data.get("scrap_reject_store_id")
        stores = Store.objects.filter(id__in=[receving_store])
        for store in stores:
            if store.id == receving_store:
                if not store.matained:
                    self.errors.append("Receiving store must be keep Stock true.")
                if store.conference:
                    self.errors.append("Receiving store must be conference false.")
            # if store.id == scrap_reject_store:
            #     if store.matained or store.conference:
            #         self.errors.append("Reject store must be keep Stock and conference false.")
            if len(self.errors) > 0:
                return False

        return False if self.errors else True

    def update_status_instance(self): 
        status_obj = CommanStatus.objects.filter(name=self.status, table="Purchase").first()
        
        if not status_obj:
            self.errors.append(f"Ask developer to add status '{self.status}' in CommanStatus.")
            return False
        self.data["status"] = status_obj.id
        return True

    def validate_numbering(self):
        conditions = {'resource': 'Purchase Order', 'default': True}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        return True

    def find_is_whole_number(self, qty, cf):
        return (qty * cf) % 1 == 0

    def validate_item_details(self):
        instance_list = []
        item_details = self.data.get('item_details', [])
        item_labels = []
        conversion_value_error = []
        if not item_details:
            self.errors.append("At least one Item Detail is required.")
            return False

        # itemmaster_ids = [data.get("item_master_id") for data in item_details]
        # duplicates = set([x for x in itemmaster_ids if itemmaster_ids.count(x) > 1])
        # if duplicates:
        #     self.errors.append("Duplicate items found in Item Details.")
        #     return False

        for item in item_details:
            part_code = ItemMaster.objects.filter(id=item.get("item_master_id")).first()
            if not part_code:
                self.errors.append(f"{part_code} not found in Item Master.")
                return False

            if not part_code.keep_stock:
                if part_code.serial or part_code.batch_number :
                    self.errors.append(
                        f"Item {part_code}: Serial or batch tracking cannot be enabled when stock tracking is disabled. "
                        f"Please update the item master configuration."
                        )
                    return False
            item_labels.append(str(part_code))

            if part_code.item_uom != part_code.purchase_uom:
                for field_ in ['po_qty',"po_uom", "po_rate", "conversion_factor","po_amount"]:
                    if item.get(field_) is None:
                        self.errors.append(f'{part_code} → {field} is required.')
                        
                if item.get("po_amount") != item.get("amount"):
                    self.errors.append("Purchase amount and base amount must be equal.")
            
            for field in ["item_master_id", "description", "category", "qty", "uom", "hsn_id", "rate", "amount"]:
                if item.get(field) is None:
                    self.errors.append(f'{part_code} → {field} is required.')

            if len(self.errors) > 0:
                return False

            if item.get('id'):
                instance = purchaseOrderItemDetails.objects.filter(id=item.get("id")).first()
                instance_list.append(instance)
            else:
                instance_list.append(None)
            if self.status == "Submit":
                if part_code.serial:
                        # conversion_result = self.find_is_whole_number(item.po_qty, item.conversion_factor) 
                        if (item.qty or 1) % 1 != 0:
                            conversion_value_error.append(part_code.item_part_code)

            if self.parent != None and self.data.get("id") is None and self.status == 'Submit':
                if item.get("parent"):
                    parent_instance = purchaseOrderItemDetails.objects.filter(id=item.get("parent")).first()
                    if not parent_instance:
                        self.errors.append(f'{part_code} → parent not Found.')
                        continue
                    else:
                        if item.get("po_qty") < (parent_instance.received or 0):
                            self.errors.append(f'{part_code} → this qty is lese than received po qty.')
                            continue
                        if parent_instance.uom.id != item.uom:
                            self.errors.append(f'{part_code} → did not allow change uom.')
                            continue
                        if parent_instance.conversion_factor != item.conversion_factor:
                            self.errors.append(f'{part_code} → did not allow change Conversion Factor.')
                            continue

                        item['received'] = (parent_instance.received or 0)
                        item['accepted_qty'] = (parent_instance.accepted_qty or 0)
                elif item.get("id") is not None and not item.get("parent"):
                    self.errors.append(f'{part_code} → Parent is required.')
         
        if len(conversion_value_error) >0: 
            self.errors.append(f"The following serial items need the quantity to be in whole numbers only: {', '.join(conversion_value_error)}")
            return False
        
        if len(self.errors):
            return False
        
        if self.parent != None and self.data.get("id") is None and self.status == 'Submit':
            for parent_item in self.parent_item_details_ids:
                if not any(item.get('parent') == parent_item.id for item in item_details):
                    self.errors.append(f"'{parent_item.item_master_id.item_part_code}' is already linked with GIN; deletion is not allowed.")
                    return False
        
        
        item_result = validate_common_data_and_send_with_instance(
            item_details, instance_list,
            purchaseOrderItemDetailsSerializer,
            item_labels,
            self.info.context
        )

        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
       
        self.item_details_instances.extend(item_result.get("instance"))
        return True

    def validate_expenses_purchase_order(self):
        instance_list = []
        other_expenses = self.data.get('other_expenses', [])
        other_labels = []

        if other_expenses and len(other_expenses) > 0:
            expense_ids = [data.get("other_expenses_id") for data in other_expenses]
            duplicates = set([x for x in expense_ids if expense_ids.count(x) > 1])
            if duplicates:
                self.errors.append("Duplicate items found in Other Expenses.")
                return False

            for exp in other_expenses:
                charge = OtherExpenses.objects.filter(id=exp.get("other_expenses_id")).first()
                if not charge:
                    self.errors.append("Other Expense charge not found.")
                    continue
                other_labels.append(charge.name)

                REQUIRED_FIELDS = ["other_expenses_id", "amount"]
                for field in REQUIRED_FIELDS:
                    if exp.get(field) is None:
                        self.errors.append(f'{charge.name} → {field} is required.')
                if len(self.errors) > 0:
                    continue
                if exp.get("id"):
                    instance = OtherExpensespurchaseOrder.objects.filter(id=exp.get("id")).first()
                    if not instance:
                        self.errors.append("Other Expense instance not found.")
                        continue
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                    if self.parent != None and self.data.get("id") is None and self.status == 'Submit':
                        if exp.get("parent"):
                            parent_instance = OtherExpensespurchaseOrder.objects.filter(id=exp.get("parent")).first()
                            if not parent_instance:
                                self.errors.append(f"{charge.name} parent Other Expense instance not found.")
                                continue
                        elif str(exp.get("id")).strip() != "" and not exp.get("parent"):
                            self.errors.append(f'{charge.name} → Parent is required.')

            if len(self.errors) > 0:
                return False
            
            if self.parent != None and self.data.get("id") is None and self.status == 'Submit':
                for parent_expence in self.parent_other_expence_ids:
                    
                    if not any(parent_expence.id == other_exp.get("parent") for other_exp in other_expenses):
                        self.errors.append(f"'{parent_expence.other_expenses_id.name}' is already linked with purchase invoice; deletion is not allowed.")
            
            if len(self.errors) > 0:
                return False
            
            expense_result = validate_common_data_and_send_with_instance(
                other_expenses, instance_list,
                OtherExpensespurchaseOrderSerializer,
                other_labels,
                self.info.context
            )
            if expense_result.get("error"):
                self.errors.extend(expense_result["error"])
                return False

            self.other_expence_instances.extend(expense_result.get("instance"))
        return True

    def validate_tax(self):
        item_details = self.data.get('item_details', []) 
        if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
            for item in item_details:
                if self.gst_transaction.place_of_supply == "Intrastate": 
                    if (
                        item.get("sgst", 0) != self.gst_transaction.sgst_rate or
                        item.get("cgst",0) != self.gst_transaction.cgst_rate or
                        item.get("cess", 0) != self.gst_transaction.cess_rate
                    ):
                        return False
                elif self.gst_transaction.place_of_supply == "Interstate":
                    
                    if (
                        item.get("igst") != self.gst_transaction.igst_rate or
                        item.get("cess") != self.gst_transaction.cess_rate
                    ):
                        return False
                return True
        elif self.gst_transaction.gst_nature_type == "As per HSN":
            for item in item_details:
                hsn = Hsn.objects.filter(id=item.hsn_id).first()
                
                if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != hsn.gst_rates.rate or (item.cess or 0) !=(hsn.cess_rate or 0):
                    return False
            return True
        else:
            # Fallback check — if all 4 rates are present, reject
            for item in item_details:
                if item.get("sgst") or item.get("cgst") or item.get("igst") or item.get("cess"):
                    return False
            return True

    def update_tax_item_details(self):
        updated_item_details = []
        updated_other_expence = []
        try:
            item_details = self.data.get("item_details", [])
            other_expence_charge = self.data.get("other_expenses", [])
            gst = self.gst_transaction
            is_specify_taxable = gst.gst_nature_type == "Specify" and gst.specify_type == "taxable"

            if is_specify_taxable:
                for item in item_details:
                    item_data = {
                        "sgst" : "0",
                        "cgst" : "0",
                        "cess" : "0",
                        "tax" : "0",
                        "igst" : "0"
                    } 
                    item_data.update({
                        'id':str(item.get("id",None)),
                    })
                    if gst.place_of_supply == "Intrastate":
                        item_data['sgst'] = str(gst.sgst_rate)
                        item_data['cgst'] = str(gst.cgst_rate)
                        item_data['cess'] = str(gst.cess_rate)
                        item_data['tax'] = str(gst.sgst_rate+gst.cgst_rate+gst.cess_rate)
                    else:
                        item_data['igst'] = str(gst.igst_rate)
                        item_data['cess'] = str(gst.cess_rate)
                        item_data['tax'] =  str(gst.igst_rate+gst.cess_rate)
                    updated_item_details.append(item_data)
            
                for expence in other_expence_charge:
                    expence_data ={
                        "id":str(expence.id),
                        "sgst" : "0",
                        "cgst" : "0",
                        "cess" : "0",
                        "tax" : "0",
                        "igst" : "0"
                    } 
                    
                    if gst.place_of_supply == "Intrastate":
                        expence_data['sgst'] = str(gst.sgst_rate)
                        expence_data['cgst'] = str(gst.cgst_rate)
                        expence_data['cess'] = str(gst.cess_rate)
                        expence_data['tax'] =  str(gst.sgst_rate+gst.cgst_rate+gst.cess_rate)
                    else:
                        expence_data['igst'] = str(gst.igst_rate)
                        expence_data['cess'] = str(gst.cess_rate)
                        expence_data['tax'] =  str(gst.igst_rate+gst.cess_rate)
                    updated_other_expence.append(expence_data)
                
            elif gst.gst_nature_type == "As per HSN":
                for item in item_details: 
                    hsn_id = item.get("hsn_id")
                    hsn = Hsn.objects.filter(id=hsn_id).first()
                    if not hsn or not hsn.gst_rates:
                        continue
                    item_data ={
                        "id" :  str(item.get("id",None))
                        }
                    
                    if str(self.data.get("state", "")).lower() == str(self.company_obj.address.state).lower():
                        rate_half = hsn.gst_rates.rate / 2
                        item_data['sgst'] =str(rate_half or 0)
                        item_data['cgst'] =str(rate_half or 0)
                        item_data['cess'] =str(hsn.cess_rate or 0)
                        item_data['tax'] = str(hsn.gst_rates.rate or 0)
                    else: 
                        item_data['igst'] =str( hsn.gst_rates.rate or 0)
                        item_data['cess'] =str( hsn.cess_rate or 0)
                        item_data['tax'] = str(hsn.gst_rates.rate or 0)
                    updated_item_details.append(item_data)
                
                for expence in other_expence_charge: 
                    expence_obj = OtherExpenses.objects.filter(id=expence.get("other_expenses_id")).first()
                    expence_data = {
                        "id": str(expence.get("id", None)),
                        } 
                    if str(self.data.get("state", "")).lower() == str(self.company_obj.address.state).lower():
                        
                        half_rate = expence_obj.HSN.gst_rates.rate / 2
                        expence_data['sgst'] = str(half_rate or 0)
                        expence_data['cgst'] = str(half_rate or 0)
                        expence_data['cess'] = str(expence_obj.HSN.cess_rate or 0)
                        expence_data['tax'] =  str(expence_obj.HSN.gst_rates.rate or 0)
                    else:
                        expence_data['igst'] = str(expence_obj.HSN.gst_rates.rate or 0)
                        expence_data['cess'] = str(expence_obj.HSN.cess_rate or 0)
                        expence_data['tax'] = str(expence_obj.HSN.gst_rates.rate or 0)
                    updated_other_expence.append(expence_data)
            
            else:
                for item in item_details:
                    item_data = ({
                        "id":str(item.id),
                        'sgst': "0",
                        'cgst': "0",
                        'igst': "0",
                        'cess': "0",
                        "tax" : "0",
                    })
                    updated_item_details.append(item_data)
                for expence in other_expence_charge:
                    expence_data = ({ 
                        "id":str(expence.id),
                        'sgst': "0",
                        'cgst': "0",
                        'igst': "0",
                        'cess': "0",
                        "tax" : "0",
                    })
                    updated_other_expence.append(expence_data) 
            self.item_details = updated_item_details
            self.other_expence_charges = updated_other_expence
        except Exception as e:
            self.errors.append(f"An exception occurred-- {str(e)}")

    def save_item_details(self):
        item_details = self.data.get('item_details', [])
        item_detail_ids = []
        try:
            for item , serializer in zip(item_details, self.item_details_instances):
                if serializer:
                    serializer.save()
                    
                    if self.parent and self.data.get("id") is None:
                        goods_inward_noods = GoodsInwardNoteItemDetails.objects.filter(purchase_order_parent=item.get('parent'))
                        if goods_inward_noods.exists():
                            for gin_item_instance in goods_inward_noods:
                                gin_item_instance.purchase_order_parent = serializer.instance
                                gin_item_instance.save()
                        rework_delivery_challan_items = ReworkDeliveryChallanItemDetails.objects.filter(purchase_invoice=item.get('parent'))
                        if rework_delivery_challan_items.exists():
                            for rework_delivery_challan_item in rework_delivery_challan_items:
                                rework_delivery_challan_item.purchase_item = serializer.instance
                                rework_delivery_challan_item.save()

                    item_detail_ids.append(serializer.instance.id)
            self.data['item_details'] = item_detail_ids
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False

    def save_expences(self):
        other_expence_ids = []
        other_expenses = self.data.get('other_expenses', [])
        try:
            for exp, serializer in zip(other_expenses, self.other_expence_instances ):
                if serializer:
                    serializer.save()
                    other_expence_ids.append(serializer.instance.id)
                    if self.parent and self.data.get("id") is None:
                        if exp.get('parent'):
                            expence_instances= OtherExpensespurchaseOrder.objects.filter(parent= exp.get('parent'))
                            if expence_instances.exists():
                                for expence_instance in expence_instances:
                                    expence_instance.parent = serializer.instance
                                    expence_instance.save()
            self.data['other_expenses'] = other_expence_ids
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving expenses: {e}")
            return False
 
    def save_purchase(self):
        try:
            serializer = None
            if self.purchase_obj:
                serializer = purchaseOrderSerializer(self.purchase_obj, data=self.data, partial=True, context={'request': self.info.context})
            else:
                serializer = purchaseOrderSerializer(data=self.data, partial=True, context={'request': self.info.context} )
            if serializer and serializer.is_valid():
                serializer.save()
                self.purchase_obj = serializer.instance
                self.version = get_all_related_version(self.purchase_obj, purchaseOrder)
                deleteCommanLinkedTable(self.old_item_details_ids, list(self.purchase_obj.item_details.values_list('id', flat=True)), purchaseOrderItemDetails)
                deleteCommanLinkedTable(self.old_other_expence_ids, list(self.purchase_obj.other_expenses.values_list('id', flat=True)), OtherExpensespurchaseOrder)
                if self.parent != None and self.data.get("id") is None and self.status == 'Submit':
                    if self.parent.reworkdeliverychallan_set.exists():
                        for rework_instance in self.parent.reworkdeliverychallan_set.all():
                            rework_instance.purchase_order_no = serializer.instance
                            rework_instance.save()
                    if self.parent.goodsinwardnote_set.exists():
                        for gin_instance in self.parent.goodsinwardnote_set.all():
                            gin_instance.purchase_order_id = serializer.instance
                            gin_instance.save()

                        pass
                return True
            else:
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                            for field, error in serializer.errors.items()])
                return False
        except Exception as e:
            self.errors.append(f"An exception error occurred while saving  purchase {str(e)}")
            return False
    
    def check_amount_with_variations_value(self):
        item_details = self.data.get("item_details", [])
        validity_list = []
        curency_obj = None

        currency_rate = (self.purchase_obj.exchange_rate or 0)

        for item in item_details:
            item_master = ItemMaster.objects.filter(id=item.get("item_master_id")).first()
            if item_master.item_types.name in ['Service']:
                continue

            if not item_master.enable_variation:
                continue 
            uom = item_master.item_uom
            purchase_uom = item_master.purchase_uom
            item_po_uom = UOM.objects.filter(id=item.get("po_uom")).first()
       

            if not item_master:
                self.errors.append(f"Item master not found for ID {item.get('item_master_id')}.")
                validity_list.append(False)
                continue
            
            variation = (item_master.variation or "").strip()
            itemmaster_rate = item_master.item_cost
            
            if not variation:
                self.errors.append(f"{item_master.item_part_code} missing variation.")
                validity_list.append(False)
                continue

            if not itemmaster_rate:
                self.errors.append(f"{item_master.item_part_code} missing item cost.")
                validity_list.append(False)
                continue
            
            item_cost = itemmaster_rate
            variation_rate = variation.replace("₹", "").replace("%", "")

            if currency_rate > 1 :
                item_cost = itemmaster_rate/currency_rate
            
            if item_po_uom == purchase_uom:
                # PO UOM = Purchase UOM
                pass

            elif item_po_uom == uom:
                # PO UOM = Main UOM
                alternate_uom = item_master.alternate_uom.filter(addtional_unit=purchase_uom).first()
                
                if not alternate_uom:
                    self.errors.append(f"{item_master.item_part_code}purchase uom not Found in alternate uom")
                    validity_list.append(False)
                    continue
                item_cost = item_cost*(alternate_uom.conversion_factor or 1)
            
            else:
                # PO UOM = Alternate UOM
                base_rate = item_cost
                item_cf = 1
                if purchase_uom != uom :
                    alternate_uom = item_master.alternate_uom.filter(addtional_unit=purchase_uom).first()
                    if not alternate_uom:
                        self.errors.append(f"{item_master.item_part_code}purchase uom not Found in alternate uom")
                        validity_list.append(False)
                        continue
                    base_rate = item_cost*(alternate_uom.conversion_factor or 1)

                if item_po_uom != purchase_uom  or item_po_uom != uom:
                    altermate_uom_1 = item_master.alternate_uom.filter(addtional_unit=item_po_uom).first()
                    if not altermate_uom_1:
                        self.errors.append(f"{item_master.item_part_code}  po uom not Found in alternate uom")
                        validity_list.append(False)
                    item_cf = (altermate_uom_1.conversion_factor or 1)
                
                item_cost = base_rate/item_cf
                

            
            
            if "%" in variation:
                variations_value = Decimal(variation_rate)
              
                variations_amount = (Decimal(item_cost) / 100 * variations_value)
                
            elif "₹" in variation:
                variations_value = Decimal(variation_rate)
                if not currency_rate:
                    self.errors.append("Currency rate is missing or invalid.")
                    validity_list.append(False)
                    continue
                
                if currency_rate > 1 :
                    variations_amount = (variations_value/currency_rate)
                else:
                    variations_amount = variations_value
            
            else:
                self.errors.append(f"{item_master.item_part_code} has invalid variation format.")
                validity_list.append(False)
                continue
 
            
             
            min_amount = Decimal(item_cost) - variations_amount
            max_amount = Decimal(item_cost) + variations_amount
            rate = item.get("po_rate", 0)
           
            
            if not (min_amount <= rate <= max_amount):
                self.errors.append(
                    f"{item_master.item_part_code} per item amount {rate:.2f} is out of allowed range "
                    f"({min_amount:.2f} - {max_amount:.2f})."
                )
                validity_list.append(False)
                continue
        # validity_list.append(False)
        return all(validity_list)
 
    def process(self):
        with transaction.atomic():
            if not self.get_purchase_field():
                return self.response()
            if not self.validate_required_fields():
                return self.response()
            if not self.validate_numbering():
                return self.response()
            if not self.validate_item_details():
                return self.response()
            if not self.validate_expenses_purchase_order():
                return self.response()
            if self.status == 'Submit':
                if self.parent == None and self.data.get("id"):
                    if not self.validate_tax():
                        self.update_tax_item_details()
                        return self.response()
                    if not self.check_amount_with_variations_value(): 
                        return self.response()
            if not self.update_status_instance():
                return self.response()
            if not self.save_item_details():
                return self.response()
            if not self.save_expences():
                return self.response()
            if not self.save_purchase():
                return self.response()

            self.success = True
        return self.response()

    def response(self):
        return {
            "purchase": self.purchase_obj,
            "success": self.success,
            "errors": [",\n ".join(self.errors)] if self.errors else None,
            "item_details" : self.item_details,
            "other_expences" : self.other_expence_charges,
            "version":  versionListType(versionList=self.version)
        }
