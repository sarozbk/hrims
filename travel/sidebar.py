from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

MENU = _("Travel")
IMG_SRC = "images/ui/travel.svg"
SUBMENUS = [{"menu": _("Travel Requests"), "redirect": reverse_lazy("travel-requests")}]
