from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# --- COREOGRAFÍA ---
class Choreography(models.Model):
    """
    Representa el catálogo principal de las coreografías disponibles en la academia.
    Almacena los metadatos de la canción, nivel de dificultad y costo del paquete de videos.
    """
    choreography_id = models.AutoField(primary_key=True)
    song_name = models.CharField('Nombre de la canción', max_length=255)
    genre = models.CharField('Género musical', max_length=100)
    difficulty_level = models.CharField('Nivel de dificultad', max_length=50)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)   
    thumbnail_url = models.URLField('URL de la miniatura de portada', max_length=500, blank=True, null=True)
    description = models.TextField('Descripción de la clase', blank=True, null=True)
    
    # Relación: Una coreografía pertenece al profesor que la crea.
    # Si el profesor es eliminado, la coreografía no se borra (ponemos null).
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_choreographies',
        verbose_name='Creador/Profesor'
    )
    creation_date = models.DateField('Fecha de creación', auto_now_add=True)

    is_active = models.BooleanField('Activa en catálogo', default=True)

    def __str__(self):
        return f"{self.song_name} ({self.genre})"

    class Meta:
        db_table = 'choreography'
        verbose_name = 'Coreografía'
        verbose_name_plural = 'Coreografías'


# --- CLIP DE VIDEO ---
class VideoClip(models.Model):
    """
    Secciones de video individuales que componen el paso a paso de una coreografía.
    Establece una relación de uno a muchos (1:N) con Coreografía.
    """
    MEDIA_TYPES = [
        ('video', 'Video'),
        ('image', 'Imagen'),
    ]
    clip_id = models.AutoField(primary_key=True)
    # Relación: Muchos video clips pertenecen a una sola coreografía (1 a N).
    # Si la coreografía se borra, todos sus clips se borran en cascada (CASCADE).
    choreography = models.ForeignKey(
        Choreography, 
        on_delete=models.CASCADE, 
        related_name='video_clips',
        verbose_name='Coreografía'
    )
    part_number = models.IntegerField('Número de parte o sección')
    
    
    media_type = models.CharField(
        'Tipo de recurso', 
        max_length=10, 
        choices=MEDIA_TYPES, 
        default='video'
    )
    
    video_url = models.URLField('URL del recurso (Video o Imagen)', max_length=500)

    def __str__(self):
        return f"{self.choreography.song_name} - Parte {self.part_number} ({self.get_media_type_display()})"

    class Meta:
        db_table = 'video_clip'
        verbose_name = 'Video Clip'
        verbose_name_plural = 'Video Clips'
        ordering = ['part_number']


# --- CALIFICACIONES (RATE) ---
class Rate(models.Model):
    """
    Almacena las puntuaciones y reseñas numéricas (1 a 5 estrellas) hechas por estudiantes.
    Restringe a que cada estudiante califique una coreografía como máximo una vez.
    """
    # Relaciones intermedias
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='ratings',
        verbose_name='Usuario'
    )
    choreography = models.ForeignKey(
        Choreography, 
        on_delete=models.CASCADE, 
        related_name='ratings',
        verbose_name='Coreografía'
    )
    
    # Puntuación del 1 al 5
    score = models.IntegerField(
        'Puntuación', 
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField('Comentario', blank=True, null=True)
    date = models.DateField('Fecha de calificación', auto_now_add=True)

    class Meta:
        db_table = 'rate'
        unique_together = ('user', 'choreography') # Un usuario califica solo una vez cada coreografía
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'

    def __str__(self):
        return f"{self.user.email} calificó {self.choreography.song_name} con {self.score}"


# --- INSCRIPCIÓN (ENROLL) ---
class Enroll(models.Model):
    """
    Asociación de acceso de los estudiantes a las coreografías compradas.
    Permite abrir y validar los permisos de reproducción de los videos en la plataforma.
    """
    STATES = [
        ('active', 'Activo'),
        ('inactive', 'Inactivo'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name='Usuario'
    )
    choreography = models.ForeignKey(
        Choreography, 
        on_delete=models.CASCADE, 
        related_name='enrollments',
        verbose_name='Coreografía'
    )
    date = models.DateField('Fecha de inscripción', auto_now_add=True)
    state = models.CharField('Estado', max_length=20, choices=STATES, default='active')
    id_source = models.CharField('Origen o Referencia de Inscripción', max_length=100, blank=True, null=True)

    class Meta:
        db_table = 'enroll'
        unique_together = ('user', 'choreography')
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'

    def __str__(self):
        return f"{self.user.email} inscrito en {self.choreography.song_name}"


# --- CARRITO DE COMPRAS ---
class ShoppingCart(models.Model):
    """
    Representa el carrito de compras del usuario.
    Mantiene un estado para determinar si está activo, pagado o anulado.
    """
    STATES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]
    shopping_cart_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='carts',
        verbose_name='Usuario'
    )
    state = models.CharField('Estado del carrito', max_length=20, choices=STATES, default='pending')
    date = models.DateField('Fecha de actualización', auto_now=True)

    def __str__(self):
        return f"Carrito {self.shopping_cart_id} - {self.user.email} ({self.state})"

    class Meta:
        db_table = 'shopping_cart'
        verbose_name = 'Carrito de compras'
        verbose_name_plural = 'Carritos de compras'


# --- ELEMENTOS AGREGADOS AL CARRITO (ADD_TO) ---
class AddTo(models.Model):
    """
    Detalle de los artículos (Coreografías) vinculados a un carrito de compras.
    Almacena el precio histórico en el momento en que se añade al carrito.
    """
    STATES = [
        ('active', 'Activo'),
        ('refunded', 'Reembolsado'),
        ('removed', 'Removido'),
    ]
    shopping_cart = models.ForeignKey(
        ShoppingCart, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name='Carrito de compras'
    )
    choreography = models.ForeignKey(
        Choreography, 
        on_delete=models.CASCADE,
        verbose_name='Coreografía'
    )
    price_at_purchase = models.DecimalField('Precio de compra', max_digits=10, decimal_places=2)
    state = models.CharField('Estado del artículo', max_length=20, choices=STATES, default='active')

    class Meta:
        db_table = 'add_to'
        unique_together = ('shopping_cart', 'choreography')
        verbose_name = 'Elemento de carrito'
        verbose_name_plural = 'Elementos de carritos'

    def __str__(self):
        return f"{self.choreography.song_name} en Carrito {self.shopping_cart.shopping_cart_id}"

class VideoView(models.Model):
    """
    Registra qué videos ha visto cada estudiante.
    Se usa para calcular 'videos vistos' y 'progreso semanal' en el dashboard.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_views'
    )
    video_clip = models.ForeignKey(
        VideoClip,
        on_delete=models.CASCADE,
        related_name='views'
    )
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'video_view'
        unique_together = ('user', 'video_clip')
        verbose_name = 'Video visto'
        verbose_name_plural = 'Videos vistos'

    def __str__(self):
        return f"{self.user.email} vio {self.video_clip}"