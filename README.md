## Что сделать на VPS (чеклист)

1) Домен: A‑record на IP VPS.
2) sudo apt install docker docker-compose-plugin nginx certbot python3-certbot-nginx
3) docker compose up -d --build (поднимет app/db/redis)
4) Прописать nginx site и включить, затем sudo nginx -t && sudo systemctl reload nginx
5) sudo certbot --nginx -d queue.example.com (получить HTTPS)
6) В .env выставить BASE_URL=https://queue.example.com и перезапустить docker compose restart app — webhook обновится автоматически.