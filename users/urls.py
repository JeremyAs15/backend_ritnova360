from django.urls import path
from .views import StudentRegistrationView, InternalUserManagementView, UserDetailView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Endpoints de Autenticación JWT estándar
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Ruta de autoregistro para estudiantes/clientes externos
    path('register/', StudentRegistrationView.as_view(), name='student-register'),
    # Ruta para administración de personal interno por administradores/directores
    path('internal/', InternalUserManagementView.as_view(), name='internal-user-management'),
    # Ruta para el detalle, actualización y eliminación de usuarios por ID
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
]