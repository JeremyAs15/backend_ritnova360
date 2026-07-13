from rest_framework import serializers
from .models import Choreography, VideoClip, Rate, Enroll, ShoppingCart, AddTo

class VideoClipSerializer(serializers.ModelSerializer):
    """
    Serializador secundario para gestionar los clips de video.
    """
    class Meta:
        model = VideoClip
        fields = ['clip_id', 'part_number', 'video_url']


class ChoreographySerializer(serializers.ModelSerializer):
    """
    Serializador principal de Coreografías.
    Maneja la lectura y la escritura anidada de clips de video relacionados.
    """
    # Flujo de lectura: Incluye la lista completa de clips detallados asociados.
    # Flujo de escritura: Permite recibir un JSON con la estructura del clip directamente.
    video_clips = VideoClipSerializer(many=True, required=False)
    creator_email = serializers.EmailField(source='creator.email', read_only=True)

    class Meta:
        model = Choreography
        fields = [
            'choreography_id', 'song_name', 'genre', 'difficulty_level',
            'price', 'creator', 'creator_email', 'creation_date', 'video_clips'
        ]
        read_only_fields = ['choreography_id', 'creation_date', 'creator']

    def create(self, validated_data):
        """
        Sobreescritura del método de creación de Django REST Framework para procesar
        e insertar los objetos relacionados de VideoClip en una sola transacción.
        """
        # Extraemos los datos de video_clips de los datos validados para procesarlos manualmente
        clips_data = validated_data.pop('video_clips', [])
        
        # El guardado de la coreografía base se realiza con la estructura predeterminada
        choreography = Choreography.objects.create(**validated_data)
        
        # Registramos cada video vinculándolo con la clave foránea recién generada
        for clip in clips_data:
            VideoClip.objects.create(choreography=choreography, **clip)
            
        return choreography

    def update(self, instance, validated_data):
        clips_data = validated_data.pop('video_clips', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if clips_data is not None:
            instance.video_clips.all().delete()
            for clip in clips_data:
                VideoClip.objects.create(choreography=instance, **clip)

        return instance


class RateSerializer(serializers.ModelSerializer):
    """
    Serializador para el registro de calificaciones de estudiantes.
    """
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Rate
        fields = ['id', 'user', 'user_email', 'choreography', 'score', 'comment', 'date']
        read_only_fields = ['id', 'user', 'date']

    def validate_score(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("La puntuación debe establecerse en un entero entre 1 y 5.")
        return value


class AddToSerializer(serializers.ModelSerializer):
    """
    Serializador para reflejar las coreografías añadidas a un carrito.
    """
    choreography_name = serializers.CharField(source='choreography.song_name', read_only=True)
    choreography_price = serializers.DecimalField(source='choreography.price', max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = AddTo
        fields = ['id', 'choreography', 'choreography_name', 'choreography_price', 'price_at_purchase', 'state']
        read_only_fields = ['id', 'price_at_purchase', 'state']


class ShoppingCartSerializer(serializers.ModelSerializer):
    """
    Serializador del carrito de compras.
    Proporciona un desglose detallado de los ítems incluidos y la sumatoria del costo total.
    """
    items = AddToSerializer(many=True, read_only=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = ShoppingCart
        fields = ['shopping_cart_id', 'user', 'state', 'date', 'items', 'total_amount']
        read_only_fields = ['shopping_cart_id', 'user', 'state', 'date']

    def get_total_amount(self, obj) -> float:
        """
        Cálculo dinámico en el flujo de lectura (GET) de la sumatoria de precios activos.
        """
        active_items = obj.items.filter(state='active')
        return float(sum(item.price_at_purchase for item in active_items))


class EnrollSerializer(serializers.ModelSerializer):
    """
    Serializador de lectura para registrar los accesos aprobados a las coreografías.
    """
    choreography_name = serializers.CharField(source='choreography.song_name', read_only=True)
    
    class Meta:
        model = Enroll
        fields = ['id', 'choreography', 'choreography_name', 'date', 'state', 'id_source']