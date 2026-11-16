from django.urls import path

from travel import views


urlpatterns = [
    path("", views.travel_requests, name="travel-requests"),
    path("create/", views.travel_request_create, name="travel-request-create"),
    path("<int:pk>/<str:decision>/", views.travel_request_decide, name="travel-request-decide"),
    path("<int:pk>/order/", views.travel_order_print, name="travel-order-print"),
]
