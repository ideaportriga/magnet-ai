FROM nginx:alpine

# Install packages
RUN apk add --no-cache jq

# Add environment variable handling script
COPY scripts/docker-entrypoint-panel.sh /docker-entrypoint-panel.sh
RUN chmod +x /docker-entrypoint-panel.sh

# Copy app and config files
COPY knowledge-magnet/panel/app /usr/share/nginx/html/
COPY packages/shared/public/config/base.main.json /usr/share/nginx/html/config/main.json
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# Use the entrypoint script instead of direct nginx command
ENTRYPOINT ["/docker-entrypoint-panel.sh"]
CMD ["nginx", "-g", "daemon off;"]