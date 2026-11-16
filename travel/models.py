from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from base.horilla_company_manager import HorillaCompanyManager
from employee.models import Employee
from horilla.models import HorillaModel


TRAVEL_STATUS = (
    ("requested", _("Requested")),
    ("approved", _("Approved")),
    ("rejected", _("Rejected")),
)


class TravelRequest(HorillaModel):
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="travel_requests", verbose_name=_("Employee")
    )
    destination = models.CharField(max_length=255, verbose_name=_("Destination"))
    purpose = models.TextField(verbose_name=_("Purpose of Travel"))
    departure_date = models.DateField(verbose_name=_("Departure Date"))
    return_date = models.DateField(verbose_name=_("Return Date"))
    mode_of_travel = models.CharField(max_length=100, blank=True, verbose_name=_("Mode of Travel"))
    estimated_cost = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Estimated Cost")
    )
    status = models.CharField(max_length=20, choices=TRAVEL_STATUS, default="requested")
    approved_by = models.ForeignKey(
        Employee, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approved_travel_requests", verbose_name=_("Approved By")
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    reject_reason = models.TextField(blank=True, verbose_name=_("Rejection Reason"))
    objects = HorillaCompanyManager(related_company_field="employee__employee_work_info__company_id")

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = _("Travel Request")
        verbose_name_plural = _("Travel Requests")

    def clean(self):
        super().clean()
        if self.departure_date and self.return_date and self.return_date < self.departure_date:
            raise ValidationError({"return_date": _("Return date must be on or after departure date.")})

    def __str__(self):
        return f"{self.employee} — {self.destination} ({self.departure_date})"
