
from itemmaster2.models import *
from itemmaster2.Serializer import *
from itemmaster.mutations.Item_master_mutations import *
from itemmaster2.mutations.Item_master2_mutations import *

class QuotationService:
    def __init__(self, data, status, info):
        self.data = data
        self.status_text = status
        self.info = info
        self.status = None
        self.success = False
        self.errors = []
        self.out_of_range_errors = []
        self.version = []
        self.quotation = None
        self.gst_transaction = None
        self.state_of_company = None
        self.item_details = None
        self.other_income_charges = None
        self.item_combo_instance = {}
        self.item_details_instance = {}
        self.other_income_charges_instance = None
        self.old_itemdetails_ids = []
        self.old_other_income_ids = []
        self.parent = None

    def process(self):
        self.data["taxable_value"] = self.data.get("item_total_befor_tax", 0) + self.data.get("other_charges_befor_tax", 0)
        with transaction.atomic():
            if self.status_text in ['Draft', 'Submit']:
                if not self.validate_required_fields(): return self.response()
                if not self.validate_numbering(): return self.response()
                if not self.validate_lead_status(): return self.response()
                if not self.validate_item_details(): return self.response()
                if not self.validate_other_income(): return self.response()
                if not self.get_quotation_id(): return self.response()
                if self.status_text == "Submit":
                    company_obj = company_info()
                    if company_obj is None:
                        self.errors.append("Company Not Found.")
                        return self.response()
                    if self.parent == None and self.data.get("id"):
                        if not self.validate_tax():
                            self.update_tax_item_details()
                            return self.response()
                    if not self.validate_rate_sell_range():
                        return self.response()
                    self.state_of_company = company_obj
                if not self.process_items(): return self.response()
                if not self.process_other_income(): return self.response()
                if not self.create_or_update(): return self.response()
            else:
                self.errors.append(f"{self.status_text} is Unexpeted status.")
            return self.response()

    def validate_required_fields(self)-> bool:
        REQUIRED_FIELDS  = ['status','quotation_date','gst_nature_transaction','customer_id',
                            'customer_address','customer_contact_person','currency','sales_person',
                            "lead_no","department","terms_conditions","terms_conditions_text","net_amount"]
        for field in REQUIRED_FIELDS:
            if self.data.get(field) is None:
                self.errors.append(f'{field} is required.')
                return False
        return True

    def validate_numbering(self)-> bool:
        # Numbering Series validation
        if self.data.get("id"):
            return True
        conditions = {'resource': 'Quotations', 'default': True, "department": self.data.get("department")}
        numbering_series = NumberingSeries.objects.filter(**conditions).first()
        if not numbering_series:
            self.errors.append("No matching NumberingSeries found.")
            return False
        return True

    def validate_lead_status(self)-> bool:
        lead_objects = Leads.objects.filter(id=self.data.get("lead_no")).first()
        if lead_objects:
            if lead_objects.status.name == "Won":
                self.errors.append(f"Lead is already Won so can't {self.status}")
                return False
            elif lead_objects.status.name == "Lost":
                self.errors.append(f"Lead is already Lost so can't {self.status}")
                return False
            return True
        else:
            self.errors.append("Lead Not Found.")
            return False

    def validate_item_combo(self, combo_data, index):
        combo_list = combo_data
        instance_list = []
        combo_lable = []
        for combo in combo_list:
            part_code = ItemMaster.objects.filter(id=combo.get('itemmaster')).first()
            combo_lable.append(part_code)
            ITEM_COMBO_REQUIRED_FIELDS = ["itemmaster","uom","qty","rate","amount" ]
            for field in ITEM_COMBO_REQUIRED_FIELDS:
                if combo.get(field) is None:
                    self.errors.append(f'{part_code}→{field} is required.')
            if combo.get('id'):
                instance = QuotationsItemComboItemDetails.objects.filter(id=combo.get("id")).first()
                if not instance:
                    self.errors.append(f"Item Combo instance Not found.")
                    return False

                instance_list.append(instance)
            else:
                instance_list.append(None)

        item_result = validate_common_data_and_send_with_instance(combo_list,instance_list,
                                                QuotationsItemComboItemDetailsSerializer,combo_lable,self.info.context)
        if item_result.get("error"):
            self.errors.extend(item_result.get("error"))
            return False
        self.item_combo_instance[index] = item_result.get("instance")

        return True

    def validate_item_details(self)-> bool:
        instance_list = []
        item_details = self.data.get('itemDetails',[])
        updated_item = []
        item_lable = []
        if len(item_details) == 0:
            self.errors.append("At least one Item Details is Required.")
            return False
        if item_details and len(item_details) > 0:
            for index , item in enumerate(item_details):
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
                    instance = QuotationsItemDetails.objects.filter(id=item.get("id")).first()
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                updated_item.append(copy_item_detail) 
        Item_result = validate_common_data_and_send_with_instance(updated_item,instance_list,
                                                QuotationsItemDetailsSerializer,item_lable, self.info.context)
        if Item_result.get("error"):
            self.errors.extend(Item_result.get("error"))
            return False
        
        self.item_details_instance = Item_result.get("instance")
        return True

    def validate_other_income(self):
        instance_list = []
        other_charges = self.data.get('other_income_charge')
        other_charges_lable = []
         

        if len(other_charges) == 0:
            return True
        other_chares_ids = [data.get("other_income_charges_id") for data in other_charges]
        # Detect duplicates
        duplicates = set([x for x in other_chares_ids if other_chares_ids.count(x) > 1])

        if duplicates:
            self.errors.append(f"Duplicate items found for other income charges.")
            return False
        
        # Validate other income charges if available
        if other_charges and len(other_charges) > 0:
            for item in other_charges:
                charge_name = OtherIncomeCharges.objects.filter(id=item.other_income_charges_id).first()
                other_charges_lable.append(charge_name.name)
                
                for field in ["other_income_charges_id","tax","amount"]:
                    if item.get(field) is None:
                        self.errors.append(f'{charge_name.name} → {field} is required.')
                        continue
                if item.get("id"):
                    instance = QuotationsOtherIncomeCharges.objects.filter(id=item.get("id")).first()
                    if not instance:
                        self.errors.append(f" Other Income Charges instance Not found.")
                        continue
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
            other_charges_result = validate_common_data_and_send_with_instance(other_charges,instance_list,
                                                QuotationsOtherIncomeChargesSerializer,other_charges_lable, self.info.context)
        if other_charges_result.get("error"):
            self.errors.extend(other_charges_result.get("error"))
            return False
        self.other_income_charges_instance = other_charges_result.get("instance")
        return True

    def get_quotation_id(self):
        if 'id' in self.data and self.data.get("id") != None: 
            quotations = Quotations.objects.filter(id=self.data.get("id")).first()
            if not quotations:
                self.errors.append("Quotations Not Found.")
            else:
                self.quotation = quotations
                
                self.gst_transaction = quotations.gst_nature_transaction
                if not self.gst_transaction:
                    self.errors.append("GST Nature Transaction is missing.")
                    return False
                if self.parent is None and self.status in ['Submit', "Draft"]:
                    self.data['gst_nature_type']= self.gst_transaction.gst_nature_type
        else:
            if self.status_text == "Submit":
                if 'parent_order' in self.data and self.data['parent_order'] is not None and Quotations.objects.filter(
                    id=self.data['parent_order']).first():
                    parent = Quotations.objects.filter(id=self.data['parent_order']).first()
                    if parent:
                        self.parent= parent
                        self.data['quotation_no'] = parent.quotation_no.id
                        self.data['gst_nature_type']= parent.gst_nature_type
                    else:
                        self.errors.append("Parent Not Found.")
                    if SalesOrder_2.salesorder_2_set.exists():
                        status = SalesOrder_2.salesorder_2_set.first().status.name
                        if status in ['Submit', 'Canceled']:
                            self.errors.append(
                                f"Amendment not allowed: This quotation is linked to a sales order with status '{status}'.")
            else:
                self.gst_transaction = GSTNatureTransaction.objects.filter(id=self.data.get("gst_nature_transaction")).first()
                if not self.gst_transaction:
                    self.errors.append("GST Nature Transaction is missing.")
                if self.parent is None and self.status in ['Submit', "Draft"]:
                    self.data['gst_nature_type'] = self.gst_transaction.gst_nature_type
            if self.errors:
                return False
            return True

    def validate_rate_sell_range(self):
        if self.status == 'Submit' and len(self.errors) == 0 and len(self.data.get('itemDetails')) > 0:
            itemDetilsValidations = SellItemCheckRange(self.data.get('itemDetails'), self.data.get("exchange_rate"))
            if not itemDetilsValidations.get("success"):
                outOfRangeErrors = itemDetilsValidations.get("error")
                self.out_of_range_errors = outOfRangeErrors
                return False
            return True
    
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
            item_details = self.data.get("itemDetails", [])
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
                    else:
                        item['igst'] = gst.igst_rate
                        item['cess'] = gst.cess_rate
                        item['tax'] = gst.igst_rate
                    updated_item_details.append(item)
                
                for charge in other_income_charge:
                    amount = charge.get("amount", "0")
                    charge_id = charge.get("other_income_charges_id")
                    charge_name = OtherIncomeCharges.objects.filter(id=charge_id).first()
                    charge.update({
                        'after_discount_value': "0",
                        'discount_value': "0",
                        "charge_name":charge_name.name
                    })

                    if gst.place_of_supply == "Intrastate":
                        charge['sgst'] = gst.sgst_rate
                        charge['cgst'] = gst.cgst_rate
                        charge['cess'] = gst.cess_rate
                        charge['tax'] = gst.sgst_rate+gst.cgst_rate
                    else:
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
                    if str(item.get("states", "")).lower() == str(self.state_of_company.get("address__state")).lower():
                        rate_half = hsn.gst_rates.rate / 2
                        item['sgst'] = rate_half
                        item['cgst'] = rate_half
                        item['cess'] = hsn.cess_rate
                        item['tax'] = hsn.gst_rates.rate
                    else:
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
                        'discount_value': "0",
                        "charge_name":charge_obj.name
                    })

                    if str(charge.get("states", "")).lower() == str(self.state_of_company.get("address__state")).lower():
                        half_rate = charge_obj.hsn.gst_rates.rate / 2
                        charge['sgst'] = half_rate
                        charge['cgst'] = half_rate
                        charge['cess'] = charge_obj.hsn.cess_rate
                        charge['tax'] = charge_obj.hsn.gst_rates.rate
                    else:
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
                    charge_id = charge.get("other_income_charges_id")
                    charge_name = OtherIncomeCharges.objects.filter(id=charge_id).first()
                    charge.update({
                        'after_discount_value': "0",
                        'discount_value': "0",
                        'sgst': "0",
                        'cgst': "0",
                        'igst': "0",
                        'cess': "0",
                        "tax" : "0",
                        "charge_name":charge_name.name
                    })
                    updated_other_income.append(charge)

            self.item_details = updated_item_details
            self.other_income_charges = updated_other_income

        except Exception as e:
            self.errors.append(f"An exception occurred-- {e}")
        
    def validate_tax(self):
        item_details = self.data.get("itemDetails", [])
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
        if not self.validate_required_fields():
            return False
        if not self.validate_numbering():
            return False
        if not self.validate_lead_status():
            return False
        if not self.validate_item_details():
            return False
        if not self.validate_other_income():
            return False
        if not self.get_quotation_id():
            return False
        
        if self.status == 'Submit':
            if self.parent == None and self.data.get("id"):
                if not self.validate_tax():
                    self.update_tax_item_details()
                    return False
            if not self.validate_rate_sell_range():
                return False 
            return True
        return True

    def process_item_combo(self, index):
        update_data =  []
        try:
            if self.item_combo_instance[index]:
                for combo_serializer in self.item_combo_instance[index]:
                    if combo_serializer:
                        combo_serializer.save()
                        update_data.append(combo_serializer.instance)
            return {"instance": update_data, "success":True, "error" : []}
        except Exception as e:
            return {"instance": [], "success":False, "error" : f"Unexpeted error occurred in {str(e)}."}

    def process_items(self):
        try:
            item_details = self.data.get('itemDetails',[])
            item_details_id= []

            if len(item_details) != len(self.item_details_instance):
                self.errors.append("Item length and item instance length is mismatch.")
                return False

    
            for item, item_serializer in zip(item_details, self.item_details_instance):
                combo_instances = None
                if self.item_combo_instance[item.get("index")]:
                    combo_instance = self.process_item_combo(item.get("index"))
                    if combo_instance.get("success"):
                        combo_instances= combo_instance
                    else:
                        self.errors.append(combo_instance.get("error"))
                if item_serializer:
                    item_serializer.save()
                    item_details_id.append(item_serializer.instance.id)
                    if combo_instances:
                        item_serializer.instance.item_combo_item_details.set(combo_instances) 
            self.data['itemDetails'] = item_details_id    
            return True
        except Exception as e:
            self.errors.append(f"Unexpeted error occurred {str(e)}")
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
            self.errors.append(f"Unexpeted error occurred {str(e)}.")
            return False
        
    def update_lead_reference(self, quotation):
        lead_id = quotation.lead_no.id if quotation.lead_no else None
        parent_id = self.data.get("parent_order")

        if not self.data.get("id") and lead_id:
            lead = Leads.objects.get(id=lead_id)
            lead.quotation_ids.add(quotation)
            if parent_id:
                lead.quotation_ids.remove(quotation.parent_order)
            lead.save()

    def update_sales_order_reference(self, quotation):
        parent_id = self.data.get("parent_order")
        if not self.data.get("id") and parent_id:
            sales_orders = SalesOrder_2.objects.filter(quotations=parent_id)
            for so in sales_orders:
                so.quotations = quotation
                so.save()

    def create_or_update(self):
        quotation_instance = self.quotation

        if self.data.get("id"):
            if not quotation_instance:
                self.errors.append("Quotation not found.")
                return False

            self.old_itemdetails_ids = list(quotation_instance.itemDetails.values_list("id", flat=True))
            self.old_other_income_ids = list(quotation_instance.other_income_charge.values_list("id", flat=True))
            serializer = QuotationsSerializer(quotation_instance, data=self.data, partial=True)
        else:
            serializer = QuotationsSerializer(data=self.data)

        if not serializer.is_valid():
            self.errors = [
                f"{field}: {'; '.join(map(str, error))}"
                for field, error in serializer.errors.items()
            ]
            return False

        try:
            serializer.save()
            self.quotation = serializer.instance
            self.success = True
            if self.data.get("parent_order"):
                self.update_lead_reference(self.quotation)
                self.update_sales_order_reference(self.quotation)

            deleteCommanLinkedTable(self.old_itemdetails_ids, list(self.quotation.itemDetails.values_list('id', flat=True)), QuotationsItemDetails)
            deleteCommanLinkedTable(self.old_other_income_ids, list(self.quotation.other_income_charge.values_list('id', flat=True)), QuotationsOtherIncomeCharges)
            
            if serializer.instance:
                self.version = get_all_related_version(serializer.instance, Quotations)
            return True
        except CommonError as ce:
            self.errors.append(str(ce))
        except Exception as e:
            self.errors.append(f"Unexpected error: {str(e)}")
        return False

    def response(self):
        return {
            "quotation": self.quotation,
            "success": self.success,
            "errors": self.errors,
            "outOfRangeErrors": self.out_of_range_errors,
            "version": versionListType(versionList=self.version),
            "item_details" : self.item_details,
            "other_income_charges" : self.other_income_charges
        }
