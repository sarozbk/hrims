from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from xhtml2pdf import pisa

from base.methods import check_manager
from travel.forms import TravelRequestForm
from travel.models import TravelRequest


def _can_manage(user, travel_request):
    employee = getattr(user, "employee_get", None)
    if employee and travel_request.employee == employee:
        return False
    if user.has_perm("travel.change_travelrequest"):
        return True
    return bool(employee and check_manager(employee, travel_request.employee))


@login_required
def travel_requests(request):
    employee = getattr(request.user, "employee_get", None)
    can_view_all = request.user.has_perm("travel.view_travelrequest")
    if employee is None and not can_view_all:
        return HttpResponseForbidden()
    requests = TravelRequest.objects.select_related("employee", "approved_by")
    if not can_view_all:
        requests = [item for item in requests if item.employee == employee or check_manager(employee, item.employee)]
    requests = list(requests)
    for item in requests:
        item.can_decide = item.status == "requested" and _can_manage(request.user, item)
    return render(request, "travel/travel_requests.html", {
        "travel_requests": requests,
        "employee": employee,
        "can_view_all": can_view_all,
    })


@login_required
def travel_request_create(request):
    employee = getattr(request.user, "employee_get", None)
    if employee is None:
        return HttpResponseForbidden()
    form = TravelRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        travel_request = form.save(commit=False)
        travel_request.employee = employee
        travel_request.full_clean()
        travel_request.save()
        messages.success(request, _("Travel request submitted."))
        return redirect("travel-requests")
    return render(request, "travel/travel_request_form.html", {"form": form})


@login_required
def travel_request_decide(request, pk, decision):
    if request.method != "POST" or decision not in ("approve", "reject"):
        return HttpResponseForbidden()
    travel_request = get_object_or_404(TravelRequest, pk=pk)
    if not _can_manage(request.user, travel_request):
        return HttpResponseForbidden()
    if travel_request.status != "requested":
        messages.info(request, _("This travel request has already been decided."))
        return redirect("travel-requests")
    if decision == "approve":
        travel_request.status = "approved"
        travel_request.approved_by = getattr(request.user, "employee_get", None)
        travel_request.approved_at = timezone.now()
        travel_request.reject_reason = ""
        messages.success(request, _("Travel request approved."))
    else:
        travel_request.status = "rejected"
        travel_request.reject_reason = request.POST.get("reject_reason", "").strip()
        messages.success(request, _("Travel request rejected."))
    travel_request.save()
    return redirect("travel-requests")


@login_required
def travel_order_print(request, pk):
    travel_request = get_object_or_404(TravelRequest, pk=pk)
    employee = getattr(request.user, "employee_get", None)
    if not (request.user.has_perm("travel.view_travelrequest") or
            travel_request.employee == employee or _can_manage(request.user, travel_request)):
        return HttpResponseForbidden()
    if travel_request.status != "approved":
        return HttpResponseForbidden(_("Only approved travel requests have a travel order."))
    html = render_to_string("travel/travel_order.html", {
        "travel_request": travel_request,
        "company": getattr(getattr(travel_request.employee, "employee_work_info", None), "company_id", None),
    }, request=request)
    output = BytesIO()
    result = pisa.CreatePDF(src=html, dest=output)
    if result.err:
        return HttpResponse(_("Unable to generate the travel order."), status=500)
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="travel-order-{travel_request.pk}.pdf"'
    return response
