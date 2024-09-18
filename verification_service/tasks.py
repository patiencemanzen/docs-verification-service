from celery import shared_task
import redis # type: ignore
from datetime import datetime
from .utils import FileDataExtraction

# Configure Redis for caching
redis_cache = redis.Redis(host='localhost', port=6379, db=0)

# Celery task to fine-tune the model and cache the result
@shared_task
def fine_tune_model():
    # Create a unique cache key based on the file path (or user)
    uniqueKey = datetime.now().strftime("%Y%m%d%H%M%S")
    cache_key = f"fine_tune_result_{uniqueKey}"

    # Check if the result is already in Redis cache
    cached_result = redis_cache.get(cache_key)
    if cached_result:
        print("Returning cached result")
        return cached_result.decode()

    # If no cached result, initialize and fine-tune the model
    print("No cache found, fine-tuning model...")

    # Perform chat Generation
    response = FileDataExtraction.initChatSession()

    # Cache the result in Redis with a TTL of 1 hour (3600 seconds)
    redis_cache.setex(cache_key, 3600, response)

    print("Model fine-tuning completed.")
    return response

@shared_task
def test_redis_connection():
    return "Celery is working!"