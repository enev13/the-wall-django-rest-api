import logging

from django.db.models import Max, Q
from django.forms import ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.serializers import Serializer
from rest_framework.viewsets import ViewSet

from .models import Day
from .serializers import CostSerializer, DaySerializer, IceSerializer, UploadSerializer
from .upload import handle_upload_data  # Function to handle an uploaded file.

YARDS_ICE_PER_FOOT = 195
GOLD_PER_YARD_ICE = 1900

log = logging.getLogger("django_log")


class ProfilesViewSet(ViewSet):
    serializer_class = Serializer

    def list(self, request, format=None):
        welcome_msg = (
            "Welcome to The Wall API! "
            + "Usage: "
            + "profiles/upload/ - to upload data file; "
            + "profiles/raw/ - to see raw db data; "
            + "profiles/overview - to see total cost for all profiles; "
            + "profiles/overview/<day_no> - to see the costs for up to a given day for all profiles; "
            + "profiles/<profile_no>/overview/<day_no> - to see the costs for up to a given day for a given profile; "
            + "profiles/<profile_no>/days/<day_no> - to see the amount of ice for a given day for a given profile"
        )
        log.info(welcome_msg)
        return Response(welcome_msg)


class UploadViewSet(ViewSet):
    serializer_class = UploadSerializer

    def list(self, request, format=None):
        return Response("Use POST request to upload data file")

    def create(self, request):
        uploaded_file = request.FILES["file_uploaded"]

        try:
            handle_upload_data(uploaded_file)
        except ValidationError as ve:
            response = f"File upload failed: {ve.message}"
            return_status = status.HTTP_400_BAD_REQUEST
        except Exception as e:
            response = "File upload failed: Error while processing the file!"
            return_status = status.HTTP_400_BAD_REQUEST
            log.error(f"{response} {e}")
        else:
            response = "File upload successful!"
            return_status = status.HTTP_200_OK
        finally:
            return Response(response, return_status)


class DayView(generics.ListAPIView):
    queryset = Day.objects.all()
    serializer_class = DaySerializer


class IceProfileDay(generics.ListAPIView):
    def get(self, request, day_id, profile_id, format=None):
        queryset = Day.objects.filter(day_no=day_id, profile_no=profile_id)
        item = get_object_or_404(queryset)

        serializer = IceSerializer(
            data={
                "day": item.day_no,
                "ice_amount": item.current_feet_done * YARDS_ICE_PER_FOOT,
            }
        )
        if serializer.is_valid():
            return Response(serializer.data)


class CostProfileDay(generics.ListAPIView):
    def get(self, request, day_id, profile_id, format=None):
        queryset = Day.objects.filter(day_no=day_id, profile_no=profile_id)
        item = get_object_or_404(queryset)

        serializer = CostSerializer(
            data={
                "day": item.day_no,
                "cost": (item.total_feet_done * YARDS_ICE_PER_FOOT * GOLD_PER_YARD_ICE),
            }
        )
        if serializer.is_valid():
            return Response(serializer.data)


class CostProfile(generics.ListAPIView):
    def get(self, request, day_id=None, format=None):
        total_feet_done = 0
        profile_count = Day.objects.aggregate(Max("profile_no"))["profile_no__max"]
        for profile_no in range(1, profile_count + 1):
            if not day_id:
                result = Day.objects.aggregate(
                    day_max=Max("day_no", filter=Q(profile_no=profile_no))
                )
                day_max = result.get("day_max")
            queryset = Day.objects.filter(
                day_no=day_id if day_id else day_max, profile_no=profile_no
            )
            item = get_object_or_404(queryset)
            total_feet_done += item.total_feet_done

        serializer = CostSerializer(
            data={
                "day": day_id,
                "cost": (total_feet_done * YARDS_ICE_PER_FOOT * GOLD_PER_YARD_ICE),
            }
        )
        if serializer.is_valid():
            return Response(serializer.data)
