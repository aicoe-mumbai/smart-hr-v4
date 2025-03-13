# Use a minimal Node.js base image
FROM node:20-alpine

# Set working directory inside the container
WORKDIR /app

# Copy package.json and package-lock.json for efficient caching
COPY package*.json ./

# Install dependencies (production if needed)
RUN npm install --production

# Copy the rest of the frontend code (excluding node_modules)
COPY . .

# Expose the frontend development port
EXPOSE 3000

# Start the React application
CMD ["npm", "start"]
