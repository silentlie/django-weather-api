from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.LoginView, name='LoginView'),
    path('users', views.UsersView, name='UsersView'),
    path('users/deactivate', views.DeactivateUsers, name='DeactivateUsers'),
    path('users/<str:ID>', views.DeleteUser, name='DeleteUser'),
    path('options', views.OptionsView, name='OptionsView'),
    path('readings', views.ReadingsView, name='ReadingsView'),
    path('sensors', views.SensorsView, name='SensorsView'),
    path('analysis/max', views.AnalysisMaxView, name='AnalysisMaxView'),
    ]