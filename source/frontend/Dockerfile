FROM node:20-alpine AS build

WORKDIR /app

COPY package.json ./
RUN npm install

COPY public/ ./public/
COPY src/ ./src/

RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
RUN sed -i 's/listen\s*80;/listen 3000;/g' /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
