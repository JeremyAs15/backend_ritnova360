from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from .models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings

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
    def request_password_reset(email: str) -> None:
        """
        Genera un token de recuperación único y envía un correo con el enlace.
        Para evitar ataques de enumeración de usuarios, si el correo no existe,
        el servicio finaliza de forma silenciosa sin revelar la existencia de la cuenta.
        """
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return  # Finalización silenciosa

        # Generación de parámetros seguros de recuperación
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

        # Enlace simulado que apuntaría a la interfaz del frontend (React/Vue)
        # Ejemplo: http://localhost:3000/reset-password?uid=XYZ&token=ABC
        reset_link = f"http://localhost:3000/reset-password?uid={uidb64}&token={token}"

        subject = "Recuperación de contraseña - Ritnova360"
        message = (
            f"Hola {user.first_name or 'Usuario'},\n\n"
            f"Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en Ritnova360.\n"
            f"Por favor, haz clic en el siguiente enlace para definir una nueva contraseña:\n\n"
            f"{reset_link}\n\n"
            f"Este enlace es de uso único. Si no solicitaste este cambio, puedes ignorar este correo."
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

    @staticmethod
    def confirm_password_reset(uidb64: str, token: str, new_password: str) -> None:
        """
        Valida el token y el ID codificado. Si son correctos, actualiza la contraseña del usuario.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise ValidationError("El enlace de recuperación no es válido o ha expirado.")

        # Verificar validez matemática del token provisto
        if not default_token_generator.check_token(user, token):
            raise ValidationError("El token de recuperación no es válido, ha expirado o ya fue utilizado.")

        with transaction.atomic():
            user.set_password(new_password)
            user.save()

    @staticmethod
    def get_internal_users():
        """
        Recupera de la base de datos los usuarios que tienen rol de 
        administrador, director o profesor.
        """
        return User.objects.filter(role__in=['admin', 'director', 'teacher', 'student'])
    
    @staticmethod
    def delete_internal_user(creator: User, user_to_delete: User) -> None:
        """
        Realiza la eliminación lógica de un usuario interno en el sistema.
        
        Restricciones y Validaciones:
        - Solo Directores, Administradores o Superusuarios pueden realizar esta acción.
        - Evita que un usuario administrativo se elimine a sí mismo.
        - Detiene el flujo si el usuario tiene dependencias activas como coreografías creadas.
        """
        # Validación de permisos de quien realiza la acción (Tarea 3)
        if creator.role not in ['admin', 'director'] and not creator.is_superuser:
            raise PermissionDenied("No tiene permisos para eliminar usuarios de la academia.")
        
        # Validación del rol a eliminar
        if user_to_delete.role == 'student':
            raise ValidationError("Para gestionar la baja de clientes utilice el módulo de gestión de clientes.")

        # Evitar la auto-eliminación
        if creator == user_to_delete:
            raise ValidationError("No puede eliminarse a sí mismo de la plataforma.")

        # Manejar error si tiene dependencias activas (Tarea 1)
        # Comprueba si tiene alguna coreografía registrada a su nombre
        if user_to_delete.created_choreographies.exists():
            raise ValidationError(
                "No se puede eliminar al usuario porque figura como creador de coreografías en el catálogo. "
                "Debe reasignar el creador o remover las coreografías primero."
            )

        # Eliminación lógica en la base de datos (Tarea 2)
        user_to_delete.is_active = False
        user_to_delete.save()