"""
Dashboard optimization utilities to improve performance of API endpoints.
"""
from django.core.cache import cache
from django.db import connection
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def cache_dashboard_response(timeout=300):
    """
    Decorator to cache dashboard API responses.
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            # Create a cache key based on the view name and request parameters
            cache_key = f"dashboard_{view_func.__name__}"
            
            # Add query parameters to the cache key
            # Handle both Django request and DRF request objects
            query_params = getattr(request, 'query_params', None) or request.GET
            if query_params:
                param_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
                cache_key += f"_{param_string}"
            
            # Try to get cached response data
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                # Return the cached data as a Response object
                from rest_framework.response import Response
                return Response(cached_data)
            
            # Generate the response
            response = view_func(self, request, *args, **kwargs)
            
            # Cache the response data instead of the response object
            if hasattr(response, 'data'):
                cache.set(cache_key, response.data, timeout)
            
            return response
        return _wrapped_view
    return decorator

def log_query_performance(view_func):
    """
    Decorator to log database query performance for dashboard views.
    """
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        # Reset query log
        connection.queries_log.clear()
        
        # Enable query logging
        original_debug = connection.force_debug_cursor
        connection.force_debug_cursor = True
        
        start_time = time.time()
        
        try:
            # Execute the view
            response = view_func(self, request, *args, **kwargs)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Log performance data
            query_count = len(connection.queries)
            if query_count > 10 or execution_time > 1.0:
                logger.warning(
                    f"Dashboard view {view_func.__name__} performance issue: "
                    f"{query_count} queries in {execution_time:.2f}s"
                )
                
                # Log the slowest queries
                queries = sorted(
                    connection.queries, 
                    key=lambda q: float(q.get('time', 0)), 
                    reverse=True
                )
                for i, query in enumerate(queries[:5]):
                    logger.warning(f"Slow query #{i+1}: {query.get('time')}s - {query.get('sql')}")
            
            return response
        finally:
            # Restore original debug setting
            connection.force_debug_cursor = original_debug
    
    return _wrapped_view

def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """
    Optimize a queryset by adding select_related and prefetch_related.
    
    Args:
        queryset: The queryset to optimize
        select_related: List of fields to select_related
        prefetch_related: List of fields to prefetch_related
    
    Returns:
        Optimized queryset
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    return queryset

def chunked_queryset(queryset, chunk_size=1000):
    """
    Break a large queryset into smaller chunks to avoid memory issues.
    
    Args:
        queryset: The queryset to chunk
        chunk_size: Size of each chunk
        
    Yields:
        Chunks of the queryset
    """
    start_pk = 0
    queryset = queryset.order_by('pk')
    
    while True:
        # Get a chunk of objects
        chunk = queryset.filter(pk__gt=start_pk)[:chunk_size]
        object_list = list(chunk)
        
        # If no objects were returned, we're done
        if not object_list:
            break
            
        # Yield the chunk
        yield object_list
        
        # Update the starting pk for the next chunk
        start_pk = object_list[-1].pk