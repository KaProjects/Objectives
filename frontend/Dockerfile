# build stage
FROM node:24-alpine AS build-stage
WORKDIR /app
COPY package*.json ./

ARG VITE_BACKEND_URL='http://127.0.0.1:8080'

RUN npm ci --include=dev
COPY . .
RUN npm run build

# production stage
FROM nginx:stable-alpine AS production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
