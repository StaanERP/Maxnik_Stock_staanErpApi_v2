from itemmaster.models import *
from itemmaster.serializer import *
from itemmaster.Utils.CommanUtils import *
from itemmaster.schema import *
from decimal import Decimal, ROUND_HALF_UP

class PurchaseRetunService:
    def __init__(self, data, status, info):
        self.data = data
        self.status_text = status
        self.status = None
        self.success = False
        self.errors = []
        self.info = info
        self.company_obj = None
        self.purchase_return = None
        self.purchase_invoice = []
        self.goods_receipt_note = []
        self.item_detail_instances = []
        self.item_details_serializer = []
        self.store = None

    def process(self):
        with transaction.atomic():
            if self.status_text == "Draft":
                if not self.get_purchase_retun():
                    return self.response()
                if not self.validate_required_fields():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                if not self.validate_numbering():
                    return self.response()
                if not self.validate_item_details():
                    return self.response()
                if not self.save_itemdetails():
                    return self.response()
                if not self.save_purchase_return():
                    return self.response()
                self.success = True
                return self.response()
            elif self.status_text == "Submit":
                if not self.get_purchase_retun():
                    return self.response()
                if not self.validate_required_fields():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                if not self.stock_check():
                    return self.response()
                if not self.reduce_stock():
                    return self.response()
                self.purchase_return.status = self.status
                self.purchase_return.save()
                self.success=True
                return self.response()
            elif self.status_text == "Dispatch":
                self.company_obj = company_info()
                if self.company_obj is None:
                    self.errors.append("Company Data Not Found.")
                    return False
                if not self.get_purchase_retun():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                if not self.check_transportation_requirements():
                        return self.response()
                if not self.validate_e_way_document():
                    return self.response()
                
                transport = None
                if self.data.get("transport"):
                    transport = SupplierFormData.objects.filter(id=self.data.get("transport")).first()
                    if not transport:
                        self.errors.append("Transport not found.")
                        return self.response()
                
                self.purchase_return.transport = transport if transport else None
                self.purchase_return.vehicle_no = self.data.get("vehicle_no") if self.data.get("vehicle_no") else None
                self.purchase_return.driver_name = self.data.get("driver_name") if self.data.get("driver_name") else None
                self.purchase_return.docket_no = self.data.get("docket_no") if self.data.get("docket_no") else None
                self.purchase_return.docket_date = self.data.get("docket_date") if self.data.get("docket_date") else None
                self.purchase_return.other_model = self.data.get("other_model") if self.data.get("other_model") else None
                self.purchase_return.eway_bill_no = self.data.get("eway_bill_no") if self.data.get("eway_bill_no") else None
                self.purchase_return.eway_bill_date = self.data.get("eway_bill_date") if self.data.get("eway_bill_date") else None
                self.purchase_return.status = self.status
                self.purchase_return.save()
                self.success=True
                return self.response()

            else:
                self.errors.append(f"{self.status_text} Unexpected status.")
                return self.response()
        
    def get_purchase_retun(self):
        self.purchase_return = None
        if 'id' in self.data and self.data.get("id"):
            self.purchase_return = PurchaseReturnChallan.objects.filter(id=self.data.get("id")).first()

            if not self.purchase_return:
                self.errors.append("Purchase return not found.")
                return False
            self.item_detail_instances.extend(self.purchase_return.purchase_return_challan_item_Details.values_list('id', flat=True))
            
            if self.status_text == "Draft" and self.purchase_return.status.name in ['Submit', "Canceled", "Dispatch"]:
                self.errors.append(f"Already {self.purchase_return.status.name} purchase return did'n make Draft again.")
            if self.status_text == "Submit" and self.purchase_return.status.name in ["Canceled", "Dispatch"]:
                self.errors.append(f"Already {self.purchase_return.status.name} purchase return did'n make Submit again.")
            if self.status_text == "Dispatch" and self.purchase_return.status.name in ["Canceled", "Draft"]:
                self.errors.append(f"{self.purchase_return.status.name} purchase return did'n make Dispatch.")
           

            if len(self.errors) > 0:
                return False
            
        if self.status_text in ['Submit', "Canceled", "Dispatch"]:
            if not self.purchase_return:
                self.errors.append("Purchase return not found.")
                return False
            
        return True

    def update_status_instance(self) ->bool:
        status = CommanStatus.objects.filter(name=self.status_text, table="Purchase Return Challan").first()

        if not status:
            self.errors.append(f"Ask developer to add status '{self.status_text}' in CommanStatus.")
            return False
        
        self.data["status"] = status.id
        self.status= status
        return True

    def validate_required_fields(self):
        REQUIRED_FIELDS = [
            "status", "purchase_return_date", "befor_tax",
            "net_amount","terms_conditions", "terms_conditions_text"
        ]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
    
        if self.errors:
            return False
        return True

    def validate_numbering(self) ->bool:
        conditions = {'resource': 'Purchase Return Challan', 'default': True}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        
        return True
    
    def check_invoice_item_grn_item(self, item_details):
        # Case 1: all have ONLY purchase_invoice_item
        all_purchase = all(
            item.get("purchase_invoice_item") and not item.get("grn_item")
            for item in item_details
        )

        # Case 2: all have ONLY grn_item
        all_grn = all(
            item.get("grn_item") and not item.get("purchase_invoice_item")
            for item in item_details
        )

        return all_purchase or all_grn

    def calc_balances(self, grn_items, is_purchase_invoice):
        purchase_return_qty = sum((g.purchase_return_qty or 0) / (g.conversion_factor or 1) for g in grn_items)
        purchase_invoice_qty = sum((g.purchase_invoice_qty or 0) /(g.conversion_factor or 1) for g in grn_items)
        if is_purchase_invoice:
            total_balance = sum(((g.qty or 0) / (g.conversion_factor or 1)) - ((g.purchase_return_qty or 0)/(g.conversion_factor or 1))  for g in grn_items)
        else:
            total_balance = sum(((g.qty or 0) / (g.conversion_factor or 1)) - ((g.purchase_return_qty or 0) / (g.conversion_factor or 1)) - ((g.purchase_invoice_qty or 0) / (g.conversion_factor or 1)) for g in grn_items)
        
        return purchase_return_qty, purchase_invoice_qty, total_balance

    def validate_item_details(self):
        item_details = self.data.get("purchase_return_challan_item_Details",[])
        instance_list = []
        item_labels = []
        
        # --- Basic validations ---
        if len(item_details) <=0 :
            self.errors.append("item detail is required.")
            return False
        
        if not (self.check_invoice_item_grn_item(item_details)):
            self.errors.append("Some items contain both Purchase Invoice Item and GRN Item," \
            " but only one type is allowed. Either all items must have Purchase Invoice Item or" \
            " all must have GRN Item — mixing both is not permitted.")
            return False
        
        try:
            for item_detail in item_details:
                # --- Setup variables for each item -
                batch_serializers = []
                nobatch_noserial_serializers = []
                purchase_invoice_item = None
                grn_item_instance_list = []
                purchase_invoice_item_id = item_detail.get("purchase_invoice_item")
                grn_item_list = item_detail.get("grn_item", [])
                batchs = item_detail.get("batch",[])
                serials = item_detail.get("serial",[])
                nobatch_noserials = item_detail.get("nobatch_noserial",[])
                requested_qty = item_detail.get("po_return_qty", 0)
                base_requested_qty = item_detail.get("base_return_qty", 0)
                itemmaster = None
                itemmaster_lable = None
                
                # --- Case 1: Linked with Purchase Invoice Item ---
     
                if purchase_invoice_item_id:
                    item_detail['grn_item'] =[]
                    purchase_invoice_item = (
                        PurchaseInvoiceItemDetails.objects.filter(id=purchase_invoice_item_id).first()
                    )

                    if purchase_invoice_item is None:
                        self.errors.append(f"{purchase_invoice_item_id} Purchase Invoice Item not found.")
                        continue

                    grn_item = purchase_invoice_item.grn_item.first()
                    if not grn_item:
                        self.errors.append(f"{purchase_invoice_item_id} has no linked GRN item")
                        continue
                    
                    itemmaster = grn_item.gin.item_master
                    itemmaster_lable = f"{itemmaster.item_part_code} - {itemmaster.item_name}"

                    purchase_invoice_instance = purchase_invoice_item.purchaseinvoice_set.first()
                    if purchase_invoice_instance and purchase_invoice_instance.status.name not in ['Submit']:
                        self.errors.append(f"{itemmaster_lable}- {purchase_invoice_instance.purchase_invoice_no.linked_model_id} \
                                        status is {purchase_invoice_instance.status.name} not allowed.")
                        continue
                    
                    if purchase_invoice_instance not in self.purchase_invoice:
                        self.purchase_invoice.append(purchase_invoice_instance)
                    
                # --- Case 2: Linked with GRN Items ---
                if grn_item_list:
                    grn_item_instance_list = GoodsReceiptNoteItemDetails.objects.filter(id__in=grn_item_list)
                    if not grn_item_instance_list:
                        self.errors.append(f"{grn_item_list} GRN Item instance not found.")
                        continue

                    grn_item = grn_item_instance_list.first()
                    itemmaster = grn_item.gin.item_master
                    itemmaster_lable = f"{itemmaster.item_part_code} - {itemmaster.item_name}"

                    for grn_item_instance in grn_item_instance_list:
                        grn_instance = grn_item_instance.goodsreceiptnote_set.first()
                        if grn_instance.status.name not in ['Received']:
                            self.errors.append(f"{grn_instance.grn_no.linked_model_id} status is  \
                                                {grn_instance.status.name} not allowed.")
                        
                        if grn_instance not in self.goods_receipt_note:
                            self.goods_receipt_note.append(grn_instance)

                # --- Multi Purchase Invoice Check ---
                if len(self.errors) > 0:
                    continue
                if len(self.purchase_invoice) > 1:
                    self.errors.append("Multi purchase invoice not allowed.")
                    continue

                item_labels.append(itemmaster_lable)

                # --- Required fields check ---
                for field in ["po_return_qty","base_return_qty", "po_amount",]:
                    if item_detail.get(field) is None:
                        self.errors.append(f'{itemmaster_lable} - {field} is required')

                if  self.errors:
                    continue
                
                # --- Batch handling ---
                if itemmaster.batch_number:
                    if not batchs:
                        self.errors.append(f'{itemmaster_lable} - batch is required')
                        continue

                    batch_qty  = sum(batch.get("qty", 0)  for batch in batchs)

                    if purchase_invoice_item and requested_qty > purchase_invoice_item.po_qty:
                        self.errors.append(f"{itemmaster_lable}-> return  QTY (PO) is more than \
                                            purchase invoice qty (PO) is {purchase_invoice_item}.")
                        continue

                    # if batch_qty != requested_qty:
                    #     self.errors.append(f"{itemmaster_lable}->Batch total QTY \
                    #                         and item QTY mismatch")
                    #     continue
                    # Validate each batch
                    for batch in batchs:
                        batch_grn_id = batch.get("batch")
                        batch_id = batch.get("id")
                        get_grn_item = None
                        purchase_invoice_qty = 0
                        batch_qty = batch.get("qty", 0)
                        if not batch_qty:
                            continue 
                        if grn_item_instance_list:
                            get_grn_item = next((grn for grn in grn_item_instance_list if grn.id == int(batch_grn_id)), None)
                            base_qty = (get_grn_item.qty or 0)/(get_grn_item.conversion_factor or 1)
                            base_qty = base_qty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_return_qty = ((get_grn_item.purchase_return_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_invoice_qty = ((get_grn_item.purchase_invoice_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            balance_qty = (base_qty or 0 ) - purchase_return_qty -  purchase_invoice_qty
                         
                            if batch_qty > balance_qty:
                                self.errors.append(
                                    f"{batch.get('batch_str')}"
                                    f"Qty exceeds limit. "
                                    f"Purchase Return Base QTY = {purchase_return_qty or 0}, "
                                    f"Purchase Invoice Base QTY = {purchase_invoice_qty or 0}. "
                                    f"Allowed Base QTY = {balance_qty}, Requested QTY = {batch_qty}.")
                                continue
                        
                        else:
                            get_grn_item = next((grn for grn in purchase_invoice_item.grn_item.all() if grn.id == int(batch_grn_id)), None)
                            base_qty = ((get_grn_item.qty or 0 ) /(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_return_qty = ((get_grn_item.purchase_return_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            balance_qty = base_qty - purchase_return_qty
                            batch_qty = batch.get("qty", 0)
                       
                            if batch_qty > balance_qty:
                                self.errors.append(
                                    f"{batch.get('batch_str')}"
                                    f"Qty exceeds limit. "
                                    f"Purchase Return Base QTY = {get_grn_item.purchase_return_qty or 0}, "
                                    f"Allowed Base QTY = {balance_qty}, Requested Base QTY = {batch_qty}.")
                                continue

                        if not get_grn_item:
                            self.errors.append(f"{itemmaster_lable} -- {batch.get('batch_str')} batch not available in selected GRN")
                            continue
                        

                        retun_batch_instance = None
                        if batch_id:
                            retun_batch_instance = PurchaseRetunBatch.objects.filter(id=batch_id).first()

                        batch_serializer = PurchaseRetunBatchSerializer(retun_batch_instance, data=batch, partial=True)
                        
                        if not batch_serializer.is_valid():
                            for field, field_errors in batch_serializer.errors.items():
                                for err in field_errors:
                                    self.errors.append(f"{itemmaster_lable} - {field}: {err}")

                        if len(self.errors) > 0:
                            continue 
                        batch_serializer.save()
                        batch_serializers.append(batch_serializer.instance.id) 
                # --- Serial handling ---
                elif itemmaster.serial:
                    
                    if not serials:
                        self.errors.append(f'{itemmaster_lable} - Serial is required')
                        continue 
                    if purchase_invoice_item and requested_qty > (purchase_invoice_item.po_qty or 0):
                        self.errors.append(f"{itemmaster_lable}-> return QTY is more than purchase invoice qty is {purchase_invoice_item.po_qty or 0}.")
                        continue
  
                    if len(serials) != base_requested_qty:
                        self.errors.append(f"{itemmaster_lable} serial qty and item QTY mismatch")
                        continue

                    if grn_item_instance_list:
                        purchase_return_qty,purchase_invoice_qty,total_balance = self.calc_balances(grn_item_instance_list , False)
                        if base_requested_qty > total_balance:
                            self.errors.append(
                                f"{itemmaster}"
                                f"Qty exceeds limit. "
                                f"Purchase Return Base QTY = {purchase_return_qty}, "
                                f"Purchase Invoice Base QTY = {purchase_invoice_qty}. "
                                f"Allowed  Base QTY = {total_balance}, Requested QTY = {base_requested_qty}.")
                            continue

                    elif purchase_invoice_item:
                        purchase_return_qty,purchase_invoice_qty,total_balance = self.calc_balances(purchase_invoice_item.grn_item.all(), True)
                        if base_requested_qty > total_balance:
                            self.errors.append(
                                f"{itemmaster}"
                                f"Qty exceeds limit. "
                                f"Purchase Return QTY = {purchase_return_qty}, "
                                f"Allowed QTY = {total_balance}, Requested QTY = {base_requested_qty}.")
                            continue

                else:
                    if not nobatch_noserials:
                        self.errors.append(f'{itemmaster_lable} - No Batch No Serial is required')
                        continue
                    # total_nobatch_noserial_qty  = sum(nobatch_noserial.get("qty", 0)  for nobatch_noserial in nobatch_noserials)
               
                    if purchase_invoice_item and requested_qty > (purchase_invoice_item.po_qty or 0):
                        self.errors.append(f"{itemmaster_lable}-> return QTY is more than purchase invoice qty is {purchase_invoice_item.po_qty or 0}.")
                        continue
                    # if total_nobatch_noserial_qty != requested_qty:
                    #     self.errors.append(f"{itemmaster_lable}->No Batch No Serial total QTY and item QTY mismatch")
                    for nobatch_noserial in nobatch_noserials:
                        nobatch_noserial_id = nobatch_noserial.get("id")
                        grn_no = nobatch_noserial.get("grn_no")
                        nobatch_noserial_grn_id = nobatch_noserial.get("nobatch_noserial")
                        nobatch_noserial_qty = nobatch_noserial.get("qty", 0)
                        if not nobatch_noserial_qty:
                            continue
                        if grn_item_instance_list:
                            get_grn_item = next((grn for grn in grn_item_instance_list if grn.id == int(nobatch_noserial_grn_id)), None)
                            base_qty = (get_grn_item.qty or 0)/(get_grn_item.conversion_factor or 1)
                            base_qty = base_qty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_return_qty = ((get_grn_item.purchase_return_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_invoice_qty = ((get_grn_item.purchase_invoice_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            balance_qty = (base_qty or 0 ) - purchase_return_qty -  purchase_invoice_qty
                          
                            if nobatch_noserial_qty > balance_qty:
                                self.errors.append(
                                    f"{itemmaster_lable}-{grn_no}"
                                    f"Qty exceeds limit. "
                                    f"Purchase Return Base QTY = {purchase_return_qty or 0}, "
                                    f"Purchase Invoice Base QTY = {purchase_invoice_qty or 0}. "
                                    f"Allowed Base QTY = {balance_qty}, Requested Base QTY = {nobatch_noserial_qty}.")
                                continue
                        else:
                            get_grn_item = next((grn for grn in purchase_invoice_item.grn_item.all() if grn.id == int(nobatch_noserial_grn_id)), None)
                            base_qty = ((get_grn_item.qty or 0 ) /(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            purchase_return_qty = ((get_grn_item.purchase_return_qty or 0)/(get_grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                            balance_qty = base_qty - purchase_return_qty
                            
                            if nobatch_noserial_qty > balance_qty:
                                self.errors.append(
                                    f"{itemmaster_lable} {grn_no}"
                                    f"Qty exceeds limit. "
                                    f"Purchase Return QTY = {get_grn_item.purchase_invoice_qty}, "
                                    f"Allowed QTY = {balance_qty}, Requested QTY = {nobatch_noserial_qty}.")
                                continue
                        
                        nobatch_noserial_instance= None
                        if nobatch_noserial_id:
                            nobatch_noserial_instance = PurchaseRetunNobatchNoserial.objects.filter(id=nobatch_noserial_id).first()

                        nobatch_noserial_serializer = PurchaseRetunNobatchNoserialSerializer(nobatch_noserial_instance, data=nobatch_noserial, partial=True)

                        if not nobatch_noserial_serializer.is_valid():
                            for field, field_errors in nobatch_noserial_serializer.errors.items():
                                for err in field_errors:
                                    self.errors.append(f"{itemmaster_lable} - {field}: {err}")
                        if len(self.errors) > 0:
                            continue
                        nobatch_noserial_serializer.save()
                        nobatch_noserial_serializers.append(nobatch_noserial_serializer.instance.id)

                if item_detail.get("id"):
                    item_detail_instance = PurchaseReturnChallanItemDetails.objects.filter(id=item_detail.get("id")).first()
                    instance_list.append(item_detail_instance)
                else:
                    instance_list.append(None) 
                if batch_serializers:
                    item_detail['batch'] = batch_serializers
                if nobatch_noserial_serializers:
                    item_detail['nobatch_noserial'] = nobatch_noserial_serializers

            if len(self.errors) > 0:
                return False
            
            item_result = validate_common_data_and_send_with_instance(
                item_details, instance_list, PurchaseReturnChallanItemDetailsSerializer,
                item_labels, self.info.context)
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.item_details_serializer = item_result.get("instance")
            return True

        except Exception as e:
            self.errors.append(f"An exception occurred while validate item details: {str(e)}")
            return False

    def save_itemdetails(self):
        item_detail_ids = []
        try:
            for serializer in self.item_details_serializer:
                if serializer:
                    serializer.save()
                    item_detail_ids.append(serializer.instance.id)
             
            self.data['purchase_return_challan_item_Details'] = item_detail_ids
            return True
        except Exception as e:
            
            self.errors.append(f"An exception occurred while validate item details: {str(e)}")
            return False
    
    def save_purchase_return(self):
        serializer = None
        try:
            if self.purchase_return: 
                serializer = PurchaseReturnChallanSerializer(self.purchase_return, 
                                                            data=self.data,partial=True, 
                                                            context={'request': self.info.context})
            else:
                serializer = PurchaseReturnChallanSerializer(data=self.data, partial=True,
                                                    context={'request': self.info.context})
            
            if serializer and serializer.is_valid():
                serializer.save()
                new_itemdetails_ids = serializer.instance.purchase_return_challan_item_Details.values_list('id', flat=True)
                self.purchase_return = serializer.instance
                if self.purchase_invoice:
                    purchase_invoice = self.purchase_invoice[0]
                    purchase_invoice.purchase_retun.add(serializer.instance)
                    
                    
                elif self.goods_receipt_note:
                    for grn_instance in self.goods_receipt_note:
                        grn_instance.purchase_retun.add(serializer.instance)
                
                deleteCommanLinkedTable(self.item_detail_instances, new_itemdetails_ids , PurchaseReturnChallanItemDetails)
                         
                return True
            else:
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                            for field, error in serializer.errors.items()])
                return False
        except Exception as e:
            self.errors.append(f"An exception error occurred while saving purchase return {str(e)}")
            return False

    def get_store_list(self, grn_items):
        """Extract all receiving_store_ids from grn_items."""
        store_ids = []
        for grn_item in grn_items:
            purchase_order = (
                grn_item.gin.purchase_order_parent.purchaseorder_set.first()
                if grn_item and grn_item.gin and grn_item.gin.purchase_order_parent
                else None
            )
            if purchase_order:
                
                store_ids.append(purchase_order.receiving_store_id) 
        return store_ids

    def validate_stock(self, qty, stock_data_existing_list):
        required_qty = qty
        total_current_stock = sum(single_stock.current_stock or 0 for single_stock in stock_data_existing_list)
        
        actual_stock = (total_current_stock or 0)
        balance = actual_stock - required_qty
        return balance >= 0, balance

    def stock_check(self):
        try:
            for item in self.purchase_return.purchase_return_challan_item_Details.all():  
                if item.is_stock_reduce:
                    continue
                if (item.base_return_qty or 0) <= 0:
                    continue
                batchs = item.batch.all()
                serial = item.serial.all()
                nobatch_noserials = item.nobatch_noserial.all()
                
                itemmaster = None
                grn_items  = []
                store_list = []
                # 🔹 Collect GRN items
                if item.purchase_invoice_item:
                    grn_items  = item.purchase_invoice_item.grn_item.all() 
                elif item.grn_item.exists(): 
                    grn_items  = item.grn_item.all()
                else:
                    continue

                if grn_items:
                    grn_item = grn_items.first()
                    itemmaster = grn_item.gin.item_master
                    store_list = self.get_store_list(grn_items)

                    

                    if len(set(store_list)) > 1:
                        self.errors.append(f"{itemmaster} multi store not allowed.")
                        continue
                
                self.store = store_list[0]
                if not itemmaster.keep_stock:
                        continue
                # 🔹 Batch check 
                if batchs:
                 
                    if item.purchase_invoice_item and (item.purchase_invoice_item.po_qty or 0 ) < (item.po_return_qty or 0):
                        self.errors.append(f"{itemmaster} - purchase return qty \
                                    {item.purchase_invoice_item.po_qty or 0} but item return qty {item.po_return_qty}.")
                        continue

                    for batch in batchs:
                        if batch.is_stock_reduce:
                            continue
                        if (batch.qty or 0) <=0:
                            continue
                        grn_item = batch.batch
                        batch_str = grn_item.batch_number
                        
                        qty = batch.qty 
                        purchase_return_qty = ((grn_item.purchase_return_qty or 0)/(grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                        purchase_invoice_qty = ((grn_item.purchase_invoice_qty or 0)/(grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                        # allowed qty calc
                        available_qty = 0
                        grn_qty = grn_item.qty/(grn_item.conversion_factor or 1)
                        if item.purchase_invoice_item:
                            available_qty = grn_qty - purchase_return_qty
                        else:
                            available_qty = grn_qty
                            - purchase_invoice_qty
                            - purchase_return_qty

                        if available_qty < (batch.qty or  0):
                            self.errors.append(
                                f"{itemmaster} - {batch_str}: Allowed base QTY {available_qty}, entered  {batch.qty}.")
                            continue

                        batch_instance = BatchNumber.objects.filter(part_number= itemmaster,  batch_number_name=batch_str).first()

                        if not batch_instance:
                            self.errors.append(f"{batch_instance} batch is not found.")

                        stock_data_existing_list = ItemStock.objects.filter(
                                                    part_number=itemmaster,
                                                    store=self.store,
                                                    batch_number=batch_instance)
                        if not stock_data_existing_list:
                            self.errors.append(f"{itemmaster} {batch_str or ''} is not available in {self.store.store_name} Store.")
                            continue
                        is_sufficient, balance_stock = self.validate_stock(qty, stock_data_existing_list)
                        if not is_sufficient:
                            self.errors.append(
                            f"The item {itemmaster} {f'batch: {batch_str}'} "
                            f"is not available. Required quantity shortfall: {abs(balance_stock)}."
                        )
                    
                elif serial: 
                    qty = item.base_return_qty
                    if item.purchase_invoice_item and (item.purchase_invoice_item.po_qty or 0 ) < (item.po_return_qty or 0):
                        self.errors.append(f"{itemmaster} - Invoice qty \
                                    {item.purchase_invoice_item.qty or 0} but item return qty {item.po_return_qty}.")
                        continue

                    if len(serial) != qty:
                        self.errors.append(f"serial qty and item QTY mismatch")
                        continue

                    stock_data_existing_list = ItemStock.objects.filter(
                                                    part_number=itemmaster,
                                                    store=self.store, serial_number__in=serial)
                    if not stock_data_existing_list:
                        self.errors.append(f"{itemmaster}  is not available in {self.store.store_name} Store.")
                        continue
                    
                    is_sufficient, balance_stock = self.validate_stock(qty, stock_data_existing_list)
                    
                    if not is_sufficient:
                        self.errors.append(
                        f"The item {itemmaster}  "
                        f"is not available. Required quantity shortfall: {abs(balance_stock)}."
                        )
                        continue

                    current_serial_ids = set(
                        id
                        for single_stock in stock_data_existing_list
                        for id in single_stock.serial_number.values_list("id", flat=True)
                    )
                    
                    serial_objects_list = serial.values_list("id","serial_number")
                    
                    missing_serials = [
                                serial_number for serial_id, serial_number in serial_objects_list if serial_id not in current_serial_ids
                            ]
                    if missing_serials:
                        self.errors.append(
                            f"The following serial numbers for {itemmaster} are not in current stock: {', '.join(missing_serials)}"
                        )

                elif nobatch_noserials:
                    # nobatch_noserials_total_qty = sum((nobatch_noserial.qty or 0) for nobatch_noserial in nobatch_noserials)
                    # if nobatch_noserials_total_qty != item.po_return_qty:
                    #     self.errors.append(f"{itemmaster} - total no batch no serials  qty \
                    #                 {nobatch_noserials_total_qty} item base qty {item.po_return_qty} is mismatch.")
                    #     continue 
                    if item.purchase_invoice_item and (item.purchase_invoice_item.po_qty or 0) < (item.po_return_qty or 0):
                        self.errors.append(f"{itemmaster} - purchase return qty  \
                                        {item.purchase_invoice_item.po_qty} but item return base qty {item.po_return_qty}.")
                        continue

                    
                    
                    for nobatch_noserial in nobatch_noserials:
                        if not nobatch_noserial.is_stock_reduce:
                            continue
                        if (nobatch_noserial.qty or 0) <=0:
                            continue
                        grn_item = nobatch_noserial.nobatch_noserial 
                        grn_no = grn_item.purchase_return_no.linked_model_id
                        qty = item.base_return_qty
                        purchase_return_qty = ((grn_item.purchase_return_qty or 0)/(grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                        purchase_invoice_qty = ((grn_item.purchase_invoice_qty or 0)/(grn_item.conversion_factor or 1)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                        available_qty = 0
                        grn_qty = grn_item.qty/(grn_item.conversion_factor or 1) 
                        if item.purchase_invoice_item:
                            available_qty = grn_qty - purchase_return_qty
                        else:
                            available_qty = grn_qty
                            - purchase_invoice_qty
                            - purchase_return_qty

                        if available_qty < (batch.qty or  0):
                            self.errors.append(
                                f"{itemmaster} - {grn_no} : Allowed base QTY {available_qty}, entered  {batch.qty}."
                            )
                            continue



                        stock_data_existing_list = ItemStock.objects.filter(
                                            part_number=itemmaster,
                                            store=self.store)
                        
                        if not stock_data_existing_list:
                            self.errors.append(f"GRN {grn_no} -> {itemmaster} is not available in {self.store.store_name} Store.")
                            continue
                        is_sufficient, balance_stock = self.validate_stock(qty, stock_data_existing_list)
                        if not is_sufficient:
                            self.errors.append(
                            f"GRN {grn_no} -> The item {itemmaster}"
                            f"is not available. Required quantity shortfall: {abs(balance_stock)}.")
            
            if len(self.errors) > 0:
                return False
            return True
        except Exception as e:
            self.errors.append(f"Unexpeted error occurred is shock check -{str(e)}")
            return False
        
    def reduce_stock(self):
        try:
            for item in self.purchase_return.purchase_return_challan_item_Details.all():

                if item.is_stock_reduce:
                    continue
                if (item.base_return_qty or 0) <= 0:
                    continue

                batchs = item.batch.all()
                serials = item.serial.values_list("id","serial_number")
                nobatch_noserials = item.nobatch_noserial.all()
                
                itemmaster = None
                grn_items  = []

                if item.purchase_invoice_item:
                    grn_items = item.purchase_invoice_item.grn_item.all()
                    
                elif item.grn_item.exists():
                    grn_items = item.grn_item.all()
                    
                if grn_items:
                    grn_item = grn_items.first()
                    itemmaster = grn_item.gin.item_master
                else:
                    continue
                if not itemmaster.keep_stock:
                    item.is_stock_reduce =  True
                    item.save()
                    continue 
                # -------------------------------
                # 🔹 CASE 1: Batch-based stock reduce
                # -------------------------------
                
                if batchs:
                    for batch in batchs:
                        if batch.is_stock_reduce:
                            continue
                        if (batch.qty or 0) <=0:
                            continue
                        grn_item = batch.batch
                        batch_str = grn_item.batch_number
                        qty = batch.qty

                        batch_instance = BatchNumber.objects.filter(
                                part_number=itemmaster,
                                batch_number_name=batch_str
                            ).first()
                        
                        if not batch_instance:
                            self.errors.append(f"{batch_instance} not Found in Batch List.")
                            continue
 

                        stockReduce = StockReduce(
                                        partCode_id=itemmaster.id,
                                        Store_id=self.store.id,
                                        batch_id=batch_instance.id,
                                        serial_id_list=[],
                                        qty=qty,
                                        partCode = itemmaster,
                                        batch = batch_str)
                        
                        result = stockReduce.reduceBatchNumber()
                        if result.get("success"):
                            batch_qty = Decimal(batch.qty * grn_item.conversion_factor)
                            batch_qty = batch_qty.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

                            grn_item.purchase_return_qty = (grn_item.purchase_return_qty or 0) + batch_qty
                            grn_item.save()
                            batch.is_stock_reduce= True
                            batch.save()
                            try:
                                stockHistoryUpdate(
                                        "DELETE",
                                        self.store,
                                        itemmaster,
                                        result['previousSates'],
                                        result['updatedState'],
                                        0,
                                        result['reduce'],
                                        self.info.context.user,
                                        "Purchase Return",
                                        self.purchase_return.id,
                                        self.purchase_return.purchase_return_no.linked_model_id,
                                        'Purchase Return',
                                        result['stocklink'],
                                        None
                                    )
                            except Exception as e:
                                self.errors.append(f'Unexpected error occurred in History save {str(e)}')
                        else:
                            self.errors.extend(result.get("error"))
                            continue
                    item.is_stock_reduce =  True
                    item.save()
                
                elif serials:
                    serial_ids = [s[0] for s in serials]
                    serial_texts = [s[1] for s in serials]
                     
                    qty = len(serial_ids) 
                    
                    stockReduce = StockReduce(
                                    partCode_id=itemmaster.id,
                                    Store_id=self.store.id,
                                    batch_id= None,
                                    qty=qty,
                                    serial_id_list=serial_ids,
                                    partCode = itemmaster,
                                    batch = None
                                    
                                )
                    
                    result = stockReduce.reduceSerialNumber()
                    
                    if result.get("success"):
                        try:
                            stockHistoryUpdate(
                                "DELETE",
                                self.store,
                                itemmaster,
                                result['previousSates'],
                                result['updatedState'],
                                0,
                                result['reduce'],
                                self.info.context.user,
                                "Purchase Return",
                                self.purchase_return.id,
                                self.purchase_return.purchase_return_no.linked_model_id,
                                'Purchase Return',
                                result['stocklink'],
                                None
                            )
                        except Exception as e:
                            self.errors.append(f'Unexpected error occurred in History save {str(e)}')
                        
                        for single_grn in grn_items:
                            count = 0
                            # handle comma-separated OR single value 
                             
                            delimiter = ',' if ',' in single_grn.serial_number else '\n'
                            
                            # Split, strip whitespace, and remove empty strings
                            grn_serials = [s.strip() for s in single_grn.serial_number.split(delimiter) if s.strip()]
                            
                            for s in serial_texts:
                                if s in grn_serials:
                                    count += 1
                            poqty = count*(single_grn.conversion_factor or 1)
                            if count > 0:
                                single_grn.purchase_return_qty = (single_grn.purchase_return_qty or 0) + poqty
                                single_grn.save()

                        item.is_stock_reduce =  True
                        item.save()
                    else:
                        self.errors.extend(result.get("error"))
                        continue
                
                else:
                    if nobatch_noserials:
                        for nobatch_noserial in nobatch_noserials:
                            if nobatch_noserial.is_stock_reduce:
                                continue
                            if (nobatch_noserial.qty or 0) <=0:
                                continue
                            grn_item = nobatch_noserial.nobatch_noserial 
                            qty = (nobatch_noserial.qty or 0)
              
                            stock_reduce = StockReduce(
                                    partCode_id=itemmaster.id,
                                    Store_id=self.store.id,
                                    batch_id=None,
                                    qty=qty,
                                    serial_id_list=[],
                                    partCode = itemmaster,
                                    batch = None)
                            result = stock_reduce.reduceNoBatchNoSerial()
                            if result.get("success"):
                                no_batch_serial_qty = Decimal(qty * grn_item.conversion_factor).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
                                grn_item.purchase_return_qty = (grn_item.purchase_return_qty or 0) + no_batch_serial_qty
                                grn_item.save()
                                nobatch_noserial.is_stock_reduce = True
                                nobatch_noserial.save()
                                try:
                                    stockHistoryUpdate(
                                        "DELETE",
                                        self.store,
                                        itemmaster,
                                        result['previousSates'],
                                        result['updatedState'],
                                        0,
                                        result['reduce'],
                                        self.info.context.user,
                                        "Purchase Return",
                                        self.purchase_return.id,
                                        self.purchase_return.purchase_return_no.linked_model_id,
                                        'Purchase Return',
                                        result['stocklink'],
                                        None
                                    )
                                except Exception as e:
                                    self.errors.append(f'Unexpected error occurred in History save {str(e)}')
                                    continue
                            else:
                                self.errors.extend(result.get("error"))
                                continue
                        item.is_stock_reduce =  True
                        item.save()

            return True
        except Exception as e:
                self.errors.append(f'Unexpected error occurred in Stock reduce {str(e)}')
        
    def check_transportation_requirements(self):
        if not self.data['transportation_mode']:
            self.errors.append("Transportation Mode is required.")
            return False
        if self.data['transportation_mode'] == "OwnVechile":
            if not self.data.get('vehicle_no') or not self.data.get('driver_name'):
                self.errors.append("Vehicle No , Driver Name is required.")
        elif self.data['transportation_mode'] == "Transport":
            if self.data['transport'] == None or self.data.get('vehicle_no') == None:
                self.errors.append("Transport ID , Vehicle No is required.")
        elif self.data['transportation_mode'] == "Courier":
            if self.data['docket_no'] == None or self.data['docket_date'] == None:
                self.errors.append("Courier is required.")
        elif self.data['transportation_mode'] == "OtherMode":
            if self.data['other_model'] == None:
                self.errors.append("Other Model is required.")
        return len(self.errors) == 0

    def validate_e_way_document(self):
        grn = None 
        if self.purchase_return.purchaseinvoice_set.all():
            invoice = self.purchase_return.purchaseinvoice_set.first()
            grn = invoice.goodsreceiptnote_set.first() if invoice and invoice.goodsreceiptnote_set else None
        elif self.purchase_return.goodsreceiptnote_set.all():
            
            grn = self.purchase_return.goodsreceiptnote_set.first()
        
        if grn.goods_inward_note and grn.goods_inward_note.purchase_order_id:
            purchase_state = grn.goods_inward_note.purchase_order_id.address.state
            amount_threshold = self.company_obj.threshold_for_intrastate if str(purchase_state).lower() == str(self.company_obj.address.state).lower() else self.company_obj.threshold_for_interstate
            if self.data['net_amount'] >= int(amount_threshold):
                if not self.kwargs.get('e_way_bill') or not self.kwargs.get('e_way_bill_date'):
                    self.errors.append(f"Net Amount is more than {amount_threshold}. E-Way Bill and Date are required.")
                    return False
            return True
            

            
        else:
            self.errors.append("purchase Not Found.")
            return False

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "purchase_return": self.purchase_return
        }


class PurchaseRetunCancelService():
    def __init__(self, id,   info):
        self.id = id 
        self.status = None
        self.success = False
        self.errors = []
        self.info = info
        self.store = None
        self.purchase_return = None
    
    def process(self):
        try:
            
            if not self.get_purchase_retun():
                return self.response()
            
            status = CommanStatus.objects.filter(name="Canceled", table="Purchase Return Challan").first()
            
            if not status:
                self.errors.append("Cancel status Not Found.")
            if self.purchase_return.status.name == "Draft":
                self.purchase_return.status = status
                self.purchase_return.save()
                self.success=True
            elif self.purchase_return.status.name in ["Submit","Dispatch"]:
                debit_note = self.purchase_return.debitnote_set.first()
                
                if debit_note and debit_note.status.name != "Canceled":
                    self.errors.append(f"Befor Cancel purchase return need to cancel the debit note{debit_note.debit_note_no.linked_model_id}")
                    return self.response()
                if not self.reduce_return_qty():
                    return self.response()
                purchase_return_general_ledger  = AccountsGeneralLedger.objects.filter(purchase_return_challan=self.id)
                if purchase_return_general_ledger.exists():
                    for general_ledger in purchase_return_general_ledger:
                        general_ledger.delete()
                self.purchase_return.status = status
                self.purchase_return.save()
                self.success=True
            return self.response()
        except Exception as e:
            self.errors.append(str(e))
            return self.response()
    
    def get_store_list(self, grn_items):
        """Extract all receiving_store_ids from grn_items."""
        store_ids = []
        for grn_item in grn_items:
            purchase_order = (
                grn_item.gin.purchase_order_parent.purchaseorder_set.first()
                if grn_item and grn_item.gin and grn_item.gin.purchase_order_parent
                else None
            )
            if purchase_order:
                store_ids.append(purchase_order.receiving_store_id)
        self.store = store_ids[0]
    
    def get_or_create_batch(self, item_master_id, batch_name):
        batch_instance = BatchNumber.objects.filter(
            part_number=item_master_id,
            batch_number_name=batch_name
        ).first()

        if batch_instance:
            return batch_instance

        batch_data = {
            "part_number": item_master_id,
            "batch_number_name": batch_name
        }
        batch_serializer = BatchNumberSerializer(data=batch_data)

        if batch_serializer.is_valid():
            batch_serializer.save()
            return batch_serializer.instance
        else:
            self.errors.append(f"Batch creation failed for '{batch_name}': {batch_serializer.errors}")
            return None

    def addBatchStockIn(self, itemmaster, batch, store, qty): 
        try:
            stock = ItemStock.objects.filter(
                part_number=itemmaster.id,
                store=store.id,
                batch_number=batch.id
            ).first()
            if stock:
                stock.current_stock += Decimal(qty)
                stock.save()
            return None
        except Exception as e:
            return f"{itemmaster.item_part_code} -- {e}"

    def addSerialStockIn(self, itemmaster, serials, store, qty):
        try:
            stock = ItemStock.objects.filter(
                part_number=itemmaster,
                store=store
            ).first()

            # normalize serial ids
            new_ids = [s.id for s in serials]

            if stock:
                # merge old + new serials
                existing_ids = set(stock.serial_number.values_list('id', flat=True))
                combined_ids = existing_ids.union(new_ids)

                stock.serial_number.set(SerialNumbers.objects.filter(id__in=combined_ids))
                stock.current_stock = (stock.current_stock or 0) + Decimal(qty)
                stock.save()
            else:
                stock = ItemStock.objects.create(
                    part_number=itemmaster,
                    store=store,
                    current_stock=Decimal(qty)
                )
                stock.serial_number.set(serials)  # many-to-many add after create

            return None
        except Exception as e:
            return f"{itemmaster.item_part_code} -- {str(e)}"

    def addNoBatchNoSerial(self, itemmaster, store, qty):
        try:
            stock = ItemStock.objects.filter(
                part_number=itemmaster.id,
                store=store.id
            ).first()
            if stock:
                stock.current_stock += Decimal(qty)
                stock.save()
            return None
        except Exception as e:
            return f"{itemmaster.item_part_code} -- {e}"

    def get_purchase_retun(self):
        self.purchase_return = None
        if not self.id:
            return self.errors.append("Id is required")
        self.purchase_return = PurchaseReturnChallan.objects.filter(id=self.id).first()

        if not self.purchase_return:
            self.errors.append("Purchase return not found.")
            return False
        
        # if self.purchase_return.status.name in ["Dispatch"]:
        #     self.errors.append("Already {self.purchase_return.status.name} purchase return did'n make Canceled.")
        #     return False
        
        
        return True
    
    def reduce_return_qty(self):
        for item in self.purchase_return.purchase_return_challan_item_Details.all():
           
            if item.is_stock_reduce:
                batchs = item.batch.all()
                serial = item.serial.all()
                nobatch_noserials = item.nobatch_noserial.all()
                grn_items  = [] 
                itemmaster = None 
                if item.purchase_invoice_item:
                    grn_items = item.purchase_invoice_item.grn_item.all()
                elif item.grn_item.exists():
                    grn_items = item.grn_item.all()
                    
                if grn_items:
                    grn_item = grn_items.first()
                    itemmaster = grn_item.gin.item_master
                    
                    self.get_store_list(grn_items)
                else:
                    continue
                if not itemmaster.keep_stock:
                    item.is_stock_reduce =  True
                    item.save()
                    continue
                
                # -------------------------------
                # 🔹 CASE 1: Batch-based stock Add
                # -------------------------------
                if batchs:
                    for batch in batchs:
                        if batch.is_stock_reduce:
                            grn_item = batch.batch
                            batch_str = grn_item.batch_number
                            batch_instance = self.get_or_create_batch(itemmaster ,batch_str)
                            error = self.addBatchStockIn(itemmaster, batch_instance, self.store, batch.qty)
                            if error is None:
                                qty = (batch.qty * grn_item.conversion_factor)
                                if grn_item.purchase_return_qty >= qty:
                                    grn_item.purchase_return_qty = (grn_item.purchase_return_qty or 0) - (qty)
                                else:
                                    grn_item.purchase_return_qty = 0
                                grn_item.save()
                                batch.is_stock_reduce= False
                                batch.save()
                            else :
                                self.errors.extend(error)
                                continue
                    if not self.errors:
                        item.is_stock_reduce = False
                        item.save()
                # -------------------------------
                # 🔹 CASE 2: serial-based stock Add
                # -------------------------------
                elif serial: 
                    
                    serial_texts = [s.serial_number for s in serial]
                    
                    error = self.addSerialStockIn(itemmaster, serial, self.store, item.base_return_qty)
                    
                    if error is None:
                        for single_grn in grn_items:
                            count = 0
                            # handle comma-separated OR single value 
                            delimiter = ',' if ',' in single_grn.serial_number else '\n'
                            
                            # Split, strip whitespace, and remove empty strings
                            grn_serials = [s.strip() for s in single_grn.serial_number.split(delimiter) if s.strip()]

                            for s in serial_texts:
                                if s in grn_serials:
                                    count += 1
                            poqty = count*(single_grn.conversion_factor or 1)
                            if poqty > 0: 
                                if (single_grn.purchase_return_qty or 0) >= poqty:
                                    single_grn.purchase_return_qty = single_grn.purchase_return_qty - poqty
                                else:
                                    single_grn.purchase_return_qty = 0 
                                single_grn.save()
                        item.is_stock_reduce =  False
                        item.save()
                # -------------------------------
                # 🔹 CASE 3: nobatch_noserials-based stock Add
                # -------------------------------
                elif nobatch_noserials: 
                    for nobatch_noserial in nobatch_noserials:
                        if nobatch_noserial.is_stock_reduce:
                            grn_item = nobatch_noserial.nobatch_noserial
                            # grn_no = grn_item.purchase_return_no.linked_model_id
                             
                            qty = nobatch_noserial.qty
                            error = self.addNoBatchNoSerial(itemmaster, self.store, qty)
                            if error is None:
                                qty = ((nobatch_noserial.qty or 0) * grn_item.conversion_factor)
                                if grn_item.purchase_return_qty >= qty:
                                    grn_item.purchase_return_qty = (grn_item.purchase_return_qty or 0) - (qty)
                                else:
                                    grn_item.purchase_return_qty = 0
                                grn_item.save()
                                nobatch_noserial.is_stock_reduce = False
                                nobatch_noserial.save()
                            else:
                                self.errors.extend(error)
                    if not self.errors:
                        item.is_stock_reduce =  False
                        item.save()
        
        historys = StockHistory.objects.filter(transaction_module="Purchase Return", transaction_id=self.purchase_return.id)
        for history in historys:
            history.is_delete = True
            history.save()

        if self.errors:
            return False
        return True

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "purchase_return": self.purchase_return
        }


def purchase_return_general_update(data):
    valid_serializers = []
    errors = []
    credit = data.get("credit", {})
    debits = data.get("debits", [])
    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "purchase_return_challan", "account", "created_by"]
    
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
                errors.append(f"debit → {field}: {'; '.join(map(str, error))}")
        else:
            valid_serializers.append(serializer)
        
    # Return errors if any
    if errors:
        return {"success": False, "errors": errors}

    # Save all valid serializers
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return {"success": True, "errors": []}