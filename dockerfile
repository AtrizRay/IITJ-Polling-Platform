FROM python:3.9-slim

ENV PYTHONUNBUFFERED True
ENV APP_HOME /app
ENV PORT 8080

WORKDIR $APP_HOME

COPY . ./

# Install dependencies including debugpy
RUN pip install flask gunicorn pandas debugpy flask_login werkzeug flask_sqlalchemy flask_migrate config 

# Add debug mode environment variable
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

CMD gunicorn --bind :${PORT} --workers 1 --threads 8 --timeout 0 app:app
