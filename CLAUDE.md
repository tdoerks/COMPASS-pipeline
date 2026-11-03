# Claude Code — Session Notes
Last active: 2026-11-03 (session 35)

## Session Start
**Always read `sessions/CURRENT.md` first**, then the relevant project file:
- `sessions/CURRENT.md` — active jobs, immediate next steps
- `sessions/COMPASS.md` — COMPASS-pipeline history, modules, branch map
- `sessions/ARBOR.md` — ARBOR runs, reference builder, known issues
- `sessions/PHINDER.md` — stress test, vConTACT2, pipeline state
- `sessions/OTHER.md` — NARMS, 3D prints, lab tools, misc

## Environment
- WSL Ubuntu-24.04 on Windows (KSU — tylerdoe)
- Claude Code runs inside Docker: `ghcr.io/tdoerks/claude-nextflow:latest`
- Launch: `cd ~/claude-workspace && docker run -it --rm -v "$PWD:/workspace" ghcr.io/tdoerks/claude-nextflow:latest`
- `/workspace` = `~/claude-workspace` on WSL host — only mounted dir, persists across restarts
- Repos: ARBOR `/workspace/ARBOR`, COMPASS `/workspace/COMPASS-pipeline`, PHINDER `/workspace/PHINDER`
- Beocat: `tylerdoe@icr-helios`, scratch `/fastscratch/tylerdoe/`, bulk `/bulk/tylerdoe/`

## GitHub Auth (once per container session)
```bash
mkdir -p ~/.config && ln -s /workspace/.gh-config ~/.config/gh
gh auth setup-git
# If expired: gh auth login → save: cp -r ~/.config/gh /workspace/.gh-config
```

## Key Patterns
- **Beocat paste**: one command per block; lines join on paste; >100 chars get spaces inserted at wrap
- COMPASS log: `tail -f compass*stdout*<JOBID>*` (NOT `slurm-<JOBID>.out`)
- ARBOR log: `tail -f arbor_head_<JOBID>.log`
- Jobs: `squeue -u tylerdoe`
- **ghcr PROTOCOL_ERROR**: `export GODEBUG=http2client=0` then re-pull
- **After scancel of a Nextflow task job**: delete work dir before resubmit (`rm -rf work/<xx>/<hash>*`) — stale `.exitcode` 143 orphans a retry
- Lock file stuck: cancel zombie → `rm -f .nextflow/cache/.../db/LOCK`
- SLURM preemption: resubmit with -resume
- BaseSpace dirs: `chmod -R u+w <dir>` before mv/rm

## Updating these notes
- Active job changes → `sessions/CURRENT.md`
- Project history → relevant `sessions/*.md`
- Say "update session notes" to save progress at end of session
