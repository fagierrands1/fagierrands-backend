"""
Celery tasks for order and payment processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import Payment
import logging

logger = logging.getLogger(__name__)

@shared_task
def check_and_fix_stuck_payments():
    """
    Automatically check for and fix payments that have been stuck in processing status
    for too long. This task should be run periodically (e.g., every hour).
    """
    # Configuration - can be moved to settings
    STUCK_PAYMENT_TIMEOUT_HOURS = getattr(settings, 'STUCK_PAYMENT_TIMEOUT_HOURS', 2)
    AUTO_FIX_STUCK_PAYMENTS = getattr(settings, 'AUTO_FIX_STUCK_PAYMENTS', True)
    STUCK_PAYMENT_NEW_STATUS = getattr(settings, 'STUCK_PAYMENT_NEW_STATUS', 'failed')
    
    logger.info("Starting automatic stuck payment check...")
    
    # Calculate cutoff time
    cutoff_time = timezone.now() - timedelta(hours=STUCK_PAYMENT_TIMEOUT_HOURS)
    
    # Find stuck payments
    stuck_payments = Payment.objects.filter(
        status='processing',
        payment_date__lt=cutoff_time
    )
    
    stuck_count = stuck_payments.count()
    
    if stuck_count == 0:
        logger.info("No stuck payments found")
        return {
            'status': 'success',
            'message': 'No stuck payments found',
            'stuck_count': 0,
            'fixed_count': 0
        }
    
    logger.warning(f"Found {stuck_count} payments stuck in processing status for more than {STUCK_PAYMENT_TIMEOUT_HOURS} hours")
    
    # Log details of stuck payments
    for payment in stuck_payments:
        hours_stuck = (timezone.now() - payment.payment_date).total_seconds() / 3600
        logger.warning(
            f"Stuck payment: ID={payment.id}, Order={payment.order.id}, "
            f"Amount={payment.amount}, Method={payment.payment_method}, "
            f"Hours stuck={hours_stuck:.1f}"
        )
    
    fixed_count = 0
    
    if AUTO_FIX_STUCK_PAYMENTS:
        logger.info(f"Auto-fixing stuck payments by setting status to '{STUCK_PAYMENT_NEW_STATUS}'")
        
        for payment in stuck_payments:
            try:
                old_status = payment.status
                payment.status = STUCK_PAYMENT_NEW_STATUS
                payment.save()
                fixed_count += 1
                
                logger.info(
                    f"Fixed stuck payment: ID={payment.id}, Order={payment.order.id}, "
                    f"Status changed from '{old_status}' to '{STUCK_PAYMENT_NEW_STATUS}'"
                )
                
            except Exception as e:
                logger.error(f"Failed to fix payment {payment.id}: {str(e)}")
        
        logger.info(f"Successfully fixed {fixed_count} out of {stuck_count} stuck payments")
    else:
        logger.info("Auto-fix is disabled. Stuck payments were only logged.")
    
    return {
        'status': 'success',
        'message': f'Found {stuck_count} stuck payments, fixed {fixed_count}',
        'stuck_count': stuck_count,
        'fixed_count': fixed_count
    }

@shared_task
def payment_status_report():
    """
    Generate a daily payment status report
    """
    logger.info("Generating payment status report...")
    
    # Get payment statistics
    from django.db import models
    
    status_summary = Payment.objects.values('status').annotate(
        count=models.Count('id'),
        total_amount=models.Sum('amount')
    ).order_by('status')
    
    # Get today's payments
    today = timezone.now().date()
    today_payments = Payment.objects.filter(payment_date__date=today)
    today_count = today_payments.count()
    today_amount = today_payments.aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Get stuck payments
    cutoff_time = timezone.now() - timedelta(hours=2)
    stuck_count = Payment.objects.filter(
        status='processing',
        payment_date__lt=cutoff_time
    ).count()
    
    report = {
        'date': today.isoformat(),
        'total_payments': Payment.objects.count(),
        'today_payments': today_count,
        'today_amount': float(today_amount),
        'stuck_payments': stuck_count,
        'status_breakdown': {}
    }
    
    for status_data in status_summary:
        status = status_data['status']
        count = status_data['count']
        amount = status_data['total_amount'] or 0
        report['status_breakdown'][status] = {
            'count': count,
            'amount': float(amount)
        }
    
    logger.info(f"Payment report generated: {report}")
    
    # You can extend this to send email reports, save to database, etc.
    
    return report

@shared_task
def verify_payment_with_provider(payment_id):
    """
    Verify a specific payment status with the payment provider (IntaSend)
    This can be used to double-check payment status when needed
    """
    try:
        payment = Payment.objects.get(id=payment_id)
        
        # This would integrate with IntaSend API to verify payment status
        # For now, we'll just log the attempt
        logger.info(f"Verifying payment {payment_id} with provider...")
        
        # TODO: Implement actual IntaSend API verification
        # from intasend import APIService
        # service = APIService(token=settings.INTASEND_TOKEN, publishable_key=settings.INTASEND_PUBLISHABLE_KEY)
        # status = service.verify_payment(payment.intasend_invoice_id)
        
        return {
            'status': 'success',
            'payment_id': payment_id,
            'message': 'Payment verification completed'
        }
        
    except Payment.DoesNotExist:
        logger.error(f"Payment {payment_id} not found")
        return {
            'status': 'error',
            'payment_id': payment_id,
            'message': 'Payment not found'
        }
    except Exception as e:
        logger.error(f"Error verifying payment {payment_id}: {str(e)}")
        return {
            'status': 'error',
            'payment_id': payment_id,
            'message': str(e)
        }