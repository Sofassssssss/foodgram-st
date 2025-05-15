from collections import defaultdict
import re
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import FollowSerializer
from users.models import CustomUser, Follow
from recipes.models import RecipeIngredient, Recipe


@api_view(["POST", "DELETE"])
@permission_classes([IsAuthenticated])
def subscribes_control(request, user_id):
    """View function for creating or deleting subscribe."""
    try:
        following = get_object_or_404(CustomUser, id=user_id)
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == "POST":
        serializer = FollowSerializer(
            data=request.data,
            context={'request': request, 'user_id': user_id}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, following=following)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        serializer = FollowSerializer(
            data=request.data,
            context={'request': request, 'user_id': user_id}
        )
        serializer.is_valid(raise_exception=True)
        Follow.objects.filter(
            user=request.user,
            following=following
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_shopping_cart(request):
    """Download shopping cart as txt."""
    recipes = Recipe.objects.filter(shopping_cart__user=request.user)

    ingredients = RecipeIngredient.objects.filter(recipe__in=recipes)

    shopping_data = defaultdict(float)

    for item in ingredients:
        key = f"{item.ingredient.name} ({item.ingredient.measurement_unit})"
        shopping_data[key] += item.amount

    content = 'Список покупок:\n\n'

    for idx, (ingredient, amount) in enumerate(shopping_data.items(), start=1):
        match = re.search(r'\((.*?)\)', ingredient)
        measurement_unit = match.group(1)
        ingredient_name = re.sub(r'\s*\(.*?\)', '', ingredient).strip()
        content += f"{idx}. {ingredient_name} — {amount} {measurement_unit}\n"

    response = HttpResponse(content, content_type='text/plain',
                            status=status.HTTP_200_OK)
    response['Content-Disposition'] = ('attachment; '
                                       'filename="shopping-list.txt"')
    return response
