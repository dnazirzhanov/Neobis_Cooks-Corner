from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Recipe, Like
from .serializers import RecipeSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema


class RecipeCreateAPIView(APIView):
    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Endpoint for creating a new recipe.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'recipe_name': openapi.Schema(type=openapi.TYPE_STRING),
                'category': openapi.Schema(type=openapi.TYPE_INTEGER),
                'cooking_time': openapi.Schema(type=openapi.TYPE_STRING),
                'difficulty': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'ingredients': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_INTEGER)),
                'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY),
            },
            required=['recipe_name', 'category', 'cooking_time', 'difficulty', 'description', 'ingredients']
        ),
        responses={
            201: "Successful creation. Returns the created recipe.",
            400: "Bad request. Invalid input.",
            401: "Unauthorized. User not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request):
        serializer = RecipeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RecipeListAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Endpoint for retrieving a list of all recipes.",
        responses={
            200: "Successful retrieval. Returns a list of recipes.",
            401: "Unauthorized. User not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def get(self, request):
        recipes = Recipe.objects.all()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RecipeDetailAPIView(APIView):
    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Endpoint for retrieving details of a specific recipe.",
        responses={
            200: "Successful retrieval. Returns the details of the recipe.",
            404: "Not found. Recipe with the specified primary key does not exist.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def get(self, request, pk):
        try:
            recipe = Recipe.objects.get(pk=pk)
            serializer = RecipeSerializer(recipe)
            return Response(serializer.data)
        except Recipe.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class RecipeCategoryAPIView(APIView):
    permission_classes = [IsAuthenticated, ]

    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Endpoint for retrieving a list of recipes by category. BREAKFAST, DINNER, or LUNCH.",
        manual_parameters=[
            openapi.Parameter('category', openapi.IN_QUERY, description="Filter recipes by category.",
                              type=openapi.TYPE_STRING),
        ],
        responses={
            200: "Successful retrieval. Returns a list of recipes.",
            401: "Unauthorized. User not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def get_queryset(self):
        category = self.kwargs['category']
        return Recipe.objects.filter(category=category)

    def get(self, request, category):
        recipes = self.get_queryset()
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)

class RecipeSearchAPIView(APIView):
    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Endpoint for searching recipes by title.",
        manual_parameters=[
            openapi.Parameter('q', openapi.IN_QUERY, description="Search query string.", type=openapi.TYPE_STRING),
        ],
        responses={
            200: RecipeSerializer(many=True),
            500: "Internal server error. Failed to process the request."
        }
    )
    def get(self, request):
        query = request.query_params.get('q', '')

        if not query:
            return Response("Search query 'q' is required.", status=status.HTTP_400_BAD_REQUEST)

        recipes = Recipe.objects.filter(title__icontains=query)
        serializer = RecipeSerializer(recipes, many=True)
        return Response(serializer.data)


class LikeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Like a recipe.",
        responses={
            201: "Recipe liked successfully.",
            400: "Bad request. Invalid input data or user has already liked this recipe.",
            404: "Recipe not found.",
            401: "Unauthorized. User is not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def post(self, request, recipe_id):
        recipe = Recipe.objects.get(pk=recipe_id)
        like, created = Like.objects.get_or_create(users=request.user,
                                                   recipe=recipe)  # Пытаемся получить объект Like для данного пользователя и рецепта, или создаем новый, если он не существует.
        if not created:
            return Response({"message": "You have already likes this recipe"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Recipe liked successfully."}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        tags=['Recipes'],
        operation_description="Remove a like from a recipe.",
        responses={
            200: "Like removed successfully.",
            400: "Bad request. User has not liked this recipe.",
            404: "Recipe not found.",
            401: "Unauthorized. User is not authenticated.",
            500: "Internal server error. Failed to process the request."
        }
    )
    def delete(self, request, recipe_id):
        recipe = Recipe.objects.get(pk=recipe_id)
        try:
            like = Like.objects.get(users=request.user, recipe=recipe)
            like.delete()
            return Response({"message": "Like removed successfully"}, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({"message": "You have not liked this recipe."}, status=status.HTTP_400_BAD_REQUEST)