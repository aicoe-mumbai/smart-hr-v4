from rest_framework import serializers
from .models import SmartGoal

class SmartGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartGoal
        fields = '__all__'
