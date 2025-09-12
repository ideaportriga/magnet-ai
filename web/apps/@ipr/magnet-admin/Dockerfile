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

EXPOSE 80

# Use the entrypoint script instead of direct nginx command
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]