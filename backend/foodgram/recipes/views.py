from django.shortcuts import redirect
from django.http import Http404

from .models import Recipe


def recipe_link(request, recipe_id):
    exists = Recipe.objects.filter(pk=recipe_id).exists()
    if not exists:
        raise Http404(f"Рецепт {recipe_id} не найден")
    return redirect(f'/recipes/{recipe_id}')
