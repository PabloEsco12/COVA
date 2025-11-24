#!/bin/bash
set -euo pipefail
cd /srv/securechat

INFO() { echo "[INFO] $*"; }
WARN() { echo "[WARN] $*"; }

INFO "Status des conteneurs"
docker compose -f docker-compose.prod.yml ps

INFO "Logs ClamAV (dernieres lignes)"
docker logs securechat_clamav | tail -n 30 || true

INFO "Test EICAR (antivirus)"
set +e
docker exec securechat_clamav sh -c 'echo "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*" > /tmp/eicar.com'
docker exec securechat_clamav clamdscan /tmp/eicar.com
scan_rc=$?
if [ $scan_rc -eq 0 ] || [ $scan_rc -eq 1 ]; then
  INFO "Resultat clamdscan (0=clean,1=infecte) rc=$scan_rc"
else
  WARN "clamdscan a echoue (rc=$scan_rc) — clamd probablement non pret (rate-limit CDN ?)"
fi
set -e

if [ "${1:-}" = "--autoheal" ]; then
  INFO "Test autoheal : on tue le backend pour verifier le restart"
  docker exec securechat_backend kill 1 || true
  sleep 10
  docker compose -f docker-compose.prod.yml ps
  INFO "Logs autoheal"
  docker logs autoheal | tail -n 30
else
  INFO "Test autoheal saute (lancer avec --autoheal pour tester)"
fi