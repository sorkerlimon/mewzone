from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    Category, Breed, SellerShop, Product, ProductImage, ProductVideo,
    ProductReview, ShopReview, ProductCategory, AdminApprovalLog,
    Mate, MateImage, MateVideo, MateReview
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin configuration"""
    
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Breed)
class BreedAdmin(admin.ModelAdmin):
    """Breed admin configuration"""
    
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'categories')
    search_fields = ('name',)
    filter_horizontal = ('categories',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name',)
        }),
        ('Categories', {
            'fields': ('categories',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class ProductImageInline(admin.TabularInline):
    """Inline admin for Product Images"""
    model = ProductImage
    extra = 0
    max_num = 3
    fields = ('image', 'alt_text', 'is_primary')


class ProductVideoInline(admin.TabularInline):
    """Inline admin for Product Videos"""
    model = ProductVideo
    extra = 0
    max_num = 2
    fields = ('video', 'thumbnail', 'duration', 'file_size')


class ProductCategoryInline(admin.TabularInline):
    """Inline admin for Product Categories"""
    model = ProductCategory
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product admin configuration"""
    
    list_display = ('name', 'breed', 'gender', 'price', 'discounted_price', 'shop', 'is_approved', 'created_at')
    list_filter = ('breed', 'gender', 'fur_type', 'is_approved', 'ready_to_go', 'available_for_pickup', 'available_for_delivery', 'created_at')
    search_fields = ('name', 'breed', 'description', 'shop__shop_name', 'shop__seller__email')
    readonly_fields = ('created_at', 'updated_at', 'discounted_price', 'product_rating')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('shop', 'name', 'breed', 'description')
        }),
        ('Cat Details', {
            'fields': ('gender', 'color', 'eye_color', 'fur_type', 'date_of_birth')
        }),
        ('Location & Availability', {
            'fields': ('location', 'ready_to_go', 'available_for_pickup', 'available_for_delivery')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_percentage', 'discounted_price')
        }),
        ('Additional Info', {
            'fields': ('additional_notes', 'other_services')
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_at', 'rejected_at', 'rejection_reason')
        }),
        ('Stats', {
            'fields': ('product_rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, ProductVideoInline, ProductCategoryInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop', 'shop__seller')


@admin.register(SellerShop)
class SellerShopAdmin(admin.ModelAdmin):
    """Seller Shop admin configuration"""
    
    list_display = ('shop_name', 'seller_email', 'location', 'is_approved', 'shop_rating', 'created_at')
    list_filter = ('is_approved', 'city', 'state', 'country', 'created_at')
    search_fields = ('shop_name', 'seller__email', 'location', 'city', 'state')
    readonly_fields = ('created_at', 'updated_at', 'shop_rating', 'approved_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Shop Info', {
            'fields': ('seller', 'shop_name', 'description', 'profile_picture')
        }),
        ('Location', {
            'fields': ('location', 'address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Social Media', {
            'fields': ('facebook_page', 'instagram_handle', 'twitter_handle', 'other_social_links')
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_at')
        }),
        ('Stats', {
            'fields': ('shop_rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def seller_email(self, obj):
        return obj.seller.email
    seller_email.short_description = 'Seller Email'
    seller_email.admin_order_field = 'seller__email'


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """Product Image admin configuration"""
    
    list_display = ('product', 'image_preview', 'alt_text', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(ProductVideo)
class ProductVideoAdmin(admin.ModelAdmin):
    """Product Video admin configuration"""
    
    list_display = ('product', 'video', 'duration', 'file_size_mb', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('product__name',)
    readonly_fields = ('uploaded_at', 'file_size')
    ordering = ('-uploaded_at',)
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "Unknown"
    file_size_mb.short_description = 'File Size (MB)'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Product Review admin configuration"""
    
    list_display = ('product', 'user_email', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(ShopReview)
class ShopReviewAdmin(admin.ModelAdmin):
    """Shop Review admin configuration"""
    
    list_display = ('shop', 'user_email', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('shop__shop_name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """Product Category admin configuration"""
    
    list_display = ('product', 'category')
    list_filter = ('category',)
    search_fields = ('product__name', 'category__name')
    ordering = ('product', 'category')


@admin.register(AdminApprovalLog)
class AdminApprovalLogAdmin(admin.ModelAdmin):
    """Admin Approval Log admin configuration"""
    
    list_display = ('content_object', 'action', 'admin_user', 'created_at')
    list_filter = ('action', 'created_at', 'content_type')
    search_fields = ('admin_user__email', 'reason')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin_user', 'content_type')


class MateImageInline(admin.TabularInline):
    """Inline admin for Mate Images"""
    model = MateImage
    extra = 0
    max_num = 5
    fields = ('image', 'alt_text', 'is_primary')


class MateVideoInline(admin.TabularInline):
    """Inline admin for Mate Videos"""
    model = MateVideo
    extra = 0
    max_num = 1
    fields = ('video',)


@admin.register(Mate)
class MateAdmin(admin.ModelAdmin):
    """Mate admin configuration"""
    
    list_display = ('name', 'breed', 'gender', 'mate_cost', 'shop', 'is_approved', 'created_at')
    list_filter = ('breed', 'gender', 'is_approved', 'created_at')
    search_fields = ('name', 'breed__name', 'description', 'shop__shop_name', 'shop__seller__email')
    readonly_fields = ('created_at', 'updated_at', 'mate_rating')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('shop', 'name', 'breed', 'description')
        }),
        ('Mate Details', {
            'fields': ('gender', 'color', 'age')
        }),
        ('Pricing', {
            'fields': ('mate_cost',)
        }),
        ('Approval', {
            'fields': ('is_approved', 'approved_at', 'rejected_at', 'rejection_reason')
        }),
        ('Stats', {
            'fields': ('mate_rating', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [MateImageInline, MateVideoInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('shop', 'shop__seller', 'breed')
    
    def save_model(self, request, obj, form, change):
        """Override save to set approved_at when approved"""
        if obj.is_approved and not obj.approved_at:
            obj.approved_at = timezone.now()
        elif not obj.is_approved and obj.approved_at:
            obj.approved_at = None
        super().save_model(request, obj, form, change)


@admin.register(MateImage)
class MateImageAdmin(admin.ModelAdmin):
    """Mate Image admin configuration"""
    
    list_display = ('mate', 'image_preview', 'alt_text', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('mate__name', 'alt_text')
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(MateVideo)
class MateVideoAdmin(admin.ModelAdmin):
    """Mate Video admin configuration"""
    
    list_display = ('mate', 'video', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('mate__name',)
    readonly_fields = ('uploaded_at',)
    ordering = ('-uploaded_at',)


@admin.register(MateReview)
class MateReviewAdmin(admin.ModelAdmin):
    """Mate Review admin configuration"""
    
    list_display = ('mate', 'user_email', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('mate__name', 'user__email', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'
