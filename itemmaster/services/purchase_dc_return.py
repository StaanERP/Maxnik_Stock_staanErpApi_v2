from itemmaster.models import *
from itemmaster.serializer import *
from itemmaster.Utils.CommanUtils import *
from itemmaster.schema import *


class ReworkDeliveryService:
    def __init__(self, data, status, info):
        self.data = data
        self.status = status
        self.status_obj = None
        self.success = False
        self.errors = []
        self.info = info
        self.rework_delivery_service = None
        self.qc = None
        self.state_of_company = None
        self.total_rework_qty = 0
        self.item_details_instances = []
        self.old_item_details_ids = []

    def get_rework_delivery_challan(self): 
        qc = self.data.get("qc") 
        if 'id' in self.data and self.data.get("id"):
            self.rework_delivery_service = ReworkDeliveryChallan.objects.filter(id=self.data.get("id")).first()
            if not self.rework_delivery_service:
                self.errors.append("Rework Delivery Challan not found.")
                return False
            self.old_item_details_ids = list(self.rework_delivery_service.rework_delivery_challan_item_details.values_list("id",flat=True))
        
        
        
        if self.status == "Submit":
            self.state_of_company = company_info()
            state = self.rework_delivery_service.address.state
            amount_threshold = self.state_of_company.threshold_for_intrastate  if str(state).lower() == str(self.state_of_company.address.state).lower() else\
            self.state_of_company.threshold_for_interstate
            if self.data['net_amount'] >= int(amount_threshold):
                if not self.data.get('e_way_bill') or not self.data.get('e_way_bill_date'):
                    self.errors.append(f"Net Amount is more than {amount_threshold}. E-Way Bill and Date are required.")
                    return False

        
        if qc and self.status == "Draft":
            self.qc = QualityInspectionReport.objects.filter(id=qc).first()
            if self.qc:
                # self.total_rework_qty = sum((item.rework or 0)  for item in self.qc.quality_inspections_report_item_detail_id.all())
                if self.qc.rework_received and self.data.get("id") is None:
                    self.errors.append("Rework Delivery Challan is already exists.")
                    return False
            if not self.qc:
                self.errors.append("Quality Inspection Report not found.")
                return False
        elif qc and self.status in ["Submit", "Dispatch"]:
            pass
        else:
            self.errors.append("Quality Inspection Report is Required.")
            return False
        return True
    
    def update_status_instance(self):
        self.status_obj = CommanStatus.objects.filter(name=self.status, table="Rework Delivery Challan").first()
        
        if not self.status_obj:
            self.errors.append(f"Ask developer to add status '{self.status}' in CommanStatus.")
            return False
        self.data["status"] = self.status_obj.id 
        return True

    def validate_required_fields(self):
        REQUIRED_FIELDS = ["status", "dc_date", "address", "purchase_order_no"]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
        if len(self.errors) > 0:
            return False
        return True
        
    def validate_numbering(self):
        conditions = {'resource': 'Rework Delivery Challan', 'default': True}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        return True
    
    def validate_item_details(self):
        instance_list = []
        item_details = self.data.get('rework_delivery_challan_item_details', [])
        item_labels = []
        actual_get = 0
        try:
            if not item_details:
                self.errors.append("At least one Item Detail is required.")
                return False
        
            for item in item_details:
                qc_instance_item = QualityInspectionsReportItemDetails.objects.filter(id=item.get("qc_item")).first()
                if not qc_instance_item:
                    self.errors.append(f"{item.get('qc_item')} Item Detail instance not found.")
                    continue
                item_master = qc_instance_item.goods_inward_note_item.item_master
                item_labels.append(item_master.item_part_code)
                purchase_cf = qc_instance_item.goods_inward_note_item.purchase_order_parent.conversion_factor
                ITEM_REQUIRED_FIELDS = [
                "purchase_item" , "rework_qty", "amount", "qc_item"
                ]
                for field in ITEM_REQUIRED_FIELDS:
                    if item.get(field) is None:
                        self.errors.append(f'{item_master.item_part_code} → {field} is required.')
                if len(self.errors) > 0:
                    continue
                qc_obj = QualityInspectionsReportItemDetails.objects.filter(id=item.get("qc_item")).first()
                if not qc_obj:
                    self.errors.append(f'{item_master.item_part_code} in Quality Inspections Not Found.')
                    continue 
                qty_rework = Decimal(f"{qc_obj.rework/purchase_cf : .2f}")
                if qty_rework != Decimal(item.get("rework_qty", 0)):
                    self.errors.append(
                                f"{item_master.item_part_code}: Quantity mismatch. "
                                f"Expected rejected quantity {qty_rework}, but got {item.get('rework_qty', 0)}."
                            )
                    continue
                if item.get('id'):
                    instance = ReworkDeliveryChallanItemDetails.objects.filter(id=item.get("id")).first()
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                if item.get("rework_qty", 0) <= 0:
                    self.errors.append(f'{item_master.item_part_code} in retun QTY is zero not allowed.')
                    continue
                actual_get += item.get("rework_qty")
            # if self.total_rework_qty != actual_get:
            #     self.errors.append(f'QC retun QTY is {self.total_rework_qty} in entered Rework QTY is {actual_get} is miss match.')
            if len(self.errors) > 0:
                return False 
            item_result = validate_common_data_and_send_with_instance(
                item_details, instance_list, ReworkDeliveryChallanItemDetailsSerializer,
                item_labels, self.info.context
            )  
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            
            self.item_details_instances = item_result.get("instance")

            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False
        
    def save_item_details(self):
        item_detail_ids = []
        try: 
            for serializer in self.item_details_instances: 
                if serializer: 
                    serializer.save() 
                    item_detail_ids.append(serializer.instance.id) 
            self.data['rework_delivery_challan_item_details'] = item_detail_ids
            return True
        except Exception as e:
            self.errors.append(f"An exception occurred while saving item details: {str(e)}")
            return False
    
    def save_rework_delivery(self):
        try:
            serializer  = None 
            if self.rework_delivery_service:
                serializer = ReworkDeliveryChallanSerializer(self.rework_delivery_service, data=self.data, partial=True, context={'request': self.info.context} )
            else:
                serializer = ReworkDeliveryChallanSerializer( data=self.data, partial=True, context={'request': self.info.context} )
            if serializer and serializer.is_valid():
                serializer.save()
                self.rework_delivery_service = serializer.instance
                qc = self.rework_delivery_service.qc
                qc.rework_received = serializer.instance
                qc.save()
                deleteCommanLinkedTable(self.old_item_details_ids, list(self.rework_delivery_service.rework_delivery_challan_item_details.values_list("id",flat=True))
                                        ,purchaseOrderItemDetails)
                self.success = True
                return True
            else:
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                            for field, error in serializer.errors.items()])
                return False
        except Exception as e:
            self.errors.append(f"An exception error occurred while saving Rework Delivery Service  {str(e)}")
            return False
    
    def update_rework_qty(self):
        try:
            if not self.rework_delivery_service:
                self.errors.append("Rework Delivery not found.")
                return False

            purchase = self.rework_delivery_service.purchase_order_no
            if not purchase:
                self.errors.append("Related Purchase Order not found.")
                return False

            rework_qty = 0
            received_qty = 0

            # Always include the current RDC (not yet committed to DB as "Submit")
            for rdc_item in self.rework_delivery_service.rework_delivery_challan_item_details.all():
                purchase_item = rdc_item.purchase_item
                purchase_item.rework_retun_qty =  (purchase_item.rework_retun_qty or 0) + (rdc_item.rework_qty or 0)
                purchase_item.save()

                rework_qty += (rdc_item.rework_qty or 0)
                received_qty += (rdc_item.received_qty or 0)

            # Include all OTHER submitted RDCs of the purchase order
            for rdc in purchase.reworkdeliverychallan_set.filter(status__name="Submit").exclude(id=self.rework_delivery_service.id):
                for item in rdc.rework_delivery_challan_item_details.all():
                    rework_qty += (item.rework_qty or 0)
                    received_qty += (item.received_qty or 0)

            # percentage = (received_qty / rework_qty) * 100 if rework_qty > 0 else 0
            # purchase.rework_percentage = percentage
            purchase.save()
 
            self.rework_delivery_service.status = self.status_obj
            self.rework_delivery_service.save()

            self.success = True
            return True

        except Exception as e:
            self.errors.append(f"An exception error occurred while saving Purchase Rework Percentage: {str(e)}")
            return False

        
    def check_transportation_requirements(self):
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
        


    def process(self):
        with transaction.atomic():
            if self.status == "Draft":
                if not self.get_rework_delivery_challan():
                    return self.response()
                
                if not self.update_status_instance():
                    return self.response()

                if not self.validate_required_fields():
                    return self.response()
                
                if not self.validate_numbering():
                    return self.response()
                
                if not self.validate_item_details():
                    return self.response()
                
                if not self.save_item_details():
                    return self.response()
                
                if not self.save_rework_delivery():
                    return self.response()
            
            elif self.status == "Submit":
                if not self.get_rework_delivery_challan():
                    return self.response()
                
                if not self.update_status_instance():
                    return self.response()

                if not self.validate_required_fields():
                    return self.response()
                
                if not self.update_rework_qty():
                    return self.response()
            
            elif self.status == "Dispatch":
                if not self.get_rework_delivery_challan():
                    return self.response()
                if not self.update_status_instance():
                    return self.response()
                
                if not self.check_transportation_requirements():
                    return self.response()
                transport = None
                if self.data.get("transport"):
                    transport = SupplierFormData.objects.filter(id=self.data.get("transport")).first()
                    if not transport:
                        self.errors.append("Transport not found.")
                        return self.response()
 
                self.rework_delivery_service.transport = transport if transport else None
                self.rework_delivery_service.vehicle_no = self.data.get("vehicle_no") if self.data.get("vehicle_no") else None
                self.rework_delivery_service.driver_name = self.data.get("driver_name") if self.data.get("driver_name") else None
                self.rework_delivery_service.docket_no = self.data.get("docket_no") if self.data.get("docket_no") else None
                self.rework_delivery_service.docket_date = self.data.get("docket_date") if self.data.get("docket_date") else None
                self.rework_delivery_service.other_model = self.data.get("other_model") if self.data.get("other_model") else None
                self.rework_delivery_service.e_way_bill = self.data.get("e_way_bill") if self.data.get("e_way_bill") else None
                self.rework_delivery_service.e_way_bill_date = self.data.get("e_way_bill_date") if self.data.get("e_way_bill_date") else None
                self.rework_delivery_service.status = self.status_obj
                self.rework_delivery_service.save()
                self.success = True 
            else:
                self.errors.append("Unexpected Status.")
            return self.response()



    def response(self):
        return {
            "rework_delivery_service": self.rework_delivery_service,
            "success": self.success,
            "errors": self.errors,
        }