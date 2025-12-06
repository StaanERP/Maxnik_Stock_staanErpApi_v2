from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from datetime import datetime, date
from EnquriFromapi.models import *


class StockdeletionService:
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
            if not self.check_the_stock():
                return self.response()
            if not self.stock_reduce():
                return self.response()
            if self.inventory_handler:
                self.inventory_handler.status = self.status_id
                self.inventory_handler.save()
                self.success=True
                return self.response()
            else:
                self.errors.append("Inventory Handler is missing.")
                return self.response()
        elif self.status == "Cancel":
            if not self.validate_requiry_field():
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
            self.errors.append(f"{self.status} not found.")
            return self.response()

    
    def get_or_create_batch(self, item_master_id, batch_name):
        batch_instance = BatchNumber.objects.filter(
            part_number=item_master_id,
            id=batch_name
        ).first()

        if batch_instance:
            return batch_instance
        else:
            self.errors.append(f"{batch_name} did not Found.")
            return None

    def get_inventory_handler(self):
        return InventoryHandler.objects.filter(id=self.kwargs.get("id")).first()

    def format_serializer_errors(self, errors):
        return [f"{field}: {'; '.join(map(str, errs))}" for field, errs in errors.items()]

    def validate_requiry_field(self):
        try:
                
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
        except Exception as e:
            print(e)
    
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
                itemmaster = ItemMaster.objects.filter(id=part_number).first()
                if not itemmaster:
                    self.errors.append(f"Part number {part_number} is not found.")
                    return False
                # Batch-tracked item
                if itemmaster.batch_number: 
                    item['serial_number'] = ""
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
                    if not serial_numbers:
                        self.errors.append(f"Serial numbers are required for {itemmaster.item_name}.")
                        return False

                    serial_id_list = []
                    for serial_obj in serial_numbers:
                        serial_id = serial_obj.get("id")
                        serial_name = serial_obj.get("serial")
                        existing_serial = SerialNumbers.objects.filter(id=serial_id).first()
                        if not existing_serial:
                            self.errors.append(f"{serial_name} Serial numbers are required for {itemmaster.item_name}.")
                            return False
                        serial_id_list.append(serial_id)
                        
                    item['deletion_serial_number'] = serial_id_list
                    item['serial_number'] = ""
                else:
                    item['serial_number'] = ""
                    if item.get("batch_number") or item.get("serial_number"):
                        self.errors.append(
                            f"Serial or Batch number not required for {itemmaster.item_name}."
                        )
                        return False
            return True
        except Exception as e:
            self.errors.append(f'An exception occurred {e}')
            return False
    
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
                    "actions": "Delete",
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
                    deleteCommanLinkedTable(self.old_inventory_approval,list(self.inventory_handler.inventory_id.values_list('id', flat=True)), ItemInventoryApproval)
                    self.success = True
                    return True
                else:
                    self.errors.extend(self.format_serializer_errors(serializer.errors))
                    return False
                
        except Exception as e:
            self.errors.append(f"Transaction failed: {str(e)}")
            return False
    
    def validate_stock(self, item, stock_data_existing_list):
        required_qty = item.qty or 0 
        conderence = self.conference.id if self.conference and self.conference.id else None
        conference_qty = get_conference_stock(item.part_number.id, self.store.id,conderence )
        total_current_stock = sum(single_stock.current_stock or 0 for single_stock in stock_data_existing_list)
        
        if self.conference:
            balance = conference_qty - required_qty
            return balance >= 0, balance
        else:
            actual_stock = (total_current_stock or 0)
            balance = actual_stock - required_qty
            return balance >= 0, balance


    def check_the_stock(self):
        try:

            if not self.inventory_handler:
                self.errors.append(f"Inventory with ID {self.kwargs.get('id')} not found.")
                return False
            if self.inventory_handler.inventory_id.exists():
                for item in self.inventory_handler.inventory_id.all():
                    if item.is_stock_added:
                        continue
                        
                    stock_data_existing_list = ItemStock.objects.filter(
                                                part_number=item.part_number,
                                                store=self.store,
                                                batch_number=item.batch_number if item.batch_number else None
                                            )
                    
                    if not stock_data_existing_list: 
                        self.errors.append(f"{item.part_number} {item.batch_number.batch_number_name or ''} is not available.")
                        return False
                    is_sufficient, balance_stock = self.validate_stock(item, stock_data_existing_list)
            
                    
                    if not is_sufficient:
                        self.errors.append(
                            f"The item {item.part_number} {f'batch: {item.batch_number.batch_number_name}' if item.batch_number and item.batch_number.batch_number_name else ''} "
                            f"is not available. Required quantity shortfall: {abs(balance_stock)}."
                        )
                        return False
                    if item.deletion_serial_number.exists():
                        serial_pairs = list(item.deletion_serial_number.values_list("id", "serial_number"))
                        # current_serial_ids = set(stock_data_existing_list.serial_number.values_list("id", flat=True))
                        current_serial_ids = set(
                                id
                                for single_stock in stock_data_existing_list
                                for id in single_stock.serial_number.values_list("id", flat=True)
                            )
                        missing_serials = [
                            serial_number for serial_id, serial_number in serial_pairs if serial_id not in current_serial_ids
                        ]
                        if missing_serials:
                            self.errors.append(
                                f"The following serial numbers for {item.part_number} are not in current stock: {', '.join(missing_serials)}"
                            )
                            return False
                return True
        except Exception as e:
            print(e)


    def stock_reduce(self):
        all_success = True
        try:
            with transaction.atomic():
                if self.inventory_handler.inventory_id.exists():
                    for item in self.inventory_handler.inventory_id.all():
                        if not item.is_stock_added:
                            serial_ids = list(item.deletion_serial_number.values_list("id", flat=True))
                            stockReduce = StockReduce(
                                partCode_id=item.part_number.id,
                                Store_id=item.store.id,
                                batch_id=item.batch_number.id if item.batch_number and item.batch_number.id else None,
                                qty=item.qty,
                                serial_id_list=serial_ids,
                                partCode = item.part_number,
                                batch = item.batch_number.batch_number_name if item.batch_number and item.batch_number.batch_number_name  else None
                            ) 
                            
                            if item.batch_number:
                                result = stockReduce.reduceBatchNumber()
                            elif serial_ids:
                                result = stockReduce.reduceSerialNumber()
                            else:
                                result = stockReduce.reduceNoBatchNoSerial()
                            if result['success']:
                                item.is_stock_added = True
                                item.save() 
                                try:
                                    stockHistoryUpdate(
                                        "DELETE",
                                        item.store,
                                        item.part_number,
                                        result['previousSates'],
                                        result['updatedState'],
                                        0,
                                        result['reduce'],
                                        self.info.context.user,
                                        "Stock Deletion",
                                        self.inventory_handler.id,
                                        self.inventory_handler.inventory_handler_id,
                                        'Stock Deletion',
                                        result['stocklink'],
                                        self.conference.id if self.conference and self.conference.id else None
                                    )
                                except Exception as e:
                                    print(e)
                                    
                            else:
                                self.errors.append(result["error"])
                                all_success = False
                                return False
                    return all_success

        except Exception as e:
            self.errors.append(f"An exception error occurred in stock reduce{e}")
            return False
    
    def response(self):
        return {"inventory_handler":self.inventory_handler,
            "success":self.success,
            "errors":self.errors}