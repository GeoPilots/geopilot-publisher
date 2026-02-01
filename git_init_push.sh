#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="geopilot-publisher"
DEFAULT_BRANCH="main"
REMOTE_NAME="origin"

if [[ ! -d "$REPO_DIR" ]]; then
  echo "❌ Can't find folder '$REPO_DIR' in current directory: $(pwd)"
  echo "   Run this script from the folder that contains '$REPO_DIR/'."
  exit 1
fi

cd "$REPO_DIR"

# Safety: ensure we won't accidentally commit secrets
if [[ -f "bootstrap/client_secret.json" ]]; then
  echo "⚠️ Found bootstrap/client_secret.json on disk."
  echo "   This file must remain gitignored and uncommitted."
fi

# Initialize git if needed
if [[ ! -d ".git" ]]; then
  echo "✅ Initializing git repo..."
  git init
fi

# Ensure branch is main
if git show-ref --verify --quiet "refs/heads/$DEFAULT_BRANCH"; then
  git checkout "$DEFAULT_BRANCH"
else
  # If current branch is master, rename it; otherwise create main
  current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo "")"
  if [[ "$current_branch" == "master" ]]; then
    git branch -m master "$DEFAULT_BRANCH"
  elif [[ -n "$current_branch" && "$current_branch" != "$DEFAULT_BRANCH" ]]; then
    git checkout -b "$DEFAULT_BRANCH"
  else
    git checkout -b "$DEFAULT_BRANCH" || true
  fi
fi

# If user accidentally generated artifacts, keep them out of git (we keep artifacts/.gitkeep only)
mkdir -p artifacts
touch artifacts/.gitkeep

# Stage & commit
echo "✅ Staging files..."
git add -A

if git diff --cached --quiet; then
  echo "ℹ️ Nothing to commit (working tree clean)."
else
  echo "✅ Creating first commit..."
  git commit -m "chore: initialize geopilot publisher repo"
fi

# If origin exists, we can push. If not, create or ask for URL.
if git remote get-url "$REMOTE_NAME" >/dev/null 2>&1; then
  echo "✅ Remote '$REMOTE_NAME' already set:"
  git remote -v
else
  echo "🔧 No remote '$REMOTE_NAME' configured."

  # If gh is available, offer to create repo automatically
  if command -v gh >/dev/null 2>&1; then
    echo "✅ GitHub CLI detected (gh)."
    echo "Do you want me to create the remote GitHub repo now and set origin? (y/n)"
    read -r yn
    if [[ "$yn" =~ ^[Yy]$ ]]; then
      echo "Public or private? (public/private) [private]"
      read -r vis
      vis="${vis:-private}"

      # Create remote repo named after folder
      repo_name="$(basename "$(pwd)")"

      # Create the repo under your currently authenticated GitHub account/org
      echo "✅ Creating GitHub repo '$repo_name' ($vis) and setting origin..."
      gh repo create "$repo_name" --"$vis" --source=. --remote="$REMOTE_NAME" --push

      echo "✅ Done. Remote set and pushed."
      exit 0
    fi
  fi

  echo ""
  echo "Next step: create an empty repo on GitHub (web UI), then paste its URL here."
  echo "Example: https://github.com/<you-or-org>/geopilot-publisher.git"
  echo ""
  echo -n "Paste remote URL: "
  read -r remote_url

  if [[ -z "$remote_url" ]]; then
    echo "❌ No URL provided. Exiting without setting origin."
    exit 1
  fi

  git remote add "$REMOTE_NAME" "$remote_url"
  echo "✅ Set remote '$REMOTE_NAME' to: $remote_url"
fi

# Push
echo "✅ Pushing '$DEFAULT_BRANCH' to '$REMOTE_NAME'..."
git push -u "$REMOTE_NAME" "$DEFAULT_BRANCH"

echo ""
echo "✅ All set."
echo "Next: add GitHub Actions secrets (YT_CLIENT_ID / YT_CLIENT_SECRET / YT_REFRESH_TOKEN / ELEVENLABS_API_KEY) in the repo settings."