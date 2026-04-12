# Git Publish Workflow

## Before every push

```bash
bash scripts/publish_check.sh
```

This validates:
- Correct branch (`new-architecture`)
- Remote reachable
- No divergence with remote
- All critical architecture files tracked
- No secrets leaked into git
- Working tree state

## Standard publish flow

```bash
# 1. Check state
bash scripts/publish_check.sh

# 2. Stage changes (be specific, not git add -A)
git add <specific files>

# 3. Commit
git commit -m "description of changes"

# 4. Push
git push origin new-architecture
```

## Rules

1. **Never `git add -A` or `git add .`** — always stage specific files
2. **Never commit secrets/** or **.env** files
3. **Always run publish_check.sh before push**
4. **`new-architecture` is the source-of-truth branch**
5. **`master` is frozen** — do not push to master

## If push says "Everything up-to-date"

This means there is nothing new to push. Common causes:
- Changes exist but were not staged (`git add`)
- Changes were staged but not committed (`git commit`)
- The commit already exists on remote

Fix: check `git status` and `git log --oneline -3`

## Emergency: file missing from GitHub after push

```bash
# Verify file is tracked
git ls-files <filename>

# If empty, the file is not tracked. Add it:
git add <filename>
git commit -m "Track missing file: <filename>"
git push origin new-architecture
```
