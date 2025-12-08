from itemmaster.models import *
from django.db.models import Sum
from itemmaster.serializer import *
from decimal import Decimal
class addStockData():

    def __init__(self, partCode, Store, batch, serial, qty, unit, transActionModel
                 , transActionId, partNumberId, savedBy, displayId, displayName):
        self.partCode = partCode
        self.Store = Store
        self.batch = batch
        self.serial = serial
        self.qty = qty
        self.unit = unit
        self.actions = ""
        self.previous = 0
        self.updated = 0
        self.added = 0
        self.transActionModel = transActionModel
        self.transActionId = transActionId
        self.partNumberId = partNumberId
        self.savedBy = savedBy
        self.stockLinkId = 0
        self.displayId = displayId
        self.displayName = displayName
        self.SaveData = {"id": "", "qty": "", "serial": []}
        self.success = False
        self.error = []

    def getTotalStock(self):
        item_stock_query = ItemStock.objects.filter(part_number=self.partCode, store__matained=True)
        total_current_stock = item_stock_query.aggregate(total_current_stock=Sum('current_stock'))[
            'total_current_stock']
        total_current_stock = total_current_stock if total_current_stock is not None else 0
        return total_current_stock

    def validateSerial(self):
        serial_list = []
        errors = []
        success = False

        if not self.serial:
            errors.append('Serial Number is required.')
        if len(self.serial) != int(self.qty):
            errors.append('Serial Number length does not match with quantity.')
        for serial in self.serial:
            if str(serial).strip() not in serial_list:
                serial_list.append(str(serial).strip())
            else:
                errors.append(f'{serial} Serial Number is already in the list.')
                break

        if len(errors) == 0:
            success = True
        return {"success": success, "errors": errors}

    def saveStockHistory(self, stockInstance, store, savedUserInstance):
        try:
            StockHistory.objects.create(action=self.actions, stock_link=stockInstance, store_link=store,
                                        part_number=self.partCode, previous_state=str(self.previous),
                                        updated_state=str(self.updated), added=str(self.added),
                                        saved_by=savedUserInstance, reduced="0",
                                        transaction_module=self.transActionModel,
                                        transaction_id=self.transActionId, display_id=self.displayId,
                                        display_name=self.displayName)
        except Exception as e:
            self.errors.append(str(e))

    def handleStockAdditions(self, serial=None):

        global batchNumberData
        global stockInstance
        selectItemmasterData = ItemMaster.objects.get(id=self.partCode.id)
        if self.SaveData['id']:
            stockInstance = ItemStock.objects.get(id=self.SaveData['id'])
        savedUserInstance = User.objects.get(id=self.savedBy)
        if self.batch:
            batchNumberData = BatchNumber.objects.get(id=self.batch)
        if self.unit:
            unitData = UOM.objects.get(id=self.unit)
        if self.Store:
            store = Store.objects.get(id=self.Store)
        if self.batch:
            if self.SaveData['id']:
                try:
                    ItemStock.objects.filter(id=self.SaveData['id']).update(
                        current_stock=self.SaveData['qty'],
                        part_number=selectItemmasterData,
                        batch_number=batchNumberData,
                        unit=unitData,
                        store=store
                    )
                    self.success = True
                    self.saveStockHistory(stockInstance, store, savedUserInstance)
                except  Exception as e:
                    self.errors.append(str(e))
            else:
                try:
                    stockInstance = ItemStock.objects.create(current_stock=self.qty,
                                                             part_number=selectItemmasterData,
                                                             batch_number=batchNumberData,
                                                             unit=unitData, store=store)
                    self.saveStockHistory(stockInstance, store, savedUserInstance)
                    self.success = True
                except Exception as e:
                    self.errors.append(str(e))
        elif serial:
            if self.SaveData['id']:
                try:
                    item_stock = ItemStock.objects.get(id=self.SaveData['id'])
                    item_stock.current_stock = self.SaveData['qty']
                    item_stock.part_number = selectItemmasterData
                    item_stock.unit = unitData
                    item_stock.store = store
                    item_stock.save()
                    serial_number_objects = SerialNumbers.objects.filter(serial_number__in=serial)
                    self.saveStockHistory(item_stock, store, savedUserInstance)
                    item_stock.serial_number.set(serial_number_objects)
                    self.success = True
                except  Exception as e:
                    self.errors.append(e)
            else:
                try:
                    item_stock = ItemStock.objects.create(current_stock=self.qty,
                                                          part_number=selectItemmasterData,
                                                          unit=unitData, store=store)
                    self.saveStockHistory(item_stock, store, savedUserInstance)
                    serial_number_objects = SerialNumbers.objects.filter(serial_number__in=serial)
                    item_stock.serial_number.set(serial_number_objects)
                    self.success = True
                except Exception as e:
                    self.errors.append(e)
        else:
            if self.SaveData['id']:
                item_stock = ItemStock.objects.get(id=self.SaveData['id'])
                item_stock.current_stock = self.SaveData['qty']
                item_stock.part_number = selectItemmasterData
                item_stock.unit = unitData
                item_stock.store = store
                item_stock.save()
                self.saveStockHistory(item_stock, store, savedUserInstance)
                self.success = True
            else:
                item_stock = ItemStock.objects.create(current_stock=self.qty,
                                                      part_number=selectItemmasterData,
                                                      unit=unitData, store=store)
                self.saveStockHistory(item_stock, store, savedUserInstance)
                self.success = True

    def addBatchNumber(self):
        existed_batch_number = BatchNumber.objects.filter(part_number=self.partCode, batch_number_name=self.batch)
        self.actions = "ADD"
        stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode, store=self.Store)
        saveData = {}
        previous_state = 0
        if len(stock_data_existing_list) > 0:
            batch_data_exists = stock_data_existing_list.filter(batch_number=self.batch).first()
            if batch_data_exists:
                self.previous = self.getTotalStock()
                self.updated = int(self.previous) + int(self.qty)
                self.added = int(self.qty)
                saveData['qty'] = int(batch_data_exists.current_stock) + int(self.qty)
                saveData['id'] = batch_data_exists.id
                self.SaveData = saveData
                self.handleStockAdditions()
            else:
                self.previous = self.getTotalStock()
                self.updated = int(self.previous) + int(self.qty)
                self.added = int(self.qty)
                self.handleStockAdditions()

        else:
            self.updated = int(self.qty)
            self.added = int(self.qty)
            self.handleStockAdditions()

        return {"success": self.success, "error": self.error}

    def addserialNumber(self):
        self.actions = "ADD"
        isValid = self.validateSerial()
        saveData = {}
        if isValid["success"]:
            stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode, store=self.Store).first()
            newSerialNumber = list(
                SerialNumbers.objects.filter(serial_number__in=self.serial).values_list('serial_number', flat=True))
            if stock_data_existing_list:
                serial_number_ids = list(stock_data_existing_list.serial_number.values_list('serial_number', flat=True))
                if serial_number_ids:
                    self.previous = self.getTotalStock()
                    self.updated = int(self.previous) + int(self.qty)
                    self.added = int(self.qty)
                    saveData['id'] = stock_data_existing_list.id
                    serial = serial_number_ids + newSerialNumber
                    saveData['qty'] = int(self.qty) + int(stock_data_existing_list.current_stock)
                    self.SaveData = saveData
                    self.handleStockAdditions(serial)
                else:
                    self.previous = self.getTotalStock()
                    self.updated = int(self.previous) + int(self.qty)
                    self.added = int(self.qty) 
                    self.handleStockAdditions(self.serial)
            else:

                self.updated = int(self.qty)
                self.added = int(self.qty)
                self.handleStockAdditions(self.serial)
            return {"success": self.success, "error": self.error}
        else:
            return {"success": False, "errors": isValid["errors"]}

    def addNoBatchNoSerial(self):
        self.actions = "ADD"
        saveData = {}
        stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode, store=self.Store).first()
        if stock_data_existing_list:
            self.previous = self.getTotalStock()
            self.updated = int(self.previous) + int(self.qty)
            self.added = int(self.qty)
            saveData["id"] = stock_data_existing_list.id
            saveData['qty'] = int(stock_data_existing_list.current_stock) + int(self.qty)
            self.SaveData = saveData
            self.handleStockAdditions(None)
        else:
            self.updated = int(self.qty)
            self.added = int(self.qty)
            self.handleStockAdditions(None)
        return {"success": self.success, "error": self.error}


class StockReduce():
    def __init__(self, partCode_id, Store_id, batch_id, serial_id_list, qty, partCode,batch ):
        self.partCode_id = partCode_id
        self.Store_id = Store_id
        self.batch_id = batch_id
        self.serial_id_list = serial_id_list
        self.qty = qty
        self.success = False
        self.error = []
        self.partCode = partCode if partCode else None
        self.batch = batch if batch else None

    def reduceBatchNumber(self):
        previousSates = ''
        total_closeing = 0
        try: 
            stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode_id, store=self.Store_id,
                                                                batch_number=self.batch_id)
            print("stock_data_existing_list", stock_data_existing_list)
            first_stock_data = stock_data_existing_list

            blance_stock_need_to_reduce = self.qty
            for stock_data_existing in stock_data_existing_list:
                if stock_data_existing.current_stock < blance_stock_need_to_reduce:
                    blance_stock_need_to_reduce = blance_stock_need_to_reduce - stock_data_existing.current_stock
                    stock_data_existing.delete()
                else:
                    stock_data_existing.current_stock = stock_data_existing - blance_stock_need_to_reduce
                    stock_data_existing.save()



            
            total_previous_stock = (
                                        ItemStock.objects
                                        .filter(part_number=self.partCode_id)
                                        .aggregate(total=Sum("current_stock"))
                                        .get("total") or 0
                                    )
 
            # previousSates = first_stock_data.current_stock
            reduce = self.qty
            updatedState = 0 
            print("----",first_stock_data , self.qty)
            if first_stock_data and  first_stock_data.current_stock - self.qty >= 0:
                updatedState = first_stock_data.current_stock - self.qty
                first_stock_data.current_stock = updatedState
                first_stock_data.save()
                self.success = True
            else:
                self.error.append(f"Check the Stock {self.partCode} batch {self.batch}")
            total_closeing = (total_previous_stock or 0) - (self.qty or 0) 
        except Exception as e: 
            self.error.append(f"Unexpeted error in stock reduce {str(e)} part {self.partCode} batch {self.batch} ")
        return {"success": self.success, "error": self.error, "previousSates": total_previous_stock,
                "reduce": reduce, "updatedState": total_closeing, "stocklink": first_stock_data}

    def reduceSerialNumber(self):
        updated_serial_list = []
        previousSates = ''
        total_closeing = 0
        try:
            
            stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode_id,
                                                                store=self.Store_id,  )
            
            first_stock_data = stock_data_existing_list.first()
            total_previous_stock = (
                                        ItemStock.objects
                                        .filter(part_number=self.partCode_id)
                                        .aggregate(total=Sum("current_stock"))
                                        .get("total") or 0
                                    )
            # previousSates = stock_data_existing_list.current_stock
            reduce = self.qty
            
            if not total_previous_stock:
                self.error.append(" Serial Stock Not available")
                return {"success": self.success, "error": self.error, "previousSates": 0,
                        "reduce": 0, "updatedState": 0, "stocklink": first_stock_data}
            
            updatedState = 0
            current_serials = first_stock_data.serial_number.all()
            for current_serial in current_serials:
                if current_serial.id not in self.serial_id_list:
                    updated_serial_list.append(current_serial)
            first_stock_data.current_stock = int(first_stock_data.current_stock) - self.qty
            first_stock_data.serial_number.set(updated_serial_list)
            first_stock_data.save()
            updatedState = int(first_stock_data.current_stock)
            self.success = True
            total_closeing = (total_previous_stock or 0) - (self.qty or 0)
        except Exception as e: 
            self.error.append(f"Unexpeted error in stock reduce {str(e)} part {self.partCode}   ")
        return {"success": self.success, "error": self.error, "previousSates": total_previous_stock,
                "reduce": reduce, "updatedState": total_closeing, "stocklink": first_stock_data}

    def reduceNoBatchNoSerial(self):
        previousSates = ''
        total_closeing = 0
        try:

            stock_data_existing_list = ItemStock.objects.filter(part_number=self.partCode_id,
                                                                store=self.Store_id)
            first_stock_data = stock_data_existing_list.first()
            total_previous_stock = (
                                        ItemStock.objects
                                        .filter(part_number=self.partCode_id)
                                        .aggregate(total=Sum("current_stock"))
                                        .get("total") or 0
                                    )
            # previousSates = first_stock_data.current_stock
            reduce = self.qty 
            updatedState = (first_stock_data.current_stock) - self.qty
             
            first_stock_data.current_stock = updatedState
            first_stock_data.save()
            self.success = True
            total_closeing = (total_previous_stock or 0) - (self.qty or 0)
        except Exception as e:
            self.error.append(f"Unexpeted error in stock reduce {str(e)} part {self.partCode}   ")
        return  {"success": self.success, "error": self.error, "previousSates": total_previous_stock,
                "reduce": reduce, "updatedState": total_closeing, "stocklink": first_stock_data}


class AddStockDataService:

    def __init__(self, part_code, store,  qty, unit,
                    transaction_model, transaction_id, saved_by,
                    display_id, display_name, rate, batch=None, serials=None, laster_serial=None, conference=None):
        self.part_code = part_code
        self.store = store
        self.batch = batch
        self.serials = serials or []
        self.laster_serial = laster_serial
        self.qty = Decimal(qty)
        self.unit = unit
        self.transaction_model = transaction_model
        self.transaction_id = transaction_id
        self.saved_by = saved_by
        self.display_id = display_id
        self.display_name = display_name
        self.rate = rate
        self.success = False
        self.errors = []
        self.stock_data = {"id": None, "qty": 0, "serial": []}
        self.previous = 0
        self.updated = 0
        self.added = 0
        self.conference = conference

    def _get_existing_stock(self, use_batch=False):
        filters = {
            "part_number": self.part_code,
            "store": self.store,
        }
        if use_batch and self.batch:
            filters["batch_number"] = self.batch 
        return ItemStock.objects.filter(**filters).first()

    def _validate_serials(self):
        if not self.serials:
            self.errors.append("Serial Number is required.")
            return False
        if len(self.serials) != self.qty:
            self.errors.append("Serial count doesn't match quantity.")
            return False
        if len(set(self.serials)) != len(self.serials):
            self.errors.append("Duplicate serial numbers found.")
            return False
        return True

    def _log_stock_history(self, stock_instance):
        try: 
            StockHistory.objects.create(
                action="ADD",
                stock_link=stock_instance,
                store_link=self.store,
                part_number=self.part_code,
                previous_state=self.previous,
                updated_state=self.updated,
                added=self.added,
                reduced=0,
                saved_by=self.saved_by,
                transaction_module=self.transaction_model,
                transaction_id=self.transaction_id,
                display_id=self.display_id,
                display_name=self.display_name,
                conference = self.conference.id if self.conference and  self.conference.id else 0
            )
            
        except Exception as e:
            self.errors.append(f"Failed to save stock history: {e}")

    def _save_or_update_stock(self, stock_instance=None, serial_numbers=None):
        
        try:
            part = self.part_code
            store = self.store
            unit = self.unit
            batch = self.batch
            rate = self.rate
             
            if stock_instance:
                stock_instance.current_stock = self.stock_data["qty"]
                stock_instance.part_number = part
                stock_instance.unit = unit
                stock_instance.store = store
                stock_instance.rate = rate
                if batch:
                    stock_instance.batch_number = batch
                stock_instance.save()
            else:
                stock_instance = ItemStock.objects.create(
                    current_stock=self.qty,
                    part_number=part,
                    unit=unit,
                    store=store,
                    batch_number=batch,
                    rate = rate
                ) 

            if serial_numbers: 
                stock_instance.serial_number.set(serial_numbers)
                stock_instance.last_serial_history = self.laster_serial
                stock_instance.save()

            self._log_stock_history(stock_instance)
            self.success = True
        except Exception as e:
            self.errors.append(f"Failed to save/update stock: {e}")

    def add_batch_stock(self):
        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty

        existing = self._get_existing_stock(use_batch=True)
  
        if existing:
            self.stock_data["id"] = existing.id
            self.stock_data["qty"] = existing.current_stock + self.qty 
        else:
            self.stock_data["qty"] = self.qty
        existing_stock = ItemStock.objects.filter(id=self.stock_data["id"]).first() if self.stock_data["id"] else None
         
        self._save_or_update_stock(existing_stock)
        return {"success": self.success, "errors": self.errors}

    def add_serial_stock(self):
        if not self._validate_serials():
            return {"success": False, "errors": self.errors}

        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty

        existing = self._get_existing_stock()
        serial_objs =  self.serials
 
        if existing:
            self.stock_data["id"] = existing.id
            self.stock_data["qty"] = existing.current_stock + self.qty
            self.serials = list(self.serials) + list(existing.serial_number.all())

        # print("----", existing, serial_objs)
        self._save_or_update_stock(existing, serial_objs) 
        return {"success": self.success, "errors": self.errors}

    def add_non_tracked_stock(self):
        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty

        existing = self._get_existing_stock()
        if existing:
            self.stock_data["id"] = existing.id
            self.stock_data["qty"] = existing.current_stock + self.qty

        self._save_or_update_stock(existing)
        return {"success": self.success, "errors": self.errors}

    def _get_total_stock(self):
        total = ItemStock.objects.filter(part_number=self.part_code, store__matained=True)\
            .aggregate(total=Sum("current_stock"))["total"]
        return total or 0


class AddStockDataService_latest:

    def __init__(self, part_code, store,  qty, unit,
                    transaction_model, transaction_id, saved_by,
                    display_id, display_name, rate, batch=None, serials=None, laster_serial=None, conference=None):
        self.part_code = part_code
        self.store = store
        self.batch = batch
        self.serials = serials or []
        self.laster_serial = laster_serial
        self.qty = Decimal(qty)
        self.unit = unit
        self.transaction_model = transaction_model
        self.transaction_id = transaction_id
        self.saved_by = saved_by
        self.display_id = display_id
        self.display_name = display_name
        self.rate = rate
        self.success = False
        self.errors = []
        self.stock_data = {"id": None, "qty": 0, "serial": []}
        self.previous = 0
        self.updated = 0
        self.added = 0
        self.conference = conference


    def _validate_serials(self):
        if not self.serials:
            self.errors.append("Serial Number is required.")
            return False
        if len(self.serials) != self.qty:
            self.errors.append("Serial count doesn't match quantity.")
            return False
        if len(set(self.serials)) != len(self.serials):
            self.errors.append("Duplicate serial numbers found.")
            return False
        return True

    def _log_stock_history(self, stock_instance):
        try: 
            StockHistory.objects.create(
                action="ADD",
                stock_link=stock_instance,
                store_link=self.store,
                part_number=self.part_code,
                previous_state=self.previous,
                updated_state=self.updated,
                added=self.added,
                reduced=0,
                saved_by=self.saved_by,
                transaction_module=self.transaction_model,
                transaction_id=self.transaction_id,
                display_id=self.display_id,
                display_name=self.display_name,
                conference = self.conference.id if self.conference and  self.conference.id else 0
            )
            
        except Exception as e:
            self.errors.append(f"Failed to save stock history: {e}")

    def _save_or_update_stock(self,  serial_numbers=None):
        
        try:
            part = self.part_code
            store = self.store
            unit = self.unit
            batch = self.batch
            rate = self.rate

            stock_instance = ItemStock.objects.create(
                current_stock=self.qty,
                part_number=part,
                unit=unit,
                store=store,
                batch_number=batch,
                rate = rate,
                conference_link = self.conference)

            if serial_numbers:
                stock_instance.serial_number.set(serial_numbers)
                stock_instance.last_serial_history = self.laster_serial
                stock_instance.save()

            self._log_stock_history(stock_instance)
            self.success = True
        except Exception as e:
            self.errors.append(f"Failed to save/update stock: {e}")

    def add_batch_stock(self):
        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty
 
        self._save_or_update_stock()
        return {"success": self.success, "errors": self.errors}

    def add_serial_stock(self):
        if not self._validate_serials():
            return {"success": False, "errors": self.errors}

        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty

        serial_objs =  self.serials

        self._save_or_update_stock(serial_objs) 
        return {"success": self.success, "errors": self.errors}

    def add_non_tracked_stock(self):
        self.previous = self._get_total_stock()
        self.updated = self.previous + self.qty
        self.added = self.qty

        self._save_or_update_stock()
        return {"success": self.success, "errors": self.errors}

    def _get_total_stock(self):
        total = ItemStock.objects.filter(part_number=self.part_code, store__matained=True)\
            .aggregate(total=Sum("current_stock"))["total"]
        return total or 0

