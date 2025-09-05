# frontend/Dockerfile

# --- Build Stage ---
FROM node:20 as builder

WORKDIR /app

COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# --- Final Stage ---
FROM nginx:stable-alpine

# Copy the built assets from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# The default command for the nginx image is to start the server
CMD ["nginx", "-g", "daemon off;"]
