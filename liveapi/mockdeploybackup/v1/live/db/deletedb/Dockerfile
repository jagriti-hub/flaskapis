FROM python:3.8.1-slim-buster
RUN addgroup --system app && adduser --system --ingroup app app
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME
RUN apt-get update && apt-get install -y --no-install-recommends netcat
COPY code/requirement.txt  $APP_HOME/requirement.txt
RUN pip install --upgrade pip -r requirement.txt
COPY code/app.py $APP_HOME
COPY code/wsgi.py $APP_HOME
RUN chown -R app:app $APP_HOME
USER app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]