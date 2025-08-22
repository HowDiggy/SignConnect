# Use an official Node.js runtime as a parent image
FROM node:20

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to the working directory.
# This is done as a separate step to take advantage of Docker's layer caching.
# The dependencies will only be re-installed if package*.json changes.
COPY package*.json ./

# Install any needed packages
RUN npm install

# Bundle the rest of the app's source code
COPY . .

# Your app binds to port 5173, so expose it
EXPOSE 5173

# The command to run when the container starts.
# --host is necessary to make the Vite dev server accessible from outside the container.
CMD ["npm", "run", "dev", "--", "--host"]
