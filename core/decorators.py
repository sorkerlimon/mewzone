from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import OTPVerification
from shop.models import SellerShop


def seller_required(view_func):
    """Decorator to ensure user is authenticated and is a seller"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        
        if request.user.role != 'SELLER':
            messages.error(request, 'This page is only for sellers.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def no_shop_required(view_func):
    """Decorator to ensure seller doesn't have a shop yet"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            request.user.seller_shop
            messages.info(request, 'You already have a shop. You can update it instead.')
            return redirect('update_shop')
        except SellerShop.DoesNotExist:
            pass
        
        return view_func(request, *args, **kwargs)
    return wrapper


def has_shop_required(view_func):
    """Decorator to ensure seller has a shop"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        try:
            request.user.seller_shop
        except SellerShop.DoesNotExist:
            messages.error(request, 'You need to create a shop first.')
            return redirect('create_shop')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def otp_session_required(view_func):
    """Decorator to ensure user has valid OTP session"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('registration_email'):
            messages.error(request, 'Please complete registration first.')
            return redirect('register')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def verified_user_required(view_func):
    """Decorator to ensure user is verified"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this page.')
            return redirect('login')
        
        if not request.user.is_verified:
            messages.error(request, 'Please verify your email first.')
            return redirect('verify_otp')
        
        return view_func(request, *args, **kwargs)
    return wrapper
