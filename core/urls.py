from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('checkout/', views.Checkout.as_view(), name='checkout'),
    path('cart-summary/', views.CartSummaryView.as_view(), name='cart-summary'),
    path('product/<slug>/', views.ProductDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', views.add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', views.remove_from_cart, name='remove-from-cart'),
    path('remove-product-from-cart/<slug>/', views.remove_a_product_from_cart, name='remove-product-from-cart'),
    path('payment/<payment_option>/', views.PaymentView.as_view(), name='payment'),
]