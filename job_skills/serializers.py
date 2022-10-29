from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User


class TrackerSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = JobTracker


class ParserDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParserData


class SkillDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillData

