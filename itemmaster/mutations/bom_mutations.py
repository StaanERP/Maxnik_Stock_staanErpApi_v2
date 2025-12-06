import graphene
from django.db.models import ProtectedError
from itemmaster.GLSchema.bomschema import *
from itemmaster.serializer import *


class BomCostVariationCreateMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()
        is_percentage = graphene.Boolean()
        variation = graphene.String()
        lead_time = graphene.String()
        modified_by = graphene.Int()
        created_by = graphene.Int()
    bom_cost_variation = graphene.Field(BomCostVariationType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, **kwargs):
        serializer = None
        bom_cost_variation_instance = None
        success = False
        errors = []
        if 'id' in kwargs:
            bom_cost_variation_instance = BomCostVariation.objects.filter(id=kwargs['id']).first()
            if not bom_cost_variation_instance:
                errors.append(f"Item {kwargs['id']} not found.")
            else:
                serializer = BomCostVariationSerializer(bom_cost_variation_instance, data=kwargs, partial=True)
        else:
            serializer = BomCostVariationSerializer(data=kwargs)
        if serializer.is_valid():
            serializer.save()
            bom_cost_variation_instance = serializer.instance
            success = True
        else:
            errors = [f"{field}: {'; '.join([str(e) for e in error])}" for field, error in serializer.errors.items()]
        return BomCostVariationCreateMutation(bom_cost_variation=bom_cost_variation_instance, success=success, errors=errors)


class BomCostVariationDeleteMutation(graphene.Mutation):
    class Arguments:
        id = graphene.ID()

    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        success = False
        errors = []
        try:
            data_instance = BomCostVariation.objects.get(id=id)
            try:
                parent_instance = Bom.objects.get(cost_variation_id=id)
                parent_instance.cost_variation = None
                parent_instance.save()
            except Exception as e:
                print(e)
                pass
            data_instance.delete()
            success = True
        except ProtectedError as e:
            print(e)
            errors.append('This data Linked with other modules')
        except Exception as e:
            errors.append(str(e))
        return BomCostVariationDeleteMutation(success=success, errors=errors)


class Mutation(graphene.ObjectType):
    bom_cost_variation_create_mutation = BomCostVariationCreateMutation.Field()
    bom_cost_variation_delete_mutation = BomCostVariationDeleteMutation.Field()