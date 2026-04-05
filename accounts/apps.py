from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    
    def ready(self):
        import accounts.signals
        try:
            from .supabase_client import initialize_supabase_storage
            initialize_supabase_storage()
        except Exception as e:
            import logging
            logging.error(f"Failed to initialize Supabase storage: {e}")
