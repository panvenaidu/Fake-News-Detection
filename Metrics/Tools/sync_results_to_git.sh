#!/usr/bin/env bash
# sync_results_to_git.sh — Helper to inspect and stage experiment result changes
#
# PURPOSE:
#   After a Colab training session, this script helps you:
#   1. See which result artifacts have changed
#   2. Stage the appropriate files for commit
#   3. Review what will be committed
#
# USAGE:
#   bash scripts/sync_results_to_git.sh          # Show status only
#   bash scripts/sync_results_to_git.sh --stage   # Stage result/context files
#
# This script does NOT auto-commit or auto-push.
# You must explicitly run 'git commit' and 'git push' after reviewing.
#
# SAFETY:
#   - Will NOT stage large dataset files, images, ZIP archives, or model caches
#   - Will NOT stage files matched by .gitignore
#   - Only stages: results/, context/, work_logs/, collab/, configs/, scripts/, src/
#   - Shows a clear diff summary before you commit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=============================================="
echo "  RESULT SYNC HELPER"
echo "  Project: $(basename "$PROJECT_ROOT")"
echo "  Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=============================================="
echo ""

# 1. Show overall git status
echo "--- Git Status ---"
git status --short
echo ""

# 2. Show changes in result/context directories specifically
echo "--- Changed Result/Context Files ---"
git status --short -- results/ context/ work_logs/ collab/ configs/ scripts/ src/
echo ""

# 3. Check for any large untracked files that should NOT be committed
echo "--- Safety Check: Large Untracked Files (>10MB) ---"
find . -maxdepth 2 -type f -size +10M ! -path './.git/*' ! -path './images/*' ! -path './data/*' 2>/dev/null | while read -r f; do
    SIZE_MB=$(du -m "$f" 2>/dev/null | cut -f1)
    echo "  WARNING: $f (${SIZE_MB}MB) — do NOT commit unless intentional"
done
echo ""

# 4. If --stage flag is passed, stage the safe directories
if [[ "${1:-}" == "--stage" ]]; then
    echo "--- Staging safe directories ---"

    # Stage only the directories that should be committed
    git add --dry-run -- \
        results/ \
        context/ \
        work_logs/ \
        collab/ \
        configs/ \
        scripts/ \
        src/ \
        requirements.txt \
        README.md \
        .gitignore \
        2>/dev/null || true

    echo ""
    echo "Files that would be staged:"
    git diff --cached --stat 2>/dev/null || true
    echo ""

    # Actually stage
    git add -- \
        results/ \
        context/ \
        work_logs/ \
        collab/ \
        configs/ \
        scripts/ \
        src/ \
        requirements.txt \
        README.md \
        .gitignore \
        2>/dev/null || true

    echo "--- Staged. Review with: git diff --cached ---"
    echo ""
    echo "To commit:  git commit -m 'your message here'"
    echo "To push:    git push origin main"
else
    echo "--- Preview mode (no files staged) ---"
    echo "To stage files, run:  bash scripts/sync_results_to_git.sh --stage"
fi

echo ""
echo "--- Reminder ---"
echo "Do NOT commit: images/, data/, *.zip, model checkpoints, __pycache__/"
echo "=============================================="
