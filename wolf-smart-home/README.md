# WOLF SMART HOME
SaaS de automação residencial enterprise.

## Instalação local
1. `cp backend/.env.example backend/.env`
2. `docker compose up -d`
3. Frontend: http://localhost:5173 | API: http://localhost:4000

## Produção Ubuntu VPS
- Instalar Docker e Docker Compose plugin.
- Configurar DNS e SSL com Nginx Proxy Manager ou Certbot.
- Publicar apenas Nginx (80/443) e bloquear portas internas.

## Variáveis
- `MONGO_URI`, `JWT_SECRET`, `JWT_REFRESH_SECRET`, `MQTT_URL`, `CORS_ORIGIN`

## Backup/Restore Mongo
- Backup: `mongodump --uri $MONGO_URI --out /backup/wolf`
- Restore: `mongorestore --uri $MONGO_URI /backup/wolf`

## Atualização
- `git pull`
- `docker compose build --no-cache`
- `docker compose up -d`
