from itemmaster.models import *
from django.shortcuts import get_object_or_404
# from ordered_set import OrderedSet

def fetch_recursive_bom(bom, result_set):
    raw_materials = bom.raw_material.all()
    for raw_material in raw_materials:
        bom_data_list = []
        try:
            rm_bom_link = get_object_or_404(RawMaterialBomLink, raw_material_id = raw_material.id)
        except:
           rm_bom_link = None
        if rm_bom_link:
            linked_child = Bom.objects.filter(id=rm_bom_link.bom.id)
            fetch_recursive_bom(linked_child[0], result_set)
            bom_data_list = bom_data_list + list(linked_child)
        result_set.append({'bom': bom_data_list, 'item_combo': [raw_material], 'parent': bom.finished_goods.part_no.id})
            
            
def fetch_recursive_bom_with_child_bom(bom, result_set, is_multi):
    raw_materials = bom.raw_material.all()
    for raw_material in raw_materials:
        bom_data_list = []
        try:
            rm_bom_link = get_object_or_404(RawMaterialBomLink, raw_material_id = raw_material.id)
        except:
           rm_bom_link = None
        if rm_bom_link:
            linked_child = Bom.objects.filter(id=rm_bom_link.bom.id)
            bom_data_list = bom_data_list + list(linked_child)
            result_set.append({'bom': bom_data_list, 'item_combo': [raw_material], 'parent': bom.finished_goods.part_no.id})
            if is_multi is not None and is_multi == True:
                fetch_recursive_bom_with_child_bom(linked_child[0], result_set, is_multi)
