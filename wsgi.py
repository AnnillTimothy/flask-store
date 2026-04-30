"""
WSGI entry point for production deployment (Gunicorn / uWSGI).

Usage with Gunicorn:
    gunicorn "wsgi:application" --workers 4 --bind 0.0.0.0:8000

On AWS EC2 / Ubuntu with Nginx reverse-proxy, typical command:
    gunicorn "wsgi:application" --workers 4 --bind 127.0.0.1:8000 \
        --access-logfile /var/log/gunicorn/access.log \
        --error-logfile  /var/log/gunicorn/error.log \
        --daemon
"""
from app import create_app

application = create_app()

if __name__ == '__main__':
    application.run()
