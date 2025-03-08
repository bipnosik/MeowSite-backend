from os.path import basename

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, RegisterView, CommentViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet, basename='recipe')  # <-- добавили basename='recipe'!
router.register(r'comments', CommentViewSet, basename='comment')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
]