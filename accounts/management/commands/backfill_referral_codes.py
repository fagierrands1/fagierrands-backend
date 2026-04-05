from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Q
import random


User = get_user_model()


def generate_unique_referral_code() -> str:
    """
    Generate a unique referral code consistent with existing signal logic:
    - Prefix 'FAGI'
    - Followed by 1 to 4 digits (left-padded with zeros to random length 1..4)
    - Ensure uniqueness on the User model
    """
    base = 'FAGI'
    # Try a reasonable number of times to avoid an infinite loop in pathological cases
    for _ in range(20):
        number = random.randint(0, 9999)
        pad_len = random.randint(1, 4)
        code = base + str(number).zfill(pad_len)
        if not User.objects.filter(referral_code=code).exists():
            return code
    # As a final fallback, force a 4-digit pad with another random number
    return base + str(random.randint(0, 9999)).zfill(4)


class Command(BaseCommand):
    help = 'Backfill referral_code for existing users where it is null/blank.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run', action='store_true', help='Show what would change without saving.'
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)

        # Users missing referral_code (NULL or empty string)
        users_qs = User.objects.filter(Q(referral_code__isnull=True) | Q(referral_code__exact=''))
        total = users_qs.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS('No users found with missing referral_code.'))
            return

        self.stdout.write(f'Found {total} user(s) missing referral_code. Generating codes...')

        updated = 0
        for user in users_qs.iterator():
            new_code = generate_unique_referral_code()
            if dry_run:
                self.stdout.write(f'[DRY-RUN] Would set referral_code for user id={user.id}, email={user.email} -> {new_code}')
            else:
                user.referral_code = new_code
                user.save(update_fields=['referral_code'])
                updated += 1
                self.stdout.write(f'Set referral_code for user id={user.id}, email={user.email} -> {new_code}')

        if dry_run:
            self.stdout.write(self.style.WARNING(f'[DRY-RUN] Completed. {total} user(s) would be updated.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Completed. Updated {updated} user(s).'))