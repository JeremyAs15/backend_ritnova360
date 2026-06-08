from django.urls import path
from .views import StudentRegistrationView, InternalUserManagementView, UserDetailView, PasswordResetRequestView, PasswordResetConfirmView, CustomTokenObtainPairView, GoogleLoginView   
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    # Endpoints de Autenticación JWT estándar
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
     path('google-login/', GoogleLoginView.as_view(), name='google_login'),
    # Ruta de autoregistro para estudiantes/clientes externos
    path('register/', StudentRegistrationView.as_view(), name='student-register'),
    # Ruta para administración de personal interno por administradores/directores
    path('internal/', InternalUserManagementView.as_view(), name='internal-user-management'),
    # Ruta para el detalle, actualización y eliminación de usuarios por ID
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    # Rutas para la recuperación de contraseña
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

]