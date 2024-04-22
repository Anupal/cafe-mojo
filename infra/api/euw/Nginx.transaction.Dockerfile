FROM nginx:stable-alpine

COPY ./infra/api/euw/nginx.transaction.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]