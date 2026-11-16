from django.apps import AppConfig


class TravelConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "travel"

    def ready(self):
        from django.conf import settings
        from django.urls import include, path

        from horilla.urls import urlpatterns

        settings.APPS.append("travel")
        urlpatterns.append(path("travel/", include("travel.urls")))
        settings.APP_URLS.append("travel.urls")
        super().ready()
