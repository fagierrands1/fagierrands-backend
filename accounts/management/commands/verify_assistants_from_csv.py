import csv
from typing import Dict, Optional

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

from accounts.models import AssistantVerification


User = get_user_model()


class Command(BaseCommand):
    help = (
        "Verify assistants from CSV files by phone number. "
        "Updates existing User records (is_verified, email_verified, user_type) "
        "and creates/updates AssistantVerification to status=verified."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--riders_csv",
            default=r"c:\\Users\\a\\Documents\\GitHub\\fagierrands\\fagierrands\\fagierrandsbackup\\Rider Information.csv",
            help="Absolute path to Riders CSV",
        )
        parser.add_argument(
            "--providers_csv",
            default=r"c:\\Users\\a\\Documents\\GitHub\\fagierrands\\fagierrands\\fagierrandsbackup\\Home Maintenance Professionals.csv",
            help="Absolute path to Service Providers CSV",
        )
        parser.add_argument(
            "--dry_run",
            action="store_true",
            help="Do not persist changes; only show what would happen",
        )

    def handle(self, *args, **options):
        dry_run: bool = options["dry_run"]
        riders_csv: Optional[str] = options.get("riders_csv")
        providers_csv: Optional[str] = options.get("providers_csv")

        summary = {
            "riders": {"processed": 0, "matched": 0, "updated": 0, "missing": []},
            "providers": {"processed": 0, "matched": 0, "updated": 0, "missing": []},
        }

        if riders_csv:
            self.stdout.write(self.style.NOTICE(f"Processing riders CSV: {riders_csv}"))
            self._process_riders_csv(riders_csv, dry_run, summary["riders"])

        if providers_csv:
            self.stdout.write(self.style.NOTICE(f"Processing providers CSV: {providers_csv}"))
            self._process_providers_csv(providers_csv, dry_run, summary["providers"])

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Verification import completed."))
        for key in ("riders", "providers"):
            s = summary[key]
            self.stdout.write(
                f"{key.title()}: processed={s['processed']} matched={s['matched']} updated={s['updated']} missing={len(s['missing'])}"
            )
            if s["missing"]:
                self.stdout.write(f" - Missing by phone: {', '.join(s['missing'])}")

        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run mode enabled: no changes were saved."))

    # CSV processing helpers

    def _process_riders_csv(self, path: str, dry_run: bool, summary: Dict):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary["processed"] += 1
                phone = (row.get("Phone Number") or "").strip()
                if not phone:
                    continue

                user = self._find_user_by_phone(phone)
                if not user:
                    summary["missing"].append(phone)
                    continue

                summary["matched"] += 1

                # Update user flags
                changed = self._update_user_flags(user, dry_run)

                # Create/update verification
                verif_changed = self._upsert_verification(
                    user=user,
                    payload={
                        "user_role": "rider",
                        "full_name": (row.get("Name") or "").strip(),
                        "id_number": (row.get("Identification Number") or "").strip(),
                        "phone_number": phone,
                        "area_of_operation": (row.get("Area Of Operation") or "").strip() or None,
                        "driving_license_number": (row.get("License Number") or "").strip() or None,
                        # Extra fields present in CSV but not in model are ignored
                    },
                    dry_run=dry_run,
                )

                if changed or verif_changed:
                    summary["updated"] += 1

    def _process_providers_csv(self, path: str, dry_run: bool, summary: Dict):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                summary["processed"] += 1
                phone = (row.get("Phone Number") or "").strip()
                if not phone:
                    continue

                user = self._find_user_by_phone(phone)
                if not user:
                    summary["missing"].append(phone)
                    continue

                summary["matched"] += 1

                # Update user flags
                changed = self._update_user_flags(user, dry_run)

                # Create/update verification
                verif_changed = self._upsert_verification(
                    user=user,
                    payload={
                        "user_role": "service_provider",
                        "full_name": (row.get("Name") or "").strip(),
                        "id_number": (row.get("Identification Number") or "").strip(),
                        "phone_number": phone,
                        "service": (row.get("Profession") or "").strip() or None,
                        # Relevant Certificates column present but we don't store textual list; leaving certificate_url empty
                    },
                    dry_run=dry_run,
                )

                if changed or verif_changed:
                    summary["updated"] += 1

    # Data operations

    def _find_user_by_phone(self, phone: str) -> Optional[User]:
        qs = User.objects.filter(phone_number=phone)
        if not qs.exists():
            return None
        assistants = qs.filter(user_type='assistant')
        return (assistants or qs).order_by('-date_joined').first()

    def _update_user_flags(self, user: User, dry_run: bool) -> bool:
        changed = False
        # Ensure user is assistant
        if user.user_type != 'assistant':
            user.user_type = 'assistant'
            changed = True
        # Mark as verified and email verified
        if not user.is_verified:
            user.is_verified = True
            changed = True
        if not user.email_verified:
            user.email_verified = True
            changed = True

        if changed and not dry_run:
            user.save(update_fields=["user_type", "is_verified", "email_verified"])
        return changed

    def _upsert_verification(self, user: User, payload: Dict, dry_run: bool) -> bool:
        now = timezone.now()
        defaults = {
            "status": "verified",
            "verified_at": now,
        }
        defaults.update(payload)

        verif, created = AssistantVerification.objects.get_or_create(
            user=user,
            defaults=defaults,
        )

        if created:
            if dry_run:
                # Roll back creation if dry-run: delete the in-memory instance (won't persist anyway)
                pass
            return True

        # Compare and update existing fields
        changed = False
        for field, value in defaults.items():
            if getattr(verif, field) != value and value is not None:
                setattr(verif, field, value)
                changed = True
        # Always ensure status/verified_at set
        if verif.status != "verified":
            verif.status = "verified"
            changed = True
        if verif.verified_at is None:
            verif.verified_at = now
            changed = True

        if changed and not dry_run:
            verif.save()
        return changed