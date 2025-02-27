# Use the official Nginx image as the base
FROM nginx:alpine

# Copy custom Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

