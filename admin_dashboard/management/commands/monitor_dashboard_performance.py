"""
Management command to monitor dashboard API performance and identify bottlenecks.
"""
import time
import logging
from django.core.management.base import BaseCommand
from django.db import connection
from django.test import Client
from django.urls import reverse
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Monitor dashboard API performance and identify bottlenecks'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--iterations',
            type=int,
            default=5,
            help='Number of test iterations to run'
        )
        parser.add_argument(
            '--threshold',
            type=float,
            default=1.0,
            help='Threshold in seconds to flag slow endpoints'
        )
    
    def handle(self, *args, **options):
        iterations = options['iterations']
        threshold = options['threshold']
        
        # Get admin user for authenticated requests
        User = get_user_model()
        try:
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                self.stdout.write(self.style.ERROR('No admin user found. Creating one...'))
                admin_user = User.objects.create_superuser(
                    username='admin',
                    email='admin@example.com',
                    password='adminpassword'
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error getting admin user: {e}'))
            return
        
        # Create test client
        client = Client()
        client.force_login(admin_user)
        
        # Dashboard endpoints to test
        endpoints = [
            ('Dashboard Overview', reverse('dashboard-overview')),
            ('Revenue Time Series', reverse('dashboard-time-series') + '?metric=total_revenue&days=30'),
            ('User Time Series', reverse('dashboard-time-series') + '?metric=total_users&days=30'),
            ('Service Comparison', reverse('dashboard-service-comparison') + '?days=30'),
            ('Rating Distribution', reverse('dashboard-rating-distribution') + '?days=30'),
        ]
        
        self.stdout.write(self.style.SUCCESS(f'Starting dashboard performance test with {iterations} iterations'))
        self.stdout.write('=' * 80)
        
        # Test each endpoint
        results = {}
        for name, url in endpoints:
            self.stdout.write(f'Testing endpoint: {name} ({url})')
            
            # Run multiple iterations
            times = []
            query_counts = []
            
            for i in range(iterations):
                # Reset query log
                connection.queries_log.clear()
                connection.force_debug_cursor = True
                
                # Time the request
                start_time = time.time()
                response = client.get(url)
                end_time = time.time()
                
                # Record metrics
                request_time = end_time - start_time
                query_count = len(connection.queries)
                
                times.append(request_time)
                query_counts.append(query_count)
                
                # Log iteration results
                status = response.status_code
                self.stdout.write(f'  Iteration {i+1}: {request_time:.2f}s, {query_count} queries, Status: {status}')
                
                # Small delay between requests
                time.sleep(0.5)
            
            # Calculate averages
            avg_time = sum(times) / len(times)
            avg_queries = sum(query_counts) / len(query_counts)
            max_time = max(times)
            
            # Store results
            results[name] = {
                'avg_time': avg_time,
                'max_time': max_time,
                'avg_queries': avg_queries,
                'is_slow': avg_time > threshold
            }
            
            # Log summary for this endpoint
            status = self.style.ERROR('SLOW') if avg_time > threshold else self.style.SUCCESS('OK')
            self.stdout.write(f'  Summary: Avg {avg_time:.2f}s, Max {max_time:.2f}s, Avg {avg_queries:.0f} queries - {status}')
            self.stdout.write('-' * 80)
        
        # Overall summary
        self.stdout.write('=' * 80)
        self.stdout.write(self.style.SUCCESS('Performance Test Summary:'))
        
        slow_endpoints = [name for name, data in results.items() if data['is_slow']]
        if slow_endpoints:
            self.stdout.write(self.style.ERROR(f'Found {len(slow_endpoints)} slow endpoints:'))
            for name in slow_endpoints:
                data = results[name]
                self.stdout.write(f'  - {name}: {data["avg_time"]:.2f}s avg, {data["avg_queries"]:.0f} queries')
                
            self.stdout.write('\nRecommendations:')
            self.stdout.write('1. Add caching for these endpoints')
            self.stdout.write('2. Optimize database queries using select_related/prefetch_related')
            self.stdout.write('3. Consider paginating large result sets')
            self.stdout.write('4. Add database indexes for frequently queried fields')
        else:
            self.stdout.write(self.style.SUCCESS('All endpoints are performing within acceptable limits'))
        
        # Disable debug cursor
        connection.force_debug_cursor = False