from rest_framework import serializers
from .models import Event,User,profile,PaymentStructure

class Eventserializer(serializers.ModelSerializer):
    class Meta:
        model=Event
        fields='__all__'
class PaymentSerializer(serializers.Serializer):
    feeAmount = serializers.IntegerField() 
