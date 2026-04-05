from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, AssistantVerification

User = get_user_model()

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # Create profile and initialize wallet
        Profile.objects.create(user=instance)
        # Generate referral code FAGI + up to 4 random digits
        import random
        base = 'FAGI'
        for _ in range(5):
            code = base + str(random.randint(0, 9999)).zfill(random.randint(1,4))
            if not User.objects.filter(referral_code=code).exists():
                instance.referral_code = code
                instance.save(update_fields=['referral_code'])
                break

@receiver(post_save, sender=AssistantVerification)
def update_verification_status(sender, instance, **kwargs):
    user = instance.user
    if instance.status == 'verified' and not user.is_verified:
        user.is_verified = True
        user.save()
    elif instance.status != 'verified' and user.is_verified:
        user.is_verified = False
        user.save()