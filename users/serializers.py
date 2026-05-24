from rest_framework import serializers
from .models import User

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

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'datos_facturacion_default'
        ]

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya se encuentra registrado.")
        return value


class InternalUserCreationSerializer(serializers.ModelSerializer):
    """
    Serializador utilizado por Directores o Administradores para registrar personal interno.
    """
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 'phone_number',
            'document_type', 'n_documento', 'birth_date', 'genre',
            'country', 'department', 'city', 'role', 'teacher_type'
        ]

    def validate_role(self, value):
        if value not in ['admin', 'director', 'teacher']:
            raise serializers.ValidationError("El rol especificado debe ser interno (admin, director o teacher).")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado.")
        return value