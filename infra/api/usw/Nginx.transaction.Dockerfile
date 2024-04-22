FROM nginx:stable-alpine

COPY ./infra/api/usw/nginx.transaction.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]