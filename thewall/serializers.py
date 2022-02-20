from rest_framework import serializers
from .models import Day


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField()

    class Meta:
        fields = ["file_uploaded"]


class DaySerializer(serializers.ModelSerializer):
    class Meta:
        model = Day
        fields = ("id", "day_no", "profile_no", "current_feet_done", "total_feet_done")


class IceSerializer(serializers.Serializer):
    day = serializers.IntegerField()
    ice_amount = serializers.IntegerField()


class CostSerializer(serializers.Serializer):
    day = serializers.IntegerField(allow_null=True)
    cost = serializers.IntegerField()
