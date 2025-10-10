/*
 * Module to track and report failed samples
 */

process TRACK_FAILURES {
    publishDir "${params.outdir}/pipeline_info", mode: 'copy'

    input:
    path execution_trace

    output:
    path "failed_samples_report.txt", emit: report
    path "failed_samples.csv", emit: csv

    script:
    """
    #!/usr/bin/env python3

import pandas as pd
import re

# Read execution trace
trace = pd.read_csv("${execution_trace}", sep='\\t')

# Identify failed processes
failed = trace[trace['status'] != 'COMPLETED']

# Extract sample IDs from task names
def extract_sample_id(task_name):
    # Try to extract sample ID from various formats
    patterns = [
        r'\\((.+?)\\)',  # (sample_id)
        r':\\s*(.+?)\\s*\$',  # : sample_id
        r'^(.+?)\\s*-',  # sample_id -
    ]
    for pattern in patterns:
        match = re.search(pattern, str(task_name))
        if match:
            return match.group(1)
    return 'unknown'

if len(failed) > 0:
    failed['sample_id'] = failed['name'].apply(extract_sample_id)
    failed['process'] = failed['process']
    failed['exit_code'] = failed['exit']
    failed['error'] = failed['error_action']

    # Create detailed report
    with open('failed_samples_report.txt', 'w') as f:
        f.write("COMPASS Pipeline - Failed Samples Report\\n")
        f.write("=" * 60 + "\\n\\n")
        f.write(f"Total failed tasks: {len(failed)}\\n")
        f.write(f"Unique processes with failures: {failed['process'].nunique()}\\n")
        f.write(f"Unique samples affected: {failed['sample_id'].nunique()}\\n\\n")

        # Group by process
        f.write("Failures by Process:\\n")
        f.write("-" * 60 + "\\n")
        for process, group in failed.groupby('process'):
            f.write(f"\\n{process}: {len(group)} failures\\n")
            for _, row in group.iterrows():
                f.write(f"  - Sample: {row['sample_id']}\\n")
                f.write(f"    Exit code: {row['exit_code']}\\n")
                f.write(f"    Action: {row['error']}\\n")

        # Sample-wise summary
        f.write("\\n\\nFailures by Sample:\\n")
        f.write("-" * 60 + "\\n")
        for sample, group in failed.groupby('sample_id'):
            f.write(f"\\n{sample}:\\n")
            for _, row in group.iterrows():
                f.write(f"  - {row['process']} (exit: {row['exit_code']})\\n")

    # Create CSV
    summary = failed[['sample_id', 'process', 'exit_code', 'error']].copy()
    summary.to_csv('failed_samples.csv', index=False)

else:
    # No failures
    with open('failed_samples_report.txt', 'w') as f:
        f.write("COMPASS Pipeline - Failed Samples Report\\n")
        f.write("=" * 60 + "\\n\\n")
        f.write("No sample failures detected!\\n")
        f.write("All samples completed successfully.\\n")

    # Empty CSV
    pd.DataFrame(columns=['sample_id', 'process', 'exit_code', 'error']).to_csv('failed_samples.csv', index=False)
    """
}
