from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Personalización del panel de administración para el modelo de usuario personalizado.
    """
    ordering = ('email',)
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'city')
    search_fields = ('email', 'first_name', 'last_name', 'n_documento')
    
    # Organización de los campos dentro del formulario de edición
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'phone_number', 'document_type', 'n_documento', 'birth_date', 'genre')
        }),
        ('Ubicación', {
            'fields': ('country', 'department', 'city')
        }),
        ('Roles y Permisos', {
            'fields': ('role', 'teacher_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Facturación', {
            'fields': ('datos_facturacion_default',)
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Campos al crear un usuario nuevo
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password', 'role', 'is_staff', 'is_active'),
        }),
    )