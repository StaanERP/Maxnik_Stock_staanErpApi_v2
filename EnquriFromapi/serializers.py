from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User


class CustomDateField(serializers.DateField):
    def to_representation(self, value):
        # Convert the date to the desired format
        return value.strftime('%m/%d/%Y') if value else None

class userSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields ="__all__"

class productSerializers(serializers.ModelSerializer):
    class Meta:
        model = product
        fields = "__all__"


class ConferenceSerializers(serializers.ModelSerializer):
    startDate = serializers.DateField(input_formats=['%Y/%m/%d'], required=False)
    endDate = serializers.DateField(input_formats=['%Y/%m/%d'], required=False)

    class Meta:
        model = Conferencedata
        fields = "__all__"



class EnquirySerializers(serializers.ModelSerializer):
    # Use the ConferencedataSerializer for the nested field
    # Interesteds = serializers.PrimaryKeyRelatedField(queryset=product.objects.all(), required=False)
    class Meta:
        model = enquiryDatas
        # exclude = ('Interesteds',)
        fields = "__all__"
