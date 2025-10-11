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

workflow COMPLETE_PIPELINE {
    take:
    input_mode     // val: 'fasta', 'metadata', or 'sra_list'
    input_data     // channel: depends on mode

    main:
    ch_assemblies = Channel.empty()
    ch_versions = Channel.empty()

    if (input_mode == 'fasta') {
        // Direct FASTA input: [meta, fasta]
        // Expected input format from samplesheet: sample, organism, fasta
        ch_assemblies = input_data

    } else if (input_mode == 'metadata') {
        // NARMS metadata mode: download metadata, filter, download SRA, assemble
        DATA_ACQUISITION('metadata', Channel.empty())

        // Assemble the downloaded reads
        ASSEMBLY(
            DATA_ACQUISITION.out.reads,
            DATA_ACQUISITION.out.metadata
        )

        ch_assemblies = ASSEMBLY.out.assemblies
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
        ch_versions = ch_versions.mix(DATA_ACQUISITION.out.versions)
        ch_versions = ch_versions.mix(ASSEMBLY.out.versions.first())
    }

    // Run AMR analysis
    AMR_ANALYSIS(ch_assemblies)
    ch_versions = ch_versions.mix(AMR_ANALYSIS.out.versions)

    // Run Phage analysis
    PHAGE_ANALYSIS(ch_assemblies)
    ch_versions = ch_versions.mix(PHAGE_ANALYSIS.out.versions)

    // Run Typing analysis (MLST, serotyping)
    TYPING(ch_assemblies)
    ch_versions = ch_versions.mix(TYPING.out.versions)

    // Run Mobile Elements analysis (plasmids)
    MOBILE_ELEMENTS(ch_assemblies)
    ch_versions = ch_versions.mix(MOBILE_ELEMENTS.out.versions)

    // Combine all results
    COMBINE_RESULTS(
        AMR_ANALYSIS.out.results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.vibrant_results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.diamond_results.map { it[1] }.collect()
    )
    ch_versions = ch_versions.mix(COMBINE_RESULTS.out.versions)

    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
    amr_results = AMR_ANALYSIS.out.results
    phage_results = PHAGE_ANALYSIS.out.vibrant_results
    diamond_results = PHAGE_ANALYSIS.out.diamond_results
    checkv_results = PHAGE_ANALYSIS.out.checkv_results
    phanotate_results = PHAGE_ANALYSIS.out.phanotate_results
    mlst_results = TYPING.out.mlst_results
    mobsuite_results = MOBILE_ELEMENTS.out.mobsuite_results
    plasmids = MOBILE_ELEMENTS.out.plasmids
    versions = ch_versions.unique()
}
