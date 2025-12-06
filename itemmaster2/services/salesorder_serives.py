from itemmaster2.models import *
from itemmaster2.Serializer import *
from itemmaster.mutations.Item_master_mutations import *
from itemmaster2.mutations.Item_master2_mutations import *
from decimal import Decimal, ROUND_HALF_UP
class SalesOrderService:
    def __init__(self, data, status, info):
        self.data = data
        self.status = status
        self.info = info
        self.success = False
        self.errors = []
        self.out_of_range_errors = []
        self.lead = None
        self.version = []
        self.salesorder = None
        self.gst_transaction= None
        self.valueIsHight = None
        self.validation = None
        self.warning = None
        self.state_of_company = None
        self.all_over_sales_order_item_taxable_value = None
        self.item_details = ""
        self.other_income_charges = ""
        self.old_itemdetails_ids = []
        self.old_other_income_ids = []
        self.item_combo_instance = {}
        self.item_details_instance = []
        self.other_income_charges_instance = None
        self.serializer = None
        self.parent = None
        self.currency = None
    
    def validate_required_fields(self):
        REQUIRED_FIELDS  = ['status','sales_order_date','gst_nature_transaction','sales_person',"due_date",
                            'credit_period','lead_no','department','currency',"buyer","buyer_address"
                            ,"buyer_contact_person","buyer_gstin_type","buyer_gstin",
                            "buyer_place_of_supply","consignee","consignee_address","consignee_contact_person",
                            "consignee_gstin_type","consignee_gstin","consignee_place_of_supply","net_amount"]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
                return False
        return True
    
    def update_status_instance(self):
        status_obj = CommanStatus.objects.filter(name=self.status, table="SalesOrder_2").first()
        if not status_obj:
            self.errors.append(f"Ask developer to add status '{self.status}' in CommanStatus.")
            return False
        self.data["status"] = status_obj.id
        return True
    
    def update_parent_order(self):
        if 'parent_order' in self.data and self.data['parent_order'] is not None and SalesOrder_2.objects.get(
                id=self.data['parent_order']):
            self.parent = SalesOrder_2.objects.filter(id=self.data['parent_order']).first()
            if self.parent: 
                self.data['sales_order_no'] = self.parent.sales_order_no.id
                return True
            else:
                self.errors.append("Parent Sales Order Not Found.")
                return False
        return True
    
    def validate_numbering(self):
        # Numbering Series validation
        conditions = {'resource': 'SalesOrder', 'default': True, "department": self.data.get("department")}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        return True
    
    def validate_item_combo(self, combo_data, index):
        combo_list = combo_data
        instance_list = []
        combo_lable = []
        for combo in combo_list:
            part_code = ItemMaster.objects.filter(id=combo.get('itemmaster')).first()
            combo_lable.append(part_code)
            for field in [ "itemmaster","uom","qty","rate","amount" ]:
                if combo.get(field) is None:
                    self.errors.append(f'{part_code}→{field} is required.')
           
            if combo.get('id'):
                instance = SalesOrder_2_temComboItemDetails.objects.filter(id=combo.get("id")).first()
                if not instance:
                    self.errors.append(f"Item Combo instance Not found.")
                    return False
                instance_list.append(instance)
            else:
                instance_list.append(None)
        if len(self.errors) > 0:
                return False

        Item_Combo_result = validate_common_data_and_send_with_instance(combo_list,instance_list,
                                                SalesOrder_2_temComboItemDetailsSerializer,combo_lable, self.info.context)
        if Item_Combo_result.get("error"):
            self.errors.extend(Item_Combo_result.get("error"))
            return False
        self.item_combo_instance[index] = Item_Combo_result.get("instance")
        return True

    def validate_item_details(self):
        instance_list = []
        item_details = self.data.get('item_details',[])
        
        updated_item = []
        item_lable = []
        if len(item_details) == 0:
            self.errors.append("At least one Item Details is Required.")
            return False
        if self.parent and self.data.get('id') is None and self.status == "Submit":
            old_ids_itemmaster_id = self.parent.item_details.all().values('id',"itemmaster__id",  'dc_submit_count')

        if item_details and len(item_details) > 0:
            for index, item in enumerate(item_details):
                if self.parent and self.data.get('id') is None and self.status == "Submit":
                    for old_details in old_ids_itemmaster_id:
                        if old_details['id'] == item.get("parent_itemDetail_id"):
                            item['dc_submit_count'] = old_details['dc_submit_count']
                

                if item.get('item_combo') and len(item.get('item_combo_item_details')) > 0:
                    if not self.validate_item_combo(item.get('item_combo_item_details'), index):
                        return False
                    else:
                        copy_item_detail = item.copy()
                        copy_item_detail["item_combo_item_details"] = []
                else:
                    copy_item_detail = item.copy()
                    copy_item_detail["item_combo_item_details"] = []
                item['index'] = index
                part_code = ItemMaster.objects.filter(id=item.get("itemmaster")).first()
                item_lable.append(part_code)
                if not part_code:
                    self.errors.append(f" Itemdetail instance Not found.")
                    return False
                
                for field in ["itemmaster","qty","rate","hsn", "uom","amount" ]:
                    if item.get(field) is None:
                        self.errors.append(f'{part_code} → {field} is required.')
                if item.get('id'):
                    instance = SalesOrder_2_ItemDetails.objects.filter(id=item.get("id")).first()
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                updated_item.append(copy_item_detail)
        
        Item_result = validate_common_data_and_send_with_instance(updated_item,instance_list,
                                                SalesOrder_2_ItemDetailsSerializer,item_lable, self.info.context)
        if Item_result.get("error"):
            self.errors.extend(Item_result.get("error"))
            return False 
        self.item_details_instance = Item_result.get("instance")
        return True

    def validate_other_income(self):
        instance_list = []
        other_charges = self.data.get('other_income_charge')
        other_charges_lable = []
        other_charges_error = None
        if len(other_charges) == 0:
            return True
        # Validate other income charges if available
        if other_charges and len(other_charges) > 0:
            for item in other_charges:
                charge_name = OtherIncomeCharges.objects.filter(id=item.other_income_charges_id).first()
                other_charges_lable.append(charge_name.name)
                
                for field in ["other_income_charges_id","amount"]:
                    if item.get(field) is None:
                        self.errors.append(f'{charge_name.name} → {field} is required.')
                if item.get("id"):
                    instance = SalesOrder_2_otherIncomeCharges.objects.filter(id=item.get("id")).first()
                    if not instance:
                        self.errors.append(f" Other Income Charges instance Not found.")
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
            other_charges_error = validate_common_data_and_send_with_instance(other_charges,instance_list,
                                                SalesOrder_2_otherIncomeChargesSerializer,other_charges_lable, self.info.context)
        if other_charges_error.get("error"):
            self.errors.extend(other_charges_error.get("error"))
            return False
        self.other_income_charges_instance = other_charges_error.get("instance")
        return True

    def validate_item_sell_range(self):
        item_data = self.data.get('item_details')
        if self.status == 'Submit' and len(item_data) > 0:
            itemDetilsValidations = SellItemCheckRange(item_data, self.data.get("exchange_rate"))
            if not itemDetilsValidations.get("success"):
                self.out_of_range_errors = itemDetilsValidations.get("error") 
                return False
            
        return True
    
    def validate_net_amount_in_lead_range(self):
        if self.data.get("lead_no"):
            try:
                taxableValue_ =  self.data.get('item_total_befor_tax', 0)

                if self.lead:
                    if self.parent or self.lead.status.name != "Won":
                        
                        id = self.data.get('id', None)
                        filter_conditions = {
                            'lead_no': self.lead.id,
                            'active': True,
                        }
                        salesOrder_list = SalesOrder_2.objects.filter(**filter_conditions)
                        if id is not None:
                            salesOrder_list = salesOrder_list.exclude(id=id)
                        if self.data.get("id") is None and self.data.get('parent_order') is not None:
                            salesOrder_list = salesOrder_list.exclude(id=self.data.get('parent_order'))
                        # Initialize variables for total sums
                        total_item_total_befor_tax_ = 0
                        # Loop through the salesOrder_list to sum item_total_befor_tax and other_charges_befor_tax
                        
                        exchange_rate = (self.currency.rate or 1)
                        for order in salesOrder_list:
                            total_item_total_befor_tax_ += Decimal(order.item_total_befor_tax/exchange_rate)
                        # Calculate the taxable value total
                        taxableValuetotal = total_item_total_befor_tax_
                        self.all_over_sales_order_item_taxable_value =Decimal((taxableValue_/exchange_rate) + taxableValuetotal).quantize(Decimal("0.000"), rounding=ROUND_HALF_UP)
                        if self.lead.lead_value < self.all_over_sales_order_item_taxable_value:
                            self.valueIsHight = True
                            self.validation = True
                        elif self.lead.lead_value == self.all_over_sales_order_item_taxable_value:
                            self.valueIsHight = None
                            self.validation = True
                            self.data['conformation_to_submit'] = True
                        elif self.lead.lead_value > self.all_over_sales_order_item_taxable_value:
                            self.valueIsHight = False
                            self.validation = False
                        if "conformation_to_submit" in self.data and not self.data.get("conformation_to_submit"):
                            self.warning = {self.lead.lead_no: float(self.lead.lead_value),
                                "Sales Order": float(Decimal(self.all_over_sales_order_item_taxable_value))}
                            self.data['conformation_to_submit'] = True
                            return False
                        else:
                            self.data['conformation_to_submit'] = False
                            self.valueIsHight = None
                            return True
                    else:
                        self.errors.append("This Lead Is Already Won.")
                        return False
                else:
                    self.errors.append("This Lead Is Not Found.")
                    return False
            except Exception as e:
                self.errors.append(f"An exception occurred -> {e}")
                return False

    def validate_activity(self):
        lead_activity_result = any(getattr(lead.status, "name", None) == "Planned" for lead in self.lead.activity.all())
        enquiry_result = False
        if self.lead.Enquiry:
            enquiry_result = any(
                        getattr(Enquiry.status, "name", None) == "Planned" for Enquiry in
                        self.lead.Enquiry.activity.all())
        if lead_activity_result and enquiry_result:
            self.errors.append("Some activity status is Planned make change completed or canceled.")
            return False
        return True
    
    def salesOrderValidateForAmend(self):
        """Validations for amending Sales Order"""
        errors = []
        try:
            # === Checking qty and rate ===
            item_details = self.data.get('item_details', [])
            if item_details:
                for item in item_details:
                    if item.get("parent_itemDetail_id"):
                        try:
                            parent_item_detail = SalesOrder_2_ItemDetails.objects.get(id=item['parent_itemDetail_id'])
                            dc_submit_qty = parent_item_detail.dc_submit_count or 0
                            dc_qty = dc_submit_qty
                            if not parent_item_detail.item_combo and dc_qty:
                            
                                parent_rate = parent_item_detail.after_discount_value_for_per_item or parent_item_detail.rate
                                current_rate = item.get('after_discount_value_for_per_item') or item.get('rate')
                                
                                if item['qty'] < dc_qty:
                                     
                                    errors.append(
                                        f"Cannot reduce quantity for part '{parent_item_detail.itemmaster.item_part_code}' "
                                        f"as {dc_qty} has already been drafted or submitted in DCs."
                                    )

                                if parent_rate != current_rate:
                                    errors.append(
                                        f"Cannot change rate for part '{parent_item_detail.itemmaster.item_part_code}' "
                                        f"as {dc_qty} has already been drafted or submitted in DCs."
                                    )

                        except SalesOrder_2_ItemDetails.DoesNotExist:
                            errors.append(f"Item detail not found for ID {item['parent_itemDetail_id']}")

            # === Checking other income charges ===
            otherincomes = self.data.get("other_income_charge", [])
            if otherincomes:
                for otherincome in otherincomes:
                    parent_id = otherincome.get('parent_other_income_id')
                    amount = otherincome.get('amount', 0)

                    if parent_id:
                        total_amount_of_child = SalesOrder_2_otherIncomeCharges.objects.filter(
                            parent=parent_id
                        ).aggregate(total=Sum('amount'))['total'] or 0

                        if amount < total_amount_of_child:
                            charge = SalesOrder_2_otherIncomeCharges.objects.filter(parent=parent_id).first()
                            errors.append(
                                f"Cannot reduce the amount in '{charge.other_income_charges_id.name}' "
                                f"because ₹{total_amount_of_child} already exists in linked records."
                            )

            # === Check for deletion of item details ===
            parent_items = list(self.parent.item_details.all().values('id', 'item_combo', 'dc_submit_count'))
            parent_others = list(self.parent.other_income_charge.values_list('id', flat=True))

            dc_contains_itemdetails = [
                item['id']
                for item in parent_items
                if  (item['dc_submit_count'] or 0) > 0
            ]
            for dc_item_detail_id in dc_contains_itemdetails:
                if not any(item.get('parent_itemDetail_id') == dc_item_detail_id for item in item_details):
                    try:
                        item_detail = SalesOrder_2_ItemDetails.objects.get(id=dc_item_detail_id)
                        errors.append(
                            f"'{item_detail.itemmaster.item_part_code}' is already linked with DC; deletion is not allowed."
                        )
                    except SalesOrder_2_ItemDetails.DoesNotExist:
                        errors.append(f"Item detail not found for ID {dc_item_detail_id}")

            for parent_other_id in parent_others:
                if not any(ch.get('parent_other_income_id') == parent_other_id for ch in otherincomes):
                    charges = SalesOrder_2_otherIncomeCharges.objects.filter(parent=parent_other_id)
                    if charges.exists():
                        first = charges.first()
                        errors.append(
                            f"'{first.other_income_charges_id.name}' is already linked with sales invoice; deletion is not allowed."
                        )

        except Exception as e:
            errors.append(f"Unexpected error occurred during validation: {str(e)}")

        return errors

    def SalesOrdervalidateQty(self):
        error =[]
        quotation = self.salesorder.quotations
        quotation_itemdetails = quotation.itemDetails.values(
                            "itemmaster__id", "itemmaster__item_part_code"
                        ).annotate(quotation_qty=Sum("qty"))
        quotation_qty_map = {
            item["itemmaster__id"]: {
                "qty": item["quotation_qty"],
                "part_code": item["itemmaster__item_part_code"]
            }
            for item in quotation_itemdetails
        }

        # 2. Get all item details from sales orders of the quotation
        sales_order_itemdetails = (
                SalesOrder_2.objects
                .filter(quotations=quotation.id, status__name="Submit", active=True)
                .values("item_details__itemmaster__id")
                .annotate(total_qty=Sum("item_details__qty"))
            ) 
        # 3. validate
        for item in sales_order_itemdetails:
            itemmaster_id = item["item_details__itemmaster__id"]
            sales_qty = item["total_qty"]
            if itemmaster_id in quotation_qty_map:
                allowed_qty = quotation_qty_map[itemmaster_id]["qty"]
                part_code = quotation_qty_map[itemmaster_id]["part_code"]
                if sales_qty > allowed_qty:
                    error.append(
                        f"Quantity for item {part_code} exceeds the quotation quantity. "
                        f"Quotation allowed: {allowed_qty}, but got: {sales_qty} in Sales Orders."
                    )
            # else:
            #     error.append(
            #         f"Item with ID {itemmaster_id} exists in Sales Orders but not in the quotation."
            #     )
        return error

    def calculate_item_combo(self, item_combo_list, amount, qty):
        item_combo_data = []

        # Calculate total value of all items
        total_value = sum(float(item['rate']) * float(item['qty']) for item in item_combo_list)

        if total_value == 0:
            return item_combo_list

        rounded_final_total = round(float(amount) / float(qty), 2)
        total_discount_needed = total_value - rounded_final_total

        # Calculate contributions and ratios
        item_contributions = [float(item['rate']) * float(item['qty']) for item in item_combo_list]
        ratios = [contribution / total_value for contribution in item_contributions]
        discounts = [total_discount_needed * ratio for ratio in ratios]

        for index, item in enumerate(item_combo_list):
            qty = float(item['qty'])
            rate = float(item['rate'])
            original_price = qty * rate

            discount = discounts[index]
            discounted_amount = original_price - discount
            final_discounted_amount = round(max(discounted_amount, 0), 3)
            after_discount_value_per_item = round(final_discounted_amount / qty, 3)

            item["afterDiscountValueForPerItem"] = str(after_discount_value_per_item)
            item["amount"] = str(final_discounted_amount)

            item_combo_data.append(item)

        return item_combo_data
    
    def update_tax_item_details(self):
        updated_item_details = []
        updated_other_income = []
        try:
            item_details = self.data.get("item_details", [])
            other_income_charge = self.data.get("other_income_charge", [])

            gst = self.gst_transaction
            is_specify_taxable = gst.gst_nature_type == "Specify" and gst.specify_type == "taxable"

            if is_specify_taxable:
                for item in item_details:
                    qty = item.get("qty", 0)
                    rate = item.get("rate", 0)
                    amount = qty * rate
                    item_combo = []
                    if item.get("item_combo") and len(item.get("item_combo_item_details", [])) > 0:
                        item_combo = json.dumps(self.calculate_item_combo(item["item_combo_item_details"], amount, qty), cls=DecimalEncoder)

                    item.update({
                        'after_discount_value_for_per_item': "0",
                        'discount_percentage': "0",
                        'discount_value': "0",
                        'final_value': "0",
                        'amount': str(amount),
                        "item_combo_item_details" :str(item_combo)
                    })

                    if gst.place_of_supply == "Intrastate":
                        item['sgst'] = gst.sgst_rate
                        item['cgst'] = gst.cgst_rate
                        item['cess'] = gst.cess_rate
                        item['tax'] = gst.sgst_rate+gst.cgst_rate
                        item['igst'] = ""
                    else:
                        item['sgst'] = ""
                        item['cgst'] = ""
                        item['igst'] = gst.igst_rate
                        item['cess'] = gst.cess_rate
                        item['tax'] = gst.igst_rate
                    updated_item_details.append(item)

                for charge in other_income_charge:
                    amount = charge.get("amount", "0")
                    charge.update({
                        'after_discount_value': "0",
                        'discount_value': "0"
                    })

                    if gst.place_of_supply == "Intrastate":
                        charge['sgst'] = gst.sgst_rate
                        charge['cgst'] = gst.cgst_rate
                        charge['cess'] = gst.cess_rate
                        charge['tax'] = gst.sgst_rate+gst.cgst_rate
                        charge['igst'] = ""
                    else:
                        charge['sgst'] = ""
                        charge['cgst'] = ""
                        charge['igst'] = gst.igst_rate
                        charge['cess'] = gst.cess_rate
                        charge['tax'] = gst.igst_rate
                    updated_other_income.append(charge)

            elif gst.gst_nature_type == "As per HSN":
                for item in item_details:
                    qty = item.get("qty", "0")
                    rate = item.get("rate", "0")
                    amount = qty * rate
                    item_combo = []
                    if item.get("item_combo") and len(item.get("item_combo_item_details", [])) > 0:
                        item_combo = json.dumps(self.calculate_item_combo(item["item_combo_item_details"], amount, qty), cls=DecimalEncoder)

                    hsn_id = item.get("hsn")
                    hsn = Hsn.objects.filter(id=hsn_id).first()
                    if not hsn or not hsn.gst_rates:
                        continue

                    item.update({
                        'after_discount_value_for_per_item': "0",
                        'discount_percentage': "0",
                        'discount_value': "0",
                        'final_value': "0",
                        'amount': str(amount),
                        "item_combo_item_details" :str(item_combo)
                    }) 
                    if str(self.data.get("buyer_state", "")).lower() == str(self.state_of_company.get("address__state")).lower():
                        rate_half = hsn.gst_rates.rate / 2
                        item['sgst'] = rate_half
                        item['cgst'] = rate_half
                        item['cess'] = hsn.cess_rate
                        item['tax'] = hsn.gst_rates.rate
                        item['igst'] = ""
                    else:
                        item['sgst'] = ""
                        item['cgst'] = ""
                        item['igst'] = hsn.gst_rates.rate
                        item['cess'] = hsn.cess_rate
                        item['tax'] = hsn.gst_rates.rate
                    updated_item_details.append(item)

                for charge in other_income_charge:
                    amount = charge.get("amount", 0)
                    charge_id = charge.get("other_income_charges_id")
                    charge_obj = OtherIncomeCharges.objects.filter(id=charge_id).first()
                    if not charge_obj or not charge_obj.hsn:
                        continue

                    charge.update({
                        'after_discount_value': "0",
                        'discount_value': "0"
                    })

                    if str(self.data.get("buyer_state", "")).lower() == str(self.state_of_company.get("address__state")).lower():
                        half_rate = charge_obj.hsn.gst_rates.rate / 2
                        charge['sgst'] = half_rate
                        charge['cgst'] = half_rate
                        charge['cess'] = charge_obj.hsn.cess_rate
                        charge['tax'] = charge_obj.hsn.gst_rates.rate
                        charge['igst'] = ""
                    else:
                        charge['sgst'] = ""
                        charge['cgst'] = ""
                        charge['igst'] = charge_obj.hsn.gst_rates.rate
                        charge['cess'] = charge_obj.hsn.cess_rate
                        charge['tax'] = charge_obj.hsn.gst_rates.rate
                    updated_other_income.append(charge)

            else:  # Exempted or others
                for item in item_details:
                    qty = item.get("qty", 0)
                    rate = item.get("rate", 0)
                    amount = qty * rate
                    item_combo = []
                    if item.get("item_combo") and len(item.get("item_combo_item_details", [])) > 0:
                        item_combo = json.dumps(self.calculate_item_combo(item["item_combo_item_details"], amount, qty), cls=DecimalEncoder)

                    item.update({
                        'after_discount_value_for_per_item': "0",
                        'discount_percentage': "0",
                        'discount_value': "0",
                        'final_value': "0",
                        'sgst': "0",
                        'cgst': "0",
                        'igst': "0",
                        'cess': "0",
                        "tax" : "0",
                        'amount': str(amount),
                        "item_combo_item_details" :str(item_combo)
                    })
                    updated_item_details.append(item)

                for charge in other_income_charge:
                    charge.update({
                        'after_discount_value': "0",
                        'discount_value': "0",
                        'sgst': "0",
                        'cgst': "0",
                        'igst': "0",
                        'cess': "0",
                        "tax" : "0",
                    })
                    updated_other_income.append(charge) 
             
            self.item_details = updated_item_details
            self.other_income_charges = updated_other_income

        except Exception as e:
            self.errors.append(f"An exception occurred-- {e}")

    def validate_tax(self):
        item_details = self.data.get("item_details", [])  
        if self.gst_transaction.gst_nature_type == "Specify" and self.gst_transaction.specify_type == "taxable":
            
            for item in item_details:
                if self.gst_transaction.place_of_supply == "Intrastate":
                    if (
                        item.get("sgst") != self.gst_transaction.sgst_rate or
                        item.get("cgst") != self.gst_transaction.cgst_rate or
                        item.get("cess") != self.gst_transaction.cess_rate
                    ):
                        return False
                elif self.gst_transaction.place_of_supply == "Interstate":
                    if (
                        item.get("igst") != self.gst_transaction.igst_rate or
                        item.get("cess") != self.gst_transaction.cess_rate
                    ):
                        return False
            
            return True

        elif self.gst_transaction.gst_nature_type == "As per HSN":
            
            for item in item_details:
                hsn = Hsn.objects.filter(id=item.hsn).first() 
                
                if ((item.sgst or 0) + (item.cgst or 0) + (item.igst or 0)) != hsn.gst_rates.rate or (item.cess or 0) !=(hsn.cess_rate or 0):
                     
                    return False 
            return True


        else: 
            # Fallback check — if all 4 rates are present, reject
            for item in item_details:
                if item.get("sgst") or item.get("cgst") or item.get("igst") or item.get("cess"):
                    return False
            return True

    def validate(self):
        self.state_of_company = CompanyMaster.objects.all().values("address__state").first()
        if not self.validate_numbering():
            return False
        if not self.update_parent_order():
            return False
        if self.parent != None and self.salesorder == None and self.status  == "Submit":
            error = self.salesOrderValidateForAmend()
            if len(error) > 0:
                self.errors.extend(error)
                return False
        if self.salesorder and self.status == "Submit" and self.salesorder.quotations :
            result = self.SalesOrdervalidateQty()
            if len(result) > 0:
                self.errors.extend(result)
                return False
        if not self.validate_item_details():
            return False
        if not self.validate_other_income():
            return False
        
        
        if self.status == 'Submit': 
            if self.parent == None and self.data.get("id"):
                if not self.validate_tax():
                    
                    self.update_tax_item_details()
                    return False  
            if not self.validate_item_sell_range():
                return False
            if not self.currency:
                self.errors.append("Currecny Not Found.")
                return False
            if not self.validate_net_amount_in_lead_range():
                return False
        if self.validation:
            if not self.validate_activity():
                return False
        return True

    def process_item_combo(self, index):
        update_data =  []
        try:
            for combo_serializer in self.item_combo_instance.get(index):
                if combo_serializer:
                    combo_serializer.save()
                    update_data.append(combo_serializer.instance)
            return {"instance": update_data, "success":True, "error" : []}
        except Exception as e:
            return {"instance": [], "success":False, "error" : f"Unexpeted error occurred in item combo save {str(e)}."}
        

    def process_items(self):
        try:
            item_details = self.data.get('item_details',[])
            item_details_id= []

            if len(item_details) != len(self.item_details_instance):
                self.errors.append("Item length and item instance length is mismatch.")
                return False

            for item, item_serializer in zip(item_details, self.item_details_instance):
                combo_instances = None
                if self.item_combo_instance.get(item.get("index")):
                    combo_instance = self.process_item_combo(item.get("index"))
                    if combo_instance.get("success"):
                        combo_instances= combo_instance.get("instance")
                    else:
                        self.errors.append(combo_instance.get("error"))
                        continue
                if item_serializer:
                    item_serializer.save() 
                    item_details_id.append(item_serializer.instance.id)
                    if combo_instances:
                        item_serializer.instance.item_combo_item_details.set(combo_instances)
            self.data['item_details'] = item_details_id
            return True
        except Exception as e: 
            self.errors.append(f"Unexpeted error occurred in item details {str(e)}.")
            return False
        

    def process_other_income(self):
        other_charge_instances = []
        try:
            if self.other_income_charges_instance:
                for other_serializer in self.other_income_charges_instance:
                    other_serializer.save()
                    other_charge_instances.append(other_serializer.instance.id)
            self.data['other_income_charge'] = other_charge_instances
            return True
        except Exception as e:
            self.errors.append(f"Unexpeted error occurred in Other Income charge {str(e)}.")
            return False

    def get_salesorder_instance(self):
        if 'id' in self.data and self.data.get("id"):
            self.salesorder = SalesOrder_2.objects.filter(id=self.data.get("id")).first()
            
            if not self.salesorder:
                self.errors.append("SalesOrder Not Found.")
                return False
            else:
                self.old_itemdetails_ids = list(self.salesorder.item_details.values_list('id', flat=True))
                self.old_other_income_ids = list(self.salesorder.other_income_charge.values_list('id', flat=True))
                self.serializer = SalesOrder_2Serializer(self.salesorder, data=self.data, partial=True, context={'request': self.info.context})
                self.gst_transaction = self.salesorder.gst_nature_transaction
                self.currency = self.salesorder.currency

                if self.parent is None and self.status in ['Submit', "Draft"]:
                    self.data['gst_nature_type']= self.gst_transaction.gst_nature_type

                if not self.gst_transaction:
                    self.errors.append("GST Nature Transaction is missing.")
                    return False
                return True
        else:
            self.gst_transaction = GSTNatureTransaction.objects.filter(id=self.data.get("gst_nature_transaction")).first()
            if not self.gst_transaction:
                    self.errors.append("GST Nature Transaction is missing.")
                    return False
            if self.parent is None and self.status in ['Submit', "Draft"]:
                self.data['gst_nature_type']= self.gst_transaction.gst_nature_type

            self.serializer = SalesOrder_2Serializer(data=self.data, context={'request': self.info.context})
            return True
        
    def create_or_update(self):
        if self.serializer.is_valid():
            try:
                self.serializer.save()
                if self.data.get("id") == None and self.serializer.instance.lead_no:  # in lead update the sales order id
                    lead = self.lead
                    lead.sales_order_id.add(self.serializer.instance)
                    lead.save()
                self.version = get_all_related_version(self.serializer.instance, SalesOrder_2)
                if self.status == 'Submit' and  self.serializer.instance.buyer.is_lead:
                    customer = self.serializer.instance.buyer
                    customer.is_lead = False
                    customer.save()
                if self.status == 'Submit' and  self.serializer.instance.consignee.is_lead:
                    customer = self.serializer.instance.consignee
                    customer.is_lead = False
                    customer.save()
                if self.serializer.instance.lead_no and self.status == 'Submit' and self.validation:
                    lead_instance = self.serializer.instance.lead_no
                    status = CommanStatus.objects.filter(name="Won", table="Leads").first()
                    if status:
                        lead_instance.status = status
                        if self.all_over_sales_order_item_taxable_value is not None:
                            lead_instance.lead_value = self.all_over_sales_order_item_taxable_value
                        lead_instance.save()
            
                new_itemdetails_ids = list(self.serializer.instance.item_details.values_list('id', flat=True))
                deleteCommanLinkedTable(self.old_itemdetails_ids,
                                        new_itemdetails_ids,
                                        SalesOrder_2_ItemDetails)
                new_otherincomeCharges_ids = list(self.serializer.instance.other_income_charge.values_list('id', flat=True))
                deleteCommanLinkedTable(self.old_other_income_ids,
                                        new_otherincomeCharges_ids,
                                        SalesOrder_2_otherIncomeCharges)
                
                if self.parent and self.data.get('id') is None and self.status == "Submit" and self.parent.delivery_challans.exists():
                        # new_ids_itemmaster_id = dict(self.serializer.instance.item_details.values_list('id', 'itemmaster__id'))
                        # reversed_map = {v: k for k, v in new_ids_itemmaster_id.items()}

                        # self.serializer.instance.dc_links.set(self.parent.dc_links.all())

                        for dc in self.parent.delivery_challans.all():
                            # for itemDetails in dc.item_details.all():
                            #     old_itemmaster_id = itemDetails.sales_order_item_detail.itemmaster.id
                            #     new_item_detail_id = reversed_map.get(old_itemmaster_id)

                            #     if not new_item_detail_id:
                            #         # Log warning or skip
                            #         continue
                            #     itemDetails.sales_order_item_detail = SalesOrder_2_ItemDetails.objects.get(id=new_item_detail_id)
                            #     itemDetails.save()
                            dc.sales_order = self.serializer.instance
                            dc.save()

                        for sales_return in self.parent.salesreturn_set.all():
                            sales_return.sales_order = self.serializer.instance
                            sales_return.save()

                return True
            except CommonError as e:
                self.errors.append(str(e))
                return False
            except Exception as e:
                self.errors.append(f'An exception occurred -- {str(e)}')
                return False

        else:
            self.errors.extend([f"{field}: {'; '.join([str(e) for e in error])}"
                        for field, error in self.serializer.errors.items()])
            return False

    def execute(self):
        self.lead = Leads.objects.get(id=self.data.get("lead_no"))
        if not self.lead:
            self.errors.append("Lead not found.")
            return self.response()
        
        self.data["taxable_value"] = self.data.get("item_total_befor_tax", 0) + self.data.get("other_charges_befor_tax", 0)
        if not self.get_salesorder_instance():  # You should get the serializer instance
            return self.response()
        if not self.validate():
            return self.response()
        if not self.update_status_instance():
            return self.response()
        if not self.process_items():
            return self.response()
        if not self.process_other_income():
            return self.response()
        if not self.create_or_update():
            return self.response()
        self.success = True
        self.salesorder = self.serializer.instance
        return self.response()

    def response(self):
        return {
            "salesorder": self.salesorder,
            "success": self.success,
            "errors": self.errors,
            "outOfRangeErrors": self.out_of_range_errors,
            "item_details" : self.item_details,
            "other_income_charges" : self.other_income_charges,
            "warning":self.warning,
            "get_conformation_to_submit" : self.data.get("conformation_to_submit"),
            "valueIsHight":self.valueIsHight,
            "version": versionListType(versionList=self.version),
        }