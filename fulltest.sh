#!/usr/bin/env bash
# End-to-end test for the URL shortener.
# Usage: bash fulltest.sh [--unit] [--clean]
#   --unit   also run ruff and pytest first
#   --clean  delete the test users (and their links and clicks) afterwards
# Needs: the stack running, python3, curl. Docker checks are skipped if docker is unavailable.
set -u

BASE=${BASE:-http://localhost:8000}
J='content-type: application/json'
PASS=0
FAIL=0
SKIP=0
GREEN=$'\033[32m'
RED=$'\033[31m'
YELLOW=$'\033[33m'
OFF=$'\033[0m'

UNIT=0
CLEAN=0
for arg in "$@"; do
  case "$arg" in
    --unit) UNIT=1 ;;
    --clean) CLEAN=1 ;;
  esac
done

# ---------- helpers ----------
sec()  { printf "\n== %s\n" "$1"; }
ok()   { PASS=$((PASS+1)); printf "  %sPASS%s %s\n" "$GREEN" "$OFF" "$1"; }
bad()  { FAIL=$((FAIL+1)); printf "  %sFAIL%s %s\n        expected: %s\n        got:      %s\n" "$RED" "$OFF" "$1" "$2" "$3"; }
skip() { SKIP=$((SKIP+1)); printf "  %sSKIP%s %s\n" "$YELLOW" "$OFF" "$1"; }

eq()  { if [ "$2" = "$3" ]; then ok "$1"; else bad "$1" "$2" "$3"; fi; }
has() { case "$3" in *"$2"*) ok "$1" ;; *) bad "$1" "contains '$2'" "$3" ;; esac; }
ge()  { if [ "${3:-0}" -ge "$2" ] 2>/dev/null; then ok "$1"; else bad "$1" ">= $2" "$3"; fi; }

status() { curl -s -o /dev/null -w "%{http_code}" "$@"; }

jget() {
  python3 -c '
import sys, json
d = json.load(sys.stdin)
for k in sys.argv[1].split("."):
    d = d[int(k)] if k.isdigit() else d[k]
print(d)
' "$1" 2>/dev/null
}

count_of() {  # count_of JSON list-key name-field value
  python3 -c '
import sys, json
d = json.loads(sys.argv[1])
print(sum(x["clicks"] for x in d[sys.argv[2]] if x[sys.argv[3]] == sys.argv[4]))
' "$1" "$2" "$3" "$4" 2>/dev/null
}

list_len() { python3 -c 'import sys,json;print(len(json.load(sys.stdin)))' 2>/dev/null; }

have_docker() { docker ps >/dev/null 2>&1; }
sql() { docker exec postgres psql -U postgres -d shortener -tAc "$1" 2>/dev/null | tr -d '[:space:]'; }
rcli() { docker exec redis sh -c "redis-cli -a \"\$REDIS_PASSWORD\" --no-auth-warning $1" 2>/dev/null; }

new_user() {  # prints the api key
  curl -s -X POST "$BASE/v1/users" -H "$J" -d "{\"email\":\"ft$RANDOM$RANDOM@example.com\"}" | jget api_key
}

post_link() {  # post_link KEY JSON -> body
  curl -s -X POST "$BASE/v1/links" -H "X-API-Key: $1" -H "$J" -d "$2"
}

link_status() {  # link_status KEY JSON -> http code
  status -X POST "$BASE/v1/links" -H "X-API-Key: $1" -H "$J" -d "$2"
}

wait_stats() {  # wait_stats N -> prints total_clicks once >= N (max ~15 s)
  local t=0
  for _ in $(seq 15); do
    t=$(curl -s "$BASE/v1/links/$CODE/stats" -H "X-API-Key: $KEY" | jget total_clicks)
    if [ "${t:-0}" -ge "$1" ] 2>/dev/null; then echo "$t"; return; fi
    sleep 1
  done
  echo "${t:-0}"
}

# ---------- 0. unit tests (optional) ----------
if [ "$UNIT" = 1 ]; then
  sec "Unit tests"
  if ruff check . >/dev/null 2>&1; then ok "ruff is clean"; else bad "ruff is clean" "no findings" "run: ruff check ."; fi
  if pytest -q >/dev/null 2>&1; then ok "pytest passes"; else bad "pytest passes" "all green" "run: pytest -q"; fi
fi

# ---------- 1. health ----------
sec "Health"
eq "GET /healthz -> 200" 200 "$(status "$BASE/healthz")"

# ---------- 2. users ----------
sec "Users"
EMAIL="ft$RANDOM$RANDOM@example.com"
R=$(curl -s -X POST "$BASE/v1/users" -H "$J" -d "{\"email\":\"$EMAIL\"}")
KEY=$(echo "$R" | jget api_key)
has "user created, key starts with sk_" "sk_" "$KEY"
if [ -z "$KEY" ]; then
  echo "Cannot continue without an API key. Response was: $R"
  exit 1
fi
eq "duplicate email -> 409" 409 "$(status -X POST "$BASE/v1/users" -H "$J" -d "{\"email\":\"$EMAIL\"}")"
eq "invalid email -> 422" 422 "$(status -X POST "$BASE/v1/users" -H "$J" -d '{"email":"nope"}')"

# ---------- 3. links ----------
sec "Links"
R=$(post_link "$KbashEY" '{"url":"https://example.com"}')
CODE=$(echo "$R" | jget code)
eq "random code has 7 characters" 7 "${#CODE}"
if [ -z "$CODE" ]; then
  echo "Cannot continue without a link. Response was: $R"
  exit 1
fi
ALIAS="ft$RANDOM"
eq "alias link -> 201" 201 "$(link_status "$KEY" "{\"url\":\"https://example.com/x\",\"alias\":\"$ALIAS\"}")"
eq "same alias again -> 409" 409 "$(link_status "$KEY" "{\"url\":\"https://example.com/y\",\"alias\":\"$ALIAS\"}")"
eq "javascript: URL -> 422" 422 "$(link_status "$KEY" '{"url":"javascript:alert(1)"}')"
eq "file: URL -> 422" 422 "$(link_status "$KEY" '{"url":"file:///etc/passwd"}')"
eq "reserved alias -> 422" 422 "$(link_status "$KEY" '{"url":"https://example.com","alias":"admin"}')"
eq "missing API key -> 401" 401 "$(status -X POST "$BASE/v1/links" -H "$J" -d '{"url":"https://example.com"}')"
eq "wrong API key -> 401" 401 "$(link_status wrong '{"url":"https://example.com"}')"
eq "list shows 2 links" 2 "$(curl -s "$BASE/v1/links" -H "X-API-Key: $KEY" | list_len)"
eq "get one link -> 200" 200 "$(status "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY")"

# ---------- 4. redirect ----------
sec "Redirect"
OUT=$(curl -s -o /dev/null -w "%{http_code} %{redirect_url}" "$BASE/$CODE")
has "GET /{code} -> 302" "302" "$OUT"
has "redirects to the target" "example.com" "$OUT"
eq "unknown code -> 404" 404 "$(status "$BASE/zzzzzzz")"
eq "invalid code format -> 404" 404 "$(status "$BASE/ab")"
if have_docker; then
  TTL=$(rcli "ttl link:$CODE")
  ge "link is cached in Redis (ttl > 0)" 1 "${TTL:-0}"
else
  skip "Redis cache check (docker not available)"
fi

# ---------- 5. click pipeline ----------
sec "Click pipeline (API -> Redis stream -> worker -> Postgres -> stats)"
IPHONE='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
DESKTOP='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
for _ in 1 2 3; do curl -s -o /dev/null -A "$IPHONE" -e "https://www.t.co/x" "$BASE/$CODE"; done
for _ in 1 2; do curl -s -o /dev/null -A "$DESKTOP" "$BASE/$CODE"; done
# 1 click from the redirect check above + 5 here = 6
TOTAL=$(wait_stats 6)
eq "worker stored all 6 clicks" 6 "$TOTAL"
STATS=$(curl -s "$BASE/v1/links/$CODE/stats" -H "X-API-Key: $KEY")
eq "mobile clicks = 3" 3 "$(count_of "$STATS" devices device mobile)"
eq "desktop clicks = 2" 2 "$(count_of "$STATS" devices device desktop)"
eq "t.co referrer clicks = 3" 3 "$(count_of "$STATS" top_referrers referrer t.co)"
ge "by_day has at least one entry" 1 "$(echo "$STATS" | python3 -c 'import sys,json;print(len(json.load(sys.stdin)["by_day"]))' 2>/dev/null)"
if have_docker; then
  PENDING=""
  for _ in $(seq 10); do
    PENDING=$(rcli "xpending clicks:stream click-workers" | head -1)
    [ "$PENDING" = "0" ] && break
    sleep 1
  done
  eq "no unacknowledged stream entries" 0 "$PENDING"
  eq "clicks is a hypertable" 1 "$(sql "select count(*) from timescaledb_information.hypertables where hypertable_name='clicks'")"
  eq "no raw IPs stored (ip_hash is 16 chars or null)" 0 "$(sql "select count(*) from clicks where ip_hash is not null and length(ip_hash) <> 16")"
else
  skip "stream, hypertable and IP checks (docker not available)"
fi

# ---------- 6. ownership ----------
sec "Ownership"
KEY2=$(new_user)
eq "other user cannot read my link -> 404" 404 "$(status "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY2")"
eq "other user cannot read my stats -> 404" 404 "$(status "$BASE/v1/links/$CODE/stats" -H "X-API-Key: $KEY2")"
eq "other user cannot delete my link -> 404" 404 "$(status -X DELETE "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY2")"
eq "other user's list is empty" 0 "$(curl -s "$BASE/v1/links" -H "X-API-Key: $KEY2" | list_len)"

# ---------- 7. update and cache invalidation ----------
sec "Update"
eq "PATCH url -> 200" 200 "$(status -X PATCH "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY" -H "$J" -d '{"url":"https://example.org/new"}')"
eq "PATCH with bad url -> 422" 422 "$(status -X PATCH "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY" -H "$J" -d '{"url":"javascript:x"}')"
OUT=$(curl -s -o /dev/null -w "%{redirect_url}" "$BASE/$CODE")
eq "redirect uses the new target immediately (cache invalidated)" "https://example.org/new" "$OUT"

# ---------- 8. expiry ----------
sec "Expiry"
SOON=$(date -u -d '+4 seconds' +%Y-%m-%dT%H:%M:%SZ)
R=$(post_link "$KEY" "{\"url\":\"https://example.com/soon\",\"expires_at\":\"$SOON\"}")
ECODE=$(echo "$R" | jget code)
eq "expiring link works before it expires -> 302" 302 "$(status "$BASE/$ECODE")"
eq "expiry in the past is rejected -> 422" 422 "$(link_status "$KEY" '{"url":"https://example.com","expires_at":"2020-01-01T00:00:00Z"}')"
echo "  (waiting 6 seconds for the link to expire)"
sleep 6
eq "expired link -> 410" 410 "$(status "$BASE/$ECODE")"

# ---------- 9. delete ----------
sec "Delete"
eq "DELETE -> 204" 204 "$(status -X DELETE "$BASE/v1/links/$CODE" -H "X-API-Key: $KEY")"
eq "deleted link -> 410 (cache invalidated)" 410 "$(status "$BASE/$CODE")"

# ---------- 10. rate limit ----------
sec "Rate limit (fresh user, 35 creations)"
KEY3=$(new_user)
OK_COUNT=0
LIMITED=0
for _ in $(seq 35); do
  c=$(link_status "$KEY3" '{"url":"https://example.com/rl"}')
  [ "$c" = "201" ] && OK_COUNT=$((OK_COUNT+1))
  [ "$c" = "429" ] && LIMITED=$((LIMITED+1))
done
echo "  created: $OK_COUNT, limited: $LIMITED"
ge "at least one request was limited (429)" 1 "$LIMITED"
ge "some requests were allowed (201)" 1 "$OK_COUNT"

# ---------- summary ----------
sec "Summary"
printf "  %s%d passed%s, %s%d failed%s, %s%d skipped%s\n" "$GREEN" "$PASS" "$OFF" "$RED" "$FAIL" "$OFF" "$YELLOW" "$SKIP" "$OFF"

if [ "$CLEAN" = 1 ]; then
  if have_docker; then
    sql "delete from users where email like 'ft%@example.com'" >/dev/null
    echo "  test users, links and clicks removed"
  else
    echo "  cannot clean up: docker not available"
  fi
fi

[ "$FAIL" = 0 ]