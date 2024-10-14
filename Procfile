web: python -m gunicorn gemini_verification_service.asgi:application -k uvicorn.workers.UvicornWorker
worker: celery -A gemini_verification_service worker --loglevel=info
