#!/usr/bin/env bash
# End-to-end smoke test for the running stack.
# Usage (from the project root):  bash scripts/smoke_test.sh [base_url]
set -u

BASE="${1:-http://127.0.0.1}"
STAMP=$(date +%s)
EMAIL="smoke-$STAMP@example.com"
TRACE="smoke-trace-$STAMP"
JOB_TRACE="smoke-job-$STAMP"
PASS=0
FAIL=0

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1 ($2)"; FAIL=$((FAIL + 1)); }

check() {  # check "description" expected actual
  if [ "$2" = "$3" ]; then pass "$1"; else fail "$1" "expected '$2', got '$3'"; fi
}

is_true() {  # is_true "description" command args...
  local desc=$1; shift
  if "$@" >/dev/null 2>&1; then pass "$desc"; else fail "$desc" "condition not met"; fi
}

request() {  # request METHOD PATH [JSON_BODY] [HEADER]  -> sets CODE and BODY
  local method=$1 path=$2 data=${3:-} header=${4:-X-Smoke: 1}
  local args=(-s -w $'\n%{http_code}' -X "$method" "$BASE$path" -H "$header")
  [ -n "$data" ] && args+=(-H "Content-Type: application/json" -d "$data")
  local out
  out=$(curl "${args[@]}")
  CODE=${out##*$'\n'}
  BODY=${out%$'\n'*}
}

jget() {  # echo "$BODY" | jget items.0.id   (prints nothing if the path is missing)
  python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    for key in sys.argv[1].split("."):
        data = data[int(key)] if isinstance(data, list) else data[key]
    print("" if data is None else data)
except Exception:
    print("")
' "$1"
}
jlen() {  # echo "$BODY" | jlen items   (length of a JSON list, empty if missing)
  python3 -c '
import json, sys
try:
    print(len(json.load(sys.stdin)[sys.argv[1]]))
except Exception:
    print("")
' "$1"
}


if ! curl -s -o /dev/null --max-time 5 "$BASE/health"; then
  echo "Cannot reach $BASE. Is the stack running, and is the port right?"
  exit 2
fi
echo "Health"
request GET /health
check "liveness returns 200" 200 "$CODE"
request GET /health/ready
check "readiness returns 200" 200 "$CODE"
check "readiness status is ok" ok "$(echo "$BODY" | jget status)"
HDR=$(curl -s -D - -o /dev/null -H "X-Request-ID: $TRACE" "$BASE/health" \
  | tr -d '\r' | awk -F': ' 'tolower($1)=="x-request-id"{print $2}')
check "a request id is echoed back in the response header" "$TRACE" "$HDR"

echo "Students"
NEW="{\"name\":\"Smoke Test\",\"email\":\"$EMAIL\",\"department\":\"SMOKE\",\"age\":21}"
request POST /students "$NEW"
check "create returns 201" 201 "$CODE"
ID=$(echo "$BODY" | jget id)
is_true "created student has an id" test -n "$ID"

request POST /students "$NEW"
check "duplicate email returns 409" 409 "$CODE"
check "duplicate error code" duplicate_email "$(echo "$BODY" | jget error)"

request POST /students "{\"name\":\"X Y\",\"email\":\"not-an-email\",\"department\":\"SMOKE\",\"age\":21}"
check "invalid email returns 422" 422 "$CODE"
check "validation error code" validation_error "$(echo "$BODY" | jget error)"

request GET "/students/$ID"
check "get by id returns 200" 200 "$CODE"
check "get returns the right email" "$EMAIL" "$(echo "$BODY" | jget email)"

request PATCH "/students/$ID" '{"age":22}'
check "patch returns 200" 200 "$CODE"
check "patch changed the age" 22 "$(echo "$BODY" | jget age)"
request PATCH "/students/$ID" '{}'
check "empty patch returns 422" 422 "$CODE"
check "empty patch error code" empty_update "$(echo "$BODY" | jget error)"

request GET /students/999999999
check "missing student returns 404" 404 "$CODE"
check "missing student error code" student_not_found "$(echo "$BODY" | jget error)"

request GET "/students?search=$EMAIL&limit=5"
check "search finds exactly our student" 1 "$(echo "$BODY" | jget total)"
request GET "/students?limit=1"
check "pagination returns one item" 1 "$(echo "$BODY" | jlen items)"
request GET "/students?limit=500"
check "limit above 100 returns 422" 422 "$CODE"
request GET /nothing
check "unknown route returns 404" 404 "$CODE"
check "unknown route error code" not_found "$(echo "$BODY" | jget error)"

echo "Reports (API -> Redis -> worker)"
request POST /reports "" "X-Request-ID: $JOB_TRACE"
check "report request returns 202" 202 "$CODE"
JOB=$(echo "$BODY" | jget job_id)
STATUS=queued
for _ in $(seq 1 30); do
  request GET "/reports/$JOB"
  STATUS=$(echo "$BODY" | jget status)
  [ "$STATUS" = finished ] || [ "$STATUS" = failed ] && break
  sleep 1
done
check "report job finishes" finished "$STATUS"
is_true "report contains at least one row" test "$(echo "$BODY" | jget result.rows)" -ge 1

if docker compose ps >/dev/null 2>&1; then
  COUNT=$(docker compose logs --no-color --since 5m student-api worker 2>/dev/null | grep -c "$JOB_TRACE")
  is_true "the request id appears in both the API and worker logs" test "$COUNT" -ge 2
else
  echo "  SKIP  log check (run from the project root with Docker available)"
fi

echo "Cleanup"
request DELETE "/students/$ID"
check "delete returns 204" 204 "$CODE"
request GET "/students/$ID"
check "deleted student is gone (404)" 404 "$CODE"

echo
echo "Passed: $PASS   Failed: $FAIL"
[ "$FAIL" -eq 0 ]