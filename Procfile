web: python -m gunicorn gemini_verification_service.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:4000
worker: celery -A gemini_verification_service worker --loglevel=info