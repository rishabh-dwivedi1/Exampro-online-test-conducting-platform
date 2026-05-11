from django.urls import path
from . import views

urlpatterns = [
    path("", views.auth_page, name="login"),
    path("dashboard/", views.dashboard_page, name="dashboard"),
    path("logout/", views.logout_view, name="logout"),
    path("exam/start/<str:subject>/", views.start_exam, name="start_exam"),
    path("exam/", views.exam_page, name="exam"),
    path("exam/download-paper/", views.download_paper, name="download_paper"),
    path("submit/", views.submit_exam, name="submit_exam"),
    path("result/", views.result_page, name="result"),
    path("result/<int:result_id>/", views.result_page, name="result_detail"),
]
