#!/usr/bin/env bash
# Adds sample students through the API.  Usage: bash scripts/seed_demo.sh [base_url]
BASE="${1:-http://127.0.0.1}"

add() {  # add NAME EMAIL DEPARTMENT AGE
  curl -s -o /dev/null -w "%{http_code}  $1\n" -X POST "$BASE/students" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"$1\",\"email\":\"$2\",\"department\":\"$3\",\"age\":$4}"
}

add "Aarav Sharma" aarav@example.com  CSE   21
add "Diya Reddy"   diya@example.com    ECE   20
add "Kabir Rao"    kabir@example.com  CSE   22
add "Meera Nair"   meera@example.com  EEE   21
add "Rohan Gupta"  rohan@example.com  MECH  23
add "Sneha Iyer"   sneha@example.com  CSE   20
add "Vikram Singh" vikram@example.com CIVIL 22
add "Ananya Das"   ananya@example.com IT    21