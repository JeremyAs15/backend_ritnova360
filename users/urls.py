from django.urls import path
from .views import StudentRegistrationView, InternalUserManagementView, UserDetailView

urlpatterns = [
    # Ruta de autoregistro para estudiantes/clientes externos
    path('register/', StudentRegistrationView.as_view(), name='student-register'),
    
    # Ruta para administración de personal interno por administradores/directores
    path('internal/', InternalUserManagementView.as_view(), name='internal-user-management'),
    
    # Ruta para el detalle, actualización y eliminación de usuarios por ID
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]