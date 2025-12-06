import graphene
from django.db.models import ProtectedError
from itemmaster.serializer import *
from  itemmaster.GLSchema.material_request_schema import *


class MaterialRequestMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        request_no = graphene.String()
        status = graphene.Int()
        request_for = graphene.Int()
        request_date = graphene.String()
        production_order = graphene.Int()
        remarks = graphene.String()
        issuing_store = graphene.Int()
        item_details = graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    material_request_item = graphene.Field(MaterialRequestMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        material_request_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            material_request_instance = MaterialRequestMaster.objects.filter(id=kwargs['id']).first()
            if not material_request_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = MaterialRequestMasterSerializer(material_request_instance, data=kwargs, partial=True)
        else:
            serializer = MaterialRequestMasterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            material_request_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return MaterialRequestMasterCreateMutation(material_request_item=material_request_instance, success=success, errors=errors)


class MaterialRequestMasterDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = MaterialRequestMaster.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return MaterialRequestMasterDeleteMutation(success=success, errors=errors)


class MaterialRequestItemDetailsCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_number = graphene.Int()
        hsn_code = graphene.Int()
        qty = graphene.Decimal()
        uom = graphene.Int()
        po_raw_material = graphene.Int()
        issued_qty = graphene.Decimal()
        modified_by = graphene.Int()
        created_by = graphene.Int()
        

    material_request_item_detail = graphene.Field(MaterialRequestItemDetailType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        material_request_item_detail_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            material_request_item_detail_instance = MaterialRequestItemDetails.objects.filter(id=kwargs['id']).first()
            if not material_request_item_detail_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = MaterialRequestItemDetailSerializer(material_request_item_detail_instance, data=kwargs, partial=True)
        else:
            serializer = MaterialRequestItemDetailSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            material_request_item_detail_instance = serializer.instance
            try:
                po_rm_instance = material_request_item_detail_instance.po_raw_material
                po_rm_instance.issued_qty = material_request_item_detail_instance.issued_qty
                po_rm_instance.save()
            except Exception as e:
                print(e, "error")
                pass
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return MaterialRequestItemDetailsCreateMutation(material_request_item_detail=material_request_item_detail_instance, success=success, errors=errors)


class MaterialRequestItemDetailsDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = MaterialRequestItemDetails.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return MaterialRequestItemDetailsDeleteMutation(success=success, errors=errors)


class Mutation(graphene.ObjectType):    
    material_request_master_create_mutation = MaterialRequestMasterCreateMutation.Field()
    material_request_master_delete_mutation = MaterialRequestMasterDeleteMutation.Field()
    
    material_request_item_details_create_mutation = MaterialRequestItemDetailsCreateMutation.Field()
    material_request_item_details_delete_mutation = MaterialRequestItemDetailsDeleteMutation.Field()
    