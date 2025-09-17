FROM nginx:alpine

# Install packages
RUN apk add --no-cache jq yarn

# Add environment variable handling script
COPY scripts/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Copy app and config files
COPY knowledge-magnet/admin/app /usr/share/nginx/html/
COPY documentation/magnet /app/docs
COPY packages/shared/public/config/base.main.json /usr/share/nginx/html/config/main.json
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /usr/share/nginx/html/config \
    && chgrp -R 0 /usr/share/nginx/html/config /usr/share/nginx/html/ \
    && chmod -R g+rwX /usr/share/nginx/html/config /usr/share/nginx/html/ \
    && chmod g+rwx /tmp

RUN chgrp -R 0 /var/cache/nginx /var/run /var/log/nginx \
    && chmod -R g+rwX /var/cache/nginx /var/run /var/log/nginx

EXPOSE 8080

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]


