/*
 * ASSEMBLY SUBWORKFLOW
 * Handles genome assembly from sequencing reads
 */

include { FASTQC } from '../modules/fastqc'
include { FASTP } from '../modules/fastp'
include { READ_QC } from '../modules/read_qc'
include { READ_QC_SUMMARY } from '../modules/read_qc_summary'
include { ASSEMBLE_SPADES } from '../modules/assembly'
include { BUSCO } from '../modules/busco'
include { QUAST } from '../modules/quast'

workflow ASSEMBLY {
    take:
    reads      // channel: [sample_id, reads]
    metadata   // channel: [sample_id, organism] (optional, can be empty)

    main:
    // Quality assessment of raw reads with FastQC
    FASTQC(reads)

    // Quality trim reads with fastp
    FASTP(reads)

    // Quality filter trimmed reads based on fastp output
    // This creates a channel with: [sample_id, trimmed_reads, fastp_json]
    ch_reads_for_qc = FASTP.out.reads.join(FASTP.out.json.map { json -> [json.baseName.replaceAll(/_fastp$/, ''), json] })

    if (!params.skip_read_qc) {
        READ_QC(ch_reads_for_qc)
        ch_reads_pass = READ_QC.out.reads_pass
        ch_read_qc_metrics = READ_QC.out.qc_metrics
        ch_read_qc_failed = READ_QC.out.qc_failed
        ch_read_qc_versions = READ_QC.out.versions

        // Generate Read QC summary report
        READ_QC_SUMMARY(ch_read_qc_metrics.collect())
        ch_read_qc_summary = READ_QC_SUMMARY.out.summary
        ch_read_qc_csv = READ_QC_SUMMARY.out.csv
        ch_read_qc_html = READ_QC_SUMMARY.out.html
    } else {
        // Skip Read QC - use all trimmed reads
        ch_reads_pass = FASTP.out.reads
        ch_read_qc_metrics = Channel.empty()
        ch_read_qc_failed = Channel.empty()
        ch_read_qc_summary = Channel.empty()
        ch_read_qc_csv = Channel.empty()
        ch_read_qc_html = Channel.empty()
        ch_read_qc_versions = Channel.empty()
    }

    // Assemble genomes using reads that passed QC
    ASSEMBLE_SPADES(ch_reads_pass)

    // Quality assessment of assemblies with BUSCO (optional)
    if (!params.skip_busco) {
        BUSCO(ASSEMBLE_SPADES.out.assembly)
        ch_busco_results = BUSCO.out.results
        ch_busco_summary = BUSCO.out.summary
        ch_busco_versions = BUSCO.out.versions
    } else {
        ch_busco_results = Channel.empty()
        ch_busco_summary = Channel.empty()
        ch_busco_versions = Channel.empty()
    }

    // Assembly statistics with QUAST
    QUAST(ASSEMBLE_SPADES.out.assembly)

    // Create meta channel for downstream processes
    // Join with metadata if available, otherwise use Unknown
    ch_metadata_default = ASSEMBLE_SPADES.out.assembly
        .map { sample_id, fasta -> [sample_id, "Unknown"] }

    ch_metadata_combined = metadata
        .mix(ch_metadata_default)
        .unique { it[0] }  // Keep first occurrence (prioritize actual metadata)

    assembly_with_meta = ASSEMBLE_SPADES.out.assembly
        .join(ch_metadata_combined, by: 0)
        .map { sample_id, fasta, organism ->
            def meta = [:]
            meta.id = sample_id
            meta.organism = organism
            [meta, fasta]
        }

    emit:
    assemblies = assembly_with_meta  // channel: [meta, fasta]
    raw_assemblies = ASSEMBLE_SPADES.out.assembly  // channel: [sample_id, fasta]
    fastqc_html = FASTQC.out.html  // channel: path(html)
    fastqc_zip = FASTQC.out.zip  // channel: path(zip)
    fastp_json = FASTP.out.json  // channel: path(json)
    fastp_html = FASTP.out.html  // channel: path(html)
    read_qc_metrics = ch_read_qc_metrics  // channel: path(json) or empty
    read_qc_summary = ch_read_qc_summary  // channel: path(txt) or empty
    read_qc_csv = ch_read_qc_csv  // channel: path(csv) or empty
    read_qc_html = ch_read_qc_html  // channel: path(html) or empty
    busco_results = ch_busco_results  // channel: path(busco_dir) or empty
    busco_summary = ch_busco_summary  // channel: path(summary.txt) or empty
    quast_results = QUAST.out.results  // channel: [sample_id, dir]
    quast_report = QUAST.out.report  // channel: path(report.tsv)
    quast_dirs = QUAST.out.results_dir  // channel: path(dir) for MultiQC
    versions = FASTQC.out.versions.mix(FASTP.out.versions).mix(ch_read_qc_versions).mix(ASSEMBLE_SPADES.out.versions).mix(ch_busco_versions).mix(QUAST.out.versions)
}
