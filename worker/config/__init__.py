from celery import Celery, shared_task
from app_config import create_app
from dotenv import load_dotenv
import worker.schedule as celeryConfig
import os

load_dotenv()


app = create_app()


def make_celery(app=app):
    celery = Celery(
        app.import_name,
        backend=os.getenv("REDIS_URL"),
        broker=os.getenv("REDIS_URL"),
    )
    celery.conf.update(app.config)
    celery.config_from_object(celeryConfig)

    # Add explicit connection pool settings
    celery.conf.broker_pool_limit = 10  # Don't use None — that causes unbounded pools
    celery.conf.redis_socket_keepalive = True
    celery.conf.redis_socket_timeout = 30
    celery.conf.redis_retry_on_timeout = True

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


celery = make_celery()


@shared_task
def add_numbers(x, y):
    print("Adding")
    return x + y
