from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),

    # 🔥 Your API routes
    path("", include("app.urls")),
]