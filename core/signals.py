from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser, SellerProfile, BuyerProfile

@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if instance.is_seller is True:
        if not hasattr(instance, 'sellerprofile'):
            SellerProfile.objects.get_or_create(user=instance)
        BuyerProfile.objects.filter(user=instance).delete()

    elif instance.is_seller is False:
        if not hasattr(instance, 'buyerprofile'):
            BuyerProfile.objects.get_or_create(user=instance)
        SellerProfile.objects.filter(user=instance).delete()

    # If is_seller is None: do nothing    
