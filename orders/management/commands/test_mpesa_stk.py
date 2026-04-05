from django.core.management.base import BaseCommand, CommandError
from orders.mpesa_service import MpesaDarajaService
import json


class Command(BaseCommand):
    help = 'Test M-Pesa STK Push flow (dry-run by default).'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, required=True, help='Phone number (07XXXXXXXX or 2547XXXXXXXX)')
        parser.add_argument('--amount', type=float, default=1.0, help='Amount to charge')
        parser.add_argument('--order', type=int, default=0, help='Order id to include in AccountReference')
        parser.add_argument('--live', action='store_true', help='Perform a live STK push (production/sandbox will still be used based on settings)')
        parser.add_argument('--callback', type=str, default=None, help='Optional callback URL override')

    def handle(self, *args, **options):
        phone = options['phone']
        amount = options['amount']
        order_id = options['order']
        live = options['live']
        callback = options['callback']

        svc = MpesaDarajaService()

        # Display key config (non-secret)
        self.stdout.write('Environment: %s' % svc.environment)
        self.stdout.write('Shortcode: %s' % svc.shortcode)
        self.stdout.write('STK Callback URL (default): %s' % svc.stk_callback_url)

        formatted = svc.format_phone_number(phone)
        valid = svc.validate_phone_number(formatted)
        self.stdout.write('Formatted phone: %s' % formatted)
        self.stdout.write('Phone valid: %s' % valid)

        if not valid:
            raise CommandError('Phone number validation failed - ensure it is a Safaricom MSISDN (07... or +2547...)')

        # Generate the payload values
        account_ref = f'Order-{order_id}' if order_id else 'Manual-Test'
        description = f'Test STK push for {account_ref}'

        if not live:
            self.stdout.write(self.style.WARNING('Dry run - not sending live STK push. Use --live to actually send.'))
            # Do a dry-run: validate access token and show the payload, but don't call
            try:
                token = svc.get_access_token()
                self.stdout.write(self.style.SUCCESS('Obtained access token (hidden for security).'))
            except Exception as e:
                raise CommandError(f'Failed to obtain access token: {e}')

            # Show sample payload (without making a network call)
            sample_payload = {
                'BusinessShortCode': svc.shortcode,
                'Password': 'GENERATED_AT_RUNTIME',
                'Timestamp': 'GENERATED_AT_RUNTIME',
                'TransactionType': 'CustomerPayBillOnline',
                'Amount': int(amount),
                'PartyA': formatted,
                'PartyB': svc.shortcode,
                'PhoneNumber': formatted,
                'CallBackURL': callback or svc.stk_callback_url,
                'AccountReference': account_ref,
                'TransactionDesc': description,
            }

            self.stdout.write('Prepared STK Push payload (preview):')
            self.stdout.write(json.dumps(sample_payload, indent=2))
            return

        # Live path - perform the STK push
        try:
            self.stdout.write(self.style.WARNING('Sending live STK push...'))
            result = svc.stk_push(
                phone_number=formatted,
                amount=amount,
                account_reference=account_ref,
                transaction_desc=description,
                callback_url=callback,
            )
            self.stdout.write('Result:')
            self.stdout.write(json.dumps(result, indent=2))
        except Exception as e:
            raise CommandError(f'Live STK push failed: {e}')
