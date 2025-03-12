FROM node:20-alpine

WORKDIR /app

# Copy package.json and package-lock.json first
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the entire frontend code
COPY  . . 

EXPOSE 3000

CMD ["npm", "run", "dev"]