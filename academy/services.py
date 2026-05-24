from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from .models import Choreography, Rate, Enroll, ShoppingCart, AddTo
from .serializers import ChoreographySerializer, RateSerializer

class AcademyService:
    """
    Administra la capa de negocio relacionada a las operaciones de la academia de danza,
    garantizando transacciones atómicas en flujos financieros y asignación de accesos.
    """

    @staticmethod
    def create_choreography(user_creator, data: dict) -> Choreography:
        """
        Verifica que el creador de la coreografía sea un profesor, administrador o director.
        """
        if user_creator.role not in ['teacher', 'admin', 'director'] and not user_creator.is_superuser:
            raise PermissionDenied("Solo el personal docente o administrativo de la academia puede registrar coreografías.")
        
        data['creator'] = user_creator
        return ChoreographySerializer().create(validated_data=data)    

    @staticmethod
    def add_choreography_to_cart(user, choreography_id: int) -> AddTo:
        """
        Añade un curso/coreografía al carrito de compras actual de tipo 'pending' del estudiante.
        Valida que no esté inscrito previamente en la coreografía seleccionada.
        """
        choreography = Choreography.objects.get(pk=choreography_id)

        # Regla: Verificar si ya tiene matrícula o acceso activo a este material
        if Enroll.objects.filter(user=user, choreography=choreography, state='active').exists():
            raise ValidationError("Ya posee acceso activo a esta coreografía.")

        with transaction.atomic():
            # Obtener o construir el carrito de compras activo de la sesión del estudiante
            cart, created = ShoppingCart.objects.get_or_create(
                user=user,
                state='pending'
            )

            # Validar si ya se encuentra enlistado en el carrito
            if AddTo.objects.filter(shopping_cart=cart, choreography=choreography, state='active').exists():
                raise ValidationError("Este artículo ya se encuentra preseleccionado en su carrito.")

            # Instanciar el elemento del carrito con el precio actual congelado
            cart_item = AddTo.objects.create(
                shopping_cart=cart,
                choreography=choreography,
                price_at_purchase=choreography.price,
                state='active'
            )
            return cart_item

    @staticmethod
    def process_cart_checkout(user, billing_info: str) -> ShoppingCart:
        """
        Procesa el pago simulado. Convierte todos los ítems activos del carrito
        en registros de inscripción formal ('Enroll') y actualiza el estado del carrito.
        """
        cart = ShoppingCart.objects.filter(user=user, state='pending').first()
        if not cart or not cart.items.filter(state='active').exists():
            raise ValidationError("Su carrito de compras pendiente está vacío.")

        active_items = cart.items.filter(state='active')

        with transaction.atomic():
            for item in active_items:
                # Regla: Si por error se duplica la compra, no genera un nuevo registro de matrícula
                Enroll.objects.get_or_create(
                    user=user,
                    choreography=item.choreography,
                    defaults={
                        'state': 'active',
                        'id_source': f"CART-{cart.shopping_cart_id}"
                    }
                )
            
            # Guardamos los datos de facturación e información simulada en el usuario
            user.datos_facturacion_default = billing_info
            user.save()

            # Marcamos el carrito como completado
            cart.state = 'completed'
            cart.save()
            
            return cart

    @staticmethod
    def rate_choreography(user, choreography_id: int, score: int, comment: str) -> Rate:
        """
        Registra una puntuación para la coreografía.
        Restricción de negocio: El cliente debe tener el curso comprado y matriculado (Enroll)
        para poder emitir un voto o dejar un comentario.
        """
        choreography = Choreography.objects.get(pk=choreography_id)

        # Regla de Negocio: Restricción estricta de validación de compra para evitar votos fraudulentos
        if not Enroll.objects.filter(user=user, choreography=choreography, state='active').exists():
            raise PermissionDenied("Debe adquirir la coreografía antes de poder calificar este curso.")

        rate, created = Rate.objects.update_or_create(
            user=user,
            choreography=choreography,
            defaults={
                'score': score,
                'comment': comment
            }
        )
        return rate