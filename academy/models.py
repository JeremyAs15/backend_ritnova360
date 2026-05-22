from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

# --- COREOGRAFÍA ---
class Choreography(models.Model):
    choreography_id = models.AutoField(primary_key=True)
    song_name = models.CharField('Nombre de la canción', max_length=255)
    genre = models.CharField('Género musical', max_length=100)
    difficulty_level = models.CharField('Nivel de dificultad', max_length=50)
    price = models.DecimalField('Precio', max_digits=10, decimal_places=2)
    
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

    def __str__(self):
        return f"{self.song_name} ({self.genre})"

    class Meta:
        db_table = 'choreography'
        verbose_name = 'Coreografía'
        verbose_name_plural = 'Coreografías'


# --- CLIP DE VIDEO ---
class VideoClip(models.Model):
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
    video_url = models.URLField('URL del video', max_length=500)

    def __str__(self):
        return f"{self.choreography.song_name} - Parte {self.part_number}"

    class Meta:
        db_table = 'video_clip'
        verbose_name = 'Video Clip'
        verbose_name_plural = 'Video Clips'
        ordering = ['part_number']


# --- CALIFICACIONES (RATE) ---
class Rate(models.Model):
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