FROM nginx
COPY ./nginx.conf /etc/nginx/nginx.conf
ADD ./api_conf.d /etc/nginx/api_conf.d/
ADD ./api_backends_conf.d /etc/nginx/api_backends_conf.d/
ADD ./api_gateway.conf /etc/nginx/
ADD ./api_backends.conf /etc/nginx/
ADD ./api_json_errors.conf /etc/nginx/
EXPOSE 80