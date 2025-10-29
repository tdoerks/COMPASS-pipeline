/*
 * COMPLETE PIPELINE WORKFLOW
 * Main workflow that orchestrates all subworkflows for end-to-end analysis
 */

include { DATA_ACQUISITION } from '../subworkflows/data_acquisition'
include { ASSEMBLY } from '../subworkflows/assembly'
include { AMR_ANALYSIS } from '../subworkflows/amr_analysis'
include { PHAGE_ANALYSIS } from '../subworkflows/phage_analysis'
include { TYPING } from '../subworkflows/typing'
include { MOBILE_ELEMENTS } from '../subworkflows/mobile_elements'
include { COMBINE_RESULTS } from '../modules/combine_results'
include { MULTIQC } from '../modules/multiqc'
include { BUSCO } from '../modules/busco'
include { QUAST } from '../modules/quast'

workflow COMPLETE_PIPELINE {
    take:
    input_mode     // val: 'fasta', 'metadata', or 'sra_list'
    input_data     // channel: depends on mode

    main:
    ch_assemblies = Channel.empty()
    ch_versions = Channel.empty()
    ch_metadata = Channel.empty()

    ch_qc_outputs = Channel.empty()
    ch_has_assembly_qc = false

    if (input_mode == 'fasta') {
        // Direct FASTA input: [meta, fasta]
        // Expected input format from samplesheet: sample, organism, fasta
        ch_assemblies = input_data

        // Run assembly QC on pre-assembled genomes
        // Convert [meta, fasta] to [sample_id, fasta] for QC tools
        ch_assemblies_for_qc = ch_assemblies.map { meta, fasta -> [meta.id, fasta] }

        // BUSCO (optional)
        if (!params.skip_busco) {
            BUSCO(ch_assemblies_for_qc)
            ch_busco_summary = BUSCO.out.summary
            ch_versions = ch_versions.mix(BUSCO.out.versions)
        } else {
            ch_busco_summary = Channel.empty()
        }

        // QUAST
        QUAST(ch_assemblies_for_qc)
        ch_quast_report = QUAST.out.report
        ch_quast_dirs = QUAST.out.results_dir  // Use directories for MultiQC
        ch_versions = ch_versions.mix(QUAST.out.versions)

    } else if (input_mode == 'metadata') {
        // NARMS metadata mode: download metadata, filter, download SRA, assemble
        DATA_ACQUISITION('metadata', Channel.empty())

        // Assemble the downloaded reads
        ASSEMBLY(
            DATA_ACQUISITION.out.reads,
            DATA_ACQUISITION.out.metadata
        )

        ch_assemblies = ASSEMBLY.out.assemblies
        ch_qc_outputs = ASSEMBLY.out
        ch_busco_summary = ASSEMBLY.out.busco_summary
        ch_quast_report = ASSEMBLY.out.quast_report
        ch_quast_dirs = ASSEMBLY.out.quast_dirs  // Use directories for MultiQC
        ch_metadata = DATA_ACQUISITION.out.metadata
        ch_versions = ch_versions.mix(DATA_ACQUISITION.out.versions)
        ch_versions = ch_versions.mix(ASSEMBLY.out.versions.first())

    } else if (input_mode == 'sra_list') {
        // SRA accession list mode: download SRA, assemble
        DATA_ACQUISITION('sra_list', input_data)

        // Assemble the downloaded reads
        ASSEMBLY(
            DATA_ACQUISITION.out.reads,
            Channel.empty()
        )

        ch_assemblies = ASSEMBLY.out.assemblies
        ch_qc_outputs = ASSEMBLY.out
        ch_busco_summary = ASSEMBLY.out.busco_summary
        ch_quast_report = ASSEMBLY.out.quast_report
        ch_quast_dirs = ASSEMBLY.out.quast_dirs  // Use directories for MultiQC
        ch_versions = ch_versions.mix(DATA_ACQUISITION.out.versions)
        ch_versions = ch_versions.mix(ASSEMBLY.out.versions.first())
    }

    // Make assemblies channel reusable for multiple downstream processes
    // Use multiMap to split channel for parallel consumption without batching
    // This allows samples to flow through independently as they complete assembly
    ch_assemblies
        .multiMap { meta, fasta ->
            amr: [meta, fasta]
            phage: [meta, fasta]
            typing: [meta, fasta]
            mobile: [meta, fasta]
        }
        .set { ch_assemblies_split }

    // Run AMR analysis - samples processed as they arrive
    AMR_ANALYSIS(ch_assemblies_split.amr)
    ch_versions = ch_versions.mix(AMR_ANALYSIS.out.versions)

    // Run Phage analysis - samples processed as they arrive
    PHAGE_ANALYSIS(ch_assemblies_split.phage)
    ch_versions = ch_versions.mix(PHAGE_ANALYSIS.out.versions)

    // Run Typing analysis (MLST, serotyping) - samples processed as they arrive
    TYPING(ch_assemblies_split.typing)
    ch_versions = ch_versions.mix(TYPING.out.versions)

    // Run Mobile Elements analysis (plasmids) - samples processed as they arrive
    MOBILE_ELEMENTS(ch_assemblies_split.mobile)
    ch_versions = ch_versions.mix(MOBILE_ELEMENTS.out.versions)

    // Combine all results
    COMBINE_RESULTS(
        AMR_ANALYSIS.out.results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.vibrant_results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.diamond_results.map { it[1] }.collect(),
        AMR_ANALYSIS.out.abricate_summary,
        ch_quast_report.collect().ifEmpty([]),
        ch_busco_summary.collect().ifEmpty([]),
        TYPING.out.mlst_results.map { it[1] }.collect().ifEmpty([]),
        TYPING.out.sistr_results.map { it[1] }.collect().ifEmpty([]),
        ch_metadata.ifEmpty(file('NO_FILE'))
    )
    ch_versions = ch_versions.mix(COMBINE_RESULTS.out.versions)

    // Collect all QC outputs for MultiQC
    ch_multiqc = Channel.empty()

    if (input_mode != 'fasta') {
        // Include read QC when we assembled from reads
        ch_multiqc = ch_multiqc
            .mix(ch_qc_outputs.fastqc_html.collect().ifEmpty([]))
            .mix(ch_qc_outputs.fastp_json.collect().ifEmpty([]))
    }

    // Always include assembly QC (BUSCO and QUAST)
    // Use QUAST directories instead of individual report.tsv files to avoid name collisions
    ch_multiqc = ch_multiqc
        .mix(ch_busco_summary.collect().ifEmpty([]))
        .mix(ch_quast_dirs.collect().ifEmpty([]))

    // Run MultiQC to aggregate all QC reports
    MULTIQC(ch_multiqc.collect())
    ch_versions = ch_versions.mix(MULTIQC.out.versions)
    ch_multiqc_report = MULTIQC.out.report

    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
    amr_results = AMR_ANALYSIS.out.results
    phage_results = PHAGE_ANALYSIS.out.vibrant_results
    diamond_results = PHAGE_ANALYSIS.out.diamond_results
    checkv_results = PHAGE_ANALYSIS.out.checkv_results
    phanotate_results = PHAGE_ANALYSIS.out.phanotate_results
    mlst_results = TYPING.out.mlst_results
    sistr_results = TYPING.out.sistr_results
    mobsuite_results = MOBILE_ELEMENTS.out.mobsuite_results
    plasmids = MOBILE_ELEMENTS.out.plasmids
    multiqc_report = ch_multiqc_report
    versions = ch_versions.unique()
}
