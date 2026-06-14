from django.urls import resolvers
from django.db import transaction
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Sum, Avg, Count, F, Q
from django.db.models.functions import TruncMonth, TruncWeek
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import Choreography, Rate, Enroll, ShoppingCart, AddTo, VideoClip, VideoView
from .serializers import ChoreographySerializer, RateSerializer

def _ultimos_6_meses(now):
    """Retorna lista de tuples (año, mes) de los últimos 6 meses en orden cronológico."""
    resultado = []
    for i in range(5, -1, -1):
        total_meses = now.month - i
        if total_meses <= 0:
            resultado.append((now.year - 1, total_meses + 12))
        else:
            resultado.append((now.year, total_meses))
    return resultado

class AcademyService:
    """
    Administra la capa de negocio relacionada a las operaciones de la academia de danza,
    garantizando transacciones atómicas en flujos financieros y asignación de accesos.
    """

    @staticmethod
    def create_choreography(user_creator, serializer: ChoreographySerializer) -> Choreography:
        """
        Verifica que el creador de la coreografía sea un profesor, administrador o director.
        """
        if user_creator.role not in ['teacher', 'admin', 'director'] and not user_creator.is_superuser:
            raise PermissionDenied("Solo el personal docente o administrativo de la academia puede registrar coreografías.")
        
        return serializer.save(creator=user_creator)    

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

    @staticmethod
    def mark_video_as_viewed(user, clip_id: int):
        """
        Registra que un estudiante vio un video clip.
        Requiere que el usuario esté inscrito en la coreografía correspondiente.
        """
        from .models import VideoView
        video_clip = VideoClip.objects.get(pk=clip_id)

        if not Enroll.objects.filter(user=user, choreography=video_clip.choreography, state='active').exists():
            raise PermissionDenied("Debe estar inscrito en la coreografía para registrar el progreso.")

        view, created = VideoView.objects.get_or_create(
            user=user,
            video_clip=video_clip
        )
        return view, created

    @staticmethod
    def get_dashboard_data(user):
        """
        Retorna los indicadores del dashboard según el rol del usuario autenticado.
        """
        User = get_user_model()
        now = timezone.now()
        hace_6_meses = now - timedelta(days=180)
        MESES = {
            1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
            5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
            9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
        }

        role = 'admin' if user.is_superuser else user.role

        if role in ['admin', 'director']:
            ingresos_mes = AddTo.objects.filter(
                state='active',
                shopping_cart__state='completed',
                shopping_cart__date__month=now.month,
                shopping_cart__date__year=now.year,
            ).aggregate(total=Sum('price_at_purchase'))['total'] or 0

            ingresos_qs = AddTo.objects.filter(
                state='active',
                shopping_cart__state='completed',
                shopping_cart__date__gte=hace_6_meses.date(),
            ).annotate(mes=TruncMonth('shopping_cart__date')) \
            .values('mes') \
            .annotate(total=Sum('price_at_purchase')) \
            .order_by('mes')

            ingresos_map = {(e['mes'].year, e['mes'].month): float(e['total']) for e in ingresos_qs}
            meses_labels = [MESES[m] for a, m in _ultimos_6_meses(now)]

            ingresos_por_mes = {
                'categories': meses_labels,
                'series': [{'name': 'Ingresos', 'data': [ingresos_map.get((a, m), 0) for a, m in _ultimos_6_meses(now)]}]
            }

            ventas_genero_qs = list(
                Enroll.objects.filter(state='active')
                .values(genero=F('choreography__genre'))
                .annotate(cantidad=Count('id'))
                .order_by('-cantidad')
            )
            ventas_por_genero = {
                'labels': [e['genero'] for e in ventas_genero_qs],
                'series': [e['cantidad'] for e in ventas_genero_qs]
            }

            top_qs = list(
                Choreography.objects.annotate(
                    ventas=Count('enrollments', filter=Q(enrollments__state='active'))
                ).order_by('-ventas')
                .values('song_name', 'ventas')[:5]
            )
            top_coreografias = {
                'categories': [c['song_name'] for c in top_qs],
                'series': [{'name': 'Ventas', 'data': [c['ventas'] for c in top_qs]}]
            }

            return {
                'role': role,
                'kpis': {
                    'usuarios_internos': User.objects.filter(
                        role__in=['admin', 'director', 'teacher'], is_active=True
                    ).count(),
                    'total_coreografias': Choreography.objects.count(),
                    'ventas_mes': Enroll.objects.filter(
                        date__month=now.month,
                        date__year=now.year,
                        state='active'
                    ).count(),
                    'ingresos_mes': float(ingresos_mes),
                },
                'ingresos_por_mes': ingresos_por_mes,
                'ventas_por_genero': ventas_por_genero,
                'top_coreografias': top_coreografias,
            }

        if role == 'teacher':
            mis_coreografias = Choreography.objects.filter(creator=user)

            ventas_qs = Enroll.objects.filter(
                choreography__in=mis_coreografias,
                state='active',
                date__gte=hace_6_meses.date(),
            ).annotate(mes=TruncMonth('date')) \
            .values('mes') \
            .annotate(cantidad=Count('id')) \
            .order_by('mes')

            ventas_map = {(e['mes'].year, e['mes'].month): e['cantidad'] for e in ventas_qs}
            ventas_por_mes = {
                'categories': [MESES[m] for a, m in _ultimos_6_meses(now)],
                'series': [{'name': 'Ventas', 'data': [ventas_map.get((a, m), 0) for a, m in _ultimos_6_meses(now)]}]
            }

            rating_promedio = Rate.objects.filter(
                choreography__in=mis_coreografias
            ).aggregate(avg=Avg('score'))['avg']

            return {
                'role': role,
                'kpis': {
                    'mis_coreografias': mis_coreografias.count(),
                    'ventas_mes': Enroll.objects.filter(
                        choreography__in=mis_coreografias,
                        date__month=now.month,
                        date__year=now.year,
                        state='active'
                    ).count(),
                    'rating_promedio': round(float(rating_promedio), 1) if rating_promedio else None,
                },
                'ventas_por_mes': ventas_por_mes,
            }

        if role == 'student':
            mis_inscripciones = Enroll.objects.filter(user=user, state='active')
            coreografias_ids = mis_inscripciones.values_list('choreography_id', flat=True)

            generos_usuario = list(
                Choreography.objects.filter(choreography_id__in=coreografias_ids)
                .values_list('genre', flat=True).distinct()
            )

            progreso_qs = VideoView.objects.filter(
                user=user,
                viewed_at__gte=hace_6_meses,
            ).annotate(semana=TruncWeek('viewed_at')) \
            .values('semana') \
            .annotate(cantidad=Count('id')) \
            .order_by('semana')

            recomendaciones_qs = Choreography.objects.exclude(
                choreography_id__in=coreografias_ids
            ).select_related('creator')
            if generos_usuario:
                recomendaciones_qs = recomendaciones_qs.filter(genre__in=generos_usuario)

            return {
                'role': role,
                'kpis': {
                    'coreografias_compradas': mis_inscripciones.count(),
                    'videos_vistos': VideoView.objects.filter(user=user).count(),
                    'generos_explorados': Choreography.objects.filter(
                        choreography_id__in=coreografias_ids
                    ).values('genre').distinct().count(),
                    'mi_rating_promedio': round(float(
                        Rate.objects.filter(user=user).aggregate(avg=Avg('score'))['avg']
                    ), 1) if Rate.objects.filter(user=user).exists() else None,
                },
                'progreso_semanal': [
                    {'semana': e['semana'].strftime('%Y-%m-%d'), 'cantidad': e['cantidad']}
                    for e in progreso_qs
                ],
                'recomendaciones': [
                    {
                        'choreography_id': c.choreography_id,
                        'nombre': c.song_name,
                        'genero': c.genre,
                        'precio': float(c.price),
                        'profesor': f"{c.creator.first_name} {c.creator.last_name}" if c.creator else None,
                    }
                    for c in recomendaciones_qs[:3]
                ],
            }

        raise PermissionDenied("Rol no reconocido para el dashboard.")