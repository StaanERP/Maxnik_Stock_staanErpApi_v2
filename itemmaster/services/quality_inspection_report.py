from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from django.db import transaction
from itemmaster.Utils.stockAddtinons import *

class QirService:
    def __init__(self, data: dict, status: str, info):
        self.data = data
        self.status = status
        self.success = False
        self.errors = []
        self.info = info
        self.qir = None
        self.item_details_instances = []
        self.status_obj = None
        self.reject_store = None
        self.last_serial = 0
        self.total_reject_qty = 0
    
    def process(self):
        with transaction.atomic():
            if self.status == "Pending":
                if not self.validate_requiry_field(): return self.response()
                if not self.validate_numbering(): return self.response()
                if not self.update_status_instance(): return self.response()
                if not self.validate_item_detail(): return self.response()
                if not self.save_item_details(): return self.response()
                if not self.save_qir(): return self.response()
            elif self.status == "Checked":
                if not self.validate_requiry_field(): return self.response()
                if not self.update_status_instance(): return self.response()
                if not self.final_validation_itemdetails(): return self.response()
                if not self.validate_item_on_submit(): return self.response()
                if not self.add_reject_stock(): return self.response()
                if not self.update_purchase_inward_percentage(): return self.response()

                
                self.qir.status = self.status_obj
                self.qir.reject_last_serial = (self.last_serial or self.qir.reject_last_serial)
                self.qir.save()
                self.success = True
            else:
                self.errors.append("Unexpected Status.")
        return self.response()

    def validate_requiry_field(self) -> bool:
        REQUIRED_FIELDS = ["status", "qir_date","goods_inward_note"]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
                return False
        if self.data.get("id"):
            self.qir = QualityInspectionReport.objects.filter(id=self.data.get("id")).first()
            if not self.qir:
                self.errors.append("QIR not found.")
                return False
        else:
            if self.status in ["Checked", "Canceled"]:
                self.errors.append(f"Quality Inspection Report id is missing.")
                return False
        return True

    def validate_numbering(self) -> bool:
        # Numbering Series validation
        conditions = {'resource': 'Quality Inspection Report', 'default': True}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        return True
    
    def update_status_instance(self) -> bool:
        status_obj = CommanStatus.objects.filter(name=self.status, table="QIR").first()
        if not status_obj:
            self.errors.append(f"Status '{self.status}' is not configured in CommanStatus.")
            return False
        self.data["status"] = status_obj.id
        self.status_obj = status_obj
        return True

    def validate_item_detail(self) -> bool:
        instance_list = []
        item_details = self.data.get('quality_inspections_report_item_detail_id',[])
        item_labels = []
        if len(item_details) == 0:
            self.errors.append("At least one Item Details is Required.")
            return False
        itemmaster_ids = [data.get("goods_inward_note_item") for data in item_details]
        # Detect duplicates
        duplicates = set([x for x in itemmaster_ids if itemmaster_ids.count(x) > 1])

        if duplicates:
            self.errors.append(f"Duplicate items found for item Details")
            return False
        for item in item_details:
            goods_inward_note_item = GoodsInwardNoteItemDetails.objects.filter(id=item.get("goods_inward_note_item")).first()
            if not goods_inward_note_item:
                self.errors.append(f"GIN ID {item.get('goods_inward_note_item')} not found.")
                return False
            itemmaster = goods_inward_note_item.item_master
            item_labels.append(str(itemmaster))
            for field in ["accepted", "rejected", "rework","checked_by"]:
                if item.get(field) is None:
                    self.errors.append(f"{itemmaster} → {field} is required.")
            if not goods_inward_note_item.qc:
                self.errors.append(f"{itemmaster} → qc is not enable.")
            if item.get("id"):
                instance = QualityInspectionsReportItemDetails.objects.filter(id=item.get("id")).first()
                if not instance:
                    self.errors.append(f"Item ID {item.get('id')} not found.")
                    return False
                instance_list.append(instance)
            else:
                instance_list.append(None)  # for new items being created
        item_result = validate_common_data_and_send_with_instance(
            item_details, instance_list,
            QualityInspectionsReportItemDetailsSerializer,
            item_labels,
            self.info.context
        )
        if item_result.get('error') and len(item_result.get('error')) > 0:
            self.errors.extend(item_result.get('error'))
            return False
        self.item_details_instances.extend(item_result.get("instance"))
        return True

    def save_item_details(self) ->bool:
        item_detail_ids = []
        try:
            for serializer in self.item_details_instances:
                if serializer:
                    serializer.save()
                
                    item_detail_ids.append(serializer.instance.id)
            self.data['quality_inspections_report_item_detail_id'] = item_detail_ids
            return True
        except Exception as e:
            self.errors.append(f"Error saving item details: {e}")
            return False
    
    def save_qir(self) -> bool:
        try:
            
            serializer = QualityInspectionReportSerializer(self.qir, data=self.data, partial=True, context={'request': self.info.context}) if self.qir else QualityInspectionReportSerializer(data=self.data, partial=True, context={'request': self.info.context})
            
            if serializer.is_valid():
                if self.status == "Pending":
                    gin_obj = GoodsInwardNote.objects.filter(id=self.data.get("goods_inward_note")).first() 
                    if self.data.get("id") != None:
                        if not gin_obj.quality_inspection_report_id:
                            self.errors.append(f"{gin_obj.gin_no.linked_model_id} -> Quality Inspection Report is missing..")
                            return False
                        if int(gin_obj.quality_inspection_report_id.id) !=  int(self.data.get("id")): 
                            self.errors.append(f'{gin_obj.gin_no.linked_model_id} this gin is already linked with other qc {gin_obj.quality_inspection_report_id.qir_no.linked_model_id}.')
                            return False
                    else: 
                        if gin_obj.quality_inspection_report_id and gin_obj.quality_inspection_report_id.id:
                            self.errors.append(f'This gin is already linked with other qc {gin_obj.quality_inspection_report_id.qir_no.linked_model_id}.')
                            return False
                
                serializer.save()
                self.qir = serializer.instance
                gin = self.qir.goods_inward_note
                gin.quality_inspection_report_id = self.qir
                gin.save()
                self.success = True
                return True
            else:
                self.errors.extend([
                    f"{field} → {', '.join(map(str, messages))}"
                    for field, messages in serializer.errors.items()
                ])
                return False
        except Exception as e:
            self.errors.append(f"An exception occurred Error saving QIR: {str(e)}")
            return False
    
    def final_validation_itemdetails(self) -> bool:
        if self.qir and self.qir.goods_inward_note and self.qir.goods_inward_note.purchase_order_id and  self.qir.goods_inward_note.purchase_order_id.scrap_reject_store_id:
            self.reject_store = self.qir.goods_inward_note.purchase_order_id.scrap_reject_store_id
            if not self.reject_store:
                self.errors.append("Reject Store Not Found.")
            
            if  self.reject_store.matained or self.reject_store.conference:
                self.errors.append(
                    f"{self.reject_store.store_name} - Keep Stock must be False and Conference must be False."
                )
        if self.qir.quality_inspections_report_item_detail_id.exists():
            for item in self.qir.quality_inspections_report_item_detail_id.all():
                purchase_conversion_factor = item.goods_inward_note_item.purchase_order_parent.conversion_factor
                received = Decimal(f"{item.goods_inward_note_item.received/purchase_conversion_factor : .3f}")
                
                if (received or 0) != (item.accepted or 0) + (item.rejected or 0) + (item.rework or 0):
                    self.errors.append(
                        f"{item.goods_inward_note_item.item_master} -> Accepted {item.accepted or 0}, "
                        f"Rejected {item.rejected or 0}, Rework {item.rework or 0} not equal to GIN received "
                        f"{received or 0}."
                    )
                    return False

            if self.qir.goods_inward_note:
                gin_qc_true_count = self.qir.goods_inward_note.goods_receipt_note_item_details_id.filter(qc=True).count()
                qc_item_count = self.qir.quality_inspections_report_item_detail_id.count()
                if gin_qc_true_count != qc_item_count:
                    self.errors.append(
                        f"GIN QC item count is {gin_qc_true_count}. This QC count is {qc_item_count}. Both are mismatched."
                    )
                    return False
            return True
        else:
            self.errors.append("QIR Item details are missing.")
            return False

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
            return batch_serializer.save()
        else:
            self.errors.append(f"Batch creation failed for '{batch_name}': {batch_serializer.errors}")
            return None

    def get_or_create_serial(self, serial_number):
        serial_instance = SerialNumbers.objects.filter(serial_number=serial_number).first()
        if serial_instance:
            return serial_instance

        serial_data = {
            "serial_number": serial_number
        }

        serial_serializer = SerialNumbersSerializer(data=serial_data)
        if serial_serializer.is_valid():
            return serial_serializer.save()
        else:
            self.errors.append(f"Serial creation failed for '{serial_number}': {serial_serializer.errors}")
            return None

    def is_serial_in_stock(self, serial_id, part_id):
        return ItemStock.objects.filter(serial_number__id=serial_id, part_number__id=part_id).exists()

    def get_serial_number(self, itemmaster_obj, qty):
        start_number = self.qir.reject_last_serial if self.qir.reject_last_serial is not None else 1
        prefix_text = self.qir.qir_no.linked_model_id
        last_serial_number = int(start_number) + int(qty)
        new_serial_instance = []
        for i in range(start_number, last_serial_number):
            serial = f"{prefix_text}-{str(i)}"
            existing_serial = SerialNumbers.objects.filter(serial_number=serial).first()
            if existing_serial:
                if self.is_serial_in_stock(existing_serial.id, itemmaster_obj.id):
                    self.errors.append(f"Serial '{serial}' already exists in stock.")
                    return None
                new_serial_instance.append(existing_serial)
            else:
                created_serial = self.get_or_create_serial(serial)
                if not created_serial:
                    self.errors.append(f"Failed to create serial '{serial}'.")
                    return None
                new_serial_instance.append(created_serial)
        return {"new_serial" : new_serial_instance, "last_serial": last_serial_number}

    def add_reject_stock(self) -> bool:
        transaction_model = "Quality Inspection report"
        saveing_user = self.info.context.user
        for item in self.qir.quality_inspections_report_item_detail_id.all():
            uom = None
            rate = 0
            if item.rejected >0 :
                self.total_reject_qty +=item.rejected
                itemmaster = item.goods_inward_note_item.item_master
                if item.goods_inward_note_item.purchase_order_parent and item.goods_inward_note_item.purchase_order_parent.uom:
                    uom = item.goods_inward_note_item.purchase_order_parent.uom
                    rate = item.goods_inward_note_item.purchase_order_parent.rate
                display_id = self.qir.qir_no.linked_model_id
                display_name = "Quality Inspection Report"
                if itemmaster.batch_number: 
                    batch_obj = self.get_or_create_batch(itemmaster.id, display_id)
                    batch = AddStockDataService(part_code = itemmaster, store = self.reject_store,  qty= item.rejected, unit = uom,
                                                        transaction_model= transaction_model,transaction_id=self.data.get("id"),
                                                        saved_by=saveing_user,
                                                        display_id= display_id,
                                                        display_name= display_name,
                                                        rate = rate,
                                                        batch= batch_obj,
                                                        conference = None)
                    batch.add_batch_stock()
                    if batch.success:
                        item.reject_stock_is_added = True
                        item.save()
                    else:
                        self.errors.extend(batch.errors)
                        return False 
                elif itemmaster.serial: 
                    serial_obj = self.get_serial_number(itemmaster, item.rejected) 
                    if serial_obj.get("new_serial") and len(serial_obj.get("new_serial")) > 0:
                        self.last_serial = serial_obj.get("last_serial") 
                        serial = AddStockDataService(part_code=itemmaster,
                                                    store=self.reject_store,
                                                    serials=serial_obj.get("new_serial"),
                                                    qty=item.rejected,
                                                    unit=uom,
                                                    transaction_model=transaction_model,
                                                    transaction_id= self.data.get("id"),
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = rate,
                                                    conference = None)
                        serial.add_serial_stock() 
                        if serial.success:
                            item.reject_stock_is_added = True
                            item.save()
                        else:
                            self.errors.extend(serial.errors)
                            return False
                    else:
                        self.errors.extend(f"{itemmaster} - New serial is Missing.")
                        return False
                else:
                    nobatch_noserial = AddStockDataService(part_code=itemmaster, store=self.reject_store, qty=item.rejected, unit=uom,
                                                            transaction_model=transaction_model,
                                                            transaction_id= self.data.get("id"),
                                                            saved_by = saveing_user,
                                                            display_id= display_id,
                                                            display_name= display_name,
                                                            rate = rate,
                                                            conference = None)
                    nobatch_noserial.add_non_tracked_stock()
                    if nobatch_noserial.success:
                        item.reject_stock_is_added = True
                        item.save()
                    else:
                        self.errors.extend(nobatch_noserial.errors)
                        return False
        return True
    
    def update_purchase_inward_percentage(self) ->bool:
        
        try:
            purchase = self.qir.goods_inward_note.purchase_order_id
            purchase_total_reject_qty = self.total_reject_qty

            # --- 1. Total rejected qty from QIR ---
            gin_list = purchase.goodsinwardnote_set.all()
            purchase_total_reject_qty += sum(
                                    (item.rejected or 0)
                                    for gin in gin_list if gin and gin.status.name == "Submit" and gin.quality_inspection_report_id and  gin.quality_inspection_report_id.status.name == "Checked"
                                    for item in gin.quality_inspection_report_id.quality_inspections_report_item_detail_id.all()
                                )
            
            # --- 2.Total  purchase qty ---
            grn_total_qty = purchase_total_reject_qty
            purchase_total_qty = purchase.item_details.aggregate(total=Sum("po_qty"))["total"] or 0
            
            # --- 3. GIN → GRNs (get total ) ---
            gins = GoodsInwardNote.objects.filter(purchase_order_id = purchase)
            
            for gin_instance in gins:
                grn_instance = gin_instance.grn
                if grn_instance and grn_instance.status and grn_instance.status.name == "Received":
                    grn_total_qty += sum(item.qty or 0 for item in grn_instance.goods_receipt_note_item_details.all())

            # --- 4. Calculate inward percentage ---
            inward_percentage = (grn_total_qty/purchase_total_qty)*100 if purchase_total_qty else 0

            # --- 5. Save purchase & GRN ---
            purchase.inward_percentage = Decimal(inward_percentage)
            purchase.save()
            return True
        except Exception as e:
            self.errors.append(f"unexpected error occurred in inward percentage update-:{str(e)}")
            return False
        
    def validate_item_on_submit(self) ->bool:
        None_whole_number = []
        if self.qir:
            for item in self.qir.quality_inspections_report_item_detail_id.all():
                cf = (item.goods_inward_note_item.purchase_order_parent.conversion_factor or 1) if item.goods_inward_note_item and item.goods_inward_note_item.purchase_order_parent else 1
                if item.goods_inward_note_item.item_master.serial and  (item.accepted/cf) %1 != 0 and (item.rejected/cf) %1 != 0:
                    None_whole_number.append(item.goods_inward_note_item.item_master.item_part_code)

        if len(None_whole_number )> 0:
            self.errors.append(f"{', '.join(None_whole_number)} these serial item received quantity and rejected quantity must be whole number.")
            return False
        return True

    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "QIR": self.qir
        }
