from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class CustomUserManager(BaseUserManager):
    """
    Gestor personalizado para el modelo de usuario donde el correo electrónico
    es el identificador único para la autenticación en lugar de un nombre de usuario.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El correo electrónico es obligatorio.')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) # Django se encarga de encriptar la contraseña automáticamente
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """
    Modelo de usuario personalizado para la gestión de miembros de la academia.
    Soporta roles internos (director, administrador, profesor) y externos (estudiante).
    """
    # Desactivamos el campo username por defecto de Django
    username = None
    
    # Mapeo de campos del diagrama
    email = models.EmailField('Correo electrónico', unique=True)
    phone_number = models.CharField('Número de teléfono', max_length=20, blank=True, null=True)
    
    DOCUMENT_TYPES = [
        ('CC', 'Cédula de Ciudadanía'),
        ('CE', 'Cédula de Extranjería'),
        ('NIT', 'NIT'),
        ('TI', 'Tarjeta de Identidad'),
        ('PASSPORT', 'Pasaporte'),
    ]
    document_type = models.CharField('Tipo de documento', max_length=15, choices=DOCUMENT_TYPES, blank=True, null=True)
    n_documento = models.CharField('Número de documento', max_length=50, blank=True, null=True)
    
    birth_date = models.DateField('Fecha de nacimiento', blank=True, null=True)
    genre = models.CharField('Género', max_length=50, blank=True, null=True)
    
    # Ubicación y facturación
    country = models.CharField('País', max_length=100, blank=True, null=True)
    department = models.CharField('Departamento', max_length=100, blank=True, null=True)
    city = models.CharField('Ciudad', max_length=100, blank=True, null=True)
    
    # Roles en el sistema
    ROLES = [
        ('student', 'Estudiante de Danza'),
        ('teacher', 'Profesor de Danza'),
        ('admin', 'Administrador'),
        ('director', 'Director'),
    ]
    role = models.CharField('Rol', max_length=20, choices=ROLES, default='student')
    
    # Campos opcionales específicos
    datos_facturacion_default = models.TextField('Datos de facturación por defecto', blank=True, null=True)
    teacher_type = models.CharField('Tipo de profesor', max_length=100, blank=True, null=True)

    # Configuración para usar el email como login
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} - {self.role}"