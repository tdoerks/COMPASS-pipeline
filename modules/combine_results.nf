process COMBINE_RESULTS {
    publishDir "${params.outdir}/summary", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    path amr_results
    path vibrant_results
    path diamond_results
    path abricate_summary, stageAs: 'abricate_summary.tsv'
    path quast_reports
    path busco_summaries
    path mlst_results
    path sistr_results
    path metadata, stageAs: 'sample_metadata.csv'

    output:
    path "combined_analysis_summary.tsv", emit: summary
    path "combined_analysis_report.html", emit: report
    path "versions.yml", emit: versions

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    import glob
    from pathlib import Path

    # Generate combined summary TSV
    print("Generating COMPASS pipeline summary...")

    # Collect AMR results
    amr_files = glob.glob("*.tsv")
    if amr_files:
        print(f"Found {len(amr_files)} AMR result files")

    # Create basic summary
    with open("combined_analysis_summary.tsv", 'w') as f:
        f.write("Pipeline\\tStatus\\n")
        f.write("COMPASS\\tCompleted\\n")

    # Create basic HTML report
    with open("combined_analysis_report.html", 'w') as f:
        f.write('''<!DOCTYPE html>
<html>
<head><title>COMPASS Pipeline Report</title></head>
<body>
<h1>COMPASS Pipeline Report</h1>
<p>Pipeline completed successfully. Use comprehensive_amr_prophage_analysis.py for detailed analysis.</p>
</body>
</html>
''')

    # Versions
    with open("versions.yml", 'w') as f:
        f.write('"COMBINE_RESULTS": {"version": "1.0.0"}\\n')

    print("Summary generation complete!")
    """
}
