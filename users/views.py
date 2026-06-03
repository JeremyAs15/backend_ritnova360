from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.pagination import PageNumberPagination 
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from .models import User
from .serializers import UserSerializer, StudentRegistrationSerializer, InternalUserCreationSerializer, UserUpdateSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer 
from .services import UserService

class UserPagination(PageNumberPagination):
    """
    Paginación estándar que limita la respuesta a un máximo de 20 registros.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 20

class StudentRegistrationView(APIView):
    """
    Endpoint para el auto-registro público de clientes/estudiantes de danza.
    Acceso: Público (AllowAny).
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.register_student(serializer.validated_data)
            output_serializer = UserSerializer(user)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InternalUserManagementView(APIView):
    """
    Endpoint para la gestión de usuarios internos (creación, edición, listado y eliminación).
    Acceso: Autenticado. La lógica de servicios restringe el uso a administradores/directores.
    """
    permission_classes = [permissions.IsAuthenticated]

    # Mapeo de valores de ordenamiento permitidos a campos del modelo
    ORDERING_FIELDS_MAP = {
        'name': ['first_name', 'last_name'],
        '-name': ['-first_name', '-last_name'],
        'date_joined': ['date_joined'],
        '-date_joined': ['-date_joined'],
    }

    def get(self, request):
        """
        Listar usuarios internos con soporte para filtros por rol y ciudad.
        """
        # Filtro de seguridad: Un estudiante no debe poder listar la nómina interna libremente
        if request.user.role not in ['admin', 'director'] and not request.user.is_superuser:
            return Response({"detail": "No autorizado."}, status=status.HTTP_403_FORBIDDEN)

        queryset = UserService.get_internal_users()
        
        # Filtros 
        role_filter = request.query_params.get('role')
        city_filter = request.query_params.get('city')
        active_filter = request.query_params.get('is_active')
        
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        if city_filter:
            queryset = queryset.filter(city__iexact=city_filter)
        if active_filter is not None:
            # Convertimos el string de la URL a booleano (maneja 'true', '1' como True, lo demás False)
            is_active_bool = active_filter.lower() in ['true', '1', 'yes']
            queryset = queryset.filter(is_active=is_active_bool)

        # Ordenamiento dinámico (por defecto: nombre ascendente)
        ordering_param = request.query_params.get('ordering', 'name')
        order_fields = self.ORDERING_FIELDS_MAP.get(ordering_param, ['first_name', 'last_name'])
        queryset = queryset.order_by(*order_fields)
        
        # Paginación        
        paginator = UserPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request, view=self)
        
        if paginated_queryset is not None:
            serializer = UserSerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Crear usuario interno (Admin, Director o Profesor).
        """
        serializer = InternalUserCreationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserService.create_internal_user(request.user, serializer.validated_data)
            output_serializer = UserSerializer(user)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserDetailView(APIView):
    """
    Endpoint para el detalle, actualización y borrado físico de usuarios individuales.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if request.user != user and request.user.role not in ['admin', 'director']:
            return Response({"detail": "Acceso denegado."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user_to_update = get_object_or_404(User, pk=pk)
        try:
            updated_user = UserService.update_user_profile(user_to_update, request.user, request.data)
            serializer = UserSerializer(updated_user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        user_to_delete = get_object_or_404(User, pk=pk)
        try:
            UserService.delete_internal_user(request.user, user_to_delete)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PasswordResetRequestView(APIView):
    """
    Endpoint para solicitar la recuperación de contraseña.
    Acceso: Público.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        try:
            UserService.request_password_reset(email)
            # Retornamos un mensaje genérico por seguridad para evitar enumeración de cuentas
            return Response(
                {"detail": "Si el correo electrónico coincide con una cuenta activa, se ha enviado un mensaje con las instrucciones."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordResetConfirmView(APIView):
    """
    Endpoint para confirmar el cambio de contraseña enviando el token y la nueva clave.
    Acceso: Público.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        uidb64 = serializer.validated_data['uidb64']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            UserService.confirm_password_reset(uidb64, token, new_password)
            return Response(
                {"detail": "La contraseña ha sido restablecida con éxito."},
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
class UserDetailView(APIView):
    """
    Endpoint para el detalle, actualización y borrado lógico de usuarios individuales.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        user = get_object_or_404(User, pk=pk)  # Validación de existencia (Tarea 3)
        if request.user != user and request.user.role not in ['admin', 'director']:
            return Response({"detail": "Acceso denegado."}, status=status.HTTP_403_FORBIDDEN)
            
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        user_to_update = get_object_or_404(User, pk=pk)
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            updated_user = UserService.update_user_profile(
                user_to_update, 
                request.user, 
                serializer.validated_data
            )
            output_serializer = UserSerializer(updated_user)
            return Response(output_serializer.data, status=status.HTTP_200_OK)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
        Endpoint DELETE para ejecutar la baja lógica del usuario. (Tarea 4)
        """
        user_to_delete = get_object_or_404(User, pk=pk)  # Validación de existencia (Tarea 3)
        try:
            UserService.delete_internal_user(request.user, user_to_delete)
            # Retorna 204 No Content para confirmar el éxito de la desactivación
            return Response(status=status.HTTP_204_NO_CONTENT)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)