#!/usr/bin/env bash
BASE=http://127.0.0.1:8000

check() {
  label=$1; method=$2; path=$3
  shift 3
  echo "=== $label"
  curl -s -w "\n-> status %{http_code}\n" -X "$method" "$BASE$path" \
    -H "Content-Type: application/json" "$@"
  echo
}

VALID='{"name":"Rahul Sharma","email":"rahul@example.com","department":"CSE","age":21}'

check "setup: create a student (201, or 409 if it already exists)" POST /students -d "$VALID"

check "1. GET /students/99999 -> 404 student_not_found" GET /students/99999
check "2. GET /students/abc -> 422 validation_error" GET /students/abc
check "3. invalid email -> 422, details names email" POST /students \
  -d '{"name":"Rahul","email":"not-an-email","department":"CSE","age":21}'
check "4. age 200 -> 422, details names age" POST /students \
  -d '{"name":"Rahul","email":"age@example.com","department":"CSE","age":200}'
check "5. existing email -> 409 duplicate_email" POST /students -d "$VALID"
check "6. extra field id -> 422 validation_error" POST /students \
  -d '{"id":5,"name":"Rahul","email":"extra@example.com","department":"CSE","age":21}'
check "7. PATCH with {} -> 422 empty_update" PATCH /students/1 -d '{}'
check "8. PATCH missing student -> 404 student_not_found" PATCH /students/99999 -d '{"age":21}'
check "9. DELETE missing student -> 404 student_not_found" DELETE /students/99999
check "10. GET /nothing -> 404 not_found" GET /nothing
check "11. PUT /students/1 -> 405 method_not_allowed" PUT /students/1 -d "$VALID"
