process READ_QC {
    tag "$sample_id"
    publishDir "${params.outdir}/read_qc", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    tuple val(sample_id), path(trimmed_reads), path(fastp_json)

    output:
    tuple val(sample_id), path(trimmed_reads), emit: reads_pass, optional: true
    path "${sample_id}_read_qc.json", emit: qc_metrics
    path "${sample_id}.read_qc_failed.txt", optional: true, emit: qc_failed

    script:
    """
    #!/usr/bin/env python3
    import json
    from pathlib import Path

    # Read QC thresholds (configurable via params)
    MIN_READS_AFTER_FILTERING = ${params.read_qc_min_reads ?: 100000}
    MIN_BASES_AFTER_FILTERING = ${params.read_qc_min_bases ?: 50000000}  # 50 Mbp
    MIN_Q30_RATE = ${params.read_qc_min_q30_rate ?: 0.7}  # 70% bases Q30+
    MIN_SURVIVAL_RATE = ${params.read_qc_min_survival ?: 0.3}  # 30% reads survive

    def parse_fastp_json(json_file):
        \"\"\"Parse fastp JSON output to extract QC metrics\"\"\"
        with open(json_file) as f:
            data = json.load(f)

        # Extract summary stats
        summary = data.get('summary', {})
        before = summary.get('before_filtering', {})
        after = summary.get('after_filtering', {})

        reads_before = before.get('total_reads', 0)
        reads_after = after.get('total_reads', 0)
        bases_after = after.get('total_bases', 0)
        q30_rate = after.get('q30_rate', 0)

        survival_rate = reads_after / reads_before if reads_before > 0 else 0

        return {
            'reads_before_filtering': reads_before,
            'reads_after_filtering': reads_after,
            'bases_after_filtering': bases_after,
            'q30_rate': q30_rate,
            'survival_rate': survival_rate,
            'read_length_mean': after.get('read1_mean_length', 0)
        }

    def check_read_qc(stats):
        \"\"\"Check if reads pass QC thresholds\"\"\"
        failures = []
        warnings = []

        # Critical: Too few reads after filtering
        if stats['reads_after_filtering'] < MIN_READS_AFTER_FILTERING:
            failures.append(
                f"Too few reads after filtering: {stats['reads_after_filtering']:,} < {MIN_READS_AFTER_FILTERING:,}"
            )

        # Critical: Too few bases for assembly
        if stats['bases_after_filtering'] < MIN_BASES_AFTER_FILTERING:
            failures.append(
                f"Insufficient bases after filtering: {stats['bases_after_filtering']:,} bp < {MIN_BASES_AFTER_FILTERING:,} bp"
            )

        # Warning: Low Q30 rate
        if stats['q30_rate'] < MIN_Q30_RATE:
            warnings.append(
                f"Low Q30 rate: {stats['q30_rate']:.1%} < {MIN_Q30_RATE:.1%}"
            )

        # Warning: Low survival rate (too many reads filtered out)
        if stats['survival_rate'] < MIN_SURVIVAL_RATE:
            warnings.append(
                f"Low read survival rate: {stats['survival_rate']:.1%} < {MIN_SURVIVAL_RATE:.1%}"
            )

        return len(failures) == 0, failures, warnings

    # Run Read QC
    fastp_json = Path("${fastp_json}")
    sample = "${sample_id}"

    if not fastp_json.exists():
        # Fastp JSON doesn't exist
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'Fastp JSON file not found',
            'stats': None
        }

        with open(f"{sample}.read_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: Fastp JSON not found\\n")

        with open(f"{sample}_read_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)

    # Parse fastp stats
    stats = parse_fastp_json(fastp_json)

    if not stats:
        # Failed to parse
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'Failed to parse fastp JSON',
            'stats': None
        }

        with open(f"{sample}.read_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: Failed to parse fastp JSON\\n")

        with open(f"{sample}_read_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)

    # Check QC thresholds
    qc_pass, failures, warnings = check_read_qc(stats)

    # Determine status
    if failures:
        status = 'FAILED'
    elif warnings:
        status = 'WARN'
    else:
        status = 'PASS'

    result = {
        'sample': sample,
        'qc_status': status,
        'stats': stats,
        'thresholds': {
            'min_reads': MIN_READS_AFTER_FILTERING,
            'min_bases': MIN_BASES_AFTER_FILTERING,
            'min_q30_rate': MIN_Q30_RATE,
            'min_survival_rate': MIN_SURVIVAL_RATE
        }
    }

    if failures:
        result['qc_failures'] = failures
    if warnings:
        result['qc_warnings'] = warnings

    # Create failure report
    if status == 'FAILED':
        with open(f"{sample}.read_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED (insufficient read quality/quantity)\\n")
            f.write(f"\\nRead Statistics:\\n")
            f.write(f"  Reads before filtering: {stats['reads_before_filtering']:,}\\n")
            f.write(f"  Reads after filtering: {stats['reads_after_filtering']:,}\\n")
            f.write(f"  Bases after filtering: {stats['bases_after_filtering']:,} bp\\n")
            f.write(f"  Q30 rate: {stats['q30_rate']:.1%}\\n")
            f.write(f"  Survival rate: {stats['survival_rate']:.1%}\\n")
            f.write(f"  Mean read length: {stats['read_length_mean']:.1f} bp\\n")
            f.write(f"\\nQC Failures:\\n")
            for failure in failures:
                f.write(f"  ❌ {failure}\\n")
            if warnings:
                f.write(f"\\nAdditional Warnings:\\n")
                for warning in warnings:
                    f.write(f"  ⚠️  {warning}\\n")

    # Write QC metrics
    with open(f"{sample}_read_qc.json", 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"\\n{'='*60}")
    print(f"Read QC: {sample}")
    print(f"{'='*60}")
    print(f"Status: {status}")
    print(f"Reads before: {stats['reads_before_filtering']:,}")
    print(f"Reads after: {stats['reads_after_filtering']:,}")
    print(f"Bases after: {stats['bases_after_filtering']:,} bp")
    print(f"Q30 rate: {stats['q30_rate']:.1%}")
    print(f"Survival: {stats['survival_rate']:.1%}")

    if failures:
        print(f"\\n❌ QC Failures:")
        for failure in failures:
            print(f"  - {failure}")

    if warnings:
        print(f"\\n⚠️  Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"{'='*60}\\n")

    # Exit with error if failed (for errorStrategy to handle)
    if status == 'FAILED':
        print("Sample FAILED read QC - will not proceed to assembly")
        exit(1)
    else:
        print("Sample PASSED read QC - proceeding to assembly")
    """
}
