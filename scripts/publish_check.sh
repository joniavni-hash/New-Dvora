#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

pass() { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; ERRORS=$((ERRORS+1)); }
warn() { echo -e "${YELLOW}!${NC} $1"; WARNINGS=$((WARNINGS+1)); }

echo "═══════════════════════════════════════"
echo "  Dvorah Publish Pre-Check"
echo "═══════════════════════════════════════"
echo ""

# 1. Branch check
BRANCH=$(git branch --show-current)
EXPECTED_BRANCH="${1:-new-architecture}"
if [ "$BRANCH" = "$EXPECTED_BRANCH" ]; then
    pass "Branch: $BRANCH"
else
    fail "Branch is '$BRANCH', expected '$EXPECTED_BRANCH'"
fi

# 2. Remote reachable
if git ls-remote --exit-code origin &>/dev/null; then
    pass "Remote 'origin' reachable"
else
    fail "Remote 'origin' unreachable"
fi

# 3. No divergence with remote
LOCAL=$(git rev-parse HEAD)
git fetch origin --quiet 2>/dev/null || true
REMOTE=$(git rev-parse "origin/$BRANCH" 2>/dev/null || echo "none")
if [ "$REMOTE" = "none" ]; then
    warn "Remote branch origin/$BRANCH does not exist yet"
elif [ "$LOCAL" = "$REMOTE" ]; then
    pass "Local and remote in sync (nothing to push)"
elif git merge-base --is-ancestor "$REMOTE" "$LOCAL" 2>/dev/null; then
    AHEAD=$(git rev-list --count "$REMOTE".."$LOCAL")
    pass "Local is $AHEAD commit(s) ahead of remote — ready to push"
else
    fail "Local has diverged from remote — rebase or merge needed"
fi

# 4. Critical files tracked
CRITICAL_FILES=(
    "AGENTS.md"
    "MEMORY_INDEX.md"
    "identity/SOUL.md"
    "identity/VOICE.md"
    "identity/OPERATING_PRINCIPLES.md"
    "identity/RULE_PRIORITY.md"
    "policies/MEMORY_POLICY.md"
    "policies/EXTERNAL_ACTIONS_POLICY.md"
    "policies/PRIVACY_POLICY.md"
    "policies/GROUP_BEHAVIOR_POLICY.md"
    "memory/PROFILE.md"
    "memory/RELATIONSHIPS.md"
    "memory/PREFERENCES.md"
    "memory/ACTIVE_CONTEXT.md"
    "state/OPEN_TASKS.md"
    "state/KNOWN_GROUPS.md"
)

echo ""
echo "Critical files:"
for f in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$f" ]; then
        fail "MISSING on disk: $f"
    elif [ -z "$(git ls-files "$f")" ]; then
        fail "UNTRACKED: $f"
    else
        pass "$f"
    fi
done

# 5. Secrets not tracked
echo ""
echo "Secrets safety:"
if git ls-files secrets/ | grep -q .; then
    fail "Files inside secrets/ are tracked by git!"
else
    pass "secrets/ not tracked"
fi

if git ls-files .env | grep -q .; then
    fail ".env is tracked by git!"
else
    pass ".env not tracked"
fi

# 6. Unstaged changes
echo ""
DIRTY=$(git diff --name-only | wc -l)
STAGED=$(git diff --cached --name-only | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)

if [ "$DIRTY" -gt 0 ]; then
    warn "$DIRTY file(s) modified but not staged"
fi
if [ "$STAGED" -gt 0 ]; then
    pass "$STAGED file(s) staged for commit"
fi
if [ "$UNTRACKED" -gt 0 ]; then
    warn "$UNTRACKED untracked file(s)"
fi
if [ "$DIRTY" -eq 0 ] && [ "$STAGED" -eq 0 ] && [ "$UNTRACKED" -eq 0 ]; then
    pass "Working tree clean"
fi

# Summary
echo ""
echo "═══════════════════════════════════════"
if [ "$ERRORS" -gt 0 ]; then
    echo -e "${RED}FAIL: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo "Fix errors before pushing."
    exit 1
else
    echo -e "${GREEN}PASS: 0 errors, $WARNINGS warning(s)${NC}"
    echo "Safe to push."
    exit 0
fi
