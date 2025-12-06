from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from django.db import transaction

class GinService:
    def __init__(self, data: dict, status: str, info):
        self.data = data
        self.status = status
        self.success = False
        self.errors = []
        self.info = info
        self.MODEL_TYPE = ['purchase_model']
        self.parent_type = None
        self.gin = None
        self.status_obj = None
        self.item_details_instances = []
        self.old_item_details_ids = []
        self.rework_qty = 0

    def process(self):
        with transaction.atomic():
            if self.status == "Inward":
                if not self.validate_required_fields(): return self.response()
                if not self.validate_rework_delivery_challan(): return self.response()
                if not self.update_status_instance(): return self.response()
                if not self.validate_numbering(): return self.response()
                if not self.validate_item_details(): return self.response()
                if not self.save_item_details(): return self.response()
                if not self.save_gin(): return self.response()

            elif self.status == "Submit":
                if not self.validate_required_fields(): return self.response()
                if not self.validate_rework_delivery_challan(): return self.response()
                if not self.update_status_instance(): return self.response()
                if not self.validate_received_qty(): return self.response()
                if not self.validate_item_on_submit(): return self.response() 
                if not self.update_the_inward(): return self.response()
                if self.gin:
                    self.gin.status = self.status_obj
                    self.gin.save()

            self.success = True
        return self.response()

    def is_status_invalid_for_transition(self, current_status_name: str) -> bool:
        return current_status_name  in ['Canceled', 'Submit']

    def validate_required_fields(self) -> bool:
        parent_type = self.data.get("parent_type")
        if parent_type not in self.MODEL_TYPE:
            self.errors.append("Invalid or missing parent_type.")
            return False

        if parent_type == "purchase_model":
            if not self.data.get("purchase_order_id"):
                self.errors.append("Purchase Order ID is required.")
                return False
            self.parent_type = parent_type

        if not self.data.get("gin_date"):
            self.errors.append("GIN date is required.")
            return False

        if self.data.get("id"):
            self.gin = GoodsInwardNote.objects.filter(id=self.data.get("id")).first()
            if not self.gin:
                self.errors.append("Goods Inward Note not found.")
                return False
            if self.status in ["Submit", "Inward"] and self.is_status_invalid_for_transition(self.gin.status.name):
                self.errors.append(f"GIN is already {self.gin.status.name}. Cannot {self.status} it again.")
                return False

            self.old_item_details_ids = list(self.gin.goods_receipt_note_item_details_id.values_list("id", flat=True))
        return True

    def validate_rework_delivery_challan(self) -> bool:
        parent_type = self.data.get("parent_type")
        has_challan = bool(self.data.get("rework_delivery_challan"))
        items = self.data.get("goods_receipt_note_item_details_id", [])
        has_item_links = any(item.get("reword_delivery_challan_item") for item in items)
        
        if parent_type != "purchase_model":
            if has_challan:
                self.errors.append("Rework Delivery Challan link allowed only for Purchase module.")
                return False
            if has_item_links:
                self.errors.append("Rework Delivery Challan item link allowed only for Purchase module.")
                return False

        if has_challan and not has_item_links:
            self.errors.append("Some item Rework Delivery Challan Item is missing.")
            return False

        if has_item_links and not has_challan:
            self.errors.append("Rework Delivery Challan id is missing.")
            return False

        return True

    def update_status_instance(self) -> bool:
        status_obj = CommanStatus.objects.filter(name=self.status, table="GIN").first()
        if not status_obj:
            self.errors.append(f"Status '{self.status}' is not configured in CommanStatus.")
            return False
        self.data["status"] = status_obj.id
        self.status_obj = status_obj
        return True

    def validate_numbering(self) -> bool:
        if not NumberingSeries.objects.filter(resource='Goods Inward Note', default=True).exists():
            self.errors.append("Default GIN numbering series is not configured.")
            return False
        return True

    def validate_item_details(self) -> bool:
        item_details = self.data.get('goods_receipt_note_item_details_id', [])
        if not item_details:
            self.errors.append("At least one Item Detail is required.")
            return False

        instance_list = []
        item_labels = []
        # itemmaster_ids = [item.get("item_master") for item in item_details]
        # duplicates = set([x for x in itemmaster_ids if itemmaster_ids.count(x) > 1])
        # if duplicates:
        #     self.errors.append("Duplicate items found in Item Details.")
        #     return False

        for item in item_details:
            item_master = ItemMaster.objects.filter(id=item.get("item_master")).first()
            if not item_master:
                self.errors.append(f"ItemMaster ID {item.get('item_master')} not found.")
                return False

            item_labels.append(str(item_master))
            for field in ["item_master", "received", "qc"]:
                if item.get(field) is None:
                    self.errors.append(f"{item_master} → {field} is required.")

            if self.parent_type == "purchase_model":
                po_parent_id = item.get("purchase_order_parent")
                if not po_parent_id:
                    self.errors.append(f"{item_master} → purchase_order_parent is missing.")
                    return False
                
                purchase_item = purchaseOrderItemDetails.objects.filter(id=po_parent_id).first()
                if not purchase_item:
                    self.errors.append(f"{item_master} → purchase_order_parent {po_parent_id} not found.")
                    return False
                
                
            if item.get("id"):
                instance = GoodsInwardNoteItemDetails.objects.filter(id=item.get("id")).first()
                if not instance:
                    self.errors.append(f"Item ID {item.get('id')} not found.")
                    return False
                instance_list.append(instance)
            else:
                instance_list.append(None)

        item_result = validate_common_data_and_send_with_instance(
            item_details, instance_list,
            GoodsInwardNoteItemDetailsSerializer,
            item_labels,
            self.info.context
        )
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False

        self.item_details_instances.extend(item_result.get("instance"))
        return True

    def save_item_details(self) -> bool:
        item_detail_ids = []
        try:
            for serializer in self.item_details_instances:
                if serializer and serializer.is_valid():
                    serializer.save()
                    item_detail_ids.append(serializer.instance.id)
            self.data['goods_receipt_note_item_details_id'] = item_detail_ids
            return True
        except Exception as e:
            self.errors.append(f"Error saving item details: {e}")
            return False

    def save_gin(self) -> bool:
        try:
            serializer = GoodsInwardNoteSerializer(self.gin, data=self.data, partial=True, context={'request': self.info.context}) if self.gin else GoodsInwardNoteSerializer(data=self.data, partial=True, context={'request': self.info.context})
            if serializer.is_valid():
                serializer.save()
                self.gin = serializer.instance
                purchase = self.gin.purchase_order_id 
                purchase.gin.add(self.gin)
                # Delete removed item details
                new_item_ids = list(self.gin.goods_receipt_note_item_details_id.values_list('id', flat=True))
                deleteCommanLinkedTable(self.old_item_details_ids, new_item_ids, purchaseOrderItemDetails)
                return True
            else:
                self.errors.extend([
                    f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items()
                ])
                return False
        except Exception as e:
            self.errors.append(f"Error saving GIN: {str(e)}")
            return False

    def validate_received_qty(self) -> bool:
        for item in self.gin.goods_receipt_note_item_details_id.all():
            item_master = item.item_master
            purchase_item = item.purchase_order_parent
            need_qty = (purchase_item.po_qty or 0)
            received_qty = (purchase_item.received or 0) + (item.received or 0)
            rework_item = item.reword_delivery_challan_item
            if rework_item:
                rework_need_qty =  (rework_item.rework_qty or 0) - (rework_item.received_qty or 0)
                if item.received > rework_need_qty:
                    exceeds_qty = item.received - rework_need_qty
                    self.errors.append(f"{item_master} → Rework Received Qty ({item.received}) exceeds Rework Qty ({exceeds_qty}).")
            if not rework_item:
                if received_qty > need_qty:
                    exceeds_qty = received_qty - need_qty
                    self.errors.append(
                        f"{item_master} → Received Qty ({received_qty}) exceeds PO Qty ({exceeds_qty})."
                        f"Already received: {purchase_item.received or 0}, new: {item.received or 0}."
                    )
        if len(self.errors) > 0:
            return False
        return True

    def update_rework_percentage( self, rework_delivery_id, total_rework_qty, total_received_qty) -> bool:
        try:
            rework_delivery_instance = ReworkDeliveryChallan.objects.filter(id=rework_delivery_id).first()
            if not rework_delivery_instance:
                self.errors.append(f"Rework Delivery Not Found.")
                return False
            rework_percentage = (total_received_qty/total_rework_qty) *100
            rework_delivery_instance.rework_percentage = rework_percentage
            rework_delivery_instance.save()
            return True
            
        except Exception as e:
            self.errors.append(f"Unexpected error occurred on rework percentage update:-{str(e)}")
            return False
    
    def update_the_inward(self) -> bool:
        total_rework_qty = 0
        total_received_qty = 0
        try:
            for item in self.gin.goods_receipt_note_item_details_id.all(): 
                try:
                    item_master = item.item_master
                    purchase_item = item.purchase_order_parent
                    qty_to_allocate = (item.received or 0)
                    rework_item = item.reword_delivery_challan_item 
                    # Allocate to RDC first
                    if rework_item: 
                        rework_item.received_qty = (rework_item.received_qty or 0) + qty_to_allocate
                        rework_item.save()
                        total_rework_qty += (rework_item.rework_qty or 0)
                        total_received_qty += (rework_item.received_qty or 0)
                        
                    if not rework_item:
                        # Remaining qty goes to PO
                        if qty_to_allocate > 0:
                            purchase_item.received = (purchase_item.received or 0) + qty_to_allocate
                            purchase_item.save()

                except Exception as e:
                    self.errors.append(
                        f"Unexpected error occurred in {item_master} on Inward qty updated, {str(e)}"
                    )
                    return False
                
            if self.data.get("rework_delivery_challan") and (total_rework_qty > 0 or total_received_qty > 0):
                if not self.update_rework_percentage(self.data.get("rework_delivery_challan"), total_rework_qty, total_received_qty):
                    return False

            return True

        except Exception as e:
            self.errors.append(f"An unexpected error occurred on inward update {str(e)}")
            return False

    def validate_item_on_submit(self) ->bool:
        None_whole_number = []
        if self.gin:
            for item in self.gin.goods_receipt_note_item_details_id.all():
                cf = (item.purchase_order_parent.conversion_factor or 1) if item.purchase_order_parent else 1
                if item.item_master.serial and  (item.received/cf) %1 != 0:
                    None_whole_number.append(item.item_master.item_part_code)

        if len(None_whole_number )> 0:
            self.errors.append(
                    f"{', '.join(None_whole_number)} these serial item received quantity must be whole number."
                )

            return False
        return True

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "gin": self.gin
        }

class GinCancelService:

    def __init__(self, data: dict, info):
        self.data = data
        self.success = False
        self.errors = []
        self.info = info
        self.MODEL_TYPE = ['purchase_model']
        self.parent_type = None
        self.gin = None
        self.status_obj = None

    def process(self) -> dict:
        if not self.validate_required_fields():
            return self.response()
        
        
        self.status_obj = CommanStatus.objects.filter(name="Canceled", table="GIN").first()
        if not self.status_obj:
            self.errors.append("Canceled status not found.")
            return self.response() 
        if self.gin.status.name == "Submit":
            qir = self.gin.quality_inspection_report_id
            if qir and qir.status.name != "Canceled":
                self.errors.append(f"Befor cancel GIN. set the status to 'Canceled' the QIR {qir.qir_no.linked_model_id}")
            grn_ = self.gin.grn
            if grn_ and  grn_.status.name != "Canceled":
                self.errors.append(f"Befor cancel GIN. set the status to 'Canceled' the GRN {grn_.grn_no.linked_model_id}")
            if len(self.errors) > 0:
                return self.response()
            if not self.reduce_inward_qty():
                return self.response()
        
        self.gin.status = self.status_obj
        self.gin.save()
        self.success = True
        return self.response()

    def validate_required_fields(self) -> bool:
        parent_type = self.data.get("parent_type")
        if parent_type not in self.MODEL_TYPE:
            self.errors.append("Invalid or missing parent_type.")
            return False

        if parent_type == "purchase_model":
           
            self.parent_type = parent_type

        gin_id = self.data.get("id")
        if not gin_id:
            self.errors.append("Goods Inward Note not found.")
            return False

        self.gin = GoodsInwardNote.objects.filter(id=gin_id).first()
        if not self.gin:
            self.errors.append("Goods Inward Note not found.")
            return False

        if self.gin.status.name in ['Inward', "Submit"]:
            return True
        elif self.gin.status.name == 'Canceled':
            self.errors.append("This Goods Inward Note is already Canceled.")
            return False
        else:
            self.errors.append("Status Undefined.")
            return False

    def reduce_inward_qty(self) -> bool:
        try:
            rework_delivery_challan = self.gin.rework_delivery_challan
            itemdetails = self.gin.goods_receipt_note_item_details_id.all()

            if rework_delivery_challan:
                total_rework_qty = 0
                total_received_qty = 0
                
                for item in itemdetails:
                    if self.parent_type == "purchase_model" and item.reword_delivery_challan_item:
                        rework_delivery_item = item.reword_delivery_challan_item

                        received = item.received or 0
                        already_received = rework_delivery_item.received_qty or 0
                        if received > 0:
                            # prevent underflow
                            new_received = max(already_received - received, 0)
                            rework_delivery_item.received_qty = new_received
                            rework_delivery_item.save()
                            total_rework_qty += (rework_delivery_item.rework_qty or 0)
                            total_received_qty += (rework_delivery_item.received_qty or 0)
                if total_rework_qty > 0:
                    rework_percentage = (total_received_qty/total_rework_qty) *100
                else:
                    rework_percentage = 0

                rework_delivery_challan.rework_percentage = rework_percentage
                rework_delivery_challan.save()

            else: 
                for item in itemdetails:
                    if self.parent_type == "purchase_model":
                        purchase_item = item.purchase_order_parent

                        received = item.received or 0
                        current_received = purchase_item.received or 0
                        
                        new_received = max(current_received - received, 0)
                        purchase_item.received = max(new_received, 0)
                        purchase_item.save()
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred: {str(e)}")
            return False

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "gin": self.gin
        }