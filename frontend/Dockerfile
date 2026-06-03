FROM node:20-alpine
WORKDIR /app

# Copy dependency manifests
COPY package.json package-lock.json ./
RUN npm install

# Copy application source
COPY . .

EXPOSE 3000
# Run Vite on 0.0.0.0 so the port maps correctly to the host OS
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
