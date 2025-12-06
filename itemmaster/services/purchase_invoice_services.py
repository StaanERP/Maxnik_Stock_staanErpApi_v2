from itemmaster.models import *
from itemmaster.serializer import *
from itemmaster.Utils.CommanUtils import *
from itemmaster.schema import *


class PurchaseInvoiceService:
    def __init__(self, data, status, info):
        self.data = data
        self.status_text = status
        self.status = None
        self.success = False
        self.errors = []
        self.info = info
        self.purchase_invoice = None
        self.grn_list = []
        self.item_details_instances = []
        self.other_expense_instances = []
        self.item_details_serializer = []
        self.other_expense_serializer = []
        self.currency = None
    
    def get_purchase_invoice(self) ->bool:
        id = self.data.get("id")

        if id:
            self.purchase_invoice = PurchaseInvoice.objects.filter(id=id).first()
            if not self.purchase_invoice:
                self.errors.append("Purchase Invoice not found.")
                return False
            
            self.item_details_instances = list(self.purchase_invoice.item_detail.values_list("id",flat=True))
            self.other_expense_instances = list(self.purchase_invoice.other_expence_charge.values_list("id",flat=True))
            if self.status_text == "Draft" and self.purchase_invoice.status.name in ['Submit', "Canceled"]:
                self.errors.append(f"Already {self.purchase_invoice.status.name} purchase invoice did'n make Draft again.")
            elif self.status_text == "Submit" and self.purchase_invoice.status.name in ["Canceled","Submit" ]:
                self.errors.append(f"Already {self.purchase_invoice.status.name} purchase invoice did'n make Submit again.")
            
            if len(self.errors):
                return False

        return True

    def update_status_instance(self) ->bool:
        status = CommanStatus.objects.filter(name=self.status_text, table="Purchase Invoice").first()

        if not status:
            self.errors.append(f"Ask developer to add status '{self.status_text}' in CommanStatus.")
            return False
        
        self.data["status"] = status.id
        self.status= status
        return True
    
    def validate_required_fields(self) ->bool:
        REQUIRED_FIELDS = ["status", "purchase_invoice_date",  "terms_conditions","terms_conditions_text",
                        "due_date","credit", "credit_date",   "place_of_supply","item_total_befor_tax",
                        "other_charges_befor_tax","net_amount"]
        
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None or str(self.data.get(field)).strip() == "":
                self.errors.append(f'{field} is required.')
        
        if len(self.errors) > 0:
            return False
        
        return True
    
    def validate_numbering(self) ->bool:

        conditions = {'resource': 'Purchase Invoice', 'default': True}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        
        return True
    
    def validate_item_details(self) ->bool:
        item_details = self.data.get("item_detail",[])
        instance_list = []
        item_labels = [] 
        if len(item_details) <=0 :
            self.errors.append("item detail is required.")
            return False
        
        try:
            for itemdetails in item_details:
                if itemdetails.get('grn_item'):
                    grns = GoodsReceiptNoteItemDetails.objects.filter(id__in= itemdetails.get('grn_item'))
                    if not grns.exists():

                        self.errors.append(f"Item Detail {itemdetails.get('id')} parent Goods Receipt Note Not Found.")
                        continue
                    
                    grn_item = grns.first()
                    itemmaster = grn_item.gin.item_master
                    itemmaster_lable = grn_item.gin.item_master.item_part_code
                    grn_item_total_qty = sum((grn_instance.qty or 0) - (grn_instance.purchase_return_qty or 0)   for grn_instance in grns)
                    all_item_have_same_id = any(item for item in grns if item.gin.item_master.id != itemmaster.id)
                    item_labels.append(itemmaster_lable)
                    cfs = [ grn_instance.conversion_factor for grn_instance in grns]
                    all_have_cf = all(cfs)
                    all_same_cf = len(set(cfs)) == 1 if all_have_cf else False
                    if not all_have_cf:
                        self.errors.append(f"{itemmaster_lable} -> Some Conversion Factor was missing")
                        continue

                    if not all_same_cf:
                        self.errors.append(f"{itemmaster_lable}-> different Conversion Factor found")
                        continue

                    for grn_item_ in grns:
                        item_grn = grn_item_.goodsreceiptnote_set.first()
                        item_grn_satus = item_grn.status.name
                        
                        if item_grn_satus not in ["Received"]:
                            self.errors.append((f"{itemmaster_lable}->{item_grn.grn_no.linked_model_id} {item_grn.status.name} Are not allowed"))
                            
                            continue
                        purchase_return_items = grn_item_.purchasereturnchallanitemdetails_set.all()
                        if purchase_return_items:
                            
                            purchase_returns = [purchase_retun_item.purchasereturnchallan_set.first() for purchase_retun_item in purchase_return_items]
                            for purchase_return in purchase_returns:  
                                if purchase_return and  purchase_return.status.name == "Draft":
                                    self.errors.append(f" {itemmaster} -> purchase return {purchase_return.purchase_return_no.linked_model_id} in draft set submit or Cancel.")
                        
                        if item_grn not in self.grn_list :
                            self.grn_list.append(item_grn)
                        
                        if itemdetails.get("id") is None:
                            if grn_item_.is_draft_purchase_invoice:
                                self.errors.append(f"{itemmaster} in {grn_item_.goodsreceiptnote_set.first().dc_no.linked_model_id} is already Draft")
                        if grn_item_.is_submited_purchase_invoice:
                                self.errors.append(f"{itemmaster} in {grn_item_.goodsreceiptnote_set.first().dc_no.linked_model_id} is already Submited")

                    if all_item_have_same_id:
                        self.errors.append(f"The Item Master ID for '{itemmaster_lable}' is different in Item details. Please report this to the administrator.")
                        continue  
                    if grn_item_total_qty !=  itemdetails.get("po_qty"):
                        self.errors.append(f"Quantity mismatch for {itemmaster_lable}: Goods Receipt Note item quantity does not match.")
                        continue
                
                elif itemdetails.get("po_item"):
                    po_item = purchaseOrderItemDetails.objects.filter(id=itemdetails.get("po_item")).first()
                    if not po_item:
                        self.errors.append(f'{itemdetails.get("po_item")} id is not found in po item details.')
                    item_master_id =  po_item.item_master_id
                    item_labels.append(f"{item_master_id.item_part_code}-{item_master_id.item_name}")
                    
                else:
                    self.errors.append(f'Po item or GRN item id both also not given.')

                for field in ["po_rate", "po_qty", "po_amount", "conversion_factor"]:
                    if itemdetails.get(field) is None:
                        self.errors.append(f'{itemmaster_lable} - {field} is required')
                
                if len(self.errors) > 0:
                    continue
                
                if itemdetails.get("id"):
                    item_detail_instance = PurchaseInvoiceItemDetails.objects.filter(id=itemdetails.get("id")).first()
                    instance_list.append(item_detail_instance)
                else:
                    instance_list.append(None)

            if len(self.errors) > 0:
                return False
            
            item_result = validate_common_data_and_send_with_instance(
                item_details, instance_list, PurchaseInvoiceItemDetailsSerializer,
                item_labels, self.info.context) 
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.item_details_serializer = item_result.get("instance")
            return True
        
        except Exception as e:
            self.errors.append(f"An exception occurred while validate item details: {str(e)}")
            return False
    
    def validate_expense(self) ->bool:
        REQUIRED_FIELDS = ["other_expenses_id", "amount"]
        instance_list = []
        item_labels = [] 
        other_expences = self.data.get('other_expence_charge', [])
        if len(other_expences) == 0:
            return True
        
        try:
            for expences in other_expences: 
                
                charge = OtherExpenses.objects.filter(id=expences.get("other_expenses_id")).first()
                
                if not charge:
                    self.errors.append("Other Expense charge not found.")
                    continue

                item_labels.append(charge.name)
                

                for field in REQUIRED_FIELDS:
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
                if expences.get("parent"):
                    parent  = OtherExpensespurchaseOrder.objects.filter(id=expences.get("parent"))
                    if not parent:
                        self.errors.append(f"{instance.name if instance else expences.get('id')} parent other Expenses Not Found.")
                        continue
                    
                    current_id = expences.get("parent") if expences.get("parent")  else None
                    
                    siblings = parent.exclude(id=current_id)
                    sibling = siblings.first()
                    
                    if siblings.exists():

                        self.errors.append(f"{sibling.other_expenses_id.name} already exists in Purchase Invoice and cannot be saved again.")
                        continue

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

            self.data['item_detail'] = item_detail_ids
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

            self.data['other_expence_charge'] = other_expence_ids
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving expenses: {e}")
            return False
    
    def save_purchase_invoice(self) ->bool:
        try:
            serializer = None
            if self.purchase_invoice:
                serializer = PurchaseInvoiceSerializer(self.purchase_invoice,
                                                    data=self.data, partial=True,
                                                    context={'request': self.info.context})
            else:
                serializer = PurchaseInvoiceSerializer(data=self.data, partial=True,
                                                    context={'request': self.info.context})
                
            if serializer and serializer.is_valid():
                serializer.save()
                self.purchase_invoice = serializer.instance

                for purchase_invoice_item in self.purchase_invoice.item_detail.all():
                    for grn_item in purchase_invoice_item.grn_item.all():
                        grn_item.is_draft_in_purchase_invoice_qty = True
                        grn_item.save()

                for grn in self.grn_list:
                    grn.purchase_invoice.add(self.purchase_invoice)

                deleteCommanLinkedTable(self.item_details_instances, list(self.purchase_invoice.item_detail.values_list("id",flat=True)), purchaseOrderItemDetails)
                deleteCommanLinkedTable(self.other_expense_instances, list(self.purchase_invoice.other_expence_charge.values_list("id",flat=True)), OtherExpensespurchaseOrder)
                
                return True
            else:
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                            for field, error in serializer.errors.items()])
                return False

        except Exception as e:
            self.errors.append(f"An exception error occurred while saving purchase invoice {str(e)}")
            return False
    
    def check_purchase_invoice_submit(self) ->bool:
        if not self.purchase_invoice:
            self.errors.append("Purchase Invoice Not Found.")
        for item in self.purchase_invoice.item_detail.all():
            grn_item_details_intance = item.grn_item.all()
            if not grn_item_details_intance:
                continue
            itemmaster = grn_item_details_intance.first().gin.item_master.item_part_code


            for grn_item_ in grn_item_details_intance:
                if grn_item_.is_submited_purchase_invoice: 
                    if (grn_note := grn_item_.goodsreceiptnote_set.first()) and grn_note.grn_no:
                        self.errors.append(f"{itemmaster} in {grn_note.grn_no.linked_model_id} is already Submitted")
                    else:
                        self.errors.append(f"{itemmaster} is already Submitted")
        if len(self.errors) > 0:
            return False
        return True
    
    def check_amount_with_variations(self):
        currency= None
        currency_lable = None
        if self.purchase_invoice.goodsreceiptnote_set.exists():
            currency = self.purchase_invoice.goodsreceiptnote_set.first().goods_inward_note.purchase_order_id.currency
            currency_lable = currency.Currency.name
        if not currency:
            self.errors.append("Currency Not Found.")
            return False
        self.currency = currency
        for item in self.purchase_invoice.item_detail.all():
            grn_item = item.grn_item.first()
            if not grn_item:
                continue

            
            item_master = grn_item.gin.item_master
            
            if not item_master.enable_variation:
                continue

            variation = item_master.variation
            item_cost = item_master.item_cost
            rate =  (item.po_rate or 0)
            uom = item_master.item_uom
            purchase_uom = item_master.purchase_uom
            item_po_uom = grn_item.gin.purchase_order_parent.po_uom
            
            if not variation:
                self.errors.append(f"{item_master.item_part_code} missing variation.")
                continue

            if variation and item_cost:
                after_converty_rate = item_cost
                variation_rate = variation.replace("₹", "").replace("%", "")

                if currency_lable != "Rupee":
                    after_converty_rate = item_cost/currency.rate

                rate_of_item = after_converty_rate

                if item_po_uom == purchase_uom:
                    # PO UOM = Purchase UOM
                    pass
                elif item_po_uom == uom:
                    # PO UOM = Main UOM
                    alternate_uom = item_master.alternate_uom.filter(addtional_unit=purchase_uom).first()
                    if not alternate_uom:
                        self.errors.append(f"{item_master.item_part_code}purchase uom not Found in alternate uom")
                        continue
                    rate_of_item = after_converty_rate*(alternate_uom.conversion_factor or 1)
                else:
                    # PO UOM = Alternate UOM
                    base_rate = item_cost
                    item_cf = 1
                    if purchase_uom != uom :
                        alternate_uom = item_master.alternate_uom.filter(addtional_unit=purchase_uom).first()
                        if not alternate_uom:
                            self.errors.append(f"{item_master.item_part_code} purchase uom not Found in alternate uom")
                            continue
                        base_rate = after_converty_rate*(alternate_uom.conversion_factor or 1)

                    if item_po_uom != purchase_uom and  item_po_uom != purchase_uom:
                        altermate_uom_1 = item_master.alternate_uom.filter(addtional_unit=item_po_uom).first()
                        if not altermate_uom_1:
                            self.errors.append(f"{item_master.item_part_code}  po uom not Found in alternate uom")
                        item_cf = (altermate_uom_1.conversion_factor or 1)

                    rate_of_item = base_rate/item_cf

                if "%" in variation:
                    variations_value = Decimal(variation_rate)  
                    variations_amount = (Decimal(rate_of_item) / 100 * variations_value)

                elif "₹" in variation:
                    variations_value = Decimal(variation_rate)
                    if not currency.rate:
                        self.errors.append("Currency rate is missing or invalid.")
                        continue
                    if currency_lable != "Rupee":
                        variations_amount = (variations_value/currency.rate) 
                    else:
                        variations_amount = variations_value
                else:
                    self.errors.append(f"{item_master.item_part_code} has invalid variation format.")
                    continue
                
                min_amount = Decimal(rate_of_item) - variations_amount
                max_amount = Decimal(rate_of_item) + variations_amount
                
                if not (min_amount <= rate <= max_amount):
                    self.errors.append(
                        f"{item_master.item_part_code} per item amount {rate:.2f} is out of allowed range "
                        f"({min_amount:.2f} - {max_amount:.2f})."
                    )
                    continue
            else:
                self.errors.append(f"{item_master.item_part_code} missing variation or item cost.")
                continue

        if len(self.errors) > 0:
            return False
        return True

    def set_purchase_invoice_submit(self) ->bool:
        po_item_value = {}

        po_instance = (
                self.purchase_invoice
                    .goodsreceiptnote_set.first()            # GRN
                    .goodsinwardnote_set.first()              # GIN
                    .purchase_order_id
                if self.purchase_invoice.goodsreceiptnote_set.first()
                and self.purchase_invoice.goodsreceiptnote_set.first().goodsinwardnote_set.first()
                else None
            )
        if not po_instance:
            self.errors.append("Purchase order not found.")
            return False
        purchase_total_qty = po_instance.item_details.aggregate(total=Sum("po_qty"))["total"] or 0
        

        try:
            for item in self.purchase_invoice.item_detail.all():
                grn_item_details_intance = item.grn_item.all()
                 
                if not grn_item_details_intance:
                    po_item = item.po_item
                    po_item.invoiced_qty = (po_item.invoiced_qty or 0) + (item.po_qty or 0)
                    po_item.save()
                    po_item_value[po_item.id] = po_item.invoiced_qty
                    continue
                
                for grn_item_ in grn_item_details_intance:
                    qty = (grn_item_.qty or 0) - (grn_item_.purchase_return_qty or 0)
                    grn_item_.is_draft_purchase_invoice = False
                    grn_item_.is_submited_purchase_invoice = True
                    grn_item_.purchase_invoice_qty = (grn_item_.purchase_invoice_qty or 0) + (qty or 0)
                    grn_item_.save()
                
                po_item = item.grn_item.first().gin.purchase_order_parent
                if po_item:
                    po_item.invoiced_qty = (po_item.invoiced_qty or 0) + (item.po_qty or 0)
                    po_item.save()
                    po_item_value[po_item.id] = po_item.invoiced_qty

            current_invoiced_qty = sum(po_item_value.values())
            purchase_total_invoiced_qty = po_instance.item_details.exclude(id__in =po_item_value.keys()).aggregate(total=Sum("invoiced_qty"))["total"] or 0

            total_invoiced_qty = current_invoiced_qty+purchase_total_invoiced_qty
            
            po_instance.invoice_percentage = (total_invoiced_qty/purchase_total_qty)*100 if purchase_total_qty else 0
            po_instance.save()

            self.purchase_invoice.status = self.status
            self.purchase_invoice.save()
            
            return True
        except Exception as e:
            self.errors.append(f"An exception error occurred while change the submit status purchase invoice {str(e)}.")
            transaction.set_rollback(True)   # <= force rollback
            return False 

    def save_import_fields(self):
        """
        Save purchase invoice import header and line items.
        """
        try:
            purchase_invoice_import = self.data.get("purchase_invoice_import")[0]  if self.data.get("purchase_invoice_import") else None
            import_lines = self.data.get("purchase_invoice_import_line")

            if not purchase_invoice_import:
                self.errors.append("Missing purchase invoice import header data.")
                return False

            # Save header
            invoice_import_serializer = PurchaseInvoiceImportSerializer(
                data=purchase_invoice_import, partial=True
            )
            if not invoice_import_serializer.is_valid():
                for field, field_errors in invoice_import_serializer.errors.items():
                    for err in field_errors:
                        self.errors.append(f"{field}: {err}")
                return False

            invoice_import_instance = invoice_import_serializer.save()

            # Save line items
            if not import_lines:
                self.errors.append("Missing import line items.")
                return False

            for import_line in import_lines:
                import_line["import_header"] = invoice_import_instance.id
                line_serializer = PurchaseInvoiceImportLineSerializer(
                    data=import_line, partial=True
                )
                if not line_serializer.is_valid():
                    for field, field_errors in line_serializer.errors.items():
                        for err in field_errors:
                            self.errors.append(f"{field}: {err}")
                    return False
                line_serializer.save()

            return True

        except Exception as e:
            self.errors.append(f"Unexpected error in save_import_fields: {str(e)}")
            return False

    def validate_import_fields(self):
        try:
            """
            Validate import-specific fields only if purchase type = 'Import Purchase'.
            """
            grn = self.purchase_invoice.goodsreceiptnote_set.first()
            if not grn or not grn.goods_inward_note:
                self.errors.append("No GRN or Goods Inward Note linked.")
                return False

            purchase = grn.goods_inward_note.purchase_order_id
            gst_nature_type = getattr(purchase, "gst_nature_type", None)

            # Skip if not Import Purchase
            if gst_nature_type != "Import Purchase":
                return True

            purchase_invoice_import = self.data.get("purchase_invoice_import")[0]
            import_lines = self.data.get("purchase_invoice_import_line")

            if not purchase_invoice_import or not import_lines:
                self.errors.append("Invoice import data is missing.")
                return False

            # total_item_value = Decimal("0.00")

            for item in import_lines:
                item_detail_instance = self.purchase_invoice.item_detail.filter(
                    id=item.get("item")
                ).first()
                if not item_detail_instance:
                    self.errors.append(f"Item {item.get('item')} not found in purchase invoice.")
                    continue
                if item_detail_instance.po_item:
                    continue
                
                # Safe item label
                item_label = (item_detail_instance.grn_item.first().gin.item_master.item_part_code or "Item Not Found")

                # Required fields
                for field in ["item", "assessable_value", "igst","assessable_hsn"]:
                    if item.get(field) is None:
                        self.errors.append(f"{item_label} - {field} is required")
                
                assessable_value = Decimal(item.get("assessable_value") or 0)
                amount = Decimal(item_detail_instance.po_amount or 0)*(self.currency.rate or 1)
                if assessable_value < amount:
                    self.errors.append(f"{item_label} Assessable Value must be >= item amount.")
            
                    continue 
                # Add duty difference 
                # total_item_value += (assessable_value - amount)
                
            # Header checks
            if purchase_invoice_import.get("purchase_invoice") != self.purchase_invoice.id:
                self.errors.append("Purchase Invoice id mismatch in import data.")

            if not purchase_invoice_import.get("bill_of_entry_no"):
                self.errors.append("Bill of Entry No is required.")
            if not purchase_invoice_import.get("bill_of_entry_date"):
                self.errors.append("Bill of Entry Date is required.")
            if not purchase_invoice_import.get("port_code"):
                self.errors.append("Port Code is required.")
            # if not purchase_invoice_import.get("total_duty"):
            #     self.errors.append("Total Duty is required.")

            # Duty match check
            # try:
            #     if total_item_value != 0:
            #         total_duty = Decimal(purchase_invoice_import.get("total_duty") or 0)
            #         if total_duty != total_item_value:
            #             self.errors.append(
            #                 f"Total Duty {total_duty} does not match item duty value {total_item_value}."
            #             )
            # except Exception:
            #     self.errors.append("Invalid Total Duty format.")
            #     transaction.set_rollback(True)

            # If any errors → return False
            if self.errors: 
                transaction.set_rollback(True)
                return False
            
            # Try saving import fields after validation passes
            return self.save_import_fields()
        except Exception as e:
            self.errors.append(f"Unexpeted error in {str(e)}")
            transaction.set_rollback(True)

    def process(self) ->bool:
        with transaction.atomic():
            if self.status_text == "Draft":
                if not self.validate_required_fields():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                if not self.get_purchase_invoice():
                    return self.response()
                if not self.validate_numbering():
                    return self.response()
                if not self.validate_item_details():
                    return self.response()
                if not self.validate_expense():
                    return self.response()
                if not self.save_item_details():
                    return self.response()
                if not self.save_expences():
                    return self.response()
                if not self.save_purchase_invoice():
                    return self.response()
                self.success = True
            elif self.status_text == "Submit":
                if not self.update_status_instance():
                    return self.response()
                if not self.get_purchase_invoice():
                    return self.response()
                if not self.check_purchase_invoice_submit():
                    return self.response()
                if not self.check_amount_with_variations():
                    return self.response()
                if not self.validate_import_fields():
                    return self.response()
                if not self.set_purchase_invoice_submit():
                    return self.response()
                self.success = True
            else:
                self.errors.append(f"{self.status_text} Unexpected status.")
            return self.response()

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "purchase_invoice": self.purchase_invoice
        }
    

 

def purchase_invoice_general_update(data): 
    valid_serializers = []
    errors = []
    credit = data.get("credit", {})
    debits = data.get("debits", [])

    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "purchase_invoice", "account", "created_by"]

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


