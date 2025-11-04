from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import User, OTPVerification
from .utils import send_otp_email, generate_otp
from .decorators import seller_required, no_shop_required, has_shop_required, otp_session_required, verified_user_required
from django.utils import timezone
from datetime import timedelta, datetime
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from django.db.models import Avg, Count


def home_view(request):
    """Home page view"""
    if request.user.is_authenticated:
        if request.user.role == 'SELLER':
            try:
                from shop.models import SellerShop
                shop = request.user.seller_shop
                return render(request, 'auth/update_shop.html', {'shop': shop})
            except:
                return render(request, 'auth/create_shop.html')
        else:
            return render(request, 'home.html')
    return render(request, 'home.html')


def login_view(request):
    """Login view"""
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'auth/login.html')


def register_view(request):
    """Registration view"""
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')
        
        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'auth/register.html')
        
        if not phone or len(phone.strip()) == 0:
            messages.error(request, 'Phone number is required.')
            return render(request, 'auth/register.html')
        
        user = User.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role=role
        )
        
        if role == 'SELLER':
            # Generate OTP for seller verification
            otp_code = generate_otp()
            OTPVerification.objects.create(
                user=user,
                email=email,
                otp_code=otp_code,
                verification_type='REGISTRATION',
                expires_at=timezone.now() + timedelta(minutes=10)
            )
            send_otp_email(email, otp_code)
            # Store email in session for OTP verification page
            request.session['registration_email'] = email
            messages.success(request, 'Registration successful! Please check your email for OTP verification.')
            return redirect('verify_otp')
        else:
            # Normal user - mark as verified
            user.is_verified = True
            user.save()
            messages.success(request, 'Registration successful! You can now login.')
            return redirect('login')
    
    return render(request, 'auth/register.html')


@otp_session_required
def verify_otp_view(request):
    """OTP verification view"""
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        try:
            otp_verification = OTPVerification.objects.get(
                otp_code=otp_code,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            
            otp_verification.is_used = True
            otp_verification.user.is_verified = True
            otp_verification.user.save()
            otp_verification.save()
            
            # Log in the user after successful OTP verification
            login(request, otp_verification.user)
            
            # Clear the session
            request.session.pop('registration_email', None)
            
            messages.success(request, 'Email verified successfully! Please create your shop.')
            return redirect('create_shop')
            
        except OTPVerification.DoesNotExist:
            messages.error(request, 'Invalid or expired OTP code.')
    
    # Get the email from session
    email = request.session.get('registration_email', 'your email')
    
    return render(request, 'auth/verify_otp.html', {'email': email})


@seller_required
@no_shop_required
def create_shop_view(request):
    """Create shop view"""
    if request.method == 'POST':
        # Create shop logic here
        shop_name = request.POST.get('shop_name')
        description = request.POST.get('description')
        location = request.POST.get('location')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        postal_code = request.POST.get('postal_code')
        facebook_page = request.POST.get('facebook_page')
        instagram_handle = request.POST.get('instagram_handle')
        twitter_handle = request.POST.get('twitter_handle')
        profile_picture = request.FILES.get('profile_picture')
        
        # Create the shop
        from shop.models import SellerShop
        shop = SellerShop.objects.create(
            seller=request.user,
            shop_name=shop_name,
            description=description,
            location=location,
            address=address,
            city=city,
            state=state,
            country=country,
            postal_code=postal_code,
            facebook_page=facebook_page,
            instagram_handle=instagram_handle,
            twitter_handle=twitter_handle,
            profile_picture=profile_picture
        )
        
        messages.success(request, 'Shop created successfully! Waiting for admin approval.')
        return redirect('login')
    
    return render(request, 'auth/create_shop.html')


@seller_required
@has_shop_required
def update_shop_view(request):
    """Update shop view"""
    from shop.models import SellerShop
    shop = request.user.seller_shop
    approved_product_count = shop.products.filter(is_approved=True).count()
    
    if request.method == 'POST':
        # Update shop logic here
        shop.shop_name = request.POST.get('shop_name', shop.shop_name)
        shop.description = request.POST.get('description', shop.description)
        shop.location = request.POST.get('location', shop.location)
        shop.address = request.POST.get('address', shop.address)
        shop.city = request.POST.get('city', shop.city)
        shop.state = request.POST.get('state', shop.state)
        shop.country = request.POST.get('country', shop.country)
        shop.postal_code = request.POST.get('postal_code', shop.postal_code)
        shop.facebook_page = request.POST.get('facebook_page', shop.facebook_page)
        shop.instagram_handle = request.POST.get('instagram_handle', shop.instagram_handle)
        shop.twitter_handle = request.POST.get('twitter_handle', shop.twitter_handle)
        if 'profile_picture' in request.FILES:
            shop.profile_picture = request.FILES['profile_picture']
        shop.save()
        
        messages.success(request, 'Shop updated successfully!')
        return redirect('update_shop')
    
    context = {
        'shop': shop,
        'approved_product_count': approved_product_count,
    }
    return render(request, 'auth/update_shop.html', context)


@seller_required
@has_shop_required
def add_product_view(request):
    """Allow sellers to submit new products for approval"""
    from shop.models import Product, Breed, ProductImage, ProductVideo, Category, ProductCategory, validate_video_file_size
    from django.core.exceptions import ValidationError

    shop = request.user.seller_shop
    breeds = Breed.objects.filter(is_active=True).order_by('name')
    categories = Category.objects.filter(is_active=True).order_by('name')
    fur_types = Product.FUR_TYPE_CHOICES
    gender_choices = Product.GENDER_CHOICES

    default_form = {
        'name': '',
        'breed': '',
        'gender': gender_choices[0][0] if gender_choices else '',
        'color': '',
        'eye_color': '',
        'fur_type': fur_types[0][0] if fur_types else '',
        'date_of_birth': '',
        'location': shop.location,
        'ready_to_go': False,
        'available_for_pickup': True,
        'available_for_delivery': False,
        'price': '',
        'discount_percentage': '0',
        'description': '',
        'additional_notes': '',
        'other_services': '',
    }

    form_data = default_form.copy()

    if request.method == 'POST':
        form_data = form_data | {
            'name': request.POST.get('name', '').strip(),
            'breed': request.POST.get('breed', ''),
            'gender': request.POST.get('gender', gender_choices[0][0] if gender_choices else ''),
            'color': request.POST.get('color', '').strip(),
            'eye_color': request.POST.get('eye_color', '').strip(),
            'fur_type': request.POST.get('fur_type', fur_types[0][0] if fur_types else ''),
            'date_of_birth': request.POST.get('date_of_birth', ''),
            'location': request.POST.get('location', '').strip() or shop.location,
            'ready_to_go': request.POST.get('ready_to_go') == 'on',
            'available_for_pickup': request.POST.get('available_for_pickup') == 'on',
            'available_for_delivery': request.POST.get('available_for_delivery') == 'on',
            'price': request.POST.get('price', '').strip(),
            'discount_percentage': request.POST.get('discount_percentage', '0').strip() or '0',
            'description': request.POST.get('description', '').strip(),
            'additional_notes': request.POST.get('additional_notes', '').strip(),
            'other_services': request.POST.get('other_services', '').strip(),
        }

        # Validation
        errors = []

        if not form_data['name']:
            errors.append('Please provide a product name.')

        try:
            breed = Breed.objects.get(id=form_data['breed'])
        except (Breed.DoesNotExist, ValueError):
            breed = None
            errors.append('Please choose a valid breed from the list.')

        try:
            dob = datetime.strptime(form_data['date_of_birth'], '%Y-%m-%d').date()
        except (ValueError, TypeError):
            dob = None
            errors.append('Please provide a valid date of birth.')

        try:
            price = Decimal(form_data['price'])
            if price < 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            price = None
            errors.append('Price must be a positive amount.')

        try:
            discount = int(form_data['discount_percentage'] or 0)
            if discount < 0 or discount > 100:
                raise ValueError
        except ValueError:
            discount = 0
            errors.append('Discount percentage must be between 0 and 100.')

        if not form_data['description']:
            errors.append('Please include a product description.')

        if not errors and breed and dob and price is not None:
            product = Product.objects.create(
                shop=shop,
                name=form_data['name'],
                breed=breed,
                gender=form_data['gender'],
                color=form_data['color'],
                eye_color=form_data['eye_color'],
                fur_type=form_data['fur_type'],
                date_of_birth=dob,
                location=form_data['location'],
                ready_to_go=form_data['ready_to_go'],
                available_for_pickup=form_data['available_for_pickup'],
                available_for_delivery=form_data['available_for_delivery'],
                price=price,
                discount_percentage=discount,
                description=form_data['description'],
                additional_notes=form_data['additional_notes'] or None,
                other_services=form_data['other_services'] or None,
            )

            images = request.FILES.getlist('images')
            for index, image_file in enumerate(images[:3]):
                ProductImage.objects.create(
                    product=product,
                    image=image_file,
                    is_primary=(index == 0)
                )

            # Handle video uploads (max 2 videos, max 100MB each)
            videos = request.FILES.getlist('videos')
            max_videos = 2
            max_video_size = 100 * 1024 * 1024  # 100MB in bytes

            if len(videos) > max_videos:
                messages.warning(request, f'Only up to {max_videos} videos are allowed. Additional videos were ignored.')

            for video_file in videos[:max_videos]:
                # Validate file size
                if video_file.size > max_video_size:
                    messages.error(request, f'Video "{video_file.name}" exceeds the 100MB limit and was not uploaded.')
                    continue

                # Validate file extension
                allowed_extensions = ['mp4', 'mov', 'avi', 'webm']
                file_extension = video_file.name.split('.')[-1].lower() if '.' in video_file.name else ''
                if file_extension not in allowed_extensions:
                    messages.error(request, f'Video "{video_file.name}" has an unsupported format. Allowed: {", ".join(allowed_extensions)}.')
                    continue

                try:
                    # Validate using the model's validator
                    validate_video_file_size(video_file)
                    ProductVideo.objects.create(
                        product=product,
                        video=video_file,
                        file_size=video_file.size
                    )
                except ValidationError as e:
                    messages.error(request, str(e))

            # Handle category selection
            selected_categories = request.POST.getlist('categories')
            if selected_categories:
                for category_id in selected_categories:
                    try:
                        category = Category.objects.get(id=category_id, is_active=True)
                        ProductCategory.objects.get_or_create(
                            product=product,
                            category=category
                        )
                    except Category.DoesNotExist:
                        pass

            messages.success(request, 'Product submitted for review. It will appear once approved by admin.')
            return redirect('profile')

        for error in errors:
            messages.error(request, error)

    context = {
        'breeds': breeds,
        'categories': categories,
        'fur_types': fur_types,
        'gender_choices': gender_choices,
        'form_data': form_data,
    }
    return render(request, 'auth/add_product.html', context)


@seller_required
@has_shop_required
def my_products_view(request):
    """Show all products for the seller's shop"""
    from shop.models import Product
    from django.db.models import Avg, Count

    shop = request.user.seller_shop
    
    # Get all products for this shop (both approved and pending)
    products = (
        Product.objects.filter(shop=shop)
        .select_related('breed', 'shop')
        .prefetch_related('images', 'videos')
        .annotate(
            avg_rating=Avg('product_reviews__rating'),
            review_count=Count('product_reviews')
        )
        .order_by('-created_at')
    )

    # Count products by status
    total_products = products.count()
    approved_products = products.filter(is_approved=True).count()
    pending_products = products.filter(is_approved=False, rejected_at__isnull=True).count()
    rejected_products = products.filter(rejected_at__isnull=False).count()

    context = {
        'products': products,
        'shop': shop,
        'total_products': total_products,
        'approved_products': approved_products,
        'pending_products': pending_products,
        'rejected_products': rejected_products,
    }
    
    return render(request, 'auth/my_products.html', context)


def logout_view(request):
    """Logout view"""
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    """User profile page"""
    from shop.models import SellerShop

    shop = None
    if request.user.role == 'SELLER':
        try:
            shop = request.user.seller_shop
        except SellerShop.DoesNotExist:
            shop = None

    context = {
        'shop': shop,
    }

    return render(request, 'auth/profile.html', context)


def browse_cats_view(request):
    """Browse cats e-commerce page"""
    from shop.models import Category, Breed, Product
    from django.db.models import Avg, Count
    
    # Get all active categories with their breed counts
    categories = Category.objects.filter(is_active=True).prefetch_related('breeds')
    breeds = Breed.objects.filter(is_active=True)
    
    latest_products = (
        Product.objects.filter(is_approved=True)
        .select_related('breed', 'shop')
        .prefetch_related('images')
        .annotate(avg_rating=Avg('product_reviews__rating'), review_count=Count('product_reviews'))
        .order_by('-created_at')[:12]
    )

    best_sellers = (
        Product.objects.filter(is_approved=True)
        .annotate(avg_rating=Avg('product_reviews__rating'), review_count=Count('product_reviews'))
        .select_related('breed', 'shop')
        .prefetch_related('images')
        .order_by('-avg_rating', '-review_count', '-created_at')[:8]
    )

    newly_coming = (
        Product.objects.filter(is_approved=True)
        .select_related('breed', 'shop')
        .prefetch_related('images')
        .annotate(avg_rating=Avg('product_reviews__rating'), review_count=Count('product_reviews'))
        .order_by('-created_at')[12:20]
    )

    # Sidebar counts
    color_counts = (
        Product.objects.filter(is_approved=True)
        .values('color')
        .annotate(cnt=Count('id'))
        .order_by('color')
    )
    breed_counts = (
        Product.objects.filter(is_approved=True)
        .values('breed__id', 'breed__name')
        .annotate(cnt=Count('id'))
        .order_by('breed__name')
    )
    gender_counts = (
        Product.objects.filter(is_approved=True)
        .values('gender')
        .annotate(cnt=Count('id'))
        .order_by('gender')
    )

    context = {
        'categories': categories,
        'breeds': breeds,
        'latest_products': latest_products,
        'best_sellers': best_sellers,
        'newly_coming': newly_coming,
        'color_counts': color_counts,
        'breed_counts': breed_counts,
        'gender_counts': gender_counts,
    }
    
    return render(request, 'shop/browse_simple.html', context)


def filter_products_view(request):
    """Return filtered products as HTML fragments for dynamic filtering"""
    from shop.models import Product
    from django.template.loader import render_to_string

    name = request.GET.get('name', '').strip()
    breed_ids = request.GET.getlist('breed')  # list of ids or names
    min_price = request.GET.get('min')
    max_price = request.GET.get('max')
    gender = request.GET.getlist('gender')  # MALE/FEMALE
    colors = request.GET.getlist('color')

    qs = Product.objects.filter(is_approved=True).select_related('breed').prefetch_related('images')
    if name:
        qs = qs.filter(name__icontains=name)
    if breed_ids:
        qs = qs.filter(breed__name__in=breed_ids) | qs.filter(breed__id__in=breed_ids)
    try:
        if min_price:
            qs = qs.filter(price__gte=Decimal(min_price))
        if max_price:
            qs = qs.filter(price__lte=Decimal(max_price))
    except Exception:
        pass
    if gender:
        qs = qs.filter(gender__in=[g.upper() for g in gender])
    if colors:
        qs = qs.filter(color__in=colors)

    qs = qs.order_by('-created_at')[:24]
    # annotate for ratings
    qs = qs.annotate(avg_rating=Avg('product_reviews__rating'), review_count=Count('product_reviews'))
    html = render_to_string('shop/partials/product_grid.html', {'products': qs}, request=request)
    return JsonResponse({'html': html})


def shop_list_view(request):
    """List all shops with ratings in card layout"""
    from shop.models import SellerShop, Category, Breed

    shops = (
        SellerShop.objects.select_related('seller')
        .prefetch_related('products', 'shop_reviews')
        .filter(is_approved=True)
        .order_by('-created_at')
    )
    categories = Category.objects.filter(is_active=True).prefetch_related('breeds')
    breeds = Breed.objects.filter(is_active=True)

    context = {
        'shops': shops,
        'categories': categories,
        'breeds': breeds,
    }

    return render(request, 'shop/shop.html', context)


def shop_detail_view(request, shop_id):
    from shop.models import SellerShop, Product
    from django.db.models import Avg, Count

    shop = SellerShop.objects.select_related('seller').get(id=shop_id, is_approved=True)
    products = (
        Product.objects.filter(shop=shop, is_approved=True)
        .select_related('breed')
        .prefetch_related('images')
        .annotate(avg_rating=Avg('product_reviews__rating'), review_count=Count('product_reviews'))
        .order_by('-created_at')
    )

    # counts for header stats
    total_products = products.count()
    avg_rating = products.aggregate(Avg('avg_rating'))['avg_rating__avg'] or 0

    return render(request, 'shop/shop_detail.html', {
        'shop': shop,
        'products': products,
        'total_products': total_products,
        'avg_rating': avg_rating,
    })


def _get_cart(request):
    cart = request.session.get('cart', {})
    return cart


def _save_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def product_detail_view(request, product_id):
    from shop.models import Product, Category, Breed
    product = Product.objects.select_related('breed', 'shop').prefetch_related('images', 'videos', 'product_reviews__user').get(id=product_id, is_approved=True)
    images = product.images.all()
    videos = product.videos.all()
    reviews = product.product_reviews.filter(is_approved=True)
    return render(request, 'shop/product_detail.html', {
        'product': product,
        'images': images,
        'videos': videos,
        'reviews': reviews,
    })


def add_to_cart_view(request, product_id):
    from shop.models import Product
    product = Product.objects.get(id=product_id, is_approved=True)
    cart = _get_cart(request)
    key = str(product.id)
    quantity = int(request.GET.get('qty', '1'))
    cart[key] = cart.get(key, 0) + max(quantity, 1)
    _save_cart(request, cart)
    messages.success(request, 'Added to cart.')
    return redirect('cart')


def cart_view(request):
    from shop.models import Product
    cart = _get_cart(request)
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids).select_related('breed')
    items = []
    total = Decimal('0')
    for p in products:
        qty = cart.get(str(p.id), 0)
        price = p.discounted_price if p.discount_percentage > 0 else p.price
        line_total = (price * qty)
        items.append({'product': p, 'qty': qty, 'price': price, 'line_total': line_total})
        total += line_total
    return render(request, 'shop/cart.html', {'items': items, 'total': total})


def checkout_view(request):
    # Simple placeholder checkout (no payment integration)
    if request.method == 'POST':
        request.session.pop('cart', None)
        messages.success(request, 'Order placed successfully!')
        return redirect('browse_cats')
    return render(request, 'shop/checkout.html')


def mate_list_view(request):
    """List all approved mates with ratings"""
    from shop.models import Mate, Category, Breed
    
    mates = (
        Mate.objects.filter(is_approved=True)
        .select_related('shop', 'shop__seller', 'breed')
        .prefetch_related('images', 'videos', 'mate_reviews')
        .annotate(
            avg_rating=Avg('mate_reviews__rating'),
            review_count=Count('mate_reviews')
        )
        .order_by('-created_at')
    )
    
    context = {
        'mates': mates,
    }
    
    return render(request, 'shop/mate_list.html', context)


def mate_detail_view(request, mate_id):
    """Mate detail page"""
    from shop.models import Mate, Category, Breed
    from django.shortcuts import get_object_or_404
    
    mate = get_object_or_404(
        Mate.objects.filter(is_approved=True)
        .select_related('shop', 'shop__seller', 'breed')
        .prefetch_related('images', 'videos', 'mate_reviews__user')
        .annotate(
            avg_rating=Avg('mate_reviews__rating'),
            review_count=Count('mate_reviews')
        ),
        id=mate_id
    )
    
    images = mate.images.all()
    videos = mate.videos.all()
    reviews = mate.mate_reviews.filter(is_approved=True)
    
    context = {
        'mate': mate,
        'images': images,
        'videos': videos,
        'reviews': reviews,
    }
    
    return render(request, 'shop/mate_detail.html', context)


def about_view(request):
    """About Us page highlighting trust and approval process"""
    from shop.models import SellerShop, Product, Mate

    context = {
        'stats': {
            'approved_shops': SellerShop.objects.filter(is_approved=True).count(),
            'approved_products': Product.objects.filter(is_approved=True).count(),
            'approved_mates': Mate.objects.filter(is_approved=True).count(),
        }
    }
    return render(request, 'shop/about.html', context)


def contact_view(request):
    """Contact Us page with simple acknowledgement form"""
    default_form = {
        'name': '',
        'email': '',
        'phone': '',
        'subject': '',
        'message': '',
    }

    form_data = default_form.copy()

    if request.method == 'POST':
        form_data = {
            'name': request.POST.get('name', '').strip(),
            'email': request.POST.get('email', '').strip(),
            'phone': request.POST.get('phone', '').strip(),
            'subject': request.POST.get('subject', '').strip(),
            'message': request.POST.get('message', '').strip(),
        }

        missing_fields = [field for field in ['name', 'email', 'message'] if not form_data[field]]
        if missing_fields:
            messages.error(request, 'Please fill in your name, email, and message so we can get back to you.')
        else:
            messages.success(request, 'Thank you for reaching out! Our support team will contact you shortly.')
            form_data = default_form.copy()

    context = {
        'form_data': form_data,
        'support_channels': {
            'phone': '+880 1819-777288',
            'email': 'support@mewzone.com',
            'hours': 'Monday - Friday, 9:00 AM to 6:00 PM (GMT+6)',
            'address': '123 Cat Street, Meow City, MC 12345',
        }
    }
    return render(request, 'shop/contact.html', context)


def terms_view(request):
    """Terms & Policies page covering platform rules"""
    policy_sections = [
        {
            'title': 'Marketplace Integrity',
            'icon': 'fas fa-balance-scale',
            'points': [
                'MewZone acts as a trusted marketplace connecting verified sellers with cat lovers.',
                'All pricing, descriptions, and media must accurately represent the cat or service offered.',
                'We reserve the right to remove listings that violate community standards or legal requirements.'
            ]
        },
        {
            'title': 'Privacy & Data Protection',
            'icon': 'fas fa-user-shield',
            'points': [
                'Personal data is collected strictly for account management, order processing, and support.',
                'We never sell personal information. Third parties only receive data essential to your transaction.',
                'Users may request data export or deletion by contacting support@mewzone.com.'
            ]
        }
    ]

    sell_policy = [
        'Only verified seller accounts may list cats, products, or mate services.',
        'Each listing requires up-to-date health records and proof of ownership for admin approval.',
        'Refund and replacement terms must be clearly stated; disputes will be mediated by MewZone admins.',
        'Sellers must respond to buyer inquiries within 24 hours on business days.'
    ]

    mate_policy = [
        'Mate listings are limited to healthy, vet-cleared cats aged 18 months or older.',
        'A maximum of five images and one video per mate profile to ensure clarity and review efficiency.',
        'All meetings for mate services should occur in safe, mutually agreed locations with proper supervision.',
        'Post-mating veterinary checkups are strongly encouraged and may be requested by MewZone for compliance.'
    ]

    context = {
        'policy_sections': policy_sections,
        'sell_policy': sell_policy,
        'mate_policy': mate_policy,
        'last_updated': timezone.now().strftime('%B %d, %Y')
    }
    return render(request, 'shop/terms.html', context)
