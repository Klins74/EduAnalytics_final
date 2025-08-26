# Dockerfile for Vite/React frontend
FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 5173
CMD ["npm", "start", "--", "--port", "5173", "--host", "0.0.0.0"]