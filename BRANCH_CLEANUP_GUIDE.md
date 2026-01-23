# Branch Cleanup Guide

**Generated:** January 23, 2026

---

## Current Branch Status

### Active Branches (Keep)

| Branch | Last Updated | Status | Action |
|--------|--------------|--------|--------|
| `v1.3-dev` | 2026-01-23 | **ACTIVE** | Current development, needs testing before merge |
| `analysis` | 2026-01-21 | Active | Analysis scripts branch |
| `main` | 2026-01-16 | **STABLE** | Production branch |
| `v1.2-mod` | 2026-01-16 | Active | Modified v1.2 |

**Decision:** Keep all - actively maintained

---

## Stale Branches (Review for Deletion)

### Recently Stale (1-3 months old)

| Branch | Last Updated | Age | Notes |
|--------|--------------|-----|-------|
| `claude/2025-12-04-1764823117364` | 2025-12-05 | ~50 days | Claude session branch |
| `v1.2-stable` | 2025-11-26 | ~60 days | Superseded by v1.2-mod? |
| `v1.1-stable` | 2025-11-03 | ~80 days | Old stable release |

**Recommendation:** Archive `v1.1-stable` and `v1.2-stable` as git tags, delete branches

### Old Stale (3+ months old)

| Branch | Last Updated | Age | Purpose |
|--------|--------------|-----|---------|
| `v1.0-stable` | 2025-10-30 | ~85 days | Old stable release |
| `v1.0-stable-conf_fix` | 2025-10-30 | ~85 days | Config fix branch |
| `claude-dev-playground` | 2025-10-23 | ~92 days | Testing branch |
| `test-checkv` | 2025-10-11 | ~104 days | Feature test |
| `enhanced-narms-filtering` | 2025-10-10 | ~105 days | Feature branch |
| `add-error-handling` | 2025-10-10 | ~105 days | Feature branch |
| `fix-phanotate-timeout` | 2025-10-10 | ~105 days | Bug fix branch |
| `refactor-module-structure` | 2025-10-10 | ~105 days | Refactoring branch |
| `test-data-profile` | 2025-10-10 | ~105 days | Testing branch |
| `modular-configs` | 2025-10-10 | ~105 days | Feature branch |
| `move-container-references` | 2025-10-10 | ~105 days | Refactoring branch |
| `auto-download-prophage-db` | 2025-10-10 | ~105 days | Feature branch |
| `fix-checkv-database-path` | 2025-10-10 | ~105 days | Bug fix branch |

**Recommendation:** All likely merged or abandoned - safe to delete

### Claude Code Session Branches

| Branch | Last Updated | Notes |
|--------|--------------|-------|
| `claude/2025-10-09-1760034911456` | 2025-10-09 | Old session |
| `claude/2025-10-09-1760049134456` | 2025-10-09 | Old session |
| `claude/2025-10-20-1760935609411` | 2025-10-09 | Old session (wrong date?) |

**Recommendation:** Delete all - session work should be in main/dev branches

---

## Cleanup Actions

### Step 1: Archive Old Stable Releases as Tags

Before deleting old stable branches, preserve them as tags:

```bash
# Archive v1.0-stable
git tag archive/v1.0-stable origin/v1.0-stable
git tag archive/v1.0-stable-conf_fix origin/v1.0-stable-conf_fix
git push origin archive/v1.0-stable archive/v1.0-stable-conf_fix

# Archive v1.1-stable
git tag archive/v1.1-stable origin/v1.1-stable
git push origin archive/v1.1-stable

# Archive v1.2-stable (if not needed)
git tag archive/v1.2-stable origin/v1.2-stable
git push origin archive/v1.2-stable
```

### Step 2: Delete Merged/Abandoned Feature Branches

First, verify they're merged (optional):

```bash
# Check if branch is merged into main
git branch -r --merged origin/main | grep -E "(enhanced-narms|add-error|fix-phanotate)"
```

Then delete:

```bash
# Delete feature branches (likely merged)
git push origin --delete enhanced-narms-filtering
git push origin --delete add-error-handling
git push origin --delete fix-phanotate-timeout
git push origin --delete refactor-module-structure
git push origin --delete modular-configs
git push origin --delete move-container-references
git push origin --delete auto-download-prophage-db
git push origin --delete fix-checkv-database-path

# Delete testing branches
git push origin --delete test-checkv
git push origin --delete test-data-profile
git push origin --delete claude-dev-playground
```

### Step 3: Delete Claude Session Branches

```bash
git push origin --delete claude/2025-10-09-1760034911646
git push origin --delete claude/2025-10-09-1760049134456
git push origin --delete claude/2025-10-20-1760935609411
git push origin --delete claude/2025-12-04-1764823117364
```

### Step 4: Delete Old Stable Branches

```bash
git push origin --delete v1.0-stable
git push origin --delete v1.0-stable-conf_fix
git push origin --delete v1.1-stable
# git push origin --delete v1.2-stable  # Only if v1.2-mod replaces it
```

### Step 5: Clean Up Local Branches

```bash
# Fetch to sync with remote deletions
git fetch --prune

# Delete local tracking branches that no longer exist on remote
git branch -vv | grep ': gone]' | awk '{print $1}' | xargs git branch -d
```

---

## Post-Cleanup Branch Structure

### Final Active Branches

```
main           - Production stable release
v1.3-dev       - Current development (merge after testing)
analysis       - Analysis scripts development
v1.2-mod       - Modified v1.2 (if still needed)
```

### Archived as Tags

```
archive/v1.0-stable
archive/v1.0-stable-conf_fix
archive/v1.1-stable
archive/v1.2-stable (optional)
```

---

## Safe Deletion Checklist

Before deleting any branch, verify:

- [ ] Branch is older than 60 days
- [ ] Branch work is merged OR abandoned
- [ ] No unique commits that need preserving
- [ ] For stable releases: archived as tag first
- [ ] Double-check with: `git log origin/<branch> --oneline -10`

**Conservative approach:** Archive first, delete later

---

## Special Cases to Review Manually

### `analysis` branch (2026-01-21)
- **Status:** Recently active
- **Action:** Keep - likely contains analysis scripts
- **Consider:** Merge to v1.3-dev or keep separate?

### `v1.2-mod` branch (2026-01-16)
- **Status:** Recently active
- **Action:** Keep for now
- **Question:** Does this replace v1.2-stable? If yes, delete v1.2-stable

---

## Execution Plan

**Option A: Conservative (Recommended for now)**
```bash
# Only delete obviously stale branches
git push origin --delete claude/2025-10-09-1760034911646
git push origin --delete claude/2025-10-09-1760049134456
git push origin --delete claude/2025-10-20-1760935609411
git push origin --delete claude/2025-12-04-1764823117364
```

**Option B: Moderate Cleanup**
```bash
# Archive and delete old stable releases
git tag archive/v1.0-stable origin/v1.0-stable
git tag archive/v1.1-stable origin/v1.1-stable
git push origin archive/v1.0-stable archive/v1.1-stable
git push origin --delete v1.0-stable v1.0-stable-conf_fix v1.1-stable

# Delete Claude session branches
git push origin --delete claude/2025-10-09-1760034911646
git push origin --delete claude/2025-10-09-1760049134456
git push origin --delete claude/2025-10-20-1760935609411
git push origin --delete claude/2025-12-04-1764823117364
```

**Option C: Aggressive Cleanup (Before publication)**
```bash
# Everything from Option B plus all merged feature branches
# (Run after verifying they're merged or no longer needed)
```

---

## Notes

- **Before cleanup:** Make sure all important work is in main or v1.3-dev
- **After v1.3-dev merge:** Can delete even more branches
- **For publication:** Aim for clean branch structure (main + maybe 1-2 active dev branches)
- **Git tags preserve history** even after branch deletion

---

**Recommended First Step:** Run Option A (conservative) to clean up Claude session branches, then reassess after v1.3-dev is merged to main.
