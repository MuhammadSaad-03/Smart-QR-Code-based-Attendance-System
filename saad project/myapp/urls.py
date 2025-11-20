from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('submitattendance', views.submitattendance, name='submitattendance'),
    path('viewhistory', views.viewhistory, name='viewhistory'),
    path('adminpanel', views.adminpanel, name='adminpanel'),
    path('generateid', views.adminpanel, name='adminpanel'),
    path('editdetails', views.editdetails, name='editdetails'),
    path('viewstudenthistory', views.viewstudenthistory, name='viewstudenthistory'),
    path('admin', views.Admin, name='Admin'),
]