from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import User
from decimal import Decimal
import uuid
import os


class Category(models.Model):
    """Category model for cat breeds or product types"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name


class Breed(models.Model):
    """Breed model for specific cat breeds"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    categories = models.ManyToManyField(Category, related_name='breeds', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'breeds'
        verbose_name = 'Breed'
        verbose_name_plural = 'Breeds'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class SellerShop(models.Model):
    """Seller shop model for cat sellers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_shop')
    shop_name = models.CharField(max_length=200)
    description = models.TextField()
    profile_picture = models.ImageField(upload_to='shop_profiles/', blank=True, null=True)
    location = models.CharField(max_length=200)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    facebook_page = models.URLField(blank=True, null=True)
    instagram_handle = models.CharField(max_length=100, blank=True, null=True)
    twitter_handle = models.CharField(max_length=100, blank=True, null=True)
    other_social_links = models.JSONField(default=dict, blank=True)
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seller_shops'
        verbose_name = 'Seller Shop'
        verbose_name_plural = 'Seller Shops'
    
    def __str__(self):
        return self.shop_name
    
    @property
    def shop_rating(self):
        """Calculate average shop rating"""
        reviews = self.shop_reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0


class Product(models.Model):
    """Product model for cats"""
    
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    FUR_TYPE_CHOICES = [
        ('SHORT', 'Short Hair'),
        ('LONG', 'Long Hair'),
        ('MEDIUM', 'Medium Hair'),
        ('CURLY', 'Curly Hair'),
        ('WIRE', 'Wire Hair'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(SellerShop, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE, related_name='products')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    color = models.CharField(max_length=100)
    eye_color = models.CharField(max_length=100)
    fur_type = models.CharField(max_length=20, choices=FUR_TYPE_CHOICES)
    date_of_birth = models.DateField()
    location = models.CharField(max_length=200)
    ready_to_go = models.BooleanField(default=False)
    available_for_pickup = models.BooleanField(default=True)
    available_for_delivery = models.BooleanField(default=False)
    additional_notes = models.TextField(blank=True, null=True)
    other_services = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_percentage = models.PositiveIntegerField(default=0, validators=[MaxValueValidator(100)])
    description = models.TextField()
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.breed.name}"
    
    @property
    def discounted_price(self):
        """Calculate discounted price"""
        if self.discount_percentage > 0:
            discount_factor = Decimal('1') - (Decimal(self.discount_percentage) / Decimal('100'))
            return (self.price * discount_factor)
        return self.price
    
    @property
    def product_rating(self):
        """Calculate average product rating"""
        reviews = self.product_reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0


class ProductImage(models.Model):
    """Product images model (max 3 per product)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='product_images/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
    
    def __str__(self):
        return f"Image for {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVideo(models.Model):
    """Product videos model (max 2 per product, max 100MB each)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(upload_to='product_videos/', validators=[])
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)
    file_size = models.PositiveIntegerField(blank=True, null=True)  # in bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_videos'
        verbose_name = 'Product Video'
        verbose_name_plural = 'Product Videos'
    
    def __str__(self):
        return f"Video for {self.product.name}"


class ProductReview(models.Model):
    """Product reviews and ratings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_reviews'
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        unique_together = ['product', 'user']  # One review per user per product
    
    def __str__(self):
        return f"Review for {self.product.name} by {self.user.email}"


class ShopReview(models.Model):
    """Shop reviews and ratings"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(SellerShop, on_delete=models.CASCADE, related_name='shop_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shop_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'shop_reviews'
        verbose_name = 'Shop Review'
        verbose_name_plural = 'Shop Reviews'
        unique_together = ['shop', 'user']  # One review per user per shop
    
    def __str__(self):
        return f"Review for {self.shop.shop_name} by {self.user.email}"


class ProductCategory(models.Model):
    """Many-to-many relationship between products and categories"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='product_categories')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='product_categories')
    
    class Meta:
        db_table = 'product_categories'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        unique_together = ['product', 'category']
    
    def __str__(self):
        return f"{self.product.name} - {self.category.name}"


class AdminApprovalLog(models.Model):
    """Track admin approval/rejection actions"""
    
    ACTION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='approval_actions')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'admin_approval_logs'
        verbose_name = 'Admin Approval Log'
        verbose_name_plural = 'Admin Approval Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.content_object} by {self.admin_user.email}"


def validate_video_file_size(value):
    """Validate video file size is max 100MB"""
    max_size = 100 * 1024 * 1024  # 100MB in bytes
    if value.size > max_size:
        raise ValidationError(f'Video file size cannot exceed 100MB. Current size: {value.size / (1024 * 1024):.2f}MB')


class Mate(models.Model):
    """Mate model for cat breeding/mating services (only sellers can create)"""
    
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shop = models.ForeignKey(SellerShop, on_delete=models.CASCADE, related_name='mates')
    name = models.CharField(max_length=200)
    breed = models.ForeignKey(Breed, on_delete=models.CASCADE, related_name='mates')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    color = models.CharField(max_length=100)
    age = models.PositiveIntegerField(help_text="Age in months")
    mate_cost = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)], help_text="Cost for mating service")
    description = models.TextField()
    is_approved = models.BooleanField(default=False)
    approved_at = models.DateTimeField(blank=True, null=True)
    rejected_at = models.DateTimeField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mates'
        verbose_name = 'Mate'
        verbose_name_plural = 'Mates'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.breed.name} ({self.gender})"
    
    @property
    def mate_rating(self):
        """Calculate average mate rating"""
        reviews = self.mate_reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(models.Avg('rating'))['rating__avg'], 1)
        return 0.0


class MateImage(models.Model):
    """Mate images model (max 5 per mate)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mate = models.ForeignKey(Mate, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='mate_images/')
    alt_text = models.CharField(max_length=200, blank=True, null=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mate_images'
        verbose_name = 'Mate Image'
        verbose_name_plural = 'Mate Images'
    
    def __str__(self):
        return f"Image for {self.mate.name}"
    
    def save(self, *args, **kwargs):
        # Ensure only one primary image per mate
        if self.is_primary:
            MateImage.objects.filter(mate=self.mate, is_primary=True).update(is_primary=False)
        
        # Check image count limit (5 images max)
        if not self.pk:  # New image being added
            current_count = MateImage.objects.filter(mate=self.mate).count()
            if current_count >= 5:
                raise ValidationError('Maximum 5 images allowed per mate.')
        
        super().save(*args, **kwargs)


class MateVideo(models.Model):
    """Mate videos model (max 1 per mate, max 100MB)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mate = models.ForeignKey(Mate, on_delete=models.CASCADE, related_name='videos')
    video = models.FileField(
        upload_to='mate_videos/',
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'webm']), validate_video_file_size]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mate_videos'
        verbose_name = 'Mate Video'
        verbose_name_plural = 'Mate Videos'
    
    def __str__(self):
        return f"Video for {self.mate.name}"
    
    def save(self, *args, **kwargs):
        # Check video count limit (1 video max)
        if not self.pk:  # New video being added
            current_count = MateVideo.objects.filter(mate=self.mate).count()
            if current_count >= 1:
                raise ValidationError('Maximum 1 video allowed per mate.')
        
        super().save(*args, **kwargs)


class MateReview(models.Model):
    """Mate reviews and ratings (with approval system)"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mate = models.ForeignKey(Mate, on_delete=models.CASCADE, related_name='mate_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mate_reviews')
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'mate_reviews'
        verbose_name = 'Mate Review'
        verbose_name_plural = 'Mate Reviews'
        unique_together = ['mate', 'user']  # One review per user per mate
    
    def __str__(self):
        return f"Review for {self.mate.name} by {self.user.email}"
