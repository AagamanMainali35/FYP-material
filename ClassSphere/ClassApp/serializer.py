from rest_framework import serializers
from .models import Event,User,profile

class Eventserializer(serializers.ModelSerializer):
    class Meta:
        model=Event
        fields='__all__'