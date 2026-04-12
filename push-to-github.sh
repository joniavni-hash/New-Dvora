#!/bin/bash
# OpenClaw/Dvorah - Push to GitHub
# Run this script from WSL: bash push-to-github.sh

cd ~/.openclaw/workspace || exit 1

# Configure git
git config user.email "joni.avni@gmail.com"
git config user.name "joniavni-hash"

# Set the remote
git remote remove origin 2>/dev/null
git remote add origin https://joniavni-hash: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@github.com/joniavni-hash/openclaw-dvorah.git

# Stage all files (respecting .gitignore)
git add -A

# Commit
git commit -m "Initial commit: OpenClaw/Dvorah workspace"

# Push
git push -u origin main 2>/dev/null || git push -u origin master 2>/dev/null || {
  # If no branch exists yet, create main
  git checkout -b main
  git push -u origin main
}

echo ""
echo "Done! Check: https://github.com/joniavni-hash/openclaw-dvorah"
