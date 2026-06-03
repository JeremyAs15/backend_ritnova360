from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Choreography, ShoppingCart, Enroll
from .serializers import ChoreographySerializer, ShoppingCartSerializer, EnrollSerializer, RateSerializer
from .services import AcademyService

class ChoreographyListView(APIView):
    """
    Endpoint para listar el catálogo de coreografías y permitir la creación de nuevos cursos.
    """
    def get_permissions(self):
        # Permite acceso sin autenticación para ver el catálogo de coreografías
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get(self, request):
        """
        Filtra el catálogo de coreografías por género musical o dificultad.
        """
        queryset = Choreography.objects.all().prefetch_related('video_clips')
        
        genre = request.query_params.get('genre')
        difficulty = request.query_params.get('difficulty')

        if genre:
            queryset = queryset.filter(genre__iexact=genre)
        if difficulty:
            queryset = queryset.filter(difficulty_level__iexact=difficulty)

        serializer = ChoreographySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Registra un curso nuevo de coreografía con sus secciones de video.
        """
        serializer = ChoreographySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            choreography = AcademyService.create_choreography(request.user, serializer)
            output_serializer = ChoreographySerializer(choreography)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ShoppingCartView(APIView):
    """
    Módulo para la interacción con el carrito de compras y control del estudiante.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """
        Muestra la preselección de compras activa del cliente.
        """
        cart, created = ShoppingCart.objects.get_or_create(user=request.user, state='pending')
        serializer = ShoppingCartSerializer(cart)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Añade un elemento a la lista del carrito de compras.
        Cuerpo esperado: {"choreography_id": 1}
        """
        choreography_id = request.data.get('choreography_id')
        if not choreography_id:
            return Response({"detail": "Es necesario el ID de la coreografía."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            cart_item = AcademyService.add_choreography_to_cart(request.user, int(choreography_id))
            return Response({"detail": "Añadido con éxito."}, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartCheckoutView(APIView):
    """
    Endpoint para procesar los pagos y convertir compras pendientes en accesos activos.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """
        Cierra el carrito simulando el pago y otorgando el acceso inmediato.
        """
        billing_info = request.data.get('datos_facturacion', '')
        try:
            cart = AcademyService.process_cart_checkout(request.user, billing_info)
            serializer = ShoppingCartSerializer(cart)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RateChoreographyView(APIView):
    """
    Permite a los estudiantes calificar el material de estudio.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        choreography_id = serializer.validated_data['choreography'].choreography_id
        score = serializer.validated_data['score']
        comment = serializer.validated_data.get('comment', '')

        try:
            rating = AcademyService.rate_choreography(request.user, choreography_id, score, comment)
            output_serializer = RateSerializer(rating)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        except PermissionDenied as e:
            return Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyEnrollmentsListView(APIView):
    """
    Retorna la lista de coreografías que el cliente ha adquirido para su reproducción.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        enrollments = Enroll.objects.filter(user=request.user, state='active')
        serializer = EnrollSerializer(enrollments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)