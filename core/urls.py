from django.urls import path
from . import views

urlpatterns = [
    # Authentication URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('create-shop/', views.create_shop_view, name='create_shop'),
    path('update-shop/', views.update_shop_view, name='update_shop'),
    path('profile/', views.profile_view, name='profile'),
    
    # Home page
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('terms/', views.terms_view, name='terms'),
    
    # E-commerce pages
    path('browse/', views.browse_cats_view, name='browse_cats'),
    path('browse/filter/', views.filter_products_view, name='filter_products'),
    path('shops/', views.shop_list_view, name='shop_list'),
    path('shops/<uuid:shop_id>/', views.shop_detail_view, name='shop_detail'),
    path('product/<uuid:product_id>/', views.product_detail_view, name='product_detail'),
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<uuid:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    
    # Mate pages
    path('mates/', views.mate_list_view, name='mate_list'),
    path('mates/<uuid:mate_id>/', views.mate_detail_view, name='mate_detail'),
]
