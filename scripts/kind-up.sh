#!/usr/bin/env bash
# scripts/kind-up.sh — implementation added in Phase 5/6.
set -euo pipefail

# Safety: abort if not running against the expected kind context.
EXPECTED_CONTEXT="kind-incident-assistant"
CURRENT_CONTEXT=$(kubectl config current-context 2>/dev/null || echo "none")
if [[ "$CURRENT_CONTEXT" != "$EXPECTED_CONTEXT" ]]; then
  echo "ERROR: Expected kubectl context '$EXPECTED_CONTEXT', got '$CURRENT_CONTEXT'." >&2
  echo "       Refusing to run against an unexpected cluster." >&2
  exit 1
fi

echo "Script not yet implemented. Run the corresponding phase first." >&2
exit 1
