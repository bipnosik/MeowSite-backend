from django.db.models import Model
from rest_framework import viewsets, status, generics, permissions, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.filters import SearchFilter
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Recipe, Comment, SearchHistory
from .serializers import RecipeSerializer, UserSerializer, CommentSerializer, SearchHistorySerializer

class SearchHistoryViewSet(viewsets.ModelViewSet):
    serializer_class = SearchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SearchHistory.objects.filter(user=self.request.user)[:20]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [SearchFilter]
    search_fields = ['name', 'description', 'ingredients']

    def get_queryset(self):
        queryset = Recipe.objects.all()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(ingredients__icontains=search_query)
            )
        return queryset

    def list(self, request, *args, **kwargs):
        print("Запрос к /api/recipes/")
        print("Параметры запроса:", request.query_params)
        queryset = self.filter_queryset(self.get_queryset())
        print("Отфильтрованный queryset:", queryset)
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=pk)
        serializer = self.serializer_class(recipe)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.user != request.user:
            return Response({"detail": "You do not have permission to edit this recipe."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(recipe, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None, *args, **kwargs):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.user != request.user:
            return Response({"detail": "You do not have permission to delete this recipe."}, status=status.HTTP_403_FORBIDDEN)
        recipe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            "access": str(refresh.access_token),
        })

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_queryset(self):
        recipe_id = self.request.query_params.get('recipe', None)
        if recipe_id is not None:
            return Comment.objects.filter(recipe_id=recipe_id)
        return Comment.objects.all()