# Django Migration Fix: 0024_remove_banking_transfer_fields

## Problem
Migration `0024_remove_banking_transfer_fields` was failing with:
```
django.db.utils.ProgrammingError: column "recipient_name" of relation "orders_bankingorder" does not exist
```

This occurred because the migration was attempting to remove database columns that either:
- Were already removed in previous migrations
- Were never created in the production database
- Had a migration history mismatch

## Solution
The migration has been updated to safely handle this scenario using a `RunPython` operation that:
1. Checks if each column exists in the database
2. Only removes the column if it exists
3. Gracefully skips the removal if the column doesn't exist
4. Handles both PostgreSQL and other database systems

## Files Changed
- `orders/migrations/0024_remove_banking_transfer_fields.py` - Updated to use safe removal logic

## How to Apply the Fix

### On Production Server (fagiserver.fagtone.com)

1. **Pull the latest changes:**
   ```bash
   cd /home3/distinc3/fagiserver.fagtone.com/fagierrandsbackup
   git pull origin main  # or your branch name
   ```

2. **Activate the virtual environment:**
   ```bash
   source /home3/distinc3/virtualenv/fagiserver.fagtone.com/3.13/bin/activate
   ```

3. **Run the updated migration:**
   ```bash
   python manage.py migrate orders 0024
   ```

   Expected output:
   ```
   Operations to perform:
     Target specific migration: 0024_remove_banking_transfer_fields, from orders
   Running migrations:
     Applying orders.0024_remove_banking_transfer_fields...
   ✓ Column 'recipient_name' does not exist (skipped)
   ✓ Column 'recipient_account' does not exist (skipped)
   OK
   ```

4. **Continue with remaining migrations (if any):**
   ```bash
   python manage.py migrate
   ```

### Verifying the Fix

After the migration completes, verify it succeeded:
```bash
python manage.py showmigrations orders | grep 0024
```

You should see:
```
[X] 0024_remove_banking_transfer_fields
```

## Why This Happened

This is a common issue in Django projects with complex migration histories, especially when:
- Multiple developers create migrations independently
- Migrations are cherry-picked or rebased
- Database schema is manually modified outside migrations
- Environment synchronization issues

The fix ensures robust migrations that can handle real-world database state inconsistencies.

## Additional Notes

- The migration preserves all data in the BankingOrder table
- No data loss occurs
- The migration is reversible (though rollback just marks it as unapplied in Django)
- All subsequent migrations should now apply cleanly

## Troubleshooting

If you still encounter issues:

1. **Check migration history:**
   ```bash
   python manage.py showmigrations orders
   ```

2. **View migration operations:**
   ```bash
   python manage.py sqlmigrate orders 0024
   ```

3. **Contact**: Reach out to the development team if issues persist

---
**Last Updated**: 2025-10-18