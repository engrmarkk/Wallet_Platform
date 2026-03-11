from celery import Celery, shared_task
from dotenv import load_dotenv
import worker.schedule as celeryConfig
import os

load_dotenv()



def make_celery():
    redis_url = os.getenv("REDIS_URL")
    
    celery = Celery(
        "app_config",
        backend=redis_url,
        broker=redis_url,
    )

    celery.config_from_object(celeryConfig)
    
    # Configure celery (no app_context here!)
    celery.conf.broker_pool_limit = 10
    celery.conf.redis_socket_keepalive = True
    celery.conf.redis_socket_timeout = 30
    celery.conf.redis_retry_on_timeout = True
    
    return celery

celery = make_celery()


@shared_task
def add_numbers(x, y):
    print("Adding")
    return x + y
