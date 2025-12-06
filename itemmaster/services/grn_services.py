from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from itemmaster.Utils.stockAddtinons import *
from django.db.models import Max
import copy


class GrnService:
    def __init__(self, data: dict, status: str, info):
        self.data = data
        self.status = status
        self.success = False
        self.errors = []
        self.info = info
        self.grn = None
        self.status_obj = None
        self.item_details_instances = []
        self.old_item_details_ids = []
        self.state_of_company = None
    
    def process(self):
        with transaction.atomic():
            if self.status == "Draft":
                if not self.validate_required_fields(): return self.response()
                if not self.update_status_instance(): return self.response()
                if not self.validate_numbering(): return self.response()
                if not self.validate_item_details(): return self.response()
                if not self.save_item_details(): return self.response()
                if not self.save_grn(): return self.response()
                return self.response()
            elif self.status == "Received":
                if not self.validate_required_fields(): return self.response()
                if not self.update_status_instance(): return self.response()
                
                if not self.add_stock(): return self.response()

                if self.grn and self.grn.goods_inward_note and self.grn.goods_inward_note.purchase_order_id:
                    purchase = self.grn.goods_inward_note.purchase_order_id

                    # --- 1. Total rejected qty from QIR ---
                    gin_list = purchase.goodsinwardnote_set.all()
                    purchase_total_reject_qty = sum(
                                (item.rejected or 0)
                                for gin in gin_list if gin.status.name == "Submit" and  gin.quality_inspection_report_id
                                for item in gin.quality_inspection_report_id.quality_inspections_report_item_detail_id.all()
                            )

                    purchase_total_qty = purchase.item_details.aggregate(total=Sum("po_qty"))["total"] or 0

                    # --- 3. GRN received qty (start with rejects + current GRN items) ---
                    grn_total_qty = purchase_total_reject_qty
                    grn_total_qty += sum(grn_item.qty or 0 for grn_item in self.grn.goods_receipt_note_item_details.all())
                    # for grn_item in self.grn.goods_inward_note.goods_receipt_note_item_details_id.all():


                    # --- 4. Other GIN → GRNs (exclude current GRN to avoid double counting) ---
                    gins = GoodsInwardNote.objects.filter(purchase_order_id = purchase).exclude(id=self.grn.goods_inward_note.id)
                    for gin_instance in gins:
                        grn_instance = gin_instance.grn
                        if grn_instance and grn_instance.status and grn_instance.status.name == "Received":
                            grn_total_qty += sum(item.qty or 0 for item in grn_instance.goods_receipt_note_item_details.all())

                    # --- 5. Calculate inward percentage ---
 
                    inward_percentage = (grn_total_qty/purchase_total_qty)*100 if purchase_total_qty else 0

                    # --- 6. Save purchase & GRN ---
                    purchase.inward_percentage = Decimal(inward_percentage)
                    purchase.save()

                self.grn.status = self.status_obj
                self.grn.all_stock_added = True
                self.grn.save()
                self.success = True
                return self.response()
            else:
                self.errors.append(f"{self.status} Unexpected status.")
                return self.response()
    
    def validate_required_fields(self) -> bool:
        REQUIRED_FIELD = ['status',"grn_date","goods_inward_note"]
        for field in REQUIRED_FIELD:
            if self.data.get(field) is None:
                self.errors.append(f"{field} is required.")
                return False
        if self.data.get("id"):
            self.grn = GoodsReceiptNote.objects.filter(id=self.data.get("id")).first()
            if not self.grn:
                self.errors.append(f"{self.data.get('id')} is Not Found in Goods Receipt Note.")
                return False
        
        return True
    
    def update_status_instance(self) -> bool:
        status_obj = CommanStatus.objects.filter(name=self.status, table="GRN").first()
        if not status_obj:
            self.errors.append(f"Status '{self.status}' is not configured in CommanStatus.")
            return False
        self.data["status"] = status_obj.id 
        self.status_obj = status_obj
        return True

    def validate_numbering(self) -> bool:
        if not NumberingSeries.objects.filter(resource='Goods Receipt Note', default=True).exists():
            self.errors.append("Default GRN numbering series is not configured.")
            return False
        return True
    
    def validate_item_details(self) -> bool:
        try:
            item_details = self.data.get('goods_receipt_note_item_details', []) 
            if not item_details:
                self.errors.append("At least one Item Detail is required.")
                return False
            instance_list = []
            item_labels = []
            itemmaster_ids = [item.get("gin") for item in item_details]
            duplicates = set([x for x in itemmaster_ids if itemmaster_ids.count(x) > 1])
            if duplicates:
                self.errors.append("Duplicate items found in Item Details.")
                return False 
            for item in item_details: 
                item_gin = GoodsInwardNoteItemDetails.objects.filter(id=item.get("gin")).first()
                qty = item.get("qty")
                if not item_gin:
                    self.errors.append(f"GRN item ID {item_gin} not found.")
                    return False
                purchase_item_instance = item_gin.purchase_order_parent
                itemmaster = item_gin.item_master
                item_labels.append(str(itemmaster))
                for field in ["gin", "qty","conversion_factor","base_qty"]:
                    if item.get(field) is None or item.get(field) == 0 :
                        self.errors.append(f"{itemmaster.item_part_code} → {field} is required.")
                        return False 
                # if item_gin.qc:
                #     qc_detail = item_gin.qualityinspectionsreportitemdetails_set.last()
                    
                #     if not qc_detail:
                #         self.errors.append(f"No QC details found for {itemmaster.item_part_code}.")
                #         return False
                #     if purchase_item_instance:
                #         qc_qty = qc_detail.accepted
                #         print("qc_qty", qc_qty)
                #         qc_qty = Decimal(f"{qc_qty/purchase_item_instance.conversion_factor:.3f}")
                #         print("qc_qtycf", qc_qty)
                #         print(qc_qty , qty)
                #         if qc_qty != qty:
                #             self.errors.append(f"{itemmaster.item_part_code} → Qc accepted qty{qc_qty} did not match with this qty {qty}.")
                #             return False
                # else:  
                #     received_qty = item_gin.received 
                #     if received_qty !=  qty:
                #         self.errors.append(f"{itemmaster.item_part_code} → Gin accepted qty{received_qty} did not match with this qty{qty}.")
                #         return False
                if itemmaster.batch_number:
                    item['serial_number'] = None
                    if not item.get("batch_number"):
                        self.errors.append(f"{itemmaster.item_part_code} -> Batch Number is required")
                elif itemmaster.serial:
                    item['batch_number'] = None
                    

                    if not itemmaster.serial_auto_gentrate:
                        serial = item.get("serial_number", [])
                        delimiter = ',' if ',' in serial else '\n'

                        # Split, strip whitespace, and remove empty strings
                        serial_numbers = [s.strip() for s in serial.split(delimiter) if s.strip()]
 
                        if not serial_numbers:
                            self.errors.append(f"Serial numbers are required for {itemmaster.item_part_code}.")
                            return False
                        
                        if len(serial_numbers) != item.base_qty:
                            self.errors.append(f"Serial numbers must be equal to Conversion QTY {itemmaster.item_part_code}.")
                            return False
                        if len(serial_numbers) > 0:
                            item['serial_number'] = item.get("serial_number", '')
                        else:
                            item['serial_number'] = None
                    else:
                        item['serial_number'] = None
                else:
                    if item.get("batch_number") or item.get("serial_number"):
                        self.errors.append(
                            f"Serial or Batch number not required for {itemmaster.item_part_code}."
                        )
                        return False
                if item.get("id"):
                    instance = GoodsReceiptNoteItemDetails.objects.filter(id=item.get("id")).first()
                    if not instance:
                        self.errors.append(f"Item ID {item.get('id')} not found.")
                        return False
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
            
            item_result = validate_common_data_and_send_with_instance(
                item_details, instance_list,
                GoodsReceiptNoteItemDetailSerializer,
                item_labels, self.info.context
            ) 
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            self.item_details_instances.extend(item_result.get("instance"))
            return True
        except Exception as e:
            self.errors.append(f"An exception error occurred in validate item- {str(e)}")

    def save_item_details(self) ->bool:
        item_detail_ids = []
        try:
            for serializer in self.item_details_instances:
                if serializer and serializer.is_valid():
                    serializer.save()
                    item_detail_ids.append(serializer.instance.id)
            self.data['goods_receipt_note_item_details'] = item_detail_ids
            return True
        except Exception as e:
            self.errors.append(f"Error saving item details: {e}")
            return False

    def save_grn(self) ->bool:
        try:
            serializer = GoodsReceiptNoteSerializer(self.grn, data=self.data, partial=True, context={'request': self.info.context}) if self.grn else \
            GoodsReceiptNoteSerializer(data=self.data, partial=True, context={'request': self.info.context})
            if serializer.is_valid():
                serializer.save()
                self.grn = serializer.instance
                gin = self.grn.goods_inward_note
                gin.grn = self.grn
                gin.save()
                self.success = True
                return True
            else:
                for field, field_errors in serializer.errors.items():
                    for err in field_errors:
                        self.errors.append(f" {field}: {err}")
            return False
        except Exception as e:
            self.errors.append(f"An exception error occurred grn save- {str(e)}")
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

    def is_serial_in_stock(self, serial_id, part_id):
        return ItemStock.objects.filter(serial_number__id=serial_id, part_number__id=part_id).exists()

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

    def generate_serial_number(self, start_number, prefix, qty, part_id):
        
        try:
            prefix_parts = prefix.split("#")
            prefix_text = prefix_parts[0]
            padding_length = int(prefix_parts[1])
            last_serial_number = int(int(start_number) + qty) 
        except (IndexError, ValueError):
            self.errors.append("Invalid prefix format. Use format like 'ABC#3'.")
            return False

        new_serial_instance = []
        for i in range(start_number, last_serial_number):
            serial = f"{prefix_text}{str(i).zfill(padding_length)}"

            existing_serial = SerialNumbers.objects.filter(serial_number=serial).first()

            if existing_serial:
                if self.is_serial_in_stock(existing_serial.id, part_id):
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

    def findUomIsInAlterUom(self, itemMaster, uom, qty) -> int:
        mainUom = itemMaster.item_uom
        alterUom = itemMaster.alternate_uom.all()
        if mainUom.id == uom:
            return 0 , mainUom
        else:
            for singleUOM in alterUom:
                if singleUOM.addtional_unit.id == uom:
                    return int(qty) * int(singleUOM.conversion_factor), mainUom

    # def validate_uom_variation_value(self):
    #     try:
    #         for item in self.grn.rework_delivery_challan_item_details.all():
    #             item_master = item.gin.item_master
    #             purchase_item = item.gin.purchase_order_parent

    #             if purchase_item.uom != purchase_item.po_uom:
    #                 alter_uom= item_master.alternate_uom.filter(id=purchase_item.po_uom).first()
    #                 if not alter_uom:
    #                     self.errors.append(f"{item_master.item_part_code} purchase uom not found in alternate UOM.")
    #                     continue

    #                 if not alter_uom.conversion_factor:
    #                     self.errors.append(f"{item_master.item_part_code} Conversion Factor is missing or invalid.")
    #                     continue

    #                 if not alter_uom.variation:
    #                     self.errors.append(f"{item_master.item_part_code} purchase uom variation is missing.")
    #                     continue

    #                 variations_value = (alter_uom.variation or 0)
    #                 convertions_value = (alter_uom.conversion_factor or 0)
                    
    #                 min_value = Decimal(convertions_value)/100 * variations_value
    #                 max_value = Decimal(convertions_value)/100 * variations_value
    #                 conversion_factor = item.conversion_factor
    #                 if not (min_value <= conversion_factor <= max_value):
    #                     self.errors.append(
    #                         f"{item_master.item_part_code} conversion factor {conversion_factor} is out of allowed range "
    #                         f"({min_value:.2f} - {max_value:.2f}).")
    #         if self.errors:
    #             return False
            
    #         return True
    #     except Exception as e:
    #         self.errors.append(f"Unexpeted error occurred  {str(e)}")
    #         return False

    def add_stock(self) ->bool:
        transaction_model= "Goods Receipt Note"
        saveing_user = self.info.context.user
        display_id = self.grn.grn_no.linked_model_id
        display_name = "Goods Receipt Note"
        item_details = self.grn.goods_receipt_note_item_details.all()
        store_id = None
        if self.grn.goods_inward_note and self.grn.goods_inward_note.purchase_order_id and self.grn.goods_inward_note.purchase_order_id.receiving_store_id.id:
            store_id = self.grn.goods_inward_note.purchase_order_id.receiving_store_id
        else:
            self.errors.append("Check Store for this module.")
            return False
        
        try:

            for item in item_details:
                itemmaster = item.gin.item_master 
                
                qty = item.qty
                need_to_add_qty = item.base_qty
                if need_to_add_qty <=0:
                    continue
                purchase_item = None
                uom = itemmaster.item_uom
                rate = None
                if item.gin and item.gin.purchase_order_parent.rate: 
                    rate = item.gin.purchase_order_parent.rate
                else:
                    self.errors.append("check purchase rate for in {itemmaster}.")
                    return False
                if item.gin.purchase_order_parent:
                    purchase_item = item.gin.purchase_order_parent

                if not itemmaster.keep_stock and not item.stock_added :
                    item.stock_added = True
                    item.save()
                    if purchase_item:
                        purchase_item.accepted_qty = (purchase_item.accepted_qty or 0) + qty
                        purchase_item.save()
                    continue
                

                if not item.stock_added:
                    if item.batch_number:
                        batch_obj = self.get_or_create_batch(itemmaster.id, item.batch_number)
                        if batch_obj:
                            batch = AddStockDataService(part_code = itemmaster, store = store_id,  qty= need_to_add_qty, unit = uom,
                                                        transaction_model= transaction_model,transaction_id=self.data.get("id"),
                                                        saved_by=saveing_user,
                                                        display_id= display_id,
                                                        display_name= display_name,
                                                        rate = rate,
                                                        batch= batch_obj,
                                                        conference = None)
                            batch.add_batch_stock()
                            if batch.success:
                                item.stock_added = True
                                item.save()
                            else:
                                self.errors.extend(batch.errors)
                                return False
                        else:
                            return False
                    elif itemmaster.serial:
                        if itemmaster.serial_auto_gentrate:
                            latest = (
                                ItemStock.objects
                                .filter(part_number__id=itemmaster.id)
                                .annotate(last_serial_as_int=Cast('last_serial_history', IntegerField()))
                                .aggregate(max_serial=Max('last_serial_as_int'))
                            )
 
                            
                            max_last_serial_history = latest.get("max_serial", 1)
                            latest_stock = max_last_serial_history if max_last_serial_history else itemmaster.serial_starting 
                            
                            serial_obj = self.generate_serial_number(int(latest_stock),itemmaster.serial_format, need_to_add_qty, itemmaster.id)
                            new_serial_instance = serial_obj.get("new_serial")
                            

                            
                            if serial_obj.get("new_serial") and len(serial_obj.get("new_serial")) > 0:
                                serial = AddStockDataService(part_code=itemmaster, 
                                                        store=store_id,
                                                        serials=new_serial_instance.copy(),
                                                        qty=need_to_add_qty,
                                                        unit=uom,
                                                        transaction_model=transaction_model,
                                                        transaction_id= self.data.get("id"),
                                                        saved_by = saveing_user,
                                                        display_id= display_id,
                                                        display_name= display_name,
                                                        rate = rate,
                                                        laster_serial = serial_obj.get("last_serial"),
                                                        conference = None)
                                serial.add_serial_stock() 
                                if serial.success: 
                                    item.stock_added = True
                                    item.serial_number= ", ".join(single_serial.serial_number for single_serial in new_serial_instance)
                                    
                                    item.save()
                                else:
                                    self.errors.extend(serial.errors)
                                    return False
                            else:
                                return False
                        else:
                            serial_list_instance = []
                            serial_text = item.serial_number
                            delimiter = ',' if ',' in serial_text else '\n'
                            
                            # Split, strip whitespace, and remove empty strings
                            serial_number_list = [s.strip() for s in serial_text.split(delimiter) if s.strip()]
                            # serial_number_list = [serial.strip() for serial in item.serial_number.split(",") if serial.strip()]
                            for serial_num in serial_number_list:
                                existing_serial = SerialNumbers.objects.filter(serial_number=serial_num).first()
                                if existing_serial:
                                    if self.is_serial_in_stock(existing_serial.id,itemmaster.id ):
                                        self.errors.append(f"{serial_num} already exists in stock.")
                                        return False
                                    serial_list_instance.append(existing_serial)
                                else:
                                    new_serial = self.get_or_create_serial(serial_num)
                                    if new_serial:
                                        serial_list_instance.append(new_serial)
                                    else:
                                        return False 
                            serial = AddStockDataService(part_code=itemmaster, 
                                                        store=store_id,
                                                        serials=serial_list_instance,
                                                        qty=need_to_add_qty,
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
                                item.stock_added = True
                                item.save()
                            else:
                                self.errors.extend(serial.errors)
                                return False
                    else:
                        nobatch_noserial = AddStockDataService(part_code=itemmaster, store=store_id, qty=need_to_add_qty, unit=uom,
                                                            transaction_model=transaction_model,
                                                            transaction_id= self.data.get("id"),
                                                            saved_by = saveing_user,
                                                            display_id= display_id,
                                                            display_name= display_name,
                                                            rate = rate,
                                                            conference = None)
                        nobatch_noserial.add_non_tracked_stock()
                        if nobatch_noserial.success:
                            item.stock_added = True
                            item.save()
                        else:
                            self.errors.extend(nobatch_noserial.errors)
                            return False
                    if purchase_item:
                        purchase_item.accepted_qty = (purchase_item.accepted_qty or 0) + qty
                        purchase_item.save()
                
            return True
        except Exception as e:
            self.errors.append(f"Unexpeted error {str(e)}.")
            return False
    
 
    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "grn": self.grn
        }



class GrnCancelService:
    def __init__(self, id: int, info):
        self.id = id
        self.success = False
        self.errors = []
        self.info = info
        self.grn = None
        self.status_obj = None
        self.store = None
    
    def Process(self):
        with transaction.atomic():
            if not self.validate_required_fields() : return self.response()
            if not self.update_status_instance() : return self.response()
            if not self.get_grn() : return  self.response()
            return self.response()

    def validate_required_fields(self) -> bool:
      
        if self.id:
            self.grn = GoodsReceiptNote.objects.filter(id=self.id).first()
            if not self.grn:
                self.errors.append(f"{self.id} is Not Found in Goods Receip Note.")
                return False
        return True
    
    def update_status_instance(self) -> bool:
        status_obj = CommanStatus.objects.filter(name="Canceled", table="GRN").first()
        if not status_obj:
            self.errors.append(f"Status Canceled is not configured in CommanStatus.")
            return False 
        self.status_obj = status_obj
        return True
    
    def validate_stock(self, qty, stock_data_existing_list):
        required_qty = qty
        total_current_stock = sum(single_stock.current_stock or 0 for single_stock in stock_data_existing_list)
        
        actual_stock = (total_current_stock or 0)
        balance = actual_stock - required_qty
        return balance >= 0, balance
            
    def check_the_stock(self):
        try:
            self.store = self.grn.goods_inward_note.purchase_order_id.receiving_store_id
            if  not self.store:
                self.errors.append("Receiving store is missing.")
                return False
            
            for item in self.grn.goods_receipt_note_item_details.all():
                itemmaster = item.gin.item_master
                if not itemmaster.keep_stock:
                    continue


                if not item.stock_added:
                    continue
                
                
                need_to_add_qty = item.base_qty
                if need_to_add_qty <=0:
                    continue
                
                stock_data_existing_list = ItemStock.objects.filter(
                                                part_number=itemmaster,
                                                store=self.store,
                                                batch_number__batch_number_name=item.batch_number if item.batch_number else None)
                
                if not stock_data_existing_list:
                    self.errors.append(f"{itemmaster} {item.batch_number or ''} is not available.")
                    return False
                is_sufficient, balance_stock = self.validate_stock(need_to_add_qty, stock_data_existing_list)
                if not is_sufficient:
                    self.errors.append(
                        f"The item {itemmaster} {f'batch: {item.batch_number}' if item.batch_number   else ''} "
                        f"is not available. Required quantity shortfall: {abs(balance_stock)}."
                    )
                    return False
                if item.serial_number:
                    current_serial_ids = set(
                        id
                        for single_stock in stock_data_existing_list
                        for id in single_stock.serial_number.values_list("id", flat=True)
                    )
                    serial_text = item.serial_number
                    delimiter = ',' if ',' in serial_text else '\n'
                    list_numbering_serial = [s.strip() for s in serial_text.split(delimiter) if s.strip()]
                    
                    serial_objecs =SerialNumbers.objects.filter(serial_number__in=list_numbering_serial).values_list("id","serial_number")
                    missing_serials = [
                                serial_number for serial_id, serial_number in serial_objecs if serial_id not in current_serial_ids
                            ]
                    if missing_serials:
                        self.errors.append(
                            f"The following serial numbers for {itemmaster} are not in current stock: {', '.join(missing_serials)}"
                        )
                        return False
            return True
        except Exception as e:
            self.errors.append(f"An exception error occurred in stock check {str(e)}")
            return False
        
    def stock_reduce(self):
        try:
            all_success = True 
            for item in self.grn.goods_receipt_note_item_details.all():
                batch_instance = None
                purchase = item.gin.purchase_order_parent
                itemmaster= purchase.item_master_id
                qty = (item.qty or 0)
                need_to_add_qty = (item.base_qty or 0)
                if need_to_add_qty <=0:
                    continue
                
                if not itemmaster.keep_stock and item.stock_added :
                    item.stock_added = True
                    item.save()
                    if purchase:
                        if (purchase.accepted_qty or 0) >= qty:
                            purchase.accepted_qty = purchase.accepted_qty-qty
                        else:
                            purchase.accepted_qty = 0
                        purchase.save()
                    continue
                
                if not item.stock_added:
                        continue
                list_numbering_serial = []
                serial_ids = []
                serial_text = item.serial_number
                if serial_text:
                    delimiter = ',' if ',' in serial_text else '\n'
                    # Split, strip whitespace, and remove empty strings
                    list_numbering_serial = [s.strip() for s in serial_text.split(delimiter) if s.strip()]

                if list_numbering_serial:
                    serial_ids =SerialNumbers.objects.filter(serial_number__in=list_numbering_serial).values_list("id", flat=True)
                
                if item.batch_number:
                    batch_instance = BatchNumber.objects.filter(
                            part_number=item.gin.item_master,
                            batch_number_name=item.batch_number
                        ).first()
                    if not batch_instance:
                        self.errors.append(f"{batch_instance} not Found.")
                itemmaster = item.gin.item_master
                stockReduce = StockReduce(
                                    partCode_id=itemmaster.id,
                                    Store_id=self.store.id,
                                    batch_id=batch_instance.id if batch_instance and item.batch_number else None,
                                    qty=need_to_add_qty,
                                    serial_id_list=serial_ids,
                                    partCode = itemmaster,
                                    batch = batch_instance.batch_number_name if batch_instance and item.batch_number else None)
                if item.batch_number:
                    result = stockReduce.reduceBatchNumber()
                elif serial_ids:
                    result = stockReduce.reduceSerialNumber()
                else:
                    result = stockReduce.reduceNoBatchNoSerial()
                
                if purchase:
                    if (purchase.accepted_qty or 0) >= qty:
                        purchase.accepted_qty = purchase.accepted_qty-qty
                    else:
                        purchase.accepted_qty = 0
                    purchase.save()

                if result['success']:
                    item.stock_added = False
                    item.save()
                else:
                    self.errors.append(result["error"])
                    all_success = False
                    return False
            historys = StockHistory.objects.filter(transaction_module="Goods Receipt Note", transaction_id=self.id)
            for history in historys:
                history.is_delete = True
                history.save()
            return all_success
        except Exception as e:
            self.errors.append(f"An exception error occurred in stock reduce {str(e)}")
            return False
        
    def purchase_update(self):
        
        try:
            purchase_total_qty = 0
            grn_total_qty = 0
            purchase = self.grn.goods_inward_note.purchase_order_id
            
            for purchase_item in purchase.item_details.all():
                purchase_total_qty += (purchase_item.po_qty or 0)
            
            gins = GoodsInwardNote.objects.filter(purchase_order_id__id = purchase.id)
            
            for gin_instance in gins:
                grn_instance = gin_instance.grn
                if grn_instance:
                    if grn_instance.id != self.grn.id:
                        if grn_instance and grn_instance.status.name == "Received" :
                            for item in grn_instance.goods_receipt_note_item_details.all():
                                grn_total_qty += (item.qty or 0)
            inward_persentage = (grn_total_qty/purchase_total_qty)*100 if purchase_total_qty else 0
            purchase.inward_percentage = Decimal(inward_persentage)
            purchase.save()
            return True
        except Exception as e:
            self.errors.append(f"An exception error occurred in purchase inward percentage {str(e)}")
            return False

    def get_grn(self) -> bool:
        if not self.grn:
            self.errors.append(f"{self.id} GRN is not found.")
            return False
        if self.grn.status.name == "Draft":
            self.grn.status = self.status_obj
            self.grn.save()
            self.success = True
            return True
        elif self.grn.status.name == "Received":
            if not self.check_the_stock():
                return False 
            if not self.stock_reduce():
                return False
            if not self.purchase_update():
                return False
            self.grn.status = self.status_obj
            self.grn.all_stock_added = False
            self.grn.save()
            self.success = True
            return True
        elif self.grn.status.name == "Canceled":
            self.errors.append("This Goods Receipt Note is already canceled.")
            return False
        else:
            self.errors.append("This Goods Receipt Note unexpected status inform to admin.")
            return False
        
    def response(self) -> dict:
        return {
            "success": self.success,
            "errors": self.errors,
            "grn": self.grn
        }
    

def grn_general_update(data):
    valid_serializers = []
    errors = []
    debit = data.get("debit", {})
    credits = data.get("credits", [])
    credits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "goods_receipt_note_no", "account", "created_by"]

    """Process credits"""
    for idx, credit in enumerate(credits):
        for field in REQUIRED_FIELDS + ["credit"]:
            if credit.get(field) in [None, ""]:
                errors.append(f"credit[{idx}] → '{field}' is required.")
        credits_amount += Decimal(str(credit.get("credit", 0)))
        serializer = AccountsGeneralLedgerSerializer(data=credit)

        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"credit[{idx}] → {field}: {'; '.join([str(e) for e in error])}")
        else:
            valid_serializers.append(serializer)
    
    """Process debit"""
    for field in REQUIRED_FIELDS + ["debit"]:
        if debit.get(field) in [None, ""]:
            errors.append(f"Debit → '{field}' is required.")
   
    serializer = AccountsGeneralLedgerSerializer(data=debit)
 
    if not serializer.is_valid():
        
        for field, error in serializer.errors.items():
            errors.append(f"Credit → {field}: {'; '.join([str(e) for e in error])}")
    else:
        valid_serializers.append(serializer)
    
    # Compare amounts
    debit_amount = Decimal(str(debit.get("debit", 0)))
    if debit_amount != credits_amount:
        errors.append(f"Debit amount ({debit_amount}) and credit amount ({credits_amount}) do not match.")
 
    if errors:
        return {"success": len(errors)== 0 , "errors":errors} 
    
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return  {"success": True , "errors":errors}