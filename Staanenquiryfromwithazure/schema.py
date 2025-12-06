import graphene
import itemmaster.GLSchema.material_request_schema
import itemmaster.GLSchema.mrpschema
import itemmaster.mutations.material_request_mutation
import itemmaster.mutations.mrpmutation
import itemmaster.GLSchema.poschema
import itemmaster.mutations.pomutation
import itemmaster.GLSchema.bomschema
import itemmaster.mutations.bom_mutations
import itemmaster.schema
import itemmaster2.mutations.Item_master2_mutations
import itemmaster2.schema.item_master2_schema
import itemmaster.mutations.Item_master_mutations
import itemmaster.mutations.QutationsMutations
import EnquriFromapi.mutations.EnquiryMutations
import EnquriFromapi.Schema
import userManagement.schema
import userManagement.Mutations.UserMutations


class Query(itemmaster.schema.Query, 
            EnquriFromapi.Schema.Query,
            itemmaster.GLSchema.mrpschema.Query, 
            itemmaster.GLSchema.poschema.Query, 
            itemmaster.GLSchema.bomschema.Query,
            itemmaster.GLSchema.material_request_schema.Query,

            itemmaster2.schema.item_master2_schema.Query,
            userManagement.schema.Query,
            graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class Mutation(itemmaster.mutations.Item_master_mutations.Mutation, 
               EnquriFromapi.mutations.EnquiryMutations.Mutation, 
               itemmaster.mutations.pomutation.Mutation, 
               itemmaster.mutations.bom_mutations.Mutation,
               itemmaster.mutations.material_request_mutation.Mutation,
               itemmaster.mutations.mrpmutation.Mutation,
               itemmaster2.mutations.Item_master2_mutations.Mutation,
               userManagement.Mutations.UserMutations.Mutation,
               graphene.ObjectType):
    pass



schema = graphene.Schema(query=Query, mutation=Mutation)
