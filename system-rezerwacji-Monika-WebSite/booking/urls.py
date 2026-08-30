from django.urls import path

from . import views


app_name = "booking"

urlpatterns = [
    path("umow-wizyte/", views.book_appointment, name="book"),
    path("rezerwacja/<uuid:public_id>/", views.booking_confirmation, name="confirmation"),
    path("rezerwacja/<uuid:public_id>/anuluj/", views.cancel_appointment, name="cancel"),
]
