from itemmaster.Utils.CommanUtils import *
from itemmaster.serializer import *
from datetime import datetime, date
from itemmaster.mutations.Item_master_mutations import *
from datetime import date

class ItemMasterService:
    def __init__(self,kwargs, info ):
        self.kwargs = kwargs
        self.errors = [] 
        self.info = info
        self.success = False
        self.item_master_obj = None

    
    def run_validations(self):
        if not self.get_item_master():
            return self.response()
        if not self.validate_item_combo_list():
            return self.response()
        if not self.validate_required_fields():
            return self.response()
        if not self.validate_alternate_uom():
            return self.response()
        if not self.validate_itemcombo():
            return self.response()
        if not self.validate_hsn_item_type():
            return self.response()
        if not self.validate_tds_tcs():
            return self.response()
        return self.save_item_master()

    def validate_required_fields(self):
        MAIN_REQUIRED_FIELDS = ["item_part_code","item_name","description","item_types"
                                ,"item_uom","item_group","item_indicators","category"]
        for field in MAIN_REQUIRED_FIELDS :
            if self.kwargs.get(field) is None:
                self.errors.append(f'{field} is required')
        if not self.kwargs.get("keep_stock"):
            if self.kwargs.get("serial") or self.kwargs.get("batch_number"):
                self.errors.append(f'Serial or batch selection is not allowed when ‘Keep Stock’ is set to False.')

        if  self.kwargs.get("item_combo_bool"):
            if self.kwargs.get("serial") or self.kwargs.get("batch_number"):
                self.errors.append(f'Serial or batch selection is not allowed when item combo  is set to True.')
        
             
        return len(self.errors) == 0

    def get_item_master(self):
        item_master_id = self.kwargs.get('id')
        if item_master_id:
            self.item_master_obj = ItemMaster.objects.filter(id=item_master_id).first()
            if not self.item_master_obj:
                self.errors.append("ItemMaster not found.")
                return False
            if self.item_master_obj.keep_stock != self.kwargs.get("keep_stock"):
                self.errors.append("Keep stock is not editable after creation.")
                return False
        else:
            self.item_master_obj = None
         

        return True
    

    def validate_item_combo_list(self):
        item_master_id = self.kwargs.get('id')
        item_combo_enabled = self.kwargs.get("item_combo_bool", False)

        if item_master_id:
            if not self.item_master_obj:
                self.errors.append("ItemMaster not found.")
                return False
            if self.item_master_obj.item_combo_bool != self.kwargs.get("item_combo_bool"):
                self.errors.append("Item Combo is not editable after creation.")
                return False
            if item_combo_enabled : 
                if not self.kwargs.get("item_combo_data", []):
                    self.errors.append("Item Combo list cannot be empty when Item_Combo is enabled.")
                    return False

        return True


    def validate_alternate_uom(self):
        alternate_list = self.kwargs.get('alternate_uom', [])
        instance_list = []
        uom_lable_list = []

        if alternate_list and len(alternate_list) > 0:

            for item in alternate_list:
                uom_data = UOM.objects.filter(id=item.get("addtional_unit")).first()
                uom_lable_list.append(uom_data.name)

                if item.get("variation") and  item.get("variation")  <= 0:
                    self.errors.append(f"{uom_data.name} variation must be greater than 0.")
                # if not item.get("variation"):
                #     self.errors.append(f"{uom_data.name} variation must be required.")
                
                if item.get('id'):
                    instance = Alternate_unit.objects.filter(id=item.get("id"))
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
                    
            if self.errors:
                return False

            alternate_uom_error = validate_common_data(alternate_list,instance_list,
                                                    Alternate_unitSerializer,
                                                        uom_lable_list,"")
            if len(alternate_uom_error) > 0:
                self.errors.append(alternate_uom_error)
                return False
        return True

    def validate_itemcombo(self):
        instance_list = []
        item_combo_list = self.kwargs.get('item_combo_data', [])
        combo_lable_list = []
        if self.kwargs.get('item_combo_data', []) and len(self.kwargs.get('item_combo_data', [])) > 0:
            for item in self.kwargs.get('item_combo_data'):
                part_code = ItemMaster.objects.filter(id=item.get('part_number')).first()
                combo_lable_list.append(part_code)
                if item.get('id'):
                    instance = Item_Combo.objects.filter(id=item.get("id")).first()
                    instance_list.append(instance)
                else:
                    instance_list.append(None)
            Item_Combo_error = validate_common_data(item_combo_list,
                                                        instance_list, ItemComboSerializer,
                                                        combo_lable_list,"")
            if len(Item_Combo_error) > 0:
                self.errors.append(Item_Combo_error)
                return False
        return True

    def validate_hsn_item_type(self):
        try:
            hsn_data = Hsn.objects.get(id=self.kwargs.get("item_hsn"))
            item_type = ItemType.objects.get(id=self.kwargs.get("item_types"))
            hsn_type = hsn_data.hsn_types.name
            if item_type.name == "Service" and hsn_type != "SAC":
                self.errors.append("Only SAC is allowed for items of type 'Service'.")
        except Hsn.DoesNotExist:
            self.errors.append("Invalid HSN ID.")
        except ItemType.DoesNotExist:
            self.errors.append("Invalid Item Type ID.")
        return    len(self.errors) == 0
    
    def validate_tds_tcs(self):
        try:
            tds_serializer= None
            TDS_REQUIRED_FIELDS = ['name', "percent_individual_with_pan",
                "percent_other_with_pan","effective_date"]
            TCS_REQUIRED_FIELDS = ['name', "percent_individual_with_pan",
                    "percent_other_with_pan",
                    "effective_date","percent_other_without_pan"]
            if "tds" in  self.kwargs and len(self.kwargs.get("tds")) >0 :
                tds_data = self.kwargs.get('tds')[0]
                for field in TDS_REQUIRED_FIELDS :
                    if tds_data.get(field) is None:
                        self.errors.append(f'{field} is required')
                if "id" in tds_data and tds_data.get("id") and len(self.errors) == 0:
                    tds_instance =  TDSMaster.objects.filter(id=tds_data.get("id")).first()
                    if tds_instance:
                        tds_serializer = TDSMasterSerializer(tds_instance, data=tds_data, partial=True)
                    else:
                        self.errors.append("TDS Not Found.")
                        return False
                elif len(self.errors) == 0:
                    tds_serializer = TDSMasterSerializer(data=tds_data)

                if tds_serializer and  not tds_serializer.is_valid():
                    self.errors.extend(
                            [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in tds_serializer.errors.items()]
                        )
                    return False
                
            if "tcs" in  self.kwargs and len(self.kwargs.get("tcs")) > 0 :
                tcs_serializer = None
                tcs_data = self.kwargs.get('tcs')[0]
                for field in TCS_REQUIRED_FIELDS :
                    if tcs_data.get(field) is None:
                        self.errors.append(f'{field} is required')
                if "id" in tcs_data and tcs_data.get("id") and len(self.errors) == 0 :
                    tcs_instance =  TCSMaster.objects.filter(id=tcs_data.get("id")).first()
                    if tcs_instance:
                        tcs_serializer = TCSMasterSerializer(tcs_instance, data=tcs_data, partial=True)
                    else:
                        self.errors.append("TDS Not Found.")
                        return False
                elif len(self.errors) == 0 :
                    tcs_serializer = TCSMasterSerializer(data=tcs_data) 
                if tcs_serializer and not tcs_serializer.is_valid():
                    self.errors.extend(
                            [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in tcs_serializer.errors.items()]
                        )
                    return False
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f'An exception occurred--- {e}')
            return False
        
    def SaveAlternateuom( self, data):
        instance_list = []
        uom_lable_list = []
        for item in data:
            uom_data = UOM.objects.filter(id=item.get("addtional_unit")).first()
            uom_lable_list.append(uom_data.name)
            if 'id' in item and item.get("id"):
                instance = Alternate_unit.objects.filter(id=item.get("id")).first()
                instance_list.append(instance)
            else:
                instance_list.append(None)
        return save_common_data(data, instance_list, Alternate_unitSerializer, uom_lable_list)

    def SaveItemcombo(self, datas, itemMasterID):
        update_data = []
        instance_list = []
        combo_lable_list = []
        for data in datas:
            if data['item_display'] is None and data['item_display_text']:
                already_exe =display_group.objects.filter(display=data['item_display_text'], part_number=itemMasterID).first()
                if already_exe:
                    data['item_display'] = already_exe.id
                else:
                    display_group_instance = display_group()
                    display_group_instance.display = data['item_display_text']
                    display_group_instance.part_number = itemMasterID
                    display_group_instance.save()
                    data['item_display'] = display_group_instance.id
                update_data.append(data)
            else:
                update_data.append(data)
        for item in update_data:
            part_code = ItemMaster.objects.filter(id=item.get('part_number')).first()
            combo_lable_list.append(part_code)
            if 'id' in item and item['id']:
                instance = Item_Combo.objects.filter(id=item.get("id")).first()
                instance_list.append(instance)
            else:
                instance_list.append(None)
        return save_common_data(datas, instance_list, ItemComboSerializer, combo_lable_list)

    def save_tds(self):
          if self.kwargs.get("tds") and len(self.kwargs.get("tds")) > 0:
            tds_data = self.kwargs.get("tds")[0]
            if tds_data.get("id"):
                tds_instance = TDSMaster.objects.filter(id=tds_data["id"]).first()
                if tds_instance:
                    if (tds_instance.percent_individual_with_pan != tds_data.get("percent_individual_with_pan")\
                        or  tds_instance.percent_other_with_pan != tds_data.get("percent_other_with_pan"))\
                        and date.today() != tds_data.get("effective_date"):
                        effective_result = SaveTdsTcsEffective_date(tds_instance, None,tds_data.get("effective_date"),
                            tds_data.get("percent_individual_with_pan"), tds_data.get("percent_other_with_pan"),
                            None, self.kwargs.get("modified_by"))
                        if effective_result.get("success"):
                            self.kwargs['tds_link'] = tds_data.get("id")
                            return True
                        else:
                            self.errors.append(effective_result.get("errors"))
                            return False
                            
                    tds_serializer = TDSMasterSerializer(tds_instance, data=tds_data, partial=True)
                    
                else:
                    self.errors.append("TDSMaster instance not found.")
                    return self.response()
            else:
                tds_serializer = TDSMasterSerializer(data=tds_data)
            if tds_serializer.is_valid():
                tds_serializer.save()
                self.kwargs['tds_link'] = tds_serializer.instance.id
                return True
            else:
                self.errors.extend([
                    f"TDS - {k}: {'; '.join(map(str, v))}" for k, v in tds_serializer.errors.items()
                ]) 
                return self.response()
        
    def save_tcs(self):
        # Save or update TCS
        if self.kwargs.get("tcs") and len(self.kwargs.get("tcs")) > 0:
            tcs_data = self.kwargs.get("tcs")[0]
            if tcs_data.get("id"):
                tcs_instance = TCSMaster.objects.filter(id=tcs_data["id"]).first() 
                if tcs_instance:
                    if (tcs_instance.percent_individual_with_pan != tcs_data.get("percent_individual_with_pan")
                        or  tcs_instance.percent_other_with_pan != tcs_data.get("percent_other_with_pan")
                        or tcs_instance.percent_other_without_pan != tcs_data.get("percent_other_without_pan"))\
                        and date.today() != tcs_data.get("effective_date"):
                        effective_result = SaveTdsTcsEffective_date( None, tcs_instance,tcs_data.get("effective_date"),
                            tcs_data.get("percent_individual_with_pan"), tcs_data.get("percent_other_with_pan"),
                              tcs_data.get("percent_other_without_pan"),self.kwargs.get("modified_by"))
                        if effective_result.get("success"):
                            self.kwargs['tcs_link'] = tcs_data.get("id")
                            return True
                        else:
                            self.errors.append(effective_result.get("errors"))
                            return False
                    tcs_serializer = TCSMasterSerializer(tcs_instance, data=tcs_data, partial=True)
                else:
                    self.errors.append("TCSMaster instance not found.")
                    return False
            else:
                tcs_serializer = TCSMasterSerializer(data=tcs_data)

            if tcs_serializer.is_valid():
                tcs_serializer.save()
                self.kwargs['tcs_link'] = tcs_serializer.instance.id
                return True
                
            else:
                self.errors.extend([
                    f"TCS - {k}: {'; '.join(map(str, v))}" for k, v in tcs_serializer.errors.items()
                ])
                return False

    def save_item_master(self):
        kwargs = self.kwargs
        prve_tds_id = None
        prve_tcs_id = None
        self.success = False
        self.save_tds()
        self.save_tcs()
        if "tds_link" not in self.kwargs:
            self.kwargs['tds_link'] = None
        if "tcs_link" not in self.kwargs:
            self.kwargs['tcs_link'] = None

        try:
            # Save combos
            if self.kwargs.get('item_combo_data'):
                result = self.SaveItemcombo(self.kwargs['item_combo_data'], self.item_master_obj)
                if not result['success']:
                    self.errors.extend(result['error'])
                    return self.response()
                else:
                    self.kwargs['item_combo_data'] = result['ids']
            # Save alternate uoms
            if self.kwargs.get('alternate_uom'):
                result = self.SaveAlternateuom(self.kwargs['alternate_uom'])
                
                if not result['success']:
                    self.errors.extend(result['error'])
                    return self.response()
                else:
                    self.kwargs['alternate_uom'] = result['ids']

            # Determine if update or create
            if 'id' in kwargs and kwargs.get("id"):
                instance = self.item_master_obj
                if not instance:
                    self.errors.append("ItemMaster not found.")
                    return self.response()
                prve_tds_id = instance.tds_link.id if instance.tds_link  else None
                prve_tcs_id = instance.tcs_link.id if instance.tcs_link else None
                alt_uom_pre = [u.id for u in instance.alternate_uom.all()]
                combo_pre = [c.id for c in instance.item_combo_data.all()]

                if instance.item_hsn.id != kwargs.get('item_hsn'):
                    kwargs['hsn_changed_date'] = datetime.now()

                serializer = ItemMasterSerializer(instance, data=kwargs, partial=True)
            else:
                kwargs['hsn_changed_date'] = datetime.now()
                serializer = ItemMasterSerializer(data=kwargs)
                alt_uom_pre, combo_pre = [], []

            if serializer.is_valid():
                serializer.save()
                self.item_master_obj = serializer.instance
                if prve_tds_id and not serializer.instance.tds_link:
                    TDSMaster.objects.filter(id=prve_tds_id).first().delete()
                if prve_tcs_id and not serializer.instance.tcs_link:
                    TCSMaster.objects.filter(id=prve_tcs_id).first().delete()
                # Auto-create serial stock history
                if not kwargs.get('id') and self.item_master_obj.serial and self.item_master_obj.serial_auto_gentrate:
                    StockSerialHistory.objects.create(
                        part_no=self.item_master_obj,
                        last_serial_history=self.item_master_obj.serial_starting
                    )
                
                current_combo_ids = self.item_master_obj.item_combo_data.values_list('id', flat=True)
                # delete combos
                deleteCommanLinkedTable(combo_pre, current_combo_ids , Item_Combo)
                current_alternate_ids = self.item_master_obj.alternate_uom.values_list('id', flat=True)
                # delete alternate uoms
                deleteCommanLinkedTable(alt_uom_pre, current_alternate_ids, Alternate_unit)

                self.item_master_obj.save()
                self.success = True
            else:
                self.errors.extend([f"{k}: {'; '.join(map(str, v))}" for k, v in serializer.errors.items()])
        except Exception as e:
            self.errors.append(str(e))

        return self.response()

    def response(self):
        return {"item_master":self.item_master_obj,
            "success":self.success,
            "errors":self.errors}