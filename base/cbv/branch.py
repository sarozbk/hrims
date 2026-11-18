"""Branch settings views."""

from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _

from base.filters import BranchFilter
from base.forms import BranchForm
from base.models import Branch
from horilla.horilla_middlewares import get_selected_company
from horilla_views.cbv_methods import login_required, permission_required
from horilla_views.generic.cbv.views import HorillaFormView, HorillaListView, HorillaNavView


@login_required
@permission_required("base.view_company")
def branch_view(request):
    return render(request, "base/branch/branch.html")


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required(perm="base.view_company"), name="dispatch")
class BranchListView(HorillaListView):
    model = Branch
    filter_class = BranchFilter
    view_id = "branch-view-container"
    search_url = reverse_lazy("branch-list")
    columns = [
        (_("Branch"), "name"),
        (_("Code"), "code"),
        (_("Company"), "company_id"),
        (_("City"), "city"),
        (_("Country"), "country"),
    ]
    row_attrs = 'id="branchTr{get_delete_instance}"'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_url = reverse("branch-list")
        self.actions = []
        if self.request.user.has_perm("base.change_company"):
            self.actions.extend(
                [
                    {
                        "action": _("Edit"),
                        "icon": "create-outline",
                        "attrs": """
                            class="oh-btn oh-btn--light-bkg oh-btn--sq-sm"
                            hx-get="{get_update_url}"
                            hx-target="#genericModalBody"
                            data-toggle="oh-modal-toggle"
                            data-target="#genericModal"
                        """,
                    },
                    {
                        "action": _("Delete"),
                        "icon": "trash-outline",
                        "attrs": """
                            class="oh-btn oh-btn--danger oh-btn--sq-sm"
                            hx-get="{get_delete_url}?model=base.branch&pk={pk}"
                            hx-target="#deleteConfirmationBody"
                            data-toggle="oh-modal-toggle"
                            data-target="#deleteConfirmation"
                        """,
                    },
                ]
            )


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required(perm="base.view_company"), name="dispatch")
class BranchNavView(HorillaNavView):
    search_url = reverse_lazy("branch-list")
    nav_title = _("Branches")
    search_swap_target = "#branch-view-container"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.request.user.has_perm("base.change_company"):
            self.create_attrs = f"""
                onclick="event.stopPropagation();"
                data-toggle="oh-modal-toggle"
                data-target="#genericModal"
                hx-target="#genericModalBody"
                hx-get="{reverse('branch-create-form')}"
            """


@method_decorator(login_required, name="dispatch")
@method_decorator(permission_required(perm="base.change_company"), name="dispatch")
class BranchCreateForm(HorillaFormView):
    model = Branch
    form_class = BranchForm
    template_name = "cbv/company/company_form.html"
    new_display_title = _("Create Branch")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        company_id = get_selected_company()
        if company_id and company_id != "all":
            from base.models import Company

            kwargs["company"] = Company._base_manager.filter(pk=company_id).first()
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Branch saved successfully."))
        return self.HttpResponse()
