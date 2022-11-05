from django.contrib.auth.models import User
from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = User


class TrackerSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ("search_text", "exclude_from_search", "areas", "employment_type", "work_experience", "work_schedule",)
        model = JobTracker

    def update(self, tracker, validated_data):
        tracker.search_text = validated_data.get("search_text", tracker.search_text)
        tracker.exclude_from_search = validated_data.get("exclude_from_search", tracker.exclude_from_search)
        tracker.areas = validated_data.get("areas", tracker.areas)
        tracker.employment_type = validated_data.get("employment_type", tracker.employment_type)
        tracker.work_experience = validated_data.get("work_experience", tracker.work_experience)
        tracker.work_schedule = validated_data.get("work_schedule", tracker.work_schedule)
        tracker.save()
        return tracker


class ParserDataSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = ParserData


class SkillDataSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = SkillData


class AreaSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Area
