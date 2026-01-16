/*
 * ASSEMBLY SUBWORKFLOW
 * Handles genome assembly from sequencing reads
 */

include { FASTQC } from '../modules/fastqc'
include { FASTP } from '../modules/fastp'
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

    // Assemble genomes using trimmed reads
    ASSEMBLE_SPADES(FASTP.out.reads)

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
    busco_results = ch_busco_results  // channel: path(busco_dir) or empty
    busco_summary = ch_busco_summary  // channel: path(summary.txt) or empty
    quast_results = QUAST.out.results  // channel: [sample_id, dir]
    quast_report = QUAST.out.report  // channel: path(report.tsv)
    quast_dirs = QUAST.out.results_dir  // channel: path(dir) for MultiQC
    versions = FASTQC.out.versions.mix(FASTP.out.versions).mix(ASSEMBLE_SPADES.out.versions).mix(ch_busco_versions).mix(QUAST.out.versions)
}
