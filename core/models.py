from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.conf import settings
from django.db import models

# Custom User Manager
class CustomUserManager(BaseUserManager):
    def create_user(self, email, phone, full_name, password=None, **extra_fields):
        if not email and not phone:
            raise ValueError("Email or phone is required")
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, phone, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_seller', True)
        return self.create_user(email, phone, full_name, password, **extra_fields)

# Custom User Model
class CustomUser(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_seller = models.BooleanField(null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'full_name']

    def __str__(self):
        return self.full_name

# Seller Profile Model
class SellerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profilePhoto = models.ImageField(upload_to='seller_profile_photo/photos/', blank=True, null=True)
    expertise = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=255, blank=True)
    experience = models.PositiveIntegerField(default=0)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"SellerProfile - {self.user.full_name}"

# Buyer Profile Model
class BuyerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    interests = models.TextField(blank=True)
    enrolled_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"BuyerProfile - {self.user.full_name}"

# Study Material Model
class StudyMaterial(models.Model):
    seller = models.ForeignKey('SellerProfile', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='study_materials/zips/')
    banner = models.ImageField(upload_to='study_materials/banners/', blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-uploaded_at']

# Purchase Model
class Purchase(models.Model):
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    material = models.ForeignKey(StudyMaterial, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)
    included_in_payout = models.BooleanField(default=False)  # True after admin payout to seller

    def __str__(self):
        return f"{self.buyer.full_name} bought {self.material.title}"

# Seller Payout Model
class SellerPayout(models.Model):
    seller = models.ForeignKey(SellerProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    from_date = models.DateTimeField()
    to_date = models.DateTimeField()
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payout ₹{self.amount} to {self.seller.user.full_name} from {self.from_date} to {self.to_date}"

# Support Ticket Model
class SupportTicket(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Support - {self.subject} by {self.user.full_name}"
