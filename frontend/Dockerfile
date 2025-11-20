# Material Dashboard Frontend Dockerfile
FROM nginx:alpine

# Install Node.js and npm for building assets
RUN apk add --no-cache nodejs npm

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all source files
COPY . .

# Build SCSS to CSS
RUN npm run compile-scss

# Copy built files to nginx
RUN mkdir -p /usr/share/nginx/html && \
    cp -r . /usr/share/nginx/html/ && \
    rm -f /usr/share/nginx/html/index.html && \
    cp /usr/share/nginx/html/pages/dashboard.html /usr/share/nginx/html/index.html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 4200
EXPOSE 4200

# Start nginx directly (no SSL needed)
CMD ["nginx", "-g", "daemon off;"]
