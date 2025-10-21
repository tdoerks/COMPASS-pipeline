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
    "generate_compass_summary.py"
}
