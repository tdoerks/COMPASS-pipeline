#!/bin/bash
# Batch fix all fastscratch scripts to write SLURM logs to /homes instead of /fastscratch

echo "Fixing all fastscratch SLURM scripts..."
echo "=========================================="
echo ""

# Fix all scripts that have SLURM output directives pointing to /fastscratch
for script in *fastscratch*.sh run_kansas_*.sh; do
    if [ -f "$script" ] && [ "$script" != "fix_fastscratch_scripts.sh" ]; then
        echo "Processing: $script"

        # Check if it has fastscratch output paths
        if grep -q "#SBATCH --output=/fastscratch" "$script"; then
            # Fix output path
            sed -i 's|#SBATCH --output=/fastscratch/tylerdoe/|#SBATCH --output=/homes/tylerdoe/|g' "$script"
            # Fix error path
            sed -i 's|#SBATCH --error=/fastscratch/tylerdoe/|#SBATCH --error=/homes/tylerdoe/|g' "$script"
            echo "  ✅ Fixed SLURM log paths"
        else
            echo "  ⏭️  Already correct or no SLURM directives"
        fi

        # Ensure cd to COMPASS-pipeline (uppercase)
        if grep -q "cd /fastscratch/tylerdoe/compass-pipeline" "$script"; then
            sed -i 's|cd /fastscratch/tylerdoe/compass-pipeline|cd /fastscratch/tylerdoe/COMPASS-pipeline|g' "$script"
            echo "  ✅ Fixed directory name (compass-pipeline → COMPASS-pipeline)"
        fi

        echo ""
    fi
done

echo "=========================================="
echo "All scripts fixed!"
echo ""
echo "Summary of changes:"
echo "  - SLURM logs now write to: /homes/tylerdoe/"
echo "  - Pipeline still runs from: /fastscratch/tylerdoe/COMPASS-pipeline"
echo "  - Results still go to: /fastscratch/tylerdoe/results_*"
echo ""
echo "This fixes the SLURM exit code 53 issue!"
