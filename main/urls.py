from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name = 'home'),
    path('o-mnie/', views.about, name = 'about'),
    path('kalkulator-kalorii/', views.calorie_calculator, name='calorie_calculator'),
    path('opinie/dodaj/', views.submit_testimonial, name='submit_testimonial'),
    path('newsletter/', views.newsletter_signup, name='newsletter_signup'),
    path('regulamin/', views.terms_of_service, name='terms_of_service'),
    path('polityka-prywatnosci/', views.privacy_policy, name='privacy_policy'),
    path('polityka-cookies/', views.cookie_policy, name='cookie_policy'),
]
