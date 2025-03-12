# Use official Node.js image
FROM node:16-alpine

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all files
COPY . .

# Expose port (typically 3000 for React development)
EXPOSE 3000

# Run the app in development mode
CMD ["npm", "start"]