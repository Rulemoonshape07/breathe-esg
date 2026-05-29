from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadBatchViewSet, IngestView

router = DefaultRouter()
router.register('batches', UploadBatchViewSet, basename='batch')
router.register('', IngestView, basename='ingest')
urlpatterns = [path('', include(router.urls))]
