from itemmaster2.models import *
from itemmaster2.Serializer import *
from django.db.models import F
from decimal import Decimal

class DeliverChallanService:
    def __init__(self, kwargs, status, info):
        self.kwargs = kwargs
        self.status_text = status
        self.status = None
        self.errors = []
        self.so_delivery_challan = None
        self.Salesorder_2 = None
        self.needStock = []
        self.state_of_company = None
        self.info = info
        self.warning = []
        self.store_id = set()
        self.combo_batch = [] # ex: [{parent_index: [{combo_index:[bacth_list]}]}]
        self.item_batch = {} # ex : {item_index: batch_list]}
        self.item_details_ids = []
        self.combo_serializer = {}
        self.item_details_serializer = []
        self.old_item_details_ids  = []
    
    def update_status_id(self):
        "Check and get Status" 
        if self.status_text:
            statusObjects = CommanStatus.objects.filter(name=self.status_text
                                                        , table="SalesOrderDeliveryChallan").first()
            
            if statusObjects:
                self.kwargs["status"] = statusObjects.id
                self.status = statusObjects
            else:
                status = self.kwargs.get("status", "default_status")
                self.errors.append(f"Ask devopole to add ${status}")
        return not self.errors
    
    def validate_so_dc_exists(self):
        "Check and get sales DC"
        if "id" in self.kwargs and self.kwargs['id']:
            so_delivery_challan = SalesOrder_2_DeliveryChallan.objects.filter(id=self.kwargs['id']).first()
            self.so_delivery_challan = so_delivery_challan
            
            if not self.so_delivery_challan:
                self.errors.append("Sales Order dc Not Found.")
            self.old_item_details_ids  = list(self.so_delivery_challan.item_details.values_list('id', flat=True))

            if self.status_text == "Draft" and so_delivery_challan.status.name in ['Submit', "Canceled"]:
                self.errors.append(f"Already {so_delivery_challan.status.name} Sales DC did'n make Draft again.")

            if self.status_text == "Submit" and so_delivery_challan.status.name in ['Submit', "Canceled"]:
                self.errors.append(f"Already {so_delivery_challan.status.name} Sales DC did'n make Submit again.")
        else:
            if self.status_text != "Draft":
                self.errors.append("initially Draft only allowed.")

        return not self.errors

    def validate_required_fields(self):
        """Validate the required Field"""
        required_field = ['dc_date', 'terms_conditions', 'sales_order', 'terms_conditions_text',
                        'before_tax', 'tax_total', 'round_off', 'nett_amount']
        for field in required_field:
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required')
        if self.Salesorder_2 is None :
            salesorder = SalesOrder_2.objects.get(id=self.kwargs['sales_order'])
            self.Salesorder_2 = salesorder
        return not self.errors
    
    def validate_sales_order_and_eway(self):
        
        try:
            if self.Salesorder_2 is None :
                salesorder = SalesOrder_2.objects.get(id=self.kwargs['sales_order'])
                self.Salesorder_2 = salesorder
            buyer_state = self.Salesorder_2.buyer_state  
            amount_threshold = self.state_of_company.threshold_for_intrastate  if str(buyer_state).lower() == str(self.state_of_company.address.state).lower() else\
            self.state_of_company.threshold_for_interstate
     
            if self.kwargs['nett_amount'] >= int(amount_threshold):
                if not self.kwargs.get('e_way_bill') or not self.kwargs.get('e_way_bill_date'):
                    self.errors.append(f"Net Amount is more than {amount_threshold}. E-Way Bill and Date are required.")
            return not self.errors
        except ObjectDoesNotExist:
            self.errors.append("sales order does not exist")
            return not self.errors
    
    def validate_numbering_series(self):
        """Validate Numbering Series"""
        if not self.kwargs['id']:
            conditions = {'resource': 'SalesOrder Delivery Challan', 'default': True, "department": self.Salesorder_2.department.id}
            numbering_series = NumberingSeries.objects.filter(**conditions).first()
            if numbering_series is None:
                self.errors.append("No matching NumberingSeries found.")
        return not self.errors

    def validate_item_combo(self, combo, parent_item, parent_index):
            """Validate Item Combo"""
            instance_list = []
            item_lable = []
            update_combo = []
            parent_lable = f'{parent_item.itemmaster.item_part_code}-{parent_item.itemmaster.item_name}'

            for index, combo_item in enumerate(combo):
                salesOrder_item_combo =  SalesOrder_2_temComboItemDetails.objects.filter(id=combo_item['item_combo']).first()
                

                if not salesOrder_item_combo:
                    self.errors.append(f"{parent_lable} -> combo id {combo_item['item_combo']} not found in sales order item combo")
                itemmaster = salesOrder_item_combo.itemmaster
                item_combo_lable = f"{itemmaster.item_part_code}-{itemmaster.item_name}"
                item_lable.append(item_combo_lable)
                
                for field in ['item_combo', 'store', 'qty']:
                    if combo_item.get(field) is None:
                        self.errors.append(f'{parent_lable}-> {item_combo_lable}{field} is required')

                if itemmaster.serial:
                    if len(combo_item["serial"]) != combo_item['qty']:
                        self.errors.append(f"{parent_lable} -> {item_combo_lable} Serial Number and qty Not Match.")

                elif itemmaster.batch_number:
                    combo_item['serial'] = [] 
                    if not combo_item["batch"]:
                        self.errors.append(f"{parent_lable} -> {item_combo_lable} Batch Number Not Found.")

                    if combo_item["batch"]:
                        total_batch_qty = sum(single_batch.get("qty", 0) for single_batch in  combo_item["batch"])

                        if combo_item['qty'] != total_batch_qty:
                            self.errors.append(f"{parent_lable}->{item_combo_lable} item qty {combo_item['qty']} \
                                            and total batch qty {total_batch_qty} is mismatch.")
                            
                        for single_batch in  combo_item["batch"]:
                            for field in ['batch','qty']:
                                if single_batch.get(field) is None:
                                    self.errors.append(f'{field} is required')
                            batch_instance= BatchNumber.objects.filter(id=single_batch.get("batch"))
                            if not batch_instance:
                                self.errors.append(f'{single_batch.get("batch_str")} batch not Found.')
                            single_batch["batch"] = batch_instance

                if combo_item.get("store"):
                    self.store_id.add(combo_item.get("store"))
                else:
                    self.errors.append(f"Store is required {item_combo_lable}.")
                
                if "id" in  combo_item and  combo_item['id']:
                    combo_instance = SalesOrder_2_DeliverChallanItemCombo.objects.filter(id=combo_item['id']).first()
                    if not combo_instance:
                        self.errors.append(f"{parent_lable} -> dc combo id {combo_item['id']} not found.")
                        continue
                    instance_list.append(combo_instance)
                else:
                    instance_list.append(None)

                if len(self.errors):
                    continue

                if itemmaster.batch_number:
                    found = False
                    for entry in self.combo_batch:
                        if parent_index in entry:  # already exists
                            entry[parent_index].append({index: combo_item["batch"]})
                            found = True
                            break

                    if not found:  # if parent_index not in list
                        self.combo_batch.append({parent_index: [{index: combo_item["batch"]}]})
                
                combo_item["batch"] = []
                update_item_combo = combo_item
                
                update_combo.append(update_item_combo)
            
            item_result = validate_common_data_and_send_with_instance(update_combo, instance_list,
                                        SalesOrder_2_DeliverChallanItemComboSerializer, item_lable, self.info.context )
            
            if item_result.get("error"):
                self.errors.extend(item_result["error"])
                return False
            self.combo_serializer[parent_index] =  item_result['instance']
                        
    def validate_item_details(self):
        """Validate item details"""
        instance_list = []
        item_details = self.kwargs.get('item_details',[])
        update_item = []
        item_lable = []

        if len(item_details) == 0:
            self.errors.append("At least one Item Details is Required.")
            return False
        
        for index , item in enumerate(item_details):
            salesorder_itemdetail = SalesOrder_2_ItemDetails.objects.filter(id=item.get("sales_order_item_detail")).first()

            if not salesorder_itemdetail:
                self.errors.append(f"{item.get('sales_order_item_detail')} did not found in sale order item.")

            itemaster = salesorder_itemdetail.itemmaster
            lable = f'{itemaster.item_part_code}-{itemaster.item_name}'
            item_lable.append(lable)
            
            """validate and update instance"""
            if salesorder_itemdetail.item_combo and 'item_combo_item_details' in item and len(item.get('item_combo_item_details')) > 0 :
                self.validate_item_combo(item.get('item_combo_item_details'), salesorder_itemdetail, index)
                
                if self.errors:
                    continue
            
            """Validate item details"""
            single_item = item
            single_item['item_combo_item_details'] = []
            
            for field in ['qty',  "amount"]:
                if single_item.get(field) is None:
                    self.errors.append(f'{lable}- {field} is required')

            if itemaster.serial and not itemaster.item_combo_bool:
                if len(single_item["serial"]) != single_item['qty']:
                    self.errors.append(f"{lable} Serial Number and qty Not Match.")

            elif itemaster.batch_number and not itemaster.item_combo_bool:
                if not single_item["batch"]:
                    self.errors.append(f"{lable} Batch Number Not Found.")
                
                for single_batch in single_item["batch"]:
                    for field in ['batch','qty']:
                        if single_batch.get(field) is None:
                            self.errors.append(f"{lable}->{single_batch.get('batch_str', None)}  - {field} is required")
                    batch_instance = BatchNumber.objects.filter(id=single_batch.get("batch")).first()
                    
                    if not batch_instance:
                        self.errors.append(f'{lable}-> {single_batch.get("batch_str")} batch not Found.')
                    single_batch['batch'] = batch_instance

    
                self.item_batch.setdefault(index, []).extend(single_item["batch"])

     
                single_item["batch"] = []
            update_item.append(single_item)

            if item.get("store"):
                self.store_id.add(item.get("store"))
            elif itemaster.item_combo_bool:
                pass
            else:
                self.errors.append(f"Store is required {itemaster.item_part_code}.")
            
            if "id"  in single_item and single_item['id']:
                item_detail_instance = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id=single_item['id']).first()
                if not item_detail_instance:
                    self.errors.append(f"{lable} -> {single_item['id']} data not found.")
                    continue
                instance_list.append(item_detail_instance)
            else:
                instance_list.append(None)
 
            if self.errors:
                return False

        store_instances = Store.objects.filter(id__in=self.store_id)
        
        if len(store_instances) != len(self.store_id):
            self.errors.append("Some store is not Found.")

        if self.errors:
            return False

        item_result = validate_common_data_and_send_with_instance(update_item, instance_list,
                                        SalesOrder_2_DeliveryChallanItemDetailsSerializer,item_lable, self.info.context)
        if item_result.get("error"):
            self.errors.extend(item_result["error"])
            return False
        
        self.item_details_serializer.extend(item_result.get("instance"))
        
        return not self.errors

    def check_stock_availability(self):
        """Check the Stock"""
        try:
            for itemdetails in self.so_delivery_challan.item_details.all():
                so_dc_id = itemdetails.sales_order_item_detail
                itemmaster = so_dc_id.itemmaster
                StockResult= None

                if itemdetails.stock_reduce:
                        continue
                if not so_dc_id.item_combo:
                    submit_count = so_dc_id.dc_submit_count or 0
                    
                    if submit_count+itemdetails.qty <= so_dc_id.qty:
                        qty = Decimal(itemdetails.qty)
                        if itemmaster.batch_number:
                            batchs = itemdetails.salesorder_2_retunbatch_set.all()
                            StockResult =  CheckStockData(so_dc_id.itemmaster, itemdetails.store, batchs, [], qty)
                        elif itemmaster.serial:
                            StockResult = CheckStockData(so_dc_id.itemmaster, itemdetails.store, None, itemdetails.serial.all(), qty)
                        else:
                            StockResult = CheckStockData(so_dc_id.itemmaster, itemdetails.store, None, [], qty)
                        if not StockResult['success']:
                            self.needStock.extend(StockResult['needStock'])
                    else:
                        self.errors.append(f"The entered quantity for part {itemmaster} is greater than the available Sales Order quantity.")
                elif so_dc_id.item_combo and itemdetails.item_combo_itemdetails.exists():
                    ItemComboStockResult = None
                    for itemCombo in itemdetails.item_combo_itemdetails.all():
                        if itemCombo.stock_reduce:
                            continue
                        salesorder_combo_itemmaster = itemCombo.item_combo.itemmaster
                        salesorder_combo = itemCombo.item_combo
                        submit_count = salesorder_combo.dc_submit_count or 0
                        
                        if submit_count+itemCombo.qty <= salesorder_combo.qty:
                            qty = Decimal(itemdetails.qty)
                            if salesorder_combo_itemmaster.batch_number:
                                batchs = itemCombo.salesorder_2_retunbatch_set.all()
                                ItemComboStockResult =  CheckStockData(salesorder_combo_itemmaster,
                                                            itemCombo.store, batchs, [], qty)
                            elif salesorder_combo_itemmaster.serial:
                                ItemComboStockResult = CheckStockData(salesorder_combo_itemmaster, itemCombo.store, None, itemCombo.serial.all(), qty)
                            else:
                                ItemComboStockResult = CheckStockData(salesorder_combo_itemmaster, itemCombo.store, None, [], qty)
                            if not ItemComboStockResult['success']:
                                self.needStock.extend(ItemComboStockResult['needStock'])
                        else:
                            self.errors.append(f"The entered quantity for part {salesorder_combo_itemmaster} is greater than the available Sales Order quantity.")
            return True if not self.errors and not self.needStock else False
        except Exception as e: 
            self.errors.append(str(e))
            return  False

    def stock_reduce(self):
        """Reduce the stock"""
        for itemdetails in self.so_delivery_challan.item_details.all():
            so_item_details = itemdetails.sales_order_item_detail
            item_master = so_item_details.itemmaster
            
            # Skip if no item master or already reduced
  
            if not item_master or itemdetails.stock_reduce or not item_master.keep_stock:
                has_draft = any(
                                    linked_dc.salesorder_2_deliverychallan_set.first() and 
                                    linked_dc.salesorder_2_deliverychallan_set.first().status.name == "Draft" and 
                                    linked_dc.salesorder_2_deliverychallan_set.first().id != self.so_delivery_challan.id
                                    for linked_dc in so_item_details.salesorder_2_deliverychallanitemdetails_set.all()
                                )
                            
                            
                so_item_details.dc_submit_count = (so_item_details.dc_submit_count or 0) + (itemdetails.qty or 0)
                so_item_details.is_have_draft = has_draft
                so_item_details.save()
                continue
            try:
                # Normal item (non-combo)
                if not itemdetails.sales_order_item_detail.item_combo:
                    dc_submit_count = (itemdetails.sales_order_item_detail.dc_submit_count or 0)

                    if dc_submit_count+itemdetails.qty > so_item_details.qty:
                        self.errors.append(f"Cannot process part {item_master}: entered quantity exceeds the Sales Order item quantity.")
                        continue
                    
                    if item_master.batch_number:
                        batchs =itemdetails.salesorder_2_retunbatch_set.all()
                        batch_error = []
                        for batch in batchs:
                            if batch.is_stock_reduce:
                                continue
                            stockReduceResult = StockReduce(
                                    partCode_id=item_master.id,
                                    Store_id=itemdetails.store.id,
                                    batch_id=batch.batch.id,
                                    qty=batch.qty,
                                    serial_id_list=[],
                                    partCode = item_master,
                                    batch = batch.batch
                                )
                            result = stockReduceResult.reduceBatchNumber()
                            if not result['success']:
                                batch_error.extend(result['error'])
                                break
                            UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                itemdetails,
                                                                                itemdetails.sales_order_item_detail,
                                                                                item_master,
                                                                                result)
                            if not batch_error:
                                batch.is_stock_reduce = True
                                batch.save()
                            else:
                                self.errors.extend(batch_error)
                                continue
                    
                    elif item_master.serial:
                        serial_ids = [s.id for s in itemdetails.serial.all()]
                        stockReduceResult = StockReduce(
                                    partCode_id=item_master.id,
                                    Store_id=itemdetails.store.id,
                                    batch_id='',
                                    qty=itemdetails.qty,
                                    serial_id_list=serial_ids,
                                    partCode = item_master,
                                    batch=None
                                )
                        result = stockReduceResult.reduceSerialNumber()
                        if not result['success']:
                            self.errors.extend(result['error'])
                            continue
                        UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                itemdetails,
                                                                                itemdetails.sales_order_item_detail,
                                                                                item_master,
                                                                                result)
                    
                    else:
                        stockReduceResult = StockReduce(
                                    partCode_id=item_master.id,
                                    Store_id=itemdetails.store.id,
                                    batch_id='',
                                    qty=itemdetails.qty,
                                    serial_id_list=[],
                                    partCode = item_master,
                                    batch=None
                                )
                        result = stockReduceResult.reduceNoBatchNoSerial()
                        if not result['success']:
                            self.errors.extend(result['error'])
                            continue
                        UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                itemdetails,
                                                                                itemdetails.sales_order_item_detail,
                                                                                item_master,
                                                                                result)
                    
                    if not self.errors:
                        has_draft = any(
                                    linked_dc.salesorder_2_deliverychallan_set.first() and 
                                    linked_dc.salesorder_2_deliverychallan_set.first().status.name == "Draft" and 
                                    linked_dc.salesorder_2_deliverychallan_set.first().id != self.so_delivery_challan.id
                                    for linked_dc in so_item_details.salesorder_2_deliverychallanitemdetails_set.all()
                                )
                            
                            
                        so_item_details.dc_submit_count = (so_item_details.dc_submit_count or 0) + (itemdetails.qty or 0)
                        so_item_details.is_have_draft = has_draft
                        so_item_details.save()

                        itemdetails.stock_reduce = True
                        itemdetails.save()
                        
                    
                elif itemdetails.item_combo_itemdetails.exists():
                    so_item_combo_parent_details = itemdetails.sales_order_item_detail
                    for combo_item in itemdetails.item_combo_itemdetails.all(): 
                        if combo_item.stock_reduce:
                            continue
                        actual_qty = combo_item.item_combo.qty
                        sales_order_item_combo = combo_item.item_combo
                        combo_item_master = combo_item.item_combo.itemmaster
                        dc_combo_submit_count = (combo_item.item_combo.dc_submit_count or 0)
                        total_qty = (dc_combo_submit_count or 0)+(combo_item.qty or 0)
                        if actual_qty < total_qty:
                            self.errors.append(f"Cannot process part {combo_item_master}: entered quantity exceeds the Sales Order item quantity.")
                            continue 
                        if combo_item_master.batch_number:
                            batchs =combo_item.salesorder_2_retunbatch_set.all()
                            batch_error = []
                            for batch in batchs:
                                if batch.is_stock_reduce:
                                    continue
                                stockReduceResult = StockReduce(
                                    partCode_id=combo_item_master.id,
                                    Store_id=combo_item.store.id,
                                    batch_id=batch.batch.id,
                                    qty=batch.qty,
                                    serial_id_list=[],
                                    partCode = combo_item_master,
                                    batch = batch.batch.batch_number_name
                                )
                                result = stockReduceResult.reduceBatchNumber()
                                
                                if not result['success']:
                                    batch_error.extend(result['error'])
                                    break
                                UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                    combo_item,
                                                                                    combo_item.item_combo,
                                                                                    combo_item_master,
                                                                                    result)
                                
                            
                            if not batch_error:
                                batch.is_stock_reduce = True
                                batch.save()
                                combo_item.stock_reduce = True
                                combo_item.save()
                                
                                sales_order_item_combo.dc_submit_count = (sales_order_item_combo.dc_submit_count or 0) + combo_item.qty
                                sales_order_item_combo.save()
                            else:
                                self.errors.extend(batch_error)
                                continue
 
                        elif combo_item_master.serial:
                            serial_ids = [s.id for s in combo_item.serial.all()]
                            stockReduceResult = StockReduce(
                                    partCode_id=combo_item_master.id,
                                    Store_id=combo_item.store.id,
                                    batch_id="",
                                    qty=combo_item.qty,
                                    serial_id_list=serial_ids,
                                    partCode = item_master,
                                    batch=None
                                )
                            result = stockReduceResult.reduceSerialNumber()
                            if not result['success']:
                                self.errors.extend(result['error'])
                                continue
                            UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                combo_item,
                                                                                combo_item.item_combo,
                                                                                combo_item_master,
                                                                                result)
                            combo_item.stock_reduce = True
                            combo_item.save()
                            
                            sales_order_item_combo.dc_submit_count = (sales_order_item_combo.dc_submit_count or 0) + combo_item.qty
                            sales_order_item_combo.save()
                        else:
                            stockReduceResult = StockReduce(
                                    partCode_id=combo_item_master.id,
                                    Store_id=combo_item.store.id,
                                    batch_id="",
                                    qty=combo_item.qty,
                                    serial_id_list=[],
                                    partCode = item_master,
                                    batch=None
                                )
                            result = stockReduceResult.reduceNoBatchNoSerial()
                            if not result['success']:
                                self.errors.extend(result['error'])
                                continue
                            UpdateTheStockHistoryAndSalesOrderItemDetails(self.so_delivery_challan,
                                                                                combo_item,
                                                                                combo_item.item_combo,
                                                                                combo_item_master,
                                                                                result)
                        
                            combo_item.stock_reduce = True
                            combo_item.save()
                            
                            sales_order_item_combo.dc_submit_count = (sales_order_item_combo.dc_submit_count or 0) + combo_item.qty
                            sales_order_item_combo.save()

                    if not self.errors:
                        has_draft = any(
                                    (linked_combo.salesorder_2_deliverychallanitemdetails_set.first() and
                                    linked_combo.salesorder_2_deliverychallanitemdetails_set.first().salesorder_2_deliverychallan_set.first() and
                                    linked_combo.salesorder_2_deliverychallanitemdetails_set.first().salesorder_2_deliverychallan_set.first().status.name == "Draft" and
                                    linked_combo.salesorder_2_deliverychallanitemdetails_set.first().salesorder_2_deliverychallan_set.first().id != self.so_delivery_challan.id)
                                    for linked_combo in sales_order_item_combo.salesorder_2_deliverchallanitemcombo_set.all()
                                )
                        so_item_combo_parent_details.dc_submit_count = (so_item_combo_parent_details.dc_submit_count or 0) + (itemdetails.qty or 0)
                        so_item_combo_parent_details.is_have_draft = has_draft
                        so_item_combo_parent_details.save()
                        sales_order_item_combo.is_have_draft = has_draft
                        # print("_____"*10)
                        # print((sales_order_item_combo.dc_submit_count or 0), (combo_item.qty or 0))
                        # sales_order_item_combo.dc_submit_count = (sales_order_item_combo.dc_submit_count or 0)+ (combo_item.qty or 0)
                        sales_order_item_combo.save()
                
            except Exception as e:
                self.errors.append(f"Unexpeted error occurred in stock reduce {str(e)}")
                transaction.set_rollback(True)
                return False
        if not self.errors:
            self.so_delivery_challan.all_stock_reduce = True
            
            self.so_delivery_challan.status = self.status
            
            self.so_delivery_challan.save() 
        else:
            transaction.set_rollback(True)

        return len(self.errors) == 0
    
    def check_transportation_requirements(self):
        if self.kwargs['transportation_mode'] == "OwnVechile":
            if not self.kwargs.get('vehicle_no') or not self.kwargs.get('driver_name'):
                self.errors.append("Vehicle No , Driver Name is required.")
        elif self.kwargs['transportation_mode'] == "Transport":
            if self.kwargs['transport'] == None or self.kwargs.get('vehicle_no') == None:
                self.errors.append("Transport ID , Vehicle No is required.")
            else:
                result = ValidationForeignKeys('itemmaster', "SupplierFormData",self.kwargs['transport'])
                if not result['success']:
                    self.errors.append(result['error'])
        elif self.kwargs['transportation_mode'] == "Courier":
            if self.kwargs['docket_no'] == None or self.kwargs['docket_date'] == None:
                self.errors.append("Courier is required.")
        elif self.kwargs['transportation_mode'] == "OtherMode":
            if self.kwargs['other_model'] == None:
                self.errors.append("Other Model is required.")
        return not self.errors
        
    def validate_tax(self):
        salesorder = SalesOrder_2.objects.get(id=self.kwargs['sales_order'])
        self.Salesorder_2 = salesorder
        item_details = salesorder.item_details.all()
        gst_transaction = salesorder.gst_nature_transaction
        if gst_transaction.gst_nature_type == "Specify" and gst_transaction.specify_type == "taxable":
            
            for item in item_details:
                if gst_transaction.place_of_supply == "Intrastate":
                    if (
                        item.sgst!= gst_transaction.sgst_rate or
                        item.cgst!= gst_transaction.cgst_rate or
                        item.cess != gst_transaction.cess_rate
                    ):
                        self.warning.append("There is a tax mismatch; please amend the sales order accordingly.")
                        return False
                elif gst_transaction.place_of_supply == "Interstate":
                    if (
                        item.igst != gst_transaction.igst_rate or
                        item.cess != gst_transaction.cess_rate
                    ):
                        self.warning.append("There is a tax mismatch; please amend the sales order accordingly.")
                        return False
            return True

        elif gst_transaction.gst_nature_type == "As per HSN":
            
            for item in item_details:
                 
                
                if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != item.hsn.gst_rates.rate or (item.cess or 0) !=(item.hsn.cess_rate or 0):
                    self.warning.append("There is a tax mismatch; please amend the sales order accordingly.")
                    return False 
            return True


        else: 
            # Fallback check — if all 4 rates are present, reject
            for item in item_details:
                if item.sgst or item.cgst or item.igst or item.cess:
                    self.warning.append("There is a tax mismatch; please amend the sales order accordingly.")
                    return False
            return True

    def run_validations(self):
        if self.status_text == "Draft":
            if not self.update_status_id():
                return False
            print("----111")
            if not self.validate_required_fields():
                return False
            print("---222")
            if not self.validate_numbering_series():
                return  False
            print("---333")
            if not self.validate_so_dc_exists():
                return False
            print("---444")
            if not self.validate_item_details():
                return False 
            print("---555")
        # self.validate_tax()
        return not self.errors

    def reduce_parent_draft_count(self, item_ids):
        """
        Reduce draft count for parent Sales Order items when Delivery Challan items are deleted.
        """ 
        try:
            # Get Delivery Challan item detail
            dc_items = SalesOrder_2_DeliveryChallanItemDetails.objects.filter(id__in=item_ids)
            print("dc_items", dc_items)
            if not dc_items:
                return
            for dc_item in dc_items:

                so_item = dc_item.sales_order_item_detail


                # --- Case 1: Handle direct Sales Order Item ---
                if so_item: 
                    # Check if any linked DC items still belong to a Draft DC
                    has_draft = any(
                        linked_dc.salesorder_2_deliverychallan_set.first() and 
                        linked_dc.salesorder_2_deliverychallan_set.first().status.name == "Draft"
                        for linked_dc in so_item.salesorder_2_deliverychallanitemdetails_set.all()
                    )

                    so_item.is_have_draft = has_draft
                    so_item.save()

                    # If not a combo, delete the DC item itself
                    if not so_item.item_combo:
                        dc_item.delete()

                print("so_item.item_combo", so_item.item_combo)
                # --- Case 2: Handle Item Combos ---
                if so_item and so_item.item_combo and dc_item.item_combo_itemdetails.exists():
                    print("so_item.item_combo in", so_item.item_combo)
                    for combo_item in dc_item.item_combo_itemdetails.all():
                        salesorder_combo = combo_item.item_combo
                        has_draft = False
                        print("salesorder_combo", salesorder_combo)
                        if salesorder_combo:
                            # Check if any linked combo DC items belong to a Draft DC
                            for linked_combo in salesorder_combo.salesorder_2_deliverchallanitemcombo_set.all():
                                item_detail = linked_combo.salesorder_2_deliverychallanitemdetails_set.first()
                                if item_detail:
                                    sales_dc = item_detail.salesorder_2_deliverychallan_set.first()
                                    if sales_dc and sales_dc.status.name == "Draft":
                                        has_draft = True
                                        break
                            print("salesorder_combo in ", salesorder_combo)
                            salesorder_combo.is_have_draft = has_draft
                            salesorder_combo.save()

                        # Delete the combo link
                        combo_item.delete()

                    # Delete the main DC item after processing combos
                    dc_item.delete()
 
            return True
        except Exception as e:
            self.errors.append(f"Error reducing DC draft count: {e}")
            return False

    def save_item_combo(self, parent_index):
        
        update_data =  [] 

        try:
            for index , combo_serializer in  enumerate(self.combo_serializer.get(parent_index)):
                if combo_serializer:
                    combo_serializer.save()
                    if combo_serializer.instance.item_combo:
                        salesorder_item_combo = combo_serializer.instance.item_combo
                        salesorder_item_combo.is_have_draft = True
                        salesorder_item_combo.save()
                    
                    combo_batch_data =  [ combo.get(parent_index) for combo in self.combo_batch if combo.get(parent_index)] 
                
                    
                    if combo_batch_data and combo_batch_data[0]:
                        batch_datas =  None
                        for single_batch in combo_batch_data[0]:
                            
                            if  index in single_batch and  single_batch[index]:
                                batch_datas  = single_batch[index]
                            else:
                                continue
                        
                        if batch_datas:
                            try:
                                for batch_data in batch_datas:
            
                                    lookup = {}
                                    if batch_data.get("id"):
                                        lookup["id"] = batch_data["id"] 
                                    else:
                                        lookup["id"] = None

                                    SalesOrder_2_RetunBatch.objects.update_or_create(
                                        **lookup,
                                        defaults={
                                            "item_combo": combo_serializer.instance,
                                            "batch": batch_data.get("batch").first(),
                                            "qty" : batch_data.get("qty"),
                                        }
                                    )
                            except Exception as e:
                                return {"instance": [], "success":False, "error" : [f"Unexpeted error occurred in batch {batch_data.get('batch_str')} - Save {str(e)}"]}

                    update_data.append(combo_serializer.instance)
            return {"instance": update_data, "success":True, "error" : []}
        except Exception as e: 
            return {"instance": [], "success":False, "error" : [f"Unexpeted error occurred in item combo save {str(e)}."]}

    def save_item_details(self):
        """Save item details after validation"""

        try:
            item_details = self.kwargs.get('item_details', [])
            if len(self.item_details_serializer) != len(item_details):
                self.errors.append("Item serializer count mismatch.")
                return False

            for index, serializer in enumerate(self.item_details_serializer):
                if not serializer:
                    continue
                serializer.save()
                self.item_details_ids.append(serializer.instance.id) 
                # update draft flag 
                if serializer.instance.sales_order_item_detail:
                    serializer.instance.sales_order_item_detail.is_have_draft = True
                    serializer.instance.sales_order_item_detail.save()

                # save batch number
                if index in self.item_batch and self.item_batch[index]:
                    try:
                        for item_batch in self.item_batch[index]:
                            lookup = {}
                            if item_batch.get("id"):
                                lookup["id"] = item_batch["id"] 
                            else:
                                lookup["id"] = None
                            SalesOrder_2_RetunBatch.objects.update_or_create(
                                            **lookup,
                                            defaults={
                                                "item": serializer.instance,
                                                "batch": item_batch.get("batch"),
                                                "qty" : item_batch.get("qty"),
                                            }
                                        )
                    except Exception as e:
                        transaction.set_rollback(True)

                        return {"instance": [], "success":False, "error" : [f"Unexpeted error occurred in batch {item_batch.get('batch_str')} - Save {str(e)}"]}


                # save combos if any
                if index in self.combo_serializer:
                    combo_result = self.save_item_combo(index) 
                    if not combo_result["success"]:
                        self.errors.extend(combo_result["error"])
                        return False
                    serializer.instance.item_combo_itemdetails.set(combo_result["instance"])
            self.kwargs['item_details'] = self.item_details_ids
            return True
        except Exception as e:
            transaction.set_rollback(True)

            self.errors.append(f"Error saving item details: {e}")
            return False

    def save_dc(self):
        serializer = None
        if 'id' in self.kwargs and self.kwargs['id']:
            serializer = SalesOrder_2_DeliveryChallanSerializer(self.so_delivery_challan,
                                                                    data=self.kwargs, partial=True,
                                                                    context={'request': self.info.context})
        else:
            serializer = SalesOrder_2_DeliveryChallanSerializer(data=self.kwargs, partial=True,
                                                                    context={'request': self.info.context})
   
        if serializer and serializer.is_valid():
            try:
                serializer.save()
                self.so_delivery_challan =  serializer.instance
                new_itemdetails_ids = list(self.so_delivery_challan.item_details.values_list('id', flat=True))
      
                deleteitemDetailIds = [id for id in self.old_item_details_ids if id not in new_itemdetails_ids]
               
                """need to delete the item and check draft and make change is_have_draft"""
                if deleteitemDetailIds and  not self.reduce_parent_draft_count(deleteitemDetailIds):
                    transaction.set_rollback(True)
                    return False 
                return True
            except Exception as e:
                transaction.set_rollback(True)
                self.errors.append(f"Unexpeted error occurred {str(e)}")
                return False
        else:
            transaction.set_rollback(True)
            self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                        for field, error in serializer.errors.items()])
            return False
            
    def Process(self):
        with transaction.atomic(): 
            if self.status_text == "Draft":
                if not self.run_validations():
                    return self.response()
                
                if not self.save_item_details():
                    return self.response()
                print("----2")
                if not self.save_dc():
                    return self.response()
                print("----3")
                return self.response()
            if self.status_text == 'Submit':
                if not self.validate_so_dc_exists():
                    return self.response()
                print("----4")
                if not self.update_status_id():
                    return self.response()
                print("----5")
                # if not self.run_validations():
                #     return self.response()
                if not self.check_stock_availability():
                    return self.response()
                print("----6")
                if not self.stock_reduce():
                    return self.response()
                print("----7")
                # self.so_delivery_challan.status = self.status
                return self.response()
                
            if self.status_text == 'Dispatch': 
                self.state_of_company = company_info()
                # if not self.run_validations():
                #     return self.response()
                if not self.validate_so_dc_exists():
                    return False
                if not self.update_status_id():
                    return self.response()
                if not self.check_transportation_requirements():
                    return self.response()
                if not self.validate_sales_order_and_eway():
                    return self.response()
                
                transport = None
                if self.kwargs.get("transport"):
                    transport = SupplierFormData.objects.filter(id=self.kwargs.get("transport")).first()
                    if not transport:
                        self.errors.append("Transport not found.")
                        return self.response()
                
                self.so_delivery_challan.transport = transport if transport else None
                self.so_delivery_challan.vehicle_no = self.kwargs.get("vehicle_no") if self.kwargs.get("vehicle_no") else None
                self.so_delivery_challan.driver_name = self.kwargs.get("driver_name") if self.kwargs.get("driver_name") else None
                self.so_delivery_challan.docket_no = self.kwargs.get("docket_no") if self.kwargs.get("docket_no") else None
                self.so_delivery_challan.docket_date = self.kwargs.get("docket_date") if self.kwargs.get("docket_date") else None
                self.so_delivery_challan.other_model = self.kwargs.get("other_model") if self.kwargs.get("other_model") else None
                self.so_delivery_challan.e_way_bill = self.kwargs.get("e_way_bill") if self.kwargs.get("e_way_bill") else None
                self.so_delivery_challan.e_way_bill_date = self.kwargs.get("e_way_bill_date") if self.kwargs.get("e_way_bill_date") else None
                self.so_delivery_challan.status = self.status
                self.so_delivery_challan.save()
                
            return {
                "success": (len(self.errors) == 0 and len(self.needStock) == 0),
                "errors": self.errors,
                "warning":self.warning,
                "needStock": self.needStock,
                "soDeliveryChallan" : self.so_delivery_challan
            }

    def response(self): 
        return {
            "success": (len(self.errors) == 0 and len(self.needStock) == 0),
            "errors": [" ,".join(self.errors)] if self.errors else [],
            "warning":self.warning,
            "needStock": self.needStock,
            "soDeliveryChallan" : self.so_delivery_challan
        }

def UpdateTheStockHistoryAndSalesOrderItemDetails(data, dcItemDetail, salesOrderItemDetail, item_master, result):
    try:
        # dcItemDetail.stock_reduce = True
        # dcItemDetail.save()

        # sales_order_item = salesOrderItemDetail
        # if sales_order_item.dc_submit_count is None:
        #     sales_order_item.dc_submit_count = Decimal('0')
        # sales_order_item.dc_submit_count += dcItemDetail.qty

        # if sales_order_item.dc_draft_count >= dcItemDetail.qty:
        #     sales_order_item.dc_draft_count -= dcItemDetail.qty
         
        # sales_order_item.save() 
        stockHistoryUpdate(
            "DELETE",
            dcItemDetail.store,
            item_master,
            result['previousSates'],
            result['updatedState'],
            0,
            result['reduce'],
            data.modified_by,
            "SalesOrder DeliveryChallan",
            data.id,
            data.dc_no.linked_model_id,
            'SalesOrder DeliveryChallan',
            result['stocklink'],
            None
        )
        
        return  {"success": True, "error": "",}
    except Exception as e:
        
        return  {"success": False, "error": f'unexpeted error -{e}',}

def addBatchStockIn(itemmaster, batchs, store, qty):
    try:
        for batch in batchs:
            if not batch.is_stock_reduce:
                continue
            stock = ItemStock.objects.filter(
                part_number=itemmaster.id,
                store=store.id,
                batch_number=batch.batch.id,
                ).first()
        if stock:
            stock.current_stock += Decimal((batch.qty or 0))
            stock.save()
            return None
        else:
            return f"{batch.batch} not Found."
    except Exception as e:
        return f"{itemmaster.item_part_code} -- {e}"

def addSerialStockIn(itemmaster, serials, store, qty):
    try:
        stock = ItemStock.objects.filter(
            part_number=itemmaster.id,
            store=store
        ).first()
        if stock:
            existing_ids = set(stock.serial_number.values_list('id', flat=True))
            new_ids = set(s.id for s in serials)
            combined_ids = existing_ids.union(new_ids)
            stock.serial_number.set(SerialNumbers.objects.filter(id__in=combined_ids))
            stock.current_stock += Decimal(qty)
            stock.save()
            return None
        else:
            return f"{itemmaster.item_part_code} stock not found."
    except Exception as e:
        return f"{itemmaster.item_part_code} -- {e}"

def addNoBatchNoSerial(itemmaster, store, qty):
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

def SalesOrderDcOnCancelAddTheStock(dc):
    errors = []
    try:
        for dc_item in dc.item_details.all():
            itemmaster = dc_item.sales_order_item_detail.itemmaster
            sales_item = dc_item.sales_order_item_detail
            added_qty = dc_item.qty
 
            # Process non-combo items
            if not sales_item.item_combo:
                if not dc_item.stock_reduce:
                    continue
                error = None
                
                if itemmaster.batch_number:
                    batchs = dc_item.salesorder_2_retunbatch_set.all()
                    error = addBatchStockIn(itemmaster, batchs, dc_item.store, added_qty)
                elif itemmaster.serial:
                    error = addSerialStockIn(itemmaster, dc_item.serial.all(), dc_item.store, added_qty)
                else:
                    error = addNoBatchNoSerial(itemmaster, dc_item.store, added_qty)
                if error is None:
                    sales_item.dc_submit_count = max(0, (sales_item.dc_submit_count or 0) - added_qty)
                    sales_item.save()
                    dc_item.stock_reduce = False
                    dc_item.save()
                else:
                    errors.append(error)
                    return errors

            # Process combo items
            elif sales_item.item_combo and dc_item.item_combo_itemdetails.exists():
                for combo_item in dc_item.item_combo_itemdetails.all():
                    if not combo_item.stock_reduce:
                        continue
                    parent_combo = combo_item.item_combo
                    combo_qty = combo_item.qty
                    combo_master = combo_item.item_combo.itemmaster
                    error = None
                    if combo_master.batch_number:
                        batchs = combo_item.salesorder_2_retunbatch_set.all()
                        error = addBatchStockIn(combo_master, batchs , combo_item.store, combo_qty)
                    elif combo_master.serial:
                        error = addSerialStockIn(combo_master, combo_item.serial.all(), combo_item.store, combo_qty)
                    else:
                        error = addNoBatchNoSerial(combo_master, combo_item.store, combo_qty)

                    if error is None:
                        parent_combo.dc_submit_count = max(0, parent_combo.dc_submit_count - combo_qty)
                        parent_combo.save()
                        combo_item.stock_reduce = False
                        combo_item.save()
                    else:
                        errors.append(error)
                        return errors
        historys = StockHistory.objects.filter(transaction_module="SalesOrder DeliveryChallan", transaction_id=dc.id)
        for history in historys:
            history.is_delete = True
            history.save()
    except Exception as e: 
            errors.append(e)
    return errors

def sales_dc_general_update(data, isvalidate):
     
    valid_serializers = []
    errors = []
    debits = data.get("debits", [])
    credit = data.get("credit", {})
    debits_amount = Decimal("0.00")
    REQUIRED_FIELDS = ["date", "voucher_type", "sales_dc_voucher_no", "account", "created_by"]
   
    # Process debits
    for idx, debit in enumerate(debits):
        for field in REQUIRED_FIELDS + ["debit"]:
            if debit.get(field) in [None, ""]:
                errors.append(f"Debits[{idx}] → '{field}' is required.")

        debits_amount += Decimal(str(debit.get("debit", 0)))
        serializer = AccountsGeneralLedgerSerializer(data=debit)
        
        if not serializer.is_valid():
            for field, error in serializer.errors.items():
                errors.append(f"Debits[{idx}] → {field}: {'; '.join([str(e) for e in error])}")
        else:
            valid_serializers.append(serializer)

    # Process credit
    for field in REQUIRED_FIELDS + ["credit"]:
        if credit.get(field) in [None, ""]:
            errors.append(f"Credit → '{field}' is required.")
   
    serializer = AccountsGeneralLedgerSerializer(data=credit)
 
    if not serializer.is_valid():
        
        for field, error in serializer.errors.items():
            errors.append(f"Credit → {field}: {'; '.join([str(e) for e in error])}")
    else:
        valid_serializers.append(serializer)
    
    # Compare amounts
    credit_amount = Decimal(str(credit.get("credit", 0)))
    if debits_amount != credit_amount:
        errors.append(f"Debit amount ({debits_amount}) and credit amount ({credit_amount}) do not match.")

    if isvalidate:
        return {"success": len(errors)== 0 , "errors":errors}

    if errors:
        return {"success": len(errors)== 0 , "errors":errors} 
    
    for valid_serializer in valid_serializers:
        valid_serializer.save()

    return  {"success": True , "errors":errors}



# def ReduceTheStock(data):
#     success = False
#     errors = []
#     for itemdetails in data.item_details.all(): 
#         item_master = itemdetails.sales_order_item_detail.itemmaster
#         so_item_details = itemdetails.sales_order_item_detail 
#         # Skip if no item master or already reduced
#         if not item_master or itemdetails.stock_reduce:
#             continue
#         try:
#             # Normal item (non-combo)
#             if not itemdetails.sales_order_item_detail.item_combo:
#                 dc_draft_count = (itemdetails.sales_order_item_detail.dc_draft_count or 0)
#                 dc_submit_count = (itemdetails.sales_order_item_detail.dc_submit_count or 0)
#                 if  dc_submit_count+itemdetails.qty <= so_item_details.qty:

#                     if item_master.batch_number:
#                         stock_result =   handleStockReduce(
#                             item_master.id,
#                             itemdetails.store.id,
#                             itemdetails.batch.id,
#                             itemdetails.qty,
#                             [],
#                             data,
#                             itemdetails,
#                             itemdetails.sales_order_item_detail,
#                             item_master
#                         )
#                     elif item_master.serial:
#                         serial_ids = [s.id for s in itemdetails.serial.all()]
#                         stock_result = handleStockReduce(
#                             item_master.id,
#                             itemdetails.store.id,
#                             "",
#                             itemdetails.qty,
#                             serial_ids,
#                             data,
#                             itemdetails,
#                             itemdetails.sales_order_item_detail,
#                             item_master
#                         )
#                     else:
#                         stock_result = handleStockReduce(
#                         item_master.id,
#                         itemdetails.store.id,
#                         "",
#                         itemdetails.qty,
#                         [],
#                         data,
#                         itemdetails,
#                         itemdetails.sales_order_item_detail,
#                         item_master
#                         )
#                     if not stock_result['success'] and len(stock_result['error'])>0:
#                         return {"success": False, "errors":errors}
#                 else:
#                     errors.append(f"Cannot process part {item_master}: entered quantity exceeds the Sales Order item quantity.")
#                     return {"success": success, "errors":errors}
#             # Combo items
#             elif itemdetails.item_combo_itemdetails.exists():
#                 for combo_item in itemdetails.item_combo_itemdetails.all():
#                     if combo_item.stock_reduce:
#                         continue
#                     actual_qty = combo_item.item_combo.qty
#                     combo_item_master = combo_item.item_combo.itemmaster
#                     dc_combo_submit_count = (combo_item.item_combo.dc_submit_count or 0)
#                     total_qty = (dc_combo_submit_count or 0)+(combo_item.qty or 0)
#                     if actual_qty >=total_qty:
#                         if combo_item_master.batch_number:
#                             stock_result_ = handleStockReduce(
#                                 combo_item_master.id,
#                                 combo_item.store.id,
#                                 combo_item.batch.id,
#                                 combo_item.qty,
#                                 [],
#                                 data,
#                                 combo_item,
#                                 combo_item.item_combo,
#                                 combo_item_master
#                             )
#                         elif combo_item_master.serial:
#                             serial_ids = [s.id for s in combo_item.serial.all()]
#                             stock_result_ = handleStockReduce(
#                                 combo_item_master.id,
#                                 combo_item.store.id,
#                                 "",
#                                 combo_item.qty,
#                                 serial_ids,
#                                 data,
#                                 combo_item,
#                                 combo_item.item_combo,
#                                 combo_item_master
#                             )
                            
#                         else:
#                             stock_result_ = handleStockReduce(
#                                 combo_item_master.id,
#                                 combo_item.store.id,
#                                 "",
#                                 combo_item.qty,
#                                 [],
#                                 data,
#                                 combo_item,
#                                 combo_item.item_combo,
#                                 combo_item_master
#                             )
#                         if not stock_result_['success'] and len(stock_result_['error'])>0:
#                             return {"success": False, "errors":errors}
                    
#                     else:
#                         errors.append(f"Cannot process part {combo_item_master}: entered quantity exceeds the Sales Order item quantity.")
#                         return {"success": success, "errors":errors}
#                 # so_item_details
#                 if so_item_details and so_item_details.item_combo and combo_item.stock_reduce:
#                     if so_item_details.dc_submit_count is None:
#                         so_item_details.dc_submit_count = Decimal('0')
#                     so_item_details.dc_submit_count += itemdetails.qty
#                     if so_item_details.dc_draft_count >= itemdetails.qty:
#                         so_item_details.dc_draft_count -= itemdetails.qty
#                     so_item_details.save()
#             data.all_stock_reduce =True
#             data.save()
#         except Exception as e:
#             errors.append(f'{e}-----')
#     success = len(errors) ==0
#     return {"success": success, "errors":errors}



# def handleStockReduce(partCode_id, store_id, batch_id, qty, serial_ids, data, dcItemDetail, salesOrderItemDetail, item_master):
#     stockReduce = StockReduce(
#         partCode_id=partCode_id,
#         Store_id=store_id,
#         batch_id=batch_id,
#         qty=qty,
#         serial_id_list=serial_ids
#     ) 
#     if serial_ids: 
#         result = stockReduce.reduceSerialNumber()
#     elif batch_id:
#         result = stockReduce.reduceBatchNumber()
#     else:
#         result = stockReduce.reduceNoBatchNoSerial()
#     if result['success']:
#         return UpdateTheStockHistoryAndSalesOrderItemDetails(data, dcItemDetail, salesOrderItemDetail, item_master, result)
#     else:
#         return result