process SUMMARIZE_SPECIES_VALIDATION {
    publishDir "${params.outdir}/species_validation", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path validation_files

    output:
    path "species_validation_summary.tsv", emit: summary
    path "species_mismatches.tsv", emit: mismatches
    path "species_validation_report.txt", emit: report
    path "versions.yml", emit: versions

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    from pathlib import Path
    import sys

    # Collect all validation files
    validation_files = "${validation_files}".split()

    all_results = []
    for vfile in validation_files:
        if Path(vfile).exists():
            df = pd.read_csv(vfile, sep='\\t')
            all_results.append(df)

    if not all_results:
        print("No validation results found!")
        # Create empty outputs
        pd.DataFrame().to_csv('species_validation_summary.tsv', sep='\\t', index=False)
        pd.DataFrame().to_csv('species_mismatches.tsv', sep='\\t', index=False)
        with open('species_validation_report.txt', 'w') as f:
            f.write("No validation results available\\n")
    else:
        combined = pd.concat(all_results, ignore_index=True)

        # Save full summary
        combined.to_csv('species_validation_summary.tsv', sep='\\t', index=False)

        # Save mismatches only
        mismatches = combined[combined['match_status'] == 'MISMATCH']
        mismatches.to_csv('species_mismatches.tsv', sep='\\t', index=False)

        # Generate report
        with open('species_validation_report.txt', 'w') as f:
            f.write("=" * 80 + "\\n")
            f.write("SPECIES VALIDATION REPORT\\n")
            f.write("=" * 80 + "\\n\\n")

            total = len(combined)
            f.write(f"Total samples validated: {total}\\n\\n")

            # Status counts
            f.write("Validation Results:\\n")
            f.write("-" * 80 + "\\n")
            for status in combined['match_status'].value_counts().index:
                count = len(combined[combined['match_status'] == status])
                pct = count / total * 100
                f.write(f"  {status:<20} {count:>6} ({pct:>5.1f}%)\\n")
            f.write("\\n")

            # Mismatch details
            if len(mismatches) > 0:
                f.write("=" * 80 + "\\n")
                f.write(f"⚠️  SPECIES MISMATCHES DETECTED: {len(mismatches)} samples\\n")
                f.write("=" * 80 + "\\n\\n")
                f.write("These samples may be mislabeled in NARMS metadata:\\n\\n")
                f.write(f"{'Sample ID':<20} {'Expected':<20} {'MLST Detected':<20} {'Scheme':<20}\\n")
                f.write("-" * 80 + "\\n")
                for _, row in mismatches.iterrows():
                    f.write(f"{row['sample_id']:<20} {row['expected_organism']:<20} "
                           f"{row['detected_organism']:<20} {row['mlst_scheme']:<20}\\n")
                f.write("\\n")
                f.write("RECOMMENDATION:\\n")
                f.write("  - Review these samples for potential metadata errors\\n")
                f.write("  - Consider excluding from organism-specific analyses\\n")
                f.write("  - Report to NARMS database curators\\n")
            else:
                f.write("✅ No species mismatches detected!\\n")
                f.write("   All samples match their expected organism.\\n")

            f.write("\\n" + "=" * 80 + "\\n")

            # Print to console
            with open('species_validation_report.txt', 'r') as report:
                print(report.read())

    with open('versions.yml', 'w') as f:
        f.write('"SUMMARIZE_SPECIES_VALIDATION": {"pandas": "1.5.2"}\\n')
    """
}
