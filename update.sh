#!/usr/bin/env bash
# Botni yangilash: kod -> image -> testlar -> konteyner.
# Ishlatish:  ./update.sh
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/4  Kod yangilanmoqda"
git pull

echo "==> 2/4  Image yig'ilmoqda"
sudo docker build -t fotobot .

echo "==> 3/4  Testlar"
# Testdan o'tmasa shu yerda to'xtaydi va eski konteyner ishlab turaveradi
sudo docker run --rm --env-file .env fotobot python selftest.py

echo "==> 4/4  Konteyner almashtirilmoqda"
touch contest.db          # mount qilinadigan fayl mavjud bo'lishi shart
sudo docker rm -f fotobot >/dev/null 2>&1 || true
sudo docker run -d --name fotobot --restart always \
  --env-file .env \
  -v "$PWD/uploads:/app/uploads" \
  -v "$PWD/exports:/app/exports" \
  -v "$PWD/contest.db:/app/contest.db" \
  fotobot >/dev/null

sudo docker ps --filter name=fotobot --format 'table {{.Names}}\t{{.Status}}'
echo
sudo docker logs --tail 10 fotobot
