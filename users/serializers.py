from rest_framework import serializers
from .models import User
import requests
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura y representación de la información detallada de un usuario.
    """
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'role',
            'datos_facturacion_default', 'teacher_type', 'date_joined'
        ]
        read_only_fields = ['id', 'role', 'date_joined']


class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para la autoregistración pública de estudiantes.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    first_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    last_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    email = serializers.EmailField(required=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'datos_facturacion_default'
        ]

    def validate_email(self, value):
        # Normalización a minúsculas y eliminación de espacios laterales
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("Este correo electrónico ya se encuentra registrado.")
        return normalized_email


class InternalUserCreationSerializer(serializers.ModelSerializer):
    """
    Serializador utilizado por Directores o Administradores para registrar personal interno.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    first_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    last_name = serializers.CharField(required=True, max_length=150, allow_blank=False)
    email = serializers.EmailField(required=True)
    role = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'role', 'teacher_type'
        ]

    def validate_role(self, value):
        valid_roles = ['admin', 'director', 'teacher']
        if value not in valid_roles:
            raise serializers.ValidationError(
                f"El rol especificado no es válido. Debe ser uno de los siguientes: {', '.join(valid_roles)}."
            )
        return value

    def validate_email(self, value):
        normalized_email = value.strip().lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return normalized_email

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializador para validar los datos permitidos en la actualización de perfiles.
    Evita la alteración del correo y rol por esta vía.
    """
    first_name = serializers.CharField(required=False, max_length=150, allow_blank=False)
    last_name = serializers.CharField(required=False, max_length=150, allow_blank=False)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'datos_facturacion_default',
            'teacher_type'
        ]

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Valida que el correo tenga un formato correcto para la solicitud de cambio de clave.
    """
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Valida los parámetros requeridos para aplicar el cambio físico de contraseña.
    """
    uidb64 = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=6)

class StudentRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializador para la autoregistración pública de estudiantes.
    Adaptado para registro rápido (Solo Nombre, Apellido, Email y Clave).
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = User
        # Redujimos los fields a estrictamente lo que manda el frontend
        fields = ['email', 'password', 'first_name', 'last_name']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya se encuentra registrado.")
        return value
    
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Serializador personalizado que hereda de SimpleJWT para validar
    el CAPTCHA del lado del backend antes de generar los tokens de acceso.
    """
    # Campo opcional u obligatorio según su flujo de desarrollo
    captcha_token = serializers.CharField(write_only=True, required=False)

    def validate(self, attrs):
        # 1. Obtener el token de CAPTCHA enviado desde el frontend
        captcha_token = attrs.get('captcha_token')
        
        # 2. Verificar si se debe omitir la validación en desarrollo
        skip_validation = getattr(settings, 'SKIP_CAPTCHA_VALIDATION', False)

        if not skip_validation:
            if not captcha_token:
                raise serializers.ValidationError(
                    {"captcha": "Es necesario proporcionar el token de verificación CAPTCHA."}
                )
            
            # Realizar petición de verificación a Google reCAPTCHA
            payload = {
                'secret': settings.RECAPTCHA_SECRET_KEY,
                'response': captcha_token
            }
            try:
                response = requests.post(
                    'https://challenges.cloudflare.com/turnstile/v0/siteverify', 
                    data=payload,
                    timeout=5
                )
                result = response.json()
                
                # Si la validación de Google falla, impedimos el inicio de sesión
                if not result.get('success'):
                    raise serializers.ValidationError(
                        {"captcha": "La validación del CAPTCHA ha fallado o el token ha expirado."}
                    )
            except requests.exceptions.RequestException:
                raise serializers.ValidationError(
                    {"captcha": "No fue posible conectar con el servicio de verificación de CAPTCHA."}
                )

        # 3. Remover el campo 'captcha_token' para no pasarlo al validador interno de SimpleJWT
        attrs.pop('captcha_token', None)

        # 4. Proceder con la validación de credenciales estándar (correo y contraseña)
        # Esto cubre la tarea AB-144 y genera los tokens de la tarea AB-146
        data = super().validate(attrs)
        return data
