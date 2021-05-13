FROM python:3.8.1-slim-buster
RUN addgroup --system --gid 150 app && adduser --system --ingroup app --uid 150 app
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
RUN mkdir -p $APP_HOME/archeplay/data
WORKDIR $APP_HOME
RUN apt-get update && apt-get install -y --no-install-recommends netcat
COPY requirement.txt  $APP_HOME/requirement.txt
RUN apt-get install -y python3-pip
RUN pip3 install --upgrade pip -r requirement.txt
COPY app.py $APP_HOME/app.py
COPY s3files.py $APP_HOME/s3files.py
RUN chown -R app:app $APP_HOME
USER app