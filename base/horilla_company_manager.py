"""
horilla_company_manager.py
"""

import logging

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.fields.reverse_related import ForeignObjectRel
from django.db.models.query import QuerySet

from horilla.horilla_middlewares import _thread_locals, get_selected_company
from horilla.signals import (
    post_bulk_update,
    post_model_clean,
    pre_bulk_update,
    pre_model_clean,
)

logger = logging.getLogger(__name__)
django_filter_update = QuerySet.update


def update(self, *args, **kwargs):
    """
    Bulk Update
    """
    # pre_update signal
    request = getattr(_thread_locals, "request", None)
    self.request = request
    pre_bulk_update.send(sender=self.model, queryset=self, args=args, kwargs=kwargs)
    result = django_filter_update(self, *args, **kwargs)
    # post_update signal
    post_bulk_update.send(sender=self.model, queryset=self, args=args, kwargs=kwargs)

    return result


django_model_clean = models.Model.clean


def clean(self, *args, **kwargs):
    """
    Method to override django clean and trigger to signals
    """
    pre_model_clean.send(sender=self._meta.model, instance=self, **kwargs)
    result = django_model_clean(self)
    post_model_clean.send(sender=self._meta.model, instance=self, **kwargs)
    return result


models.Model.clean = clean

setattr(QuerySet, "update", update)


def has_multi_valued_join(query):
    """Return True when the query joins through a many-valued relation."""
    for join in query.alias_map.values():
        join_field = getattr(join, "join_field", None)
        if isinstance(join_field, ForeignObjectRel) and join_field.multiple:
            return True
    return False


class DistinctGuardMixin:
    """Queryset mixin that applies DISTINCT only where duplicate rows can occur."""

    def _apply_guard(self):
        if not self._query.distinct and has_multi_valued_join(self._query):
            self._query.distinct = True
        return self

    def _filter_or_exclude_inplace(self, negate, args, kwargs):
        super()._filter_or_exclude_inplace(negate, args, kwargs)
        self._apply_guard()

    def order_by(self, *field_names):
        return super().order_by(*field_names)._apply_guard()

    def annotate(self, *args, **kwargs):
        return super().annotate(*args, **kwargs)._apply_guard()

    def alias(self, *args, **kwargs):
        return super().alias(*args, **kwargs)._apply_guard()

    def _aligned_with(self, other):
        if (
            isinstance(other, DistinctGuardMixin)
            and self.query.distinct != other.query.distinct
        ):
            left, right = self._chain(), other._chain()
            left.query.distinct = right.query.distinct = True
            return left, right
        return self, other

    def __or__(self, other):
        left, right = self._aligned_with(other)
        return super(DistinctGuardMixin, left).__or__(right)

    def __and__(self, other):
        left, right = self._aligned_with(other)
        return super(DistinctGuardMixin, left).__and__(right)

    def __reduce__(self):
        return (
            _restore_guarded_queryset,
            (self._unguarded_queryset_class, self.__getstate__()),
        )


def _restore_guarded_queryset(queryset_class, state):
    """Rebuild a pickled guarded queryset from its original queryset class."""
    guarded = guarded_queryset_class(queryset_class)
    queryset = guarded.__new__(guarded)
    queryset.__setstate__(state)
    return queryset


_guarded_queryset_classes = {}


def guarded_queryset_class(queryset_class):
    """Return the queryset class extended with the DISTINCT guard."""
    if issubclass(queryset_class, DistinctGuardMixin):
        return queryset_class
    guarded = _guarded_queryset_classes.get(queryset_class)
    if guarded is None:
        guarded = type(
            f"Guarded{queryset_class.__name__}",
            (DistinctGuardMixin, queryset_class),
            {
                "__module__": queryset_class.__module__,
                "_unguarded_queryset_class": queryset_class,
            },
        )
        _guarded_queryset_classes[queryset_class] = guarded
    return guarded


class HorillaCompanyManager(models.Manager):

    company_filter_path = None

    def __new__(cls, related_company_field=None, *args, **kwargs):
        if cls is HorillaCompanyManager:
            cls = type(
                cls.__name__,
                (cls,),
                {"company_filter_path": related_company_field},
            )
        return super().__new__(cls)

    def __init__(self, related_company_field=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if related_company_field is not None:
            self.company_filter_path = related_company_field

    def _resolve_related_field(self, model, part):
        # Forward field
        try:
            return model._meta.get_field(part)
        except FieldDoesNotExist:
            pass

        # Reverse relation
        for rel in model._meta.related_objects:
            if rel.get_accessor_name() == part:
                return rel

        raise FieldDoesNotExist(part)

    def _field_exists(self, path):
        model = self.model

        parts = path.split("__")
        for i, part in enumerate(parts):
            try:
                field = self._resolve_related_field(model, part)
            except FieldDoesNotExist:
                logger.exception(
                    f"Invalid company filter path '{path}' for model {self.model.__name__}. "
                    f"Failed at field '{part}'."
                )
                return False

            # Only traverse if relational AND not last field
            if (
                getattr(field, "is_relation", False)
                and field.related_model
                and i < len(parts) - 1
            ):
                model = field.related_model
            elif i < len(parts) - 1:
                # Non-relational field in middle of path = invalid
                logger.exception(
                    f"Invalid company filter path '{path}' for model {self.model.__name__}. "
                    f"Field '{part}' is not relational."
                )
                return False

        return True

    def _has_company_id_fk_or_m2m(self):
        try:
            field = self.model._meta.get_field("company_id")
            return isinstance(field, (models.ForeignKey, models.ManyToManyField))
        except FieldDoesNotExist:
            return False

    def get_company_filter_path(self):
        if self.company_filter_path and self._field_exists(self.company_filter_path):
            return self.company_filter_path

        if self._has_company_id_fk_or_m2m():
            return "company_id"

        return None

    def get_branch_filter_path(self):
        """Resolve a branch path for branch-owned or employee-owned records."""
        try:
            field = self.model._meta.get_field("branch_id")
            if getattr(field, "is_relation", False) and field.related_model._meta.model_name == "branch":
                return "branch_id"
        except FieldDoesNotExist:
            pass

        # Employee itself owns work information through a reverse one-to-one.
        if self.model._meta.model_name == "employee":
            path = "employee_work_info__branch_id"
            return path if self._field_exists(path) else None

        # Most HR records point to their employee through employee_id. Apply
        # the employee's branch to those rows without requiring every model
        # to declare another manager configuration.
        for field in self.model._meta.fields:
            if (
                isinstance(field, models.ForeignKey)
                and field.related_model._meta.model_name == "employee"
            ):
                path = f"{field.name}__employee_work_info__branch_id"
                return path if self._field_exists(path) else None
        return None

    def _apply_selected_branch(self, queryset):
        request = getattr(_thread_locals, "request", None)
        path = self.get_branch_filter_path()
        if not request or not path:
            return queryset

        selected_company = get_selected_company()
        if not selected_company:
            return queryset

        try:
            from base.models import Branch, Company

            company_is_branch_based = selected_company == "all"
            if selected_company != "all":
                company_is_branch_based = Company._base_manager.filter(
                    pk=selected_company, organization_structure="branches"
                ).exists()
            if not company_is_branch_based:
                return queryset

            branch_id = request.session.get("selected_branch")
            can_view_all_branches = request.user.is_superuser or request.user.has_perm(
                "base.change_company"
            )
            employee = getattr(request.user, "employee_get", None)
            work_info = getattr(employee, "employee_work_info", None)
            own_branch_id = getattr(work_info, "branch_id_id", None)

            if not can_view_all_branches:
                if not own_branch_id:
                    return queryset.none()
                if branch_id not in (None, "all", str(own_branch_id)):
                    return queryset.none()
                branch_id = own_branch_id
            elif branch_id in (None, "all"):
                return queryset

            if branch_id == "none":
                return queryset.none()

            branch = (
                Branch._base_manager.filter(pk=branch_id, is_active=True)
                .only("company_id")
                .first()
            )
            if not branch:
                return queryset.none()
            if selected_company != "all" and str(branch.company_id_id) != str(selected_company):
                return queryset.none()
            if selected_company == "all" and not request.user.is_superuser:
                allowed_company_ids = getattr(request, "all_my_company_ids", None)
                if allowed_company_ids is None:
                    allowed_company_ids = getattr(request, "allowed_company_ids", None)
                if (
                    allowed_company_ids is not None
                    and branch.company_id_id not in allowed_company_ids
                ):
                    return queryset.none()

            branch_filter = Q(**{path: branch_id})
            if getattr(self.model, "include_shared_branch_rows", False):
                branch_filter |= Q(**{f"{path}__isnull": True})
            return queryset.filter(branch_filter)
        except (TypeError, ValueError, FieldDoesNotExist):
            return queryset.none()

    def get_queryset(self):
        qs = super().get_queryset()
        company = get_selected_company()
        filter_path = self.get_company_filter_path()

        if not filter_path or not company:
            return self._apply_selected_branch(qs)

        # Superuser / legacy "all": no company filter (true tenant-wide).
        # Non-superuser "all" (All my companies): restrict to assignment
        # companies (all_my_company_ids), falling back to allowed ids.
        if company == "all":
            request = getattr(_thread_locals, "request", None)
            filter_ids = None
            if request:
                filter_ids = getattr(request, "all_my_company_ids", None)
                if filter_ids is None:
                    filter_ids = getattr(request, "allowed_company_ids", None)
            if filter_ids is None:
                return self._apply_selected_branch(qs)
            if not filter_ids:
                return self._apply_selected_branch(qs.none())
            try:
                qs = self._guarded_queryset().filter(
                    Q(**{f"{filter_path}__in": list(filter_ids)})
                    | Q(**{f"{filter_path}__isnull": True})
                )
            except Exception as e:
                logger.exception(
                    f"Company filter (all-my-companies) failed for model "
                    f"{self.model.__name__} with path '{filter_path}': {e}"
                )
                return self._apply_selected_branch(qs.none())

        try:
            qs = self._guarded_queryset().filter(
                Q(**{filter_path: company}) | Q(**{f"{filter_path}__isnull": True})
            )
        except Exception as e:
            logger.exception(
                f"Company filter failed for model {self.model.__name__} "
                f"with path '{filter_path}': {e}"
            )
            return self._apply_selected_branch(qs.none())
        return self._apply_selected_branch(qs)

    def _guarded_queryset(self):
        """Return an empty queryset of this manager's class with the DISTINCT guard."""
        queryset_class = guarded_queryset_class(self._queryset_class)
        return queryset_class(model=self.model, using=self._db, hints=self._hints)

    def _get_is_active_filter(self):
        """
        Return True unless the request explicitly passes is_active=False/false.
        """
        request = getattr(_thread_locals, "request", None)
        raw = request.GET.get("is_active", True) if request else True
        return raw not in ["False", "false", False]

    def all(self):
        """
        Override all() to exclude inactive records by default.
        Only applies is_active filtering when a request context is active (not during startup/scheduler).
        - For `employee` model: respect request.GET `is_active` param; default to active only.
        - For `offboardingemployee` model: return unfiltered.
        - For other models:
            1. If the model itself has `is_active`, filter by it (respects GET param, default True).
            2. If the model has `employee_id` FK to Employee, hide records of inactive employees.
               Else, find the first FK to Employee and use that.
        """
        queryset = self.get_queryset()
        request = getattr(_thread_locals, "request", None)
        if not request:
            return queryset

        try:
            model_name = queryset.model._meta.model_name

            if model_name == "employee":
                # ?is_active=all asks for active and inactive together (a chart
                # that counts both kinds of people opens its list this way).
                # A window of exits or joins (the dashboard's Hire vs Turnover chart) is
                # about people who may have left, so it is not narrowed to active ones.
                everyone = request.GET.get("is_active") == "all" or any(
                    request.GET.get(k)
                    for k in (
                        "exited_from",
                        "exited_till",
                        "joined_from",
                        "joined_till",
                    )
                )
                if not everyone:
                    queryset = queryset.filter(is_active=self._get_is_active_filter())

            elif model_name == "offboardingemployee":
                return queryset

            else:
                model_fields = queryset.model._meta.fields
                model_field_names = {f.name for f in model_fields}

                if "is_active" in model_field_names:
                    queryset = queryset.filter(is_active=self._get_is_active_filter())

                try:
                    employee_model = apps.get_model("employee", "Employee")
                    if "employee_id" in model_field_names:
                        queryset = queryset.filter(employee_id__is_active=True)
                    else:
                        for field in model_fields:
                            if (
                                isinstance(field, models.ForeignKey)
                                and field.related_model is employee_model
                            ):
                                if field.null:
                                    queryset = queryset.filter(
                                        Q(**{f"{field.name}__isnull": True})
                                        | Q(**{f"{field.name}__is_active": True})
                                    )
                                else:
                                    queryset = queryset.filter(
                                        **{f"{field.name}__is_active": True}
                                    )
                                break
                except LookupError:
                    pass

        except Exception as e:
            logger.error(e)

        return queryset

    def entire(self):
        return super().get_queryset()
