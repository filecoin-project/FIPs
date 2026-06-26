#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MD_FILE="$SCRIPT_DIR/../../FRCs/frc-0104.md"
JSON_FILE="$SCRIPT_DIR/common-node-api.json"

MD_METHODS=$(awk '/^\| Method.*\| Category.*\| Description/ {
  getline
  while (getline && /^\|/) {
    if ($0 !~ /^\|---/) {
      gsub(/^ *\| */, "", $0)
      gsub(/ *\|.*/, "", $0)
      gsub(/^ *| *$/, "", $0)
      print $0
    }
  }
}' "$MD_FILE" | sort)

JSON_METHODS=$(grep -o '"name": "Filecoin\.[^"]*"' "$JSON_FILE" |
  grep -v '\.Result"' |
  sed 's/"name": "Filecoin\.//;s/"//' |
  sort)

DIFF=$(diff <(echo "$MD_METHODS") <(echo "$JSON_METHODS"))

if [[ -z "$DIFF" ]]; then
  echo "✅ Methods are in sync."
else
  echo "❌ Methods are not in sync."
  echo "$DIFF"
fi
