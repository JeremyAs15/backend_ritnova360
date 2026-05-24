from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from .models import User

class UserService:
    """
    Capa de servicios encargada de la lógica de negocio para la gestión de usuarios,
    inscripciones de roles y restricciones de acceso para la creación de cuentas.
    """

    @staticmethod
    def register_student(validated_data: dict) -> User:
        """
        Registra de manera pública y autónoma a un nuevo cliente/estudiante en la plataforma.
        """
        validated_data['role'] = 'student'
        validated_data['is_staff'] = False
        validated_data['is_superuser'] = False
        
        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            return user

    @staticmethod
    def create_internal_user(creator: User, validated_data: dict) -> User:
        """
        Registra un usuario interno (Administrador, Director o Profesor).
        Restricción de negocio: Solo Directores o Administradores pueden realizar esta acción.
        Los profesores no pueden auto-gestionarse ni crearse de manera autónoma.
        """
        # Validación de autorización del creador
        if creator.role not in ['admin', 'director'] and not creator.is_superuser:
            raise PermissionDenied("No tiene permisos para crear usuarios internos en la academia.")

        target_role = validated_data.get('role')
        if target_role not in ['admin', 'director', 'teacher']:
            raise ValidationError("El rol especificado no corresponde a un tipo de usuario interno válido.")

        # Configuración de permisos administrativos de Django según el rol
        if target_role in ['admin', 'director']:
            validated_data['is_staff'] = True
        else:
            validated_data['is_staff'] = False
            
        validated_data['is_superuser'] = False

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            return user

    @staticmethod
    def update_user_profile(user_to_update: User, editor: User, validated_data: dict) -> User:
        """
        Actualiza los datos del perfil de un usuario.
        Un estudiante solo puede editar su propio perfil.
        Un Administrador o Director puede editar perfiles de usuarios internos.
        """
        if user_to_update != editor and editor.role not in ['admin', 'director'] and not editor.is_superuser:
            raise PermissionDenied("No tiene autorización para modificar este perfil.")

        # Restricción: No se permite cambiar de rol a través de la actualización estándar de perfil
        validated_data.pop('role', None)
        validated_data.pop('email', None)  # El email actúa como ID único y no debe cambiarse arbitrariamente

        for attr, value in validated_data.items():
            setattr(user_to_update, attr, value)

        user_to_update.save()
        return user_to_update

    @staticmethod
    def delete_internal_user(creator: User, user_to_delete: User) -> None:
        """
        Elimina un usuario interno de la base de datos.
        Restricción: Solo Directores o Administradores pueden realizar esta acción.
        """
        if creator.role not in ['admin', 'director'] and not creator.is_superuser:
            raise PermissionDenied("No tiene permisos para eliminar usuarios de la academia.")
        
        if user_to_delete.role == 'student':
            raise ValidationError("Para gestionar la baja de clientes utilice el módulo de gestión de clientes.")

        user_to_delete.delete()