FROM node:20-alpine AS assets_builder

WORKDIR /app

COPY package.json package-lock.json* vite.config.js /app/
COPY src /app/src
COPY static/css /app/static/css
RUN npm install && npm run build

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=assets_builder /app/static/dist /app/static/dist
RUN chmod +x entrypoint.sh && mkdir -p /data/images

EXPOSE 8083

CMD ["./entrypoint.sh"]
