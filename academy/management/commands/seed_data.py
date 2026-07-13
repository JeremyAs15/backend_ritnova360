import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from academy.models import Choreography, VideoClip, ShoppingCart, AddTo, Enroll, Rate, VideoView

User = get_user_model()

# Datasets simulados para realismo
NOMBRES_ESTUDIANTES = ["Carlos", "Sofía", "Mateo", "Camila", "Alejandro", "Valentina", "Andrés", "Mariana", "Diego", "Gabriela", "Felipe", "Isabella", "Juan", "Daniela", "Lucas", "Elena", "Santiago", "Natalia", "Nicolás", "Lucía"]
APELLIDOS = ["Gómez", "Rodríguez", "López", "Martínez", "Pérez", "González", "Sánchez", "Ramírez", "Díaz", "Torres", "Muñoz", "Rojas", "Silva", "Castro", "Ortiz", "Ruiz"]

GENEROS_DANCE = ["Salsa", "Bachata", "Reggaetón", "Hip-Hop", "Zumba", "Dancehall"]
DIFICULTADES = ["Principiante", "Intermedio", "Avanzado", "Todos los niveles"]

CHOREOGRAPHIES_DATA = [
    {
        "song_name": "Salsa Caleña Fundamentals",
        "genre": "Salsa",
        "difficulty_level": "Principiante",
        "price": 99000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?q=80&w=500&auto=format&fit=crop",
        "description": "Domina los pasos básicos, el conteo rítmico y la postura de la salsa caleña tradicional desde la comodidad de tu hogar."
    },
    {
        "song_name": "Bachata Sensual Masterclass",
        "genre": "Bachata",
        "difficulty_level": "Intermedio",
        "price": 120000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=500&auto=format&fit=crop",
        "description": "Aprende conexión corporal, ondas y giros fluidos con la guía del estilo sensual moderno."
    },
    {
        "song_name": "Urbano & Reggaetón Flow",
        "genre": "Reggaetón",
        "difficulty_level": "Todos los niveles",
        "price": 85000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=500&auto=format&fit=crop",
        "description": "Suelta tu cuerpo y gana confianza con rutinas enérgicas enfocadas en la disociación y el ritmo urbano."
    },
    {
        "song_name": "Hip-Hop Street Grooves",
        "genre": "Hip-Hop",
        "difficulty_level": "Intermedio",
        "price": 110000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1504609773096-104ff2c73ba4?q=80&w=500&auto=format&fit=crop",
        "description": "Explora el bounce, rock y isolaciones clásicas de la cultura hip-hop de los 90 y 2000."
    },
    {
        "song_name": "Zumba Cardio Party",
        "genre": "Zumba",
        "difficulty_level": "Principiante",
        "price": 75000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?q=80&w=500&auto=format&fit=crop",
        "description": "Una excelente alternativa para ejercitarte mientras te diviertes al ritmo de música latina e internacional."
    },
    {
        "song_name": "Dancehall Queen Vibes",
        "genre": "Dancehall",
        "difficulty_level": "Avanzado",
        "price": 115000.00,
        "thumbnail_url": "https://images.unsplash.com/photo-1535525153412-5a42439a210d?q=80&w=500&auto=format&fit=crop",
        "description": "Aprende pasos auténticos y coreografías llenas de fuerza, técnica y expresividad jamaiquina."
    }
]

class Command(BaseCommand):
    help = "Pobla la base de datos con información realista e histórica para pruebas y métricas del dashboard."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Iniciando la generación de datos simulados..."))
        
        # Fecha base para el cálculo histórico (los últimos 6 meses)
        now = timezone.now()

        with transaction.atomic():
            # 1. CREACIÓN DE PROFESORES (si no existen)
            teachers = []
            profesores_datos = [
                ("carlos.danza@ritnova360.com", "Carlos", "Rojas", "Instructor Principal Salsa"),
                ("lucia.dance@ritnova360.com", "Lucía", "Mora", "Especialista Bachata"),
                ("esteban.flow@ritnova360.com", "Esteban", "Suárez", "Coreógrafo Urbano")
            ]
            for email, name, last, spec in profesores_datos:
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": name,
                        "last_name": last,
                        "role": "teacher",
                        "teacher_type": spec,
                        "is_active": True
                    }
                )
                if created:
                    user.set_password("Password123")
                    user.save()
                teachers.append(user)
            self.stdout.write(self.style.SUCCESS(f"Profesores validados: {len(teachers)}"))

            # 2. CREACIÓN DE ESTUDIANTES (simular base de clientes activa)
            students = []
            for i in range(30):  # Generar 30 estudiantes
                email = f"estudiante.{i+1}@correo.com"
                first_name = random.choice(NOMBRES_ESTUDIANTES)
                last_name = f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}"
                user, created = User.objects.get_or_create(
                    email=email,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "role": "student",
                        "is_active": True,
                        "country": "Colombia",
                        "city": random.choice(["Cali", "Bogotá", "Medellín", "Barranquilla", "Bucaramanga"])
                    }
                )
                if created:
                    user.set_password("Password123")
                    user.save()
                students.append(user)
            self.stdout.write(self.style.SUCCESS(f"Estudiantes validados: {len(students)}"))

            # 3. CREACIÓN DE COREOGRAFÍAS Y CLIPS (con imágenes y videos mixtos)
            choreographies = []
            for ch_dict in CHOREOGRAPHIES_DATA:
                ch, created = Choreography.objects.get_or_create(
                    song_name=ch_dict["song_name"],
                    defaults={
                        "genre": ch_dict["genre"],
                        "difficulty_level": ch_dict["difficulty_level"],
                        "price": ch_dict["price"],
                        "thumbnail_url": ch_dict["thumbnail_url"],
                        "description": ch_dict["description"],
                        "creator": random.choice(teachers)
                    }
                )
                choreographies.append(ch)

                # Generar secciones (clips de video e imágenes combinadas)
                if created:
                    # Crear 4 secciones para esta coreografía
                    VideoClip.objects.create(
                        choreography=ch,
                        part_number=1,
                        media_type="video",
                        video_url="https://res.cloudinary.com/demo/video/upload/v1619012484/samples/elephants.mp4"
                    )
                    VideoClip.objects.create(
                        choreography=ch,
                        part_number=2,
                        media_type="image",  # Demostrar soporte de la nueva característica de imagen
                        video_url="https://images.unsplash.com/photo-1508700115892-45ecd05ae2ad?q=80&w=500"
                    )
                    VideoClip.objects.create(
                        choreography=ch,
                        part_number=3,
                        media_type="video",
                        video_url="https://res.cloudinary.com/demo/video/upload/v1619012484/samples/sea.mp4"
                    )
                    VideoClip.objects.create(
                        choreography=ch,
                        part_number=4,
                        media_type="image",
                        video_url="https://images.unsplash.com/photo-1547153760-18fc86324498?q=80&w=500"
                    )
            self.stdout.write(self.style.SUCCESS(f"Catálogo de coreografías validado: {len(choreographies)}"))

            # 4. CREACIÓN DE TRANSACCIONES E INSCRIPCIONES HISTÓRICAS (últimos 6 meses)
            # Para simular flujo de caja, distribuiremos compras a lo largo del tiempo
            sales_count = 0
            enrollments_count = 0

            # Crear un pool de compras distribuidas cronológicamente
            for month_offset in range(0, 6):  # De hace 5 meses hasta el mes actual
                # Definir rango del mes para simulación
                base_month_date = now - timedelta(days=month_offset * 30)
                
                # Simularemos que cada mes se hicieron entre 6 y 12 ventas
                monthly_purchases = random.randint(6, 12)
                for _ in range(monthly_purchases):
                    student = random.choice(students)
                    ch_to_buy = random.sample(choreographies, random.randint(1, 2)) # Compra 1 o 2 cursos
                    
                    purchase_date = base_month_date - timedelta(days=random.randint(0, 28))
                    
                    # Evitamos crear carritos duplicados completados para la misma fecha
                    cart = ShoppingCart.objects.create(
                        user=student,
                        state="completed"
                    )
                    
                    # Truco técnico: Forzar la fecha histórica en campos que tienen auto_now o auto_now_add
                    # Usamos .update() para evitar que Django sobrescriba el valor con la fecha actual de guardado.
                    ShoppingCart.objects.filter(pk=cart.pk).update(date=purchase_date.date())
                    
                    for ch in ch_to_buy:
                        # Registrar el item comprado en el histórico
                        AddTo.objects.get_or_create(
                            shopping_cart=cart,
                            choreography=ch,
                            defaults={
                                "price_at_purchase": ch.price,
                                "state": "active"
                            }
                        )

                        # Crear la matrícula de acceso al curso
                        enroll, en_created = Enroll.objects.get_or_create(
                            user=student,
                            choreography=ch,
                            defaults={
                                "state": "active",
                                "id_source": f"SEED-CART-{cart.shopping_cart_id}"
                            }
                        )
                        if en_created:
                            Enroll.objects.filter(pk=enroll.pk).update(date=purchase_date.date())
                            enrollments_count += 1
                        
                        # Simular calificaciones (Rate) opcionales (un 70% de probabilidad si compró)
                        if random.random() < 0.7:
                            rate, rt_created = Rate.objects.get_or_create(
                                user=student,
                                choreography=ch,
                                defaults={
                                    "score": random.randint(3, 5), # Calificaciones mayormente positivas
                                    "comment": random.choice([
                                        "Excelente explicación de los pasos.",
                                        "Me encantó la música elegida, muy divertida.",
                                        "El ritmo de enseñanza es muy cómodo para aprender en casa.",
                                        "Muy recomendado el profesor, excelente técnica.",
                                        "Las imágenes sustitutas son de gran ayuda."
                                    ])
                                }
                            )
                            if rt_created:
                                Rate.objects.filter(pk=rate.pk).update(date=purchase_date.date())

                        # Simular progreso de visualización (VideoView)
                        # El estudiante ve entre 1 y 4 secciones de los cursos matriculados
                        clips_of_ch = ch.video_clips.all()
                        for clip in random.sample(list(clips_of_ch), random.randint(1, len(clips_of_ch))):
                            view, vw_created = VideoView.objects.get_or_create(
                                user=student,
                                video_clip=clip
                            )
                            if vw_created:
                                # Las vistas ocurren unos días después de la compra
                                view_date = purchase_date + timedelta(days=random.randint(1, 10))
                                VideoView.objects.filter(pk=view.pk).update(viewed_at=view_date)

                    sales_count += 1

            self.stdout.write(self.style.SUCCESS(f"Ventas simuladas registradas: {sales_count}"))
            self.stdout.write(self.style.SUCCESS(f"Inscripciones activas simuladas: {enrollments_count}"))
            self.stdout.write(self.style.SUCCESS("¡Base de datos poblada exitosamente!"))