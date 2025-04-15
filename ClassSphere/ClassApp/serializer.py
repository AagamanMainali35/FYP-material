from rest_framework import serializers
from .models import Event,User,profile,Notification

class Eventserializer(serializers.ModelSerializer):
    class Meta:
        model=Event
        fields='__all__'
        extra_kwargs = {
    'eventbanner': {'required': False, 'allow_null': True}
}



class PaymentSerializer(serializers.Serializer):
    feeAmount = serializers.IntegerField() 


class NotificationSerilizer(serializers.ModelSerializer):
    class Meta:
       model=Notification
       fields = ['NotificationMsg']