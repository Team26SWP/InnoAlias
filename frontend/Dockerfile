FROM node:20 as builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --force
COPY . .
RUN npm run build
FROM nginx:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
