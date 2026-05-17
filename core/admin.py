from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, SellerProfile, BuyerProfile,
    StudyMaterial, Purchase, SellerPayout, SupportTicket
)

# ----------------------------
# Custom User Admin
# ----------------------------
class CustomUserAdmin(BaseUserAdmin):
    model = CustomUser
    list_display = ('email', 'phone', 'full_name', 'is_seller', 'is_staff')
    list_filter = ('is_seller', 'is_staff', 'is_superuser')
    
    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        ('Personal info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_seller', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'full_name', 'password1', 'password2', 'is_seller')}
        ),
    )
    
    search_fields = ('email', 'phone', 'full_name')
    ordering = ('email',)

# ----------------------------
# Purchase Admin
# ----------------------------
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('buyer', 'material', 'is_paid', 'razorpay_payment_id', 'created_at', 'included_in_payout')
    list_filter = ('is_paid', 'included_in_payout', 'created_at')
    search_fields = ('buyer__full_name', 'material__title', 'razorpay_order_id', 'razorpay_payment_id')

# ----------------------------
# Seller Payout Admin
# ----------------------------
@admin.register(SellerPayout)
class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ('seller', 'amount', 'from_date', 'to_date', 'paid_at')
    search_fields = ('seller__user__full_name',)

# ----------------------------
# Register Other Models
# ----------------------------
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(SellerProfile)
admin.site.register(BuyerProfile)
admin.site.register(StudyMaterial)
admin.site.register(SupportTicket)
