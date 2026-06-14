from django.urls import path
from .views import (
    ChoreographyListView, ShoppingCartView, CartCheckoutView, 
    RateChoreographyView, MyEnrollmentsListView, MarkVideoViewedView
)

urlpatterns = [
    # Gestión general y listado de catálogo
    path('choreographies/', ChoreographyListView.as_view(), name='choreography-list-create'),
    
    # Interacción de los clientes con su preselección de compras
    path('cart/', ShoppingCartView.as_view(), name='shopping-cart'),
    
    # Ejecución de pago y facturación del pedido
    path('cart/checkout/', CartCheckoutView.as_view(), name='cart-checkout'),
    
    # Registro de valoraciones y reseñas numéricas
    path('rate/', RateChoreographyView.as_view(), name='rate-choreography'),
    
    # Listado de productos comprados con acceso habilitado
    path('my-courses/', MyEnrollmentsListView.as_view(), name='my-enrollments'),

    # Registro de progreso del estudiante
    path('videos/<int:clip_id>/view/', MarkVideoViewedView.as_view(), name='mark-video-viewed'),
]