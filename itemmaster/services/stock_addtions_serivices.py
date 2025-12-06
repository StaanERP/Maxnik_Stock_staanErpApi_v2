from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from datetime import datetime, date
from EnquriFromapi.models import *
from django.db.models import Max

class StockAdditionService:
    def __init__(self, kwargs, info, status):
        self.kwargs = kwargs
        self.errors = []
        self.info = info
        self.status = status
        self.status_id = None
        self.success = False
        self.inventory_handler = None
        self.store = None
        self.conference = None
        self.inventory_serializers = []
        self.old_inventory_approval = []

    def process(self):
        if self.status == "Draft":
            if not self.validate_requiry_field():
                return self.response()
            if not self.validate_inventory_approval():
                return self.response()
            if not self.validate_inventory_approval_with_serializer():
                return self.response()
            if not self.save_inventory_handler():
                return self.response()
            return self.response()
        elif self.status == "Submit":
            if not self.validate_requiry_field():
                return self.response()
            if self.status == "Submit" or self.inventory_handler.status != "Cancel":
                if not self.add_stock():
                    return self.response()
                if self.inventory_handler:
                    self.inventory_handler.status = self.status_id
                    self.inventory_handler.save()
                    self.success=True
                    return self.response()
                else:
                    self.errors.append("Inventory Handler is missing.")
                    return self.response()
            else:
                self.errors.append("Inventory Handler is already cancel.")
                return self.response()
        elif self.status == "Cancel":
            if not self.validate_requiry_field():
                return self.response()
            if self.inventory_handler:
                if self.status == "Draft" or self.inventory_handler.status != "Submit":
                    self.inventory_handler.status = self.status_id
                    self.inventory_handler.save()
                    self.success=True
                else:
                    self.errors.append("Already submited did allow to Cancel.")
                return self.response()
            else:
                self.errors.append("Inventory Handler is missing.")
                return self.response()
        else:
            self.errors.append(f"{self.status} not found.")
            return self.response()

            

    def format_serializer_errors(self, errors):
        return [f"{field}: {'; '.join(map(str, errs))}" for field, errs in errors.items()]

    def get_inventory_handler(self):
        return InventoryHandler.objects.filter(id=self.kwargs.get("id")).first()

    def validate_requiry_field(self):
        store_id = self.kwargs.get("store")
        conference_id = self.kwargs.get("conference")
        
        # Validate inventory handler
        if self.kwargs.get("id"):
            inventory = self.get_inventory_handler()
            if not inventory:
                self.errors.append(f"Inventory with ID {self.kwargs.get('id')} not found.")
                return False
            self.inventory_handler = inventory
            self.old_inventory_approval = list(inventory.inventory_id.values_list("id",flat=True))
            
            
        # Validate store
        if store_id:
            self.store = Store.objects.filter(id=store_id).first()
            if not self.store:
                self.errors.append(f"Store with ID {store_id} not found.")
                return False

            if self.store.conference and not conference_id:
                self.errors.append("Conference is required for the selected store.")
                return False

        # Validate conference
        if conference_id:
            self.conference = Conferencedata.objects.filter(id=conference_id).first()
            if not self.conference:
                self.errors.append("Conference not found.")
                return False

        # Validate status
        if self.status:
            self.status_id = CommanStatus.objects.filter(name=self.status, table="stock").first()
            if not self.status_id:
                self.errors.append(f"Status '{self.status}' not found. Ask admin to create it.")
                return False
        else:
            self.errors.append("Status is required.")
            return False

        return True

    def validate_inventory_approval(self):
        try:
            item_approval = self.kwargs.get("inventory_id")
            
            if not item_approval:
                self.errors.append("At least one inventory item is required.")
                return False
            
            for item in item_approval:
                part_number = item.get("part_number")
                batch_input = item.get("batch_number")
                qty = item.get("qty")
                item['store'] = self.store.id
                if not part_number:
                    self.errors.append("Part number is missing for one of the items.")
                    return False
                itemmaster = ItemMaster.objects.filter(id=part_number).first()
                if not itemmaster:
                    self.errors.append(f"{part_number} not found in Item Master.")
                    return False
                # Batch-tracked item
                if itemmaster.batch_number:
                    item['serial_number'] = None
                    if not batch_input:
                        self.errors.append(f"Batch number is required for {itemmaster.item_name}.")
                        return False
                    else:
                        batch_obj = self.get_or_create_batch(itemmaster.id, batch_input)
                        if batch_obj:
                            item['batch_number'] = batch_obj.id
                        else:
                            return False

                # Serial-tracked item
                elif itemmaster.serial:
                    serial_numbers = item.get("serial_number", [])
                    if not itemmaster.serial_auto_gentrate:
                        item['batch_number'] = None
                        if not serial_numbers:
                            self.errors.append(f"Serial numbers are required for {itemmaster.item_name}.")
                            return False
                        if len(serial_numbers) != qty:
                            self.errors.append(f"Serial numbers must be equal to qty {itemmaster.item_name}.")
                            return False
                        if len(serial_numbers) > 0:
                            item['serial_number'] = ", ".join(serial_numbers)
                        else:
                            item['serial_number'] = None
                    else:
                         item['serial_number'] = None

                # Non-tracked item
                else:
                    item['serial_number'] = None
                    if item.get("batch_number") or item.get("serial_number"):
                        self.errors.append(
                            f"Serial or Batch number not required for {itemmaster.item_name}."
                        )
                        return False

            return True
        except Exception as e:
            self.errors.append(str(e))
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

    def validate_inventory_approval_with_serializer(self):
        item_approval = self.kwargs.get("inventory_id")
        inventory_serializer = None
        for item in item_approval: 
            id_inventory = item.get("id")
            if id_inventory:
                inventory_obj = ItemInventoryApproval.objects.filter(id=id_inventory).first()
                if inventory_obj:
                    inventory_serializer = ItemInventoryApprovalSerializer(inventory_obj, data=item)
                else:
                    self.errors.append(f"inventory Approval id {id_inventory} not Found.")
                    return False
            else:
                inventory_serializer = ItemInventoryApprovalSerializer(data=item)

            if not inventory_serializer.is_valid():
                self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}" for field, error in inventory_serializer.errors.items()])
                return False
            self.inventory_serializers.append(inventory_serializer)
        return True

    def save_inventory_handler(self): 
        inventory_instances = []
        try:
            with transaction.atomic():
                # Save each inventory item
                for inventory in self.inventory_serializers:
                    inventory.save()
                    inventory_instances.append(inventory.instance)
                handler_data = {
                    "id": self.kwargs.get("id"),
                    "status": self.status_id.id if self.status_id else None,
                    "inventory_id": [obj.id for obj in inventory_instances],
                    "store": self.store.id if self.store else None,
                    "conference": self.conference.id if self.conference else None,
                    "actions": "Add",
                    "saved_by":  None,
                    "modified_by": None,
                } 
                if self.inventory_handler:
                    handler_data['modified_by'] = self.info.context.user.id
                    handler_data['saved_by'] = self.inventory_handler.saved_by.id
                    serializer = InventoryHandlerSerializer(self.inventory_handler, data=handler_data, partial=True)
                    
                else:
                    handler_data['saved_by'] = self.info.context.user.id
                    serializer = InventoryHandlerSerializer(data=handler_data) 
                if serializer.is_valid():
                    self.inventory_handler = serializer.save()
                    self.success = True 
                    deleteCommanLinkedTable(self.old_inventory_approval,list(self.inventory_handler.inventory_id.values_list('id', flat=True)), ItemInventoryApproval)
                    return True
                else:
                    self.errors.extend(self.format_serializer_errors(serializer.errors))
                    return False
        except Exception as e:
            self.errors.append(f"Transaction failed: {str(e)}")
            return False

    def generate_serial_number(self, start_number, prefix, qty, part_id):
        try:
            prefix_parts = prefix.split("#")
            prefix_text = prefix_parts[0]
            padding_length = int(prefix_parts[1])
            last_serial_number = int(start_number) + qty 
        except (IndexError, ValueError):
            self.errors.append("Invalid prefix format. Use format like 'ABC#3'.")
            return False

        new_serial_instance = []

        for i in range(start_number, start_number + qty):
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

    def add_stock(self):
        try:
            with transaction.atomic():
                inventory = self.get_inventory_handler()
                transaction_model = "InventoryHandler"
                transaction_id = self.kwargs.get("id")
                saveing_user = self.info.context.user
                display_id = inventory.inventory_handler_id
                display_name= "Stock Addition"
                
                if not inventory:
                    self.errors.append(f"Inventory with ID {self.kwargs.get('id')} not found.")
                    return False
                
                if inventory.inventory_id.exists():
                    for item in inventory.inventory_id.all():

                        if not item.is_stock_added:
                            if item.batch_number:
                                batch =  AddStockDataService(part_code=item.part_number, 
                                                    store=item.store,
                                                    batch=item.batch_number,
                                                    qty=item.qty,
                                                    unit=item.unit,
                                                    transaction_model=transaction_model,
                                                    transaction_id= transaction_id,
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = item.rate,
                                                    conference = self.conference)
                                batch.add_batch_stock()
                                if batch.success:
                                    item.is_stock_added = True
                                    item.save()
                                else:
                                    self.errors.extend(batch.errors)
                                    return False
                            elif item.part_number.serial:
                                if item.part_number.serial_auto_gentrate:
                                    latest = ItemStock.objects.filter(part_number__id=item.part_number.id).aggregate(
                                        max_serial=Max("last_serial_history")
                                    )

                                    max_last_serial_history = latest.get("max_serial")
                                    latest_stock = max_last_serial_history if max_last_serial_history else item.part_number.serial_starting
                                    
                                    
                                    serial_obj = self.generate_serial_number(int(latest_stock),item.part_number.serial_format, item.qty, item.part_number.id)
                                
                                    if serial_obj.get("new_serial") and len(serial_obj.get("new_serial")) > 0:
                                        serial = AddStockDataService(part_code=item.part_number, 
                                                    store=item.store,
                                                    serials=serial_obj.get("new_serial"),
                                                    qty=item.qty,
                                                    unit=item.unit,
                                                    transaction_model=transaction_model,
                                                    transaction_id= transaction_id,
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = item.rate,
                                                    laster_serial = serial_obj.get("last_serial"),
                                                    conference = self.conference)
                                        serial.add_serial_stock() 
                                        if serial.success:
                                            item.is_stock_added = True
                                            item.save()
                                        else:
                                            self.errors.extend(serial.errors)
                                            return False
                                    else:
                                        return False
                                
                                else:
                                    serial_list_instance = []
                                    serial_number_list = [serial.strip() for serial in item.serial_number.split(",") if serial.strip()]
                                    for serial_num in serial_number_list:
                                        existing_serial = SerialNumbers.objects.filter(serial_number=serial_num).first()
                                        if existing_serial:
                                            if self.is_serial_in_stock(existing_serial.id,item.part_number.id ):
                                                self.errors.append(f"{serial_num} already exists in stock.")
                                                return False
                                            serial_list_instance.append(existing_serial)
                                        else:
                                            new_serial = self.get_or_create_serial(serial_num)
                                            if new_serial:
                                                serial_list_instance.append(new_serial)
                                            else:
                                                return False 
                                    serial = AddStockDataService(part_code=item.part_number, 
                                                    store=item.store,
                                                    serials=serial_list_instance,
                                                    qty=item.qty,
                                                    unit=item.unit,
                                                    transaction_model=transaction_model,
                                                    transaction_id= transaction_id,
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = item.rate,
                                                    conference = self.conference)
                                    serial.add_serial_stock()
                                    if serial.success:
                                        item.is_stock_added = True
                                        item.save()
                                    else:
                                        self.errors.extend(serial.errors)
                                        return False
                            else:
                                nobatch_noserial = AddStockDataService(part_code=item.part_number, 
                                                    store=item.store,
                                                    qty=item.qty,
                                                    unit=item.unit,
                                                    transaction_model=transaction_model,
                                                    transaction_id= transaction_id,
                                                    saved_by = saveing_user,
                                                    display_id= display_id,
                                                    display_name= display_name,
                                                    rate = item.rate,
                                                    conference = self.conference)
                              
                                
                                nobatch_noserial.add_non_tracked_stock() 
                                if nobatch_noserial.success:
                                    item.is_stock_added = True
                                    item.save()
                                else:
                                    self.errors.extend(nobatch_noserial.errors)
                                    return False
                    
                    if self.inventory_handler:
                        self.inventory_handler.status = self.status_id
                        self.inventory_handler.save()
                    return True
                else:
                    self.errors.append(f"Inventory Approval not found.")
                    return False
        except Exception as e:
            self.errors.append(f"An exception error occurred {str(e)}")

    def response(self):
        return {"inventory_handler":self.inventory_handler,
            "success":self.success,
            "errors":self.errors}