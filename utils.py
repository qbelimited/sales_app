from flask import request
import redis
from functools import wraps
import json
from datetime import timedelta

# Initialize Redis client
redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def get_client_ip():
    """Safely retrieve the client's IP address, accounting for proxies."""
    if request.headers.get('X-Forwarded-For'):
        # Get the first IP in the list (client's IP), which could be comma-separated
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    else:
        # Fallback to the direct remote address if no forwarding header is present
        ip = request.remote_addr

    # If no valid IP is found, default to '0.0.0.0'
    return ip or '0.0.0.0'

def cache_response(ttl=300):  # Default TTL of 5 minutes
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get cached result
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # If not cached, execute function
            result = f(*args, **kwargs)

            # Cache the result
            redis_client.setex(
                cache_key,
                timedelta(seconds=ttl),
                json.dumps(result)
            )

            return result
        return decorated_function
    return decorator

def invalidate_cache(pattern):
    """Invalidate cache entries matching a pattern"""
    keys = redis_client.keys(pattern)
    if keys:
        redis_client.delete(*keys)
