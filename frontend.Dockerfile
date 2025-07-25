# frontend.Dockerfile

# Use an official Node runtime as a parent image
FROM node:20

# Set the working directory inside the container
WORKDIR /app

# Change to the frontend directory to run npm commands
WORKDIR /app/frontend

# Copy the package.json and package-lock.json files
# This is done first to leverage Docker's layer caching
COPY frontend/package*.json ./

# Install project dependencies
RUN npm install

# Copy the rest of the frontend source code
# Note: We are copying the content of the local 'frontend' folder
# into the '/app/frontend' directory inside the container.
COPY frontend/ .

# The command to run when the container starts.
# --host is necessary to make the Vite dev server accessible from outside the container.
CMD ["npm", "run", "dev", "--", "--host"]