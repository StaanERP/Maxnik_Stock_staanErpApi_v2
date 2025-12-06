import graphene
from django.db.models import ProtectedError
from itemmaster.GLSchema.mrpschema import *
from itemmaster.serializer import *


class MrpMasterCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        is_sales_order = graphene.Boolean()
        is_production_order = graphene.Boolean()
        is_item_group = graphene.Boolean()
        item_group = graphene.List(graphene.Int)
        mrp_item = graphene.Int()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    mrp_master = graphene.Field(MrpMasterType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        mrp_master_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            mrp_master_instance = MrpMaster.objects.filter(id=kwargs['id']).first()
            if not mrp_master_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = MrpMasterSerializer(mrp_master_instance, data=kwargs, partial=True)
        else:
            serializer = MrpMasterSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            mrp_master_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return MrpMasterCreateMutation(mrp_master=mrp_master_instance, success=success, errors=errors)


class MrpMasterDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = MrpMaster.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return MrpMasterDeleteMutation(success=success, errors=errors)


class MrpItemCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        part_code = graphene.Int()
        bom = graphene.Int()
        cost = graphene.String()
        qty = graphene.Decimal()
        source_type = graphene.Int()
        supplier=graphene.List(graphene.Int)
        modified_by = graphene.Int()
        created_by = graphene.Int()

    mrp_item = graphene.Field(MrpItemType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        mrp_item_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            mrp_item_instance = MrpItem.objects.filter(id=kwargs['id']).first()
            if not mrp_item_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = MrpItemSerializer(mrp_item_instance, data=kwargs, partial=True)
        else:
            serializer = MrpItemSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            mrp_item_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return MrpItemCreateMutation(mrp_item=mrp_item_instance, success=success, errors=errors)


class MrpItemDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = MrpItem.objects.get(id=id)
            data_instance.delete()
            success = True
        except ProtectedError as e:
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return MrpItemDeleteMutation(success=success, errors=errors)


class Mutation(graphene.ObjectType):
    mrp_master_create_mutation = MrpMasterCreateMutation.Field()
    mrp_master_delete_mutation = MrpMasterDeleteMutation.Field()
    
    mrp_item_create_mutation = MrpItemCreateMutation.Field()
    mrp_item_delete_mutation = MrpItemDeleteMutation.Field()