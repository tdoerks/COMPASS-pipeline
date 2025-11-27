# IMPORTANT: Verify Fastscratch Issue Before Using "Fixed" Scripts

## The Claim

The overnight session concluded that **SLURM cannot write output files to `/fastscratch/`** and "fixed" all 17 scripts to write to `/homes/` instead.

## The Problem

**This conclusion may be incorrect!**

There's no clear evidence in the codebase of actual tests that proved SLURM can't write to `/fastscratch/`. We need to verify this before deploying the "fixed" scripts.

## What We Need to Test

### Test 1: Can SLURM Write to /fastscratch?

```bash
cd /fastscratch/tylerdoe/COMPASS-pipeline
sbatch test_fastscratch_output.sh
```

**Watch for:**
- Does the job fail instantly with exit code 53?
- Does it run and create `/fastscratch/tylerdoe/TEST_slurm_JOBID.out`?

### Test 2: Can SLURM Write to /homes?

```bash
sbatch test_homes_output.sh
```

**Watch for:**
- Does this work when /fastscratch doesn't?
- Or do both work?

### Test 3: Check Actual Job That Failed

Look at your actual failed jobs:
```bash
sacct -j 4246768,4246521 --format=JobID,State,ExitCode,Elapsed,NodeList
scontrol show job 4246768  # If still in history
```

**Questions:**
1. What was the **exact** error message?
2. Did it say anything about filesystem permissions?
3. Was `/fastscratch/` mentioned specifically?

## Possible Alternative Explanations

### 1. Directory Didn't Exist
If `/fastscratch/tylerdoe/` didn't exist when SLURM tried to create the output file, you'd get exit code 53.

**Test:**
```bash
ls -ld /fastscratch/tylerdoe/
```

### 2. Permissions Issue
Maybe SLURM can write to /fastscratch but there was a permissions problem with that specific directory.

**Test:**
```bash
ls -la /fastscratch/ | grep tylerdoe
```

### 3. Disk Full
If /fastscratch was full, file creation would fail.

**Test:**
```bash
df -h /fastscratch
```

### 4. /homes Was Actually Full
If /homes was full, even jobs writing there would fail!

**Test:**
```bash
quota -s
df -h /homes/tylerdoe
```

## What to Do

### Before Running the "Fixed" Scripts

1. **Run both test scripts** to see which filesystem actually works
2. **Check the actual error** from your failed jobs
3. **Verify disk space** on both filesystems
4. **Check directory permissions**

### If /fastscratch Actually Works

Then the original scripts were probably fine, and the issue was something else:
- Directory didn't exist
- Disk was full
- Permissions problem
- Different issue entirely

We may have "fixed" a non-existent problem!

### If /fastscratch Really Doesn't Work

Then the fixes are valid. But we should document:
- Why Beocat restricts SLURM this way
- Official documentation about this limitation
- Whether other users have this issue

## Commands to Run on Beocat

```bash
# 1. Navigate to repo
cd /fastscratch/tylerdoe/COMPASS-pipeline

# 2. Pull test scripts
git pull origin v1.2-mod

# 3. Make them executable
chmod +x test_fastscratch_output.sh test_homes_output.sh

# 4. Test fastscratch
sbatch test_fastscratch_output.sh

# 5. Note the job ID, then check result
squeue -u tylerdoe
# Wait a minute, then:
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed

# 6. Test homes
sbatch test_homes_output.sh
sacct -j <JOBID> --format=JobID,State,ExitCode,Elapsed

# 7. Check for output files
ls -lrt /fastscratch/tylerdoe/TEST_slurm_*.out
ls -lrt /homes/tylerdoe/TEST_slurm_*.out

# 8. If fastscratch file exists and has content, SLURM CAN write there!
cat /fastscratch/tylerdoe/TEST_slurm_*.out
```

## Expected Results

### Scenario A: Fastscratch Works Fine
```
/fastscratch/tylerdoe/TEST_slurm_12345.out exists and contains "SLURM CAN write to /fastscratch!"
/homes/tylerdoe/TEST_slurm_12346.out exists and contains "SLURM CAN write to /homes!"
```
**Conclusion:** Original scripts were fine. Issue was something else.

### Scenario B: Only Homes Works
```
Job writing to /fastscratch fails with exit code 0:53
Job writing to /homes succeeds
```
**Conclusion:** Fixes are correct. SLURM really can't write to /fastscratch.

### Scenario C: Both Fail
```
Both jobs fail
```
**Conclusion:** Different problem entirely (disk full, quota exceeded, permissions, etc.)

## Next Steps

**DO NOT assume the "fixes" are correct until you've run these tests!**

The safest approach:
1. Test first
2. Understand the real issue
3. Apply the minimal necessary fix
4. Document what you found

---

**Bottom Line:** We jumped to a conclusion about /fastscratch without solid evidence. Let's verify it properly before using the "fixed" scripts in production.
