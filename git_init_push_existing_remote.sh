#!/usr/bin/env bash
set -euo pipefail

DEFAULT_BRANCH="main"
REMOTE_NAME="origin"
REMOTE_URL="https://github.com/GeoPilots/geopilot-publisher.git"

# Detect repo directory:
# - If we're already in the repo (contains pyproject.toml or .git or geopilot_publisher/), use "."
# - Else, if ./geopilot-publisher exists, cd into it
if [[ -f "pyproject.toml" || -d ".git" || -d "geopilot_publisher" ]]; then
  REPO_DIR="."
elif [[ -d "geopilot-publisher" ]]; then
  REPO_DIR="geopilot-publisher"
else
  echo "❌ Can't find repo. Run from inside 'geopilot-publisher/' or its parent directory."
  echo "   Current directory: $(pwd)"
  exit 1
fi

cd "$REPO_DIR"

echo "✅ Working directory: $(pwd)"
echo "✅ Using existing remote repo:"
echo "   $REMOTE_URL"
echo ""

# Safety: ensure we won't accidentally commit secrets
if [[ -f "bootstrap/client_secret.json" ]]; then
  echo "⚠️ Found bootstrap/client_secret.json on disk."
  echo "   Good: it should be gitignored. Do NOT commit it."
fi

# Initialize git if needed
if [[ ! -d ".git" ]]; then
  echo "✅ Initializing git repo..."
  git init
fi

# Ensure branch is main
current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo "")"
if [[ "$current_branch" != "$DEFAULT_BRANCH" ]]; then
  if git show-ref --verify --quiet "refs/heads/$DEFAULT_BRANCH"; then
    echo "✅ Switching to existing branch '$DEFAULT_BRANCH'..."
    git checkout "$DEFAULT_BRANCH"
  else
    if [[ "$current_branch" == "master" ]]; then
      echo "✅ Renaming 'master' -> '$DEFAULT_BRANCH'..."
      git branch -m master "$DEFAULT_BRANCH"
    else
      echo "✅ Creating branch '$DEFAULT_BRANCH'..."
      git checkout -b "$DEFAULT_BRANCH"
    fi
  fi
fi

# Ensure artifacts folder exists, keep only .gitkeep tracked
mkdir -p artifacts
touch artifacts/.gitkeep

# Stage & commit (only if needed)
echo "✅ Staging files..."
git add -A

if git diff --cached --quiet; then
  echo "ℹ️ Nothing new to commit."
else
  echo "✅ Creating commit..."
  git commit -m "chore: initialize geopilot publisher repo"
fi

# Set or verify origin
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  existing_url="$(git remote get-url "$REMOTE_NAME")"
  if [[ "$existing_url" != "$REMOTE_URL" ]]; then
    echo "⚠️ Remote '$REMOTE_NAME' already set but does not match:"
    echo "   existing: $existing_url"
    echo "   expected: $REMOTE_URL"
    echo "✅ Updating '$REMOTE_NAME' to expected URL..."
    git remote set-url "$REMOTE_NAME" "$REMOTE_URL"
  else
    echo "✅ Remote '$REMOTE_NAME' already set correctly."
  fi
else
  echo "✅ Setting remote '$REMOTE_NAME'..."
  git remote add "$REMOTE_NAME" "$REMOTE_URL"
fi

# Push main
echo "✅ Pushing '$DEFAULT_BRANCH' to '$REMOTE_NAME'..."
git push -u "$REMOTE_NAME" "$DEFAULT_BRANCH"

echo ""
echo "✅ Done. Repo is now pushed to GitHub:"
echo "   https://github.com/GeoPilots/geopilot-publisher"
echo ""
echo "Next step:"
echo "  Repo → Settings → Secrets and variables → Actions"
echo "  Add: YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN, ELEVENLABS_API_KEY"