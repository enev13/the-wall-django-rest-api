from django.urls import path, reverse_lazy
from django.views.generic import RedirectView
from rest_framework.urlpatterns import format_suffix_patterns
from thewall import views

redirect_view = RedirectView.as_view(url=reverse_lazy("profiles"))
profiles_views = views.ProfilesViewSet.as_view({"get": "list"})
upload_view = views.UploadViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    path("", redirect_view, name="redirect_profiles"),
    path("profiles/", profiles_views, name="profiles"),
    path("profiles/raw/", views.DayView.as_view(), name="raw"),
    path("profiles/upload/", upload_view, name="upload"),
    path("profiles/overview/", views.CostProfile.as_view()),
    path("profiles/overview/<int:day_id>/", views.CostProfile.as_view()),
    path(
        "profiles/<int:profile_id>/overview/<int:day_id>/",
        views.CostProfileDay.as_view(),
    ),
    path("profiles/<int:profile_id>/days/<int:day_id>/", views.IceProfileDay.as_view()),
]

urlpatterns = format_suffix_patterns(urlpatterns)
