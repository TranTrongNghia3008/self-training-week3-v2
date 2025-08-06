from django.core.cache import cache

def delete_cache_by_prefix(prefix: str):
    """
    Delete all cache keys that start with a specific prefix.
    Only works with Redis + django-redis backend.
    """
    try:
        keys = cache.keys(f"{prefix}*")
        if keys:
            cache.delete_many(keys)
    except Exception as e:
        # Log nếu dùng production logger
        print(f"Error deleting cache with prefix {prefix}: {e}")

