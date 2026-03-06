process BUSCO_QC {
    tag "$sample_id"
    publishDir "${params.outdir}/busco_qc", mode: 'copy'
    container = 'quay.io/biocontainers/python:3.9'

    input:
    tuple val(sample_id), path(busco_summary)

    output:
    tuple val(sample_id), path("${sample_id}_busco_qc.json"), emit: qc_pass
    path "${sample_id}_busco_qc.json", emit: qc_metrics
    path "${sample_id}.busco_qc_failed.txt", optional: true, emit: qc_failed

    script:
    """
    #!/usr/bin/env python3
    import json
    import re
    from pathlib import Path

    # BUSCO QC thresholds (configurable via params)
    MAX_DUPLICATED_PCT = ${params.busco_qc_max_duplicated ?: 5.0}    # Max % duplicated BUSCOs (contamination)
    MIN_COMPLETE_PCT = ${params.busco_qc_min_complete ?: 80.0}       # Min % complete BUSCOs (quality)
    MAX_FRAGMENTED_PCT = ${params.busco_qc_max_fragmented ?: 10.0}   # Max % fragmented BUSCOs
    MAX_MISSING_PCT = ${params.busco_qc_max_missing ?: 20.0}         # Max % missing BUSCOs

    def parse_busco_summary(summary_file):
        \"\"\"Parse BUSCO short_summary.txt file\"\"\"
        stats = {}

        with open(summary_file) as f:
            content = f.read()

        # Extract results line by line
        # Format: "C:95.2%[S:94.1%,D:1.1%],F:2.3%,M:2.5%,n:124"
        results_match = re.search(r'C:([\\d.]+)%\\[S:([\\d.]+)%,D:([\\d.]+)%\\],F:([\\d.]+)%,M:([\\d.]+)%,n:(\\d+)', content)

        if results_match:
            complete_pct = float(results_match.group(1))
            complete_single_pct = float(results_match.group(2))
            duplicated_pct = float(results_match.group(3))
            fragmented_pct = float(results_match.group(4))
            missing_pct = float(results_match.group(5))
            total_buscos = int(results_match.group(6))

            stats = {
                'complete_pct': complete_pct,
                'complete_single_pct': complete_single_pct,
                'duplicated_pct': duplicated_pct,
                'fragmented_pct': fragmented_pct,
                'missing_pct': missing_pct,
                'total_buscos': total_buscos,
                'complete_count': int(complete_pct * total_buscos / 100),
                'duplicated_count': int(duplicated_pct * total_buscos / 100),
                'fragmented_count': int(fragmented_pct * total_buscos / 100),
                'missing_count': int(missing_pct * total_buscos / 100)
            }

        # Extract lineage info
        lineage_match = re.search(r'lineage is: (\\S+)', content)
        if lineage_match:
            stats['lineage'] = lineage_match.group(1)

        return stats if stats else None

    def check_busco_qc(stats):
        \"\"\"Check if assembly passes BUSCO QC thresholds\"\"\"
        failures = []
        warnings = []

        # CRITICAL: High duplication suggests contamination
        if stats['duplicated_pct'] > MAX_DUPLICATED_PCT:
            failures.append(
                f"High duplication: {stats['duplicated_pct']:.1f}% > {MAX_DUPLICATED_PCT}% "
                f"({stats['duplicated_count']}/{stats['total_buscos']} BUSCOs) - possible contamination"
            )

        # High duplication but not critical (warning threshold)
        elif stats['duplicated_pct'] > MAX_DUPLICATED_PCT * 0.6:
            warnings.append(
                f"Moderate duplication: {stats['duplicated_pct']:.1f}% "
                f"({stats['duplicated_count']}/{stats['total_buscos']} BUSCOs)"
            )

        # Low completeness suggests poor quality or wrong organism
        if stats['complete_pct'] < MIN_COMPLETE_PCT:
            failures.append(
                f"Low completeness: {stats['complete_pct']:.1f}% < {MIN_COMPLETE_PCT}% "
                f"({stats['complete_count']}/{stats['total_buscos']} BUSCOs) - poor assembly or wrong lineage"
            )

        # High fragmentation suggests assembly issues
        if stats['fragmented_pct'] > MAX_FRAGMENTED_PCT:
            warnings.append(
                f"High fragmentation: {stats['fragmented_pct']:.1f}% > {MAX_FRAGMENTED_PCT}% "
                f"({stats['fragmented_count']}/{stats['total_buscos']} BUSCOs) - fragmented assembly"
            )

        # High missing rate
        if stats['missing_pct'] > MAX_MISSING_PCT:
            failures.append(
                f"Too many missing BUSCOs: {stats['missing_pct']:.1f}% > {MAX_MISSING_PCT}% "
                f"({stats['missing_count']}/{stats['total_buscos']} BUSCOs)"
            )

        return len(failures) == 0, failures, warnings

    # Run BUSCO QC
    summary_file = Path("${busco_summary}")
    sample = "${sample_id}"

    if not summary_file.exists():
        # BUSCO summary doesn't exist
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'BUSCO summary file not found',
            'stats': None
        }

        with open(f"{sample}.busco_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: BUSCO summary file not found\\n")

        with open(f"{sample}_busco_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)

    # Parse BUSCO summary
    stats = parse_busco_summary(summary_file)

    if stats is None:
        # Failed to parse BUSCO results
        result = {
            'sample': sample,
            'qc_status': 'FAILED',
            'reason': 'Failed to parse BUSCO summary',
            'stats': None
        }

        with open(f"{sample}.busco_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED\\n")
            f.write(f"Reason: Failed to parse BUSCO summary\\n")

        with open(f"{sample}_busco_qc.json", 'w') as f:
            json.dump(result, f, indent=2)

        exit(1)

    # Check QC thresholds
    qc_pass, failures, warnings = check_busco_qc(stats)

    # Determine status: PASS, WARN (has warnings but no failures), or FAILED
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
            'max_duplicated_pct': MAX_DUPLICATED_PCT,
            'min_complete_pct': MIN_COMPLETE_PCT,
            'max_fragmented_pct': MAX_FRAGMENTED_PCT,
            'max_missing_pct': MAX_MISSING_PCT
        }
    }

    if failures:
        result['qc_failures'] = failures
    if warnings:
        result['qc_warnings'] = warnings

    # Create detailed report for failures
    if status == 'FAILED':
        with open(f"{sample}.busco_qc_failed.txt", 'w') as f:
            f.write(f"Sample: {sample}\\n")
            f.write(f"Status: FAILED (contamination/quality issues)\\n")
            f.write(f"\\nBUSCO Statistics:\\n")
            f.write(f"  Lineage: {stats.get('lineage', 'Unknown')}\\n")
            f.write(f"  Complete: {stats['complete_pct']:.1f}% ({stats['complete_count']}/{stats['total_buscos']})\\n")
            f.write(f"  Single-copy: {stats['complete_single_pct']:.1f}%\\n")
            f.write(f"  Duplicated: {stats['duplicated_pct']:.1f}% ({stats['duplicated_count']}/{stats['total_buscos']})\\n")
            f.write(f"  Fragmented: {stats['fragmented_pct']:.1f}% ({stats['fragmented_count']}/{stats['total_buscos']})\\n")
            f.write(f"  Missing: {stats['missing_pct']:.1f}% ({stats['missing_count']}/{stats['total_buscos']})\\n")
            f.write(f"\\nQC Failures:\\n")
            for failure in failures:
                f.write(f"  ❌ {failure}\\n")
            if warnings:
                f.write(f"\\nAdditional Warnings:\\n")
                for warning in warnings:
                    f.write(f"  ⚠️  {warning}\\n")

    # Write QC metrics
    with open(f"{sample}_busco_qc.json", 'w') as f:
        json.dump(result, f, indent=2)

    # Print summary
    print(f"\\n{'='*60}")
    print(f"BUSCO QC: {sample}")
    print(f"{'='*60}")
    print(f"Status: {status}")
    print(f"Lineage: {stats.get('lineage', 'Unknown')}")
    print(f"Complete: {stats['complete_pct']:.1f}% ({stats['complete_count']}/{stats['total_buscos']})")
    print(f"  Single-copy: {stats['complete_single_pct']:.1f}%")
    print(f"  Duplicated: {stats['duplicated_pct']:.1f}% ({stats['duplicated_count']}/{stats['total_buscos']})")
    print(f"Fragmented: {stats['fragmented_pct']:.1f}% ({stats['fragmented_count']}/{stats['total_buscos']})")
    print(f"Missing: {stats['missing_pct']:.1f}% ({stats['missing_count']}/{stats['total_buscos']})")

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
        exit(1)
    """
}
