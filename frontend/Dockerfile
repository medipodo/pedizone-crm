# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json yarn.lock ./

# Install dependencies
RUN yarn install

# Copy source code
COPY . .

# Build argument for backend URL
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build the app
RUN yarn build

# Production stage
FROM nginx:alpine

# Copy built files from builder
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
