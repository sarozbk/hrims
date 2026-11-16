from django.contrib import admin

from travel.models import TravelRequest


@admin.register(TravelRequest)
class TravelRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "destination", "departure_date", "return_date", "status")
    list_filter = ("status", "departure_date")
    search_fields = ("employee__badge_id", "destination", "purpose")
