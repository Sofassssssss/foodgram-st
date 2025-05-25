from django.urls import path

from .views import recipe_link

app_name = 'recipes'

urlpatterns = [
    path('recipes/<int:recipe_id>/', recipe_link, name='get_recipe_link'),
]
