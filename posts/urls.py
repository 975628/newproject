from django.urls import path

from . import views


urlpatterns = [
    path("<int:post_id>/like/", views.toggle_like, name="toggle_like"),
    path("<int:post_id>/comment/", views.add_comment, name="add_comment"),
    path("<int:post_id>/delete/", views.delete_post, name="delete_post"),
    path("<int:post_id>/report/", views.report_post, name="report_post"),
]
