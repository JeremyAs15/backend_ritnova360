from django.contrib import admin
from .models import Choreography, VideoClip, Rate, Enroll, ShoppingCart, AddTo

class VideoClipInline(admin.TabularInline):
    """
    Permite agregar o editar videoclips directamente desde el formulario de la coreografía.
    """
    model = VideoClip
    extra = 1  # Espacios vacíos por defecto para nuevos clips


class AddToInline(admin.TabularInline):
    """
    Muestra los ítems añadidos a un carrito de compras.
    """
    model = AddTo
    extra = 0
    readonly_fields = ('price_at_purchase',)


@admin.register(Choreography)
class ChoreographyAdmin(admin.ModelAdmin):
    list_display = ('song_name', 'genre', 'difficulty_level', 'price', 'creator', 'creation_date')
    list_filter = ('genre', 'difficulty_level', 'creation_date')
    search_fields = ('song_name', 'genre', 'creator__email')
    inlines = [VideoClipInline]


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('shopping_cart_id', 'user', 'state', 'date')
    list_filter = ('state', 'date')
    search_fields = ('user__email', 'shopping_cart_id')
    inlines = [AddToInline]


@admin.register(Enroll)
class EnrollAdmin(admin.ModelAdmin):
    list_display = ('user', 'choreography', 'date', 'state', 'id_source')
    list_filter = ('state', 'date')
    search_fields = ('user__email', 'choreography__song_name')


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ('user', 'choreography', 'score', 'date')
    list_filter = ('score', 'date')
    search_fields = ('user__email', 'choreography__song_name')