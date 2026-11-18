"""
admin.py

This page is used to register base models with admins site.
"""

from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin

from base.models import (
    Announcement,
    Attachment,
    AttendanceAllowedIP,
    Branch,
    Company,
    CompanyGroupAssignment,
    CompanyLeaves,
    DashboardEmployeeCharts,
    DefaultExportPermission,
    Department,
    DynamicEmailConfiguration,
    DynamicPagination,
    EmailLog,
    EmployeeShift,
    EmployeeShiftDay,
    EmployeeShiftSchedule,
    EmployeeType,
    Holidays,
    JobPosition,
    JobRole,
    MultipleApprovalCondition,
    MultipleApprovalManagers,
    DateTable,
    NepaliCalendarMonth,
    PenaltyAccounts,
    RotatingShift,
    RotatingShiftAssign,
    RotatingWorkType,
    RotatingWorkTypeAssign,
    ShiftRequest,
    ShiftRequestComment,
    Tags,
    WorkType,
    WorkTypeRequest,
    WorkTypeRequestComment,
)

# Register your models here.

admin.site.register(CompanyGroupAssignment)
admin.site.register(Company)
admin.site.register(Branch)


@admin.register(DateTable)
class DateTableAdmin(admin.ModelAdmin):
    list_display = ("ad_date", "bs_date", "ws", "we", "ms", "me", "fys", "fye")
    search_fields = ("bs_date",)
    ordering = ("ad_date",)
    readonly_fields = tuple(field.name for field in DateTable._meta.fields)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(NepaliCalendarMonth)
class NepaliCalendarMonthAdmin(admin.ModelAdmin):
    list_display = ("bs_year", "bs_month", "days_in_month")
    list_filter = ("bs_year",)
    ordering = ("bs_year", "bs_month")
    fields = ("bs_year", "bs_month", "days_in_month", "bs_year_start_ad")
    actions = ("rebuild_date_table",)

    @admin.action(description="Rebuild AD ↔ BS date table from calendar settings")
    def rebuild_date_table(self, request, queryset):
        from django.contrib import messages

        from base.nepali_calendar_data import rebuild_nepali_date_table

        try:
            count = rebuild_nepali_date_table()
        except ValueError as error:
            self.message_user(request, str(error), level=messages.ERROR)
            return
        self.message_user(request, f"Rebuilt {count:,} date rows from calendar settings.")

    def has_add_permission(self, request):
        return False

    def get_readonly_fields(self, request, obj=None):
        readonly = ["bs_year", "bs_month"]
        if obj is None or obj.bs_month != 1:
            readonly.append("bs_year_start_ad")
        return tuple(readonly)

    def has_delete_permission(self, request, obj=None):
        return False
admin.site.register(Department, SimpleHistoryAdmin)
admin.site.register(JobPosition)
admin.site.register(JobRole)
admin.site.register(EmployeeShift)
admin.site.register(EmployeeShiftSchedule)
admin.site.register(EmployeeShiftDay)
admin.site.register(EmployeeType)
admin.site.register(WorkType)
admin.site.register(RotatingWorkType)
admin.site.register(RotatingWorkTypeAssign)
admin.site.register(RotatingShift)
admin.site.register(RotatingShiftAssign)
admin.site.register(ShiftRequest)
admin.site.register(WorkTypeRequest)
admin.site.register(Tags)
admin.site.register(DynamicEmailConfiguration)
admin.site.register(MultipleApprovalManagers)
admin.site.register(ShiftRequestComment)
admin.site.register(WorkTypeRequestComment)
admin.site.register(DynamicPagination)
admin.site.register(Announcement)
admin.site.register(Attachment)
admin.site.register(EmailLog)
admin.site.register(DashboardEmployeeCharts)
admin.site.register(Holidays)
admin.site.register(CompanyLeaves)
admin.site.register(PenaltyAccounts)
admin.site.register(MultipleApprovalCondition)
admin.site.register(AttendanceAllowedIP)
admin.site.register(DefaultExportPermission)
