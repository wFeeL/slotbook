# syntax=docker/dockerfile:1
FROM node:20-alpine AS builder
WORKDIR /app
ENV CI=true
COPY package.json package-lock.json* ./
RUN npm ci
COPY tsconfig*.json vite.config.ts tailwind.config.ts postcss.config.js index.html eslint.config.js .prettierrc ./
COPY src ./src
COPY public ./public
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
