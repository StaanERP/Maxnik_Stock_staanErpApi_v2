from decimal import Decimal
from django.utils.dateparse import parse_datetime
from itemmaster.models import User, ItemMaster, States, Districts, Pincode, AreaNames, purchaseOrder, SalesOrder, \
    StockHistoryLog, StockHistory, BatchNumber
from django.db.models import Sum
from datetime import datetime
import pytz
from django.forms.models import model_to_dict
from itemmaster.models import ItemStock, InventoryHandler
from django.db import connection
import csv
from django.conf import settings
from itemmaster.serializer import BatchNumberSerializer
ist_timezone = pytz.timezone('Asia/Kolkata')
from itemmaster.models import NumberingSeriesLinking, paymentMode
from django.contrib.auth.decorators import login_required


def get_stock_history_details(stock_history_master_data):
    processed_data = []
    for stock_items in stock_history_master_data:
        start_stock = int(Decimal(stock_items['previous_state']))
        end_stock = int(Decimal(int(Decimal(stock_items['updated_state']))))
        total_item_added = int(Decimal(stock_items['added']))
        if total_item_added != 0:
            total_item_added = f'+ {total_item_added}'
        total_item_deleted = int(Decimal(stock_items['reduced']))
        if total_item_deleted != 0:
            total_item_deleted = f'- {total_item_deleted}'
        user_obj = User.objects.filter(id=stock_items['saved_by']).first()
        try:
            timestamp = datetime.fromisoformat(str(stock_items['modified_date'])).astimezone(ist_timezone)
            formatted_date = timestamp.strftime("%d-%m-%Y %H:%M:%S")
        except ValueError:
            formatted_date = str(stock_items['modified_date'])
        user_name = None
        if user_obj:
            user_name = user_obj.username
        unit_name = ''
        try:
            unit_obj = ItemStock.objects.get(id=stock_items['stock_link'])
            if unit_obj:
                unit_name = unit_obj.unit.name


        except Exception as e:
            unit_name = ''
        data = {
            "id": stock_items['id'],
            'transaction_id': stock_items['transaction_id'],
            'transaction_module': stock_items['transaction_module'],
            'date': formatted_date,
            'part_code_id': stock_items['part_number'],
            'start_stock': start_stock,
            'end_stock': end_stock,
            'added': total_item_added,
            'reduced': total_item_deleted,
            'saved_by': user_name,
            'unit': unit_name,
            'display_id': stock_items['display_id'],
            "display_name": stock_items['display_name'],
            "is_delete": stock_items['is_delete']
        }
        processed_data.append(data)
    return processed_data


def get_all_related_orders(queryset):
    """using for get version of that current data of purchaseOrder"""
    version = set()  # Use a set to avoid duplicates
    version.add(queryset.id)

    def check_related(order):
        if order is None:
            return

        # Check for child orders
        child_orders = purchaseOrder.objects.filter(parent_order=order.id)
        for child in child_orders:
            if child.id not in version:
                version.add(child.id)
                check_related(child)

        # Check for parent order
        if order.parent_order and order.parent_order.id not in version:
            version.add(order.parent_order.id)
            check_related(order.parent_order)

    try:
        check_related(queryset)
    except Exception as e:
        print(f"Error accessing related orders for instance {queryset.id}: {e}")
    print(version)
    return sorted(version)  # Convert to list if needed


# Example usage:
# ids = get_all_related_orders(some_queryset)

# def get_all_child_praneted(queryset):
#     version = set()  # Use a set to avoid duplicates
#     version.add(queryset.id)
#
#     def check_parent(parent):
#         if parent is None:
#             return
#         child_orders_child = purchaseOrder.objects.filter(parent_order=parent.id)
#
#         for child in child_orders_child:
#             print(child,">>>>")
#             if child.id not in version:
#                 version.add(child.id)
#                 check_parent(child.parent_order)
#         child_orders_currenet = purchaseOrder.objects.filter(id=parent.id).first()
#         if child_orders_currenet.parent_order:
#             check_parent(child_orders_currenet.parent_order)
#             print(child_orders_currenet.parent_order,"---->>")
#
#     try:
#         if queryset.parent_order:
#             version.add(queryset.parent_order.id)
#             child_orders = queryset.parent_order
#             # print(child_orders, "paranted")
#             check_parent(child_orders)
#             # check_parent(child_orders)
#         check_parent(queryset)
#     except Exception as e:
#         print(f"Error accessing child orders for instance {queryset.id}: {e}")
#     print(version)
#     # print("List of IDs:", sorted(list(version)))
#     return sorted(list(version))  # Convert to list if needed


def posDetailsReports(reportDatas):
    processed_data = []
    totalAmount = {"FinalTotalValue": 0, "balanceAmount": 0, "bank": {}}
    for posData in reportDatas:
        pos_id = NumberingSeriesLinking.objects.filter(id=posData['POS_ID']).first()
        pos_id = pos_id.linked_model_id

        data = {
            "id": posData['id'],
            "IsPOS": posData['posType'],
            "OrderDate": posData['OrderDate'],
            "POSId": pos_id,
            "CosName": posData['CosName'],
            "Mobile": posData['Mobile'],
            "FinalTotalValue": posData['FinalTotalValue'],
            "balanceAmount": "",
            "Remarks": posData['Remarks'],
            "Payments": {}
        }
        totalAmount["FinalTotalValue"] += Decimal(posData['FinalTotalValue'])

        max_payment_id = max(posData['payment'], default=None)
        if max_payment_id != None:
            blance = paymentMode.objects.filter(id=max_payment_id).first()
            if blance:
                data['balanceAmount'] = (blance.balance_amount)
                totalAmount["balanceAmount"] += Decimal(blance.balance_amount)
        else:
            data['balanceAmount'] = posData['balance_Amount']
        try:
            for payment in posData.get('payment', []):
                paymentDetails = paymentMode.objects.filter(id=payment).first()
                if paymentDetails:
                    amount = paymentDetails.pay_amount
                    account = paymentDetails.payby.accounts_name
                    amount = float(amount)
                    if account in data["Payments"]:
                        data["Payments"][account] += amount
                    else:
                        data["Payments"][account] = amount
                    if account in totalAmount['bank']:
                        totalAmount['bank'][account] += amount
                    else:
                        totalAmount['bank'][account] = amount
            processed_data.append(data)
        except Exception as e:
            print(e)

    return processed_data, totalAmount


def process_item_combo_stock_statement(master, store):
    stock_check_ids = []
    total_qty = 0
    try:
        # stock_check_ids.append(master['id'])
        if master['item_combo_data']:
            for item in master['item_combo_data']:
                item_combo_dict = model_to_dict(item)
                stock_check_ids.append(item_combo_dict['part_number'])
        stock_check_ids = list(set(stock_check_ids))
        stock_items = ItemStock.objects.filter(part_number__in=stock_check_ids)
        if store:
            stock_items = stock_items.filter(store=store)
        fetched_part_numbers = list(set([x['part_number'] for x in stock_items.values('part_number')]))
        if len(stock_check_ids) != len(fetched_part_numbers):
            total_qty = 0
        else:
            filtered_items = stock_items.values('part_number').annotate(total_value=Sum('current_stock'))
            least_total_value_item = min(filtered_items, key=lambda x: x['total_value'])
            if least_total_value_item:
                total_qty = least_total_value_item['total_value']
    except:
        total_qty = 0
    return total_qty


def stockReduceFuntions(conference_id):
    reduced_id = []
    stock_historys = StockHistory.objects.filter(conference=conference_id, isTransfered=False)
    success = True
    error = []
    try:
        for stock_history in stock_historys:
            if stock_history.stock_link not in reduced_id:
                reduced_id.append(stock_history.stock_link)  # Avoid duplicate processing

                # Calculate total reduced count
                total_delete = stock_historys.filter(stock_link=stock_history.stock_link, action="DELETE", isTransfered=False)
                total_reduce_count = sum(float(item.reduced) for item in total_delete)
                if total_delete.exists():
                    try:
                        total_added = stock_historys.filter(stock_link=stock_history.stock_link, action="ADD", isTransfered=False)
                        remaining_reduce_count = total_reduce_count
                        iscompleted = False

                        for item in total_added:
                            if not iscompleted:
                                added_value = float(item.added)
                                if remaining_reduce_count == added_value:
                                    iscompleted = True
                                    item.isTransfered = True
                                elif remaining_reduce_count < added_value:
                                    item.added = remaining_reduce_count # Fully consumed the 'added' value
                                    item.isTransfered = True
                                    iscompleted =True
                                else:
                                    remaining_reduce_count -= added_value
                                    if remaining_reduce_count < 0:
                                        item.added = abs(remaining_reduce_count)
                                        iscompleted = True
                                        remaining_reduce_count = 0  # All reductions applied
                                        item.isTransfered = True

                                item.save()
                            else:
                                " remained item we want to delete "
                        try:
                            current_stock_instance = ItemStock.objects.get(id=stock_history.stock_link.id)
                            current_stock_instance.current_stock = max(0, float(
                                current_stock_instance.current_stock) - total_reduce_count)
                            current_stock_instance.save()
                        except ItemStock.DoesNotExist:
                            error.append(f"ItemStock with ID {stock_history.stock_link.id} not found.")
                    except Exception as e:
                        print(e,"---->")
                        error.append(e)
                    # Persist the updated 'added' value
                    # Debug prints for confirmation 
                else: 
                    total_added = stock_historys.filter(stock_link=stock_history.stock_link, action="ADD",
                                                        isTransfered=False)
                    total_added.delete()
    except Exception as e:
        print("->>", e)
        error.append(e)
    if len(error) > 0:
        success = False
    return {success : success, error : error}



def get_pos_stock_report_data(reportDatas):
    listOfPosStock = []
    for reportData in reportDatas:
        part_number = reportData['part_number']
        Itemmaster_detail = ItemMaster.objects.get(id=part_number)
        item_part_code = Itemmaster_detail.item_part_code
        item_name = Itemmaster_detail.item_name
        stock_id = reportData['store_link']
        history_id = reportData['id']

        # Extract action and count based on the action
        action = reportData['action']
        count_str = reportData['added' if action == 'ADD' else 'reduced']

        try:
            count = int(float(count_str))  # Convert to float first to handle decimal values, then to int
        except ValueError as e:
            print(f"Error converting count: {e}")
            continue  # Skip this record if there is a conversion error

        # Find the index of the part_number in listOfPosStock if it exists
        index = next((i for i, item in enumerate(listOfPosStock) if part_number in item), None)

        if index is not None:  # If part_number exists in listOfPosStock
            try:
                if action == 'ADD':
                    listOfPosStock[index][part_number]['stock_in'] = listOfPosStock[index].get(part_number, {}).get(
                        'stock_in',
                        0) + count
                elif action == 'DELETE':
                    listOfPosStock[index][part_number]['stock_out'] = listOfPosStock[index].get(part_number, {}).get(
                        'stock_out',
                        0) + count
            except Exception as e:
                print(e, "iddd")
        else:  # If part_number does not exist in listOfPosStock
            try:
                if action == 'ADD':
                    listOfPosStock.append(
                        {part_number: {'stock_in': count, 'part_number': item_part_code, 'part_name': item_name, }})
                elif action == 'DELETE':
                    listOfPosStock.append(
                        {part_number: {'stock_out': count, 'part_number': item_part_code, 'part_name': item_name}})
            except Exception as e:
                print(e, "else")

        # Calculate balance for each part number
    for item in listOfPosStock:
        part_number = list(item.keys())[0]
        in_count = item[part_number].get('stock_in', 0)
        out_count = item[part_number].get('stock_out', 0)
        item[part_number]['stock_blance'] = in_count - out_count
        # if blance_ >=0:
        #     print( "in_count", in_count , "out_count", out_count,"blance_", blance_)
        #     stockReduceFuntions(blance_)
    all_values = [value for item in listOfPosStock for value in item.values()]
    sorted_values = sorted(all_values, key=lambda x: x['part_number'])
    for index, item in enumerate(sorted_values, start=1):
        item['sno'] = index
    return sorted_values


from django.db.models import Count

from django.db.models import Min, Max, F


# def mergeTheBatchNumber():
#     """Count how many times the same part_number has been added to stock for each batch_number."""
#     data_list = []
#     exit_id = []
#     try:
#         # Group by part_number and batch_number, then annotate with min stock_id and total quantity
#         stock_summary = (
#             ItemStock.objects
#             .values('part_number_id', 'batch_number_id', 'batch_number__batch_number_name',
#                     'part_number__item_part_code')
#             .annotate(min_stock_id=Min('id'))
#         )
#         for entry in stock_summary:
#             part_number_id = entry['part_number_id']
#             batch_number_id = entry['batch_number_id']
#             batch_name = entry['batch_number__batch_number_name']
#             part_code = entry['part_number__item_part_code']
#
#             # Get all stock entries for the specific part number and batch
#             stock_entries = ItemStock.objects.filter(
#                 part_number_id=part_number_id,
#                 batch_number_id=batch_number_id,
#                 store__store_name="Conference"
#             )
#             total_qty = sum(stock.current_stock for stock in stock_entries)
#
#             # Update the minimum stock_id entry with the total_qty
#             if stock_entries:
#                 print(part_code)
#                 print("entry['min_stock_id']", entry['min_stock_id'])
#                 min_stock_entry = stock_entries.filter(id=entry['min_stock_id']).first()
#                 print("min_stock_entry", min_stock_entry)
#                 if min_stock_entry:
#                     # Update the total_qty for the minimum stock_id entry
#                     min_stock_entry.current_stock = total_qty
#                     min_stock_entry.save()
#                     # Update StockHistoryLog and StockHistory to reference min_stock_entry
#                     try:
#                         StockHistoryLog.objects.filter(stock_link__in=stock_entries).update(stock_link=min_stock_entry)
#                         StockHistory.objects.filter(stock_link__in=stock_entries).update(stock_link=min_stock_entry)
#                     except Exception as e:
#                         print(e, "on update")
#                     # Delete all entries except the min_stock_entry
#                     try:
#                         stock_entries.exclude(id=min_stock_entry.id).delete()
#                     except  Exception as e:
#                         print(e)
#
#                     data_list.append({
#                         'stock_id': min_stock_entry.id,
#                         'id': min_stock_entry.part_number.id,
#                         'part_code': part_code,
#                         'batch': batch_name,
#                         'batch_id': batch_number_id,
#                         'total_qty': min_stock_entry.current_stock,
#                     })
#                     print({
#                         'stock_id': min_stock_entry.id,
#                         'id': min_stock_entry.part_number.id,
#                         'part_code': part_code,
#                         'batch': batch_name,
#                         'batch_id': batch_number_id,
#                         'total_qty': min_stock_entry.current_stock,
#                     })
#     except Exception as e:
#         print(f"Error: {e}")
def mergeTheBatchNumber():
    """Count how many times the same part_number has been added to stock for each batch_number."""
    data_list = []
    try:
        # Group by part_number and batch_number, then annotate with total quantity
        stock_summary = (
            ItemStock.objects
            .values('part_number_id', 'batch_number_id', 'batch_number__batch_number_name',
                    'part_number__item_part_code')
        )

        for entry in stock_summary:
            part_number_id = entry['part_number_id']
            batch_number_id = entry['batch_number_id']
            batch_name = entry['batch_number__batch_number_name']
            part_code = entry['part_number__item_part_code']

            # Get all stock entries for the specific part number and batch
            stock_entries = ItemStock.objects.filter(
                part_number_id=part_number_id,
                batch_number_id=batch_number_id,
                store__store_name="Conference"
            )

            if stock_entries.exists():
                # Calculate total quantity and find the minimum stock ID
                total_qty = sum(stock.current_stock for stock in stock_entries)
                min_stock_entry = stock_entries.order_by('id').first()  # Get the entry with the smallest ID

                if min_stock_entry:
                    # Update total_qty for the minimum stock_id entry
                    min_stock_entry.current_stock = total_qty
                    min_stock_entry.save()

                    # Update StockHistoryLog and StockHistory to reference min_stock_entry
                    try:
                        StockHistoryLog.objects.filter(stock_link__in=stock_entries).update(stock_link=min_stock_entry)
                        StockHistory.objects.filter(stock_link__in=stock_entries).update(stock_link=min_stock_entry)
                    except Exception as e:
                        print(e, "on update")

                    # Delete all entries except the min_stock_entry
                    try:
                        stock_entries.exclude(id=min_stock_entry.id).delete()
                    except Exception as e:
                        print(e)

                    # Append the result to data_list
                    data_list.append({
                        'stock_id': min_stock_entry.id,
                        'id': min_stock_entry.part_number.id,
                        'part_code': part_code,
                        'batch': batch_name,
                        'batch_id': batch_number_id,
                        'total_qty': min_stock_entry.current_stock,
                    })
                    print({
                        'stock_id': min_stock_entry.id,
                        'id': min_stock_entry.part_number.id,
                        'part_code': part_code,
                        'batch': batch_name,
                        'batch_id': batch_number_id,
                        'total_qty': min_stock_entry.current_stock,
                    })
    except Exception as e:
        print(f"Error: {e}")


def correct_the_batch_number_and_part_code_in_stock():
    for index, data in enumerate(ItemStock.objects.all()):
        # if index < 10:
        try:
            if data.batch_number:
                # Check for existing BatchNumber using the part_number ID and batch_number_name
                batch_number_queryset = BatchNumber.objects.filter(
                    part_number__id=data.part_number.id,
                    batch_number_name=data.batch_number.batch_number_name
                )

                # If an existing BatchNumber is found, update the current item
                if batch_number_queryset.exists():
                    # Set the batch_number to the existing one
                    data.batch_number = batch_number_queryset.first()  # Get the first matching instance
                    data.save()
                else:
                    # Create a new BatchNumber if none exists
                    kwargs = {
                        "part_number": data.part_number.id,
                        "batch_number_name": data.batch_number.batch_number_name
                    }
                    serializer = BatchNumberSerializer(data=kwargs)
                    if serializer.is_valid():
                        batch_number_item = serializer.save()
                        # Optionally, update the data.batch_number to the newly created item
                        data.batch_number = batch_number_item
                        data.save()

                # Print debug information
                print("index", index)
                print("data.batch_number", data.batch_number)
                print("data.part_number.id", data.part_number.id)
                print("batch_number_name", data.batch_number.batch_number_name)
                print("stockid", data.id)
        except Exception as e:
            print(f"Error processing index {index}: {e}")


def count_stock_entries():
    """Count how many times the same part_number has been added to stock for each batch_number."""
    data_list = []
    exit_id = []
    # Filter the ItemStock records for the specified part_number
    try:
        for i in ItemStock.objects.all():
            if i.part_number.batch_number:
                stock_entries = (
                    ItemStock.objects
                    .filter(part_number_id=i.part_number.id, store__store_name="Conference")  # Filtering by part_number
                    # .values('batch_number__id', 'batch_number__batch_number_name', "part_number__item_part_code",
                    #         "part_number__id")  # Group by batch_number
                    # .annotate(count=Count('id'))  # Count occurrences
                )
                if len(stock_entries) >= 1:

                    for entry in stock_entries:
                        if entry.id not in exit_id   :
                            exit_id.append(entry.id)

                            try:
                                data_list.append({
                                    'stock_id': entry.id,
                                    'id': entry.part_number.id,
                                    'part_code': entry.part_number.item_part_code,
                                    'batch': entry.batch_number.batch_number_name,
                                    'batch_id': entry.batch_number.id,
                                    'total_qty': entry.current_stock,
                                })
                                print({
                                    'stock_id': entry.id,
                                    'id': entry.part_number.id,
                                    'part_code': entry.part_number.item_part_code,
                                    'batch': entry.batch_number.batch_number_name,
                                    'batch_id': entry.batch_number.id,
                                    'total_qty': entry.current_stock,
                                })
                            except Exception as e:
                                print(e, entry.part_number.item_part_code)
    except Exception as e:
        print(e)
    # Save to CSV
    print(data_list)
    save_data_to_csv(data_list, "test_data.csv")

# merge the dup
# def dataFrominventerHandlear():
#     start_date = parse_datetime('2024-07-27T00:00:00')
#     end_date = parse_datetime('2024-08-04T23:59:59')
#     part_list = []
#     inventory_handler = InventoryHandler.objects.filter(created_at__range=(start_date, end_date))
#     for i in inventory_handler:
#         for j in i.inventory_id.all():
#             print("part", j.part_number.item_part_code,)
#             try:
#                 if j:
#                     part_list.append({
#                         "part_code": j.part_number.item_part_code,  # Assuming part_code has an item_part_code attribute
#                         "item_name": j.qty,  # Assuming part_code has an item_name attribute
#
#                     })
#             except Exception as e:
#                 print(e)
#     print(part_list)
#     save_data_to_csv(part_list, "inventory_list.csv")


# def get_current_con_data():
#     part_list = []
#     pos = SalesOrder.objects.filter(marketingEvent="31")
#
#     part_code_qty = {}
#
#     # Iterate over SalesOrder objects
#     for data in pos:
#         # Iterate over related itemDetails
#         for data_2 in data.itemDetails.all():
#             part_code = data_2.part_code
#             qty = float(data_2.qty)  # Ensure qty is treated as a float for accurate aggregation
#
#             # If part_code already in dictionary, add the quantity
#             if part_code in part_code_qty:
#                 part_code_qty[part_code] += qty
#             else:
#                 # If part_code not in dictionary, add it with the current qty
#                 part_code_qty[part_code] = qty
#
#     # Convert dictionary to list of dictionaries
#     for part_code, total_qty in part_code_qty.items():
#         part_list.append({
#             "part_code": part_code.item_part_code,  # Assuming part_code has an item_part_code attribute
#             "item_name": part_code.item_name,  # Assuming part_code has an item_name attribute
#             "total_qty": total_qty
#         })
#     save_data_to_csv(part_list, "part_stock_data.csv")
#

def save_data_to_csv(data, filename):
    # Define the CSV fieldnames
    fieldnames = ["stock_id", 'id', 'part_code', 'batch', 'batch_id', 'total_qty']

    # Write data to CSV file
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data rows
        for row in data:
            writer.writerow(row)


import pandas as pd


def reactCSV():
    print("-->>>")
    url = r"C:\Users\Jegathish.E.STDOMAIN\OneDrive - Staan Bio-Med Engineering Private Limited\staan_erp\api\staan_api_v3\Item_Master_Duplicate_data.xlsx"

    try:
        # Use pd.read_excel to read the Excel file
        stock_report_df = pd.read_excel(url).fillna('')  # Fill NaN values with empty strings
        total_stock = 0
        data_index = 1

        for index, stock_data in stock_report_df.iterrows():
            part_code = stock_data['part_code']
            batch = stock_data['batch']
            print("part_code", part_code)
            print("batch", batch)
            data = ItemStock.objects.filter(part_number__item_part_code=part_code,
                                            batch_number__batch_number_name=batch,
                                            store__store_name="Conference")

            if len(data) > 1:
                data_index += 1
                print(data)
                for i in data:
                    print("id", i.id)
                    print("part_number", i.part_number.item_part_code)
                    print("batch_number", i.batch_number.batch_number_name)
                    print("---->>>> ")

    except Exception as e:
        print(f"Error: {e}")


def removeduplicate_address_master(reportDatas):
    states_list = []
    district_list = []
    pincode_list = []
    area_name_list = []
    states_object_list = []
    district_object_list = []
    pincode_object_list = []
    area_name_object_list = []
    for reportData in reportDatas:
        states_id = reportData['state']
        district_id = reportData['district']
        pincode_id = reportData['pincode']
        area_name_id = reportData['area_name']
        if states_id not in states_list:
            states_object = States.objects.filter(id=states_id)
            states_object_list.append(states_object)
            states_list.append(states_id)
        if district_id not in district_list:
            districts_object = Districts.objects.filter(id=district_id)
            district_object_list.append(districts_object)
            district_list.append(district_id)
        if pincode_id not in pincode_list:
            pincode_object = Pincode.objects.filter(id=pincode_id)
            pincode_object_list.append(pincode_object)
            pincode_list.append(pincode_id)
        if area_name_id not in area_name_list:
            Area_names_object = AreaNames.objects.filter(id=area_name_id)
            pincode_object_list.append(pincode_object)
            area_name_list.append(area_name_id)

    #     print(states_id, district_id, pincode_id, area_name_id)
    # print(len(states_list))
    # print(len(district_list))
    # print(len(pincode_list))
    # print(len(area_name_list))


def clearUnwantedBomData():
    try:
        with connection.cursor() as cursor:
            fg_item_delete_query = """
            delete from public.itemmaster_finishedgoods where id not in (select finished_goods_id from public.itemmaster_bom)
            """
            cursor.execute(fg_item_delete_query)

            scrap_item_delete_query = """
            delete from public.itemmaster_scrap where id not in (select scrap_id from public.itemmaster_bom_scrap)
            """
            cursor.execute(scrap_item_delete_query)

            rm_item_delete_query = """
            delete from public.itemmaster_rawmaterial where id not in (select rawmaterial_id from public.itemmaster_bom_raw_material)
            """
            cursor.execute(rm_item_delete_query)

            route_item_delete_query = """
            delete from public.itemmaster_bomrouting where id not in (select bomrouting_id from public.itemmaster_bom_routes)
            """
            cursor.execute(route_item_delete_query)
    except Exception as e:
        pass
