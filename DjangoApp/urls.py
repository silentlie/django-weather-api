from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.LoginView, name='LoginView'),
    path('users', views.UsersView, name='UsersView'),
    path('users/role', views.UsersRoleView, name="UsersRoleView"),
    path('readings', views.ReadingsView, name='ReadingsView'),
    path('sensors', views.SensorsView, name='SensorsView'),
    path('analysis', views.AnalysisView, name='AnalysisView'),
    path('analysis/max', views.AnalysisMaxView, name='AnalysisMaxView'),
    ]