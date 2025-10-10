/*
 * ========================================================================================
 *  COMPASS: COmprehensive Mobile element & Pathogen ASsessment Suite
 * ========================================================================================
 *  Main workflow for integrated bacterial genomic analysis
 *  Combines AMR detection and phage characterization
 */

include { AMR_ANALYSIS } from '../subworkflows/amr_analysis'
include { PHAGE_ANALYSIS } from '../subworkflows/phage_analysis'
include { COMBINE_RESULTS } from '../modules/combine_results'

workflow COMPASS {
    take:
    samples  // channel: [meta, fasta]

    main:
    // Run AMR analysis
    AMR_ANALYSIS(samples)

    // Transform channel for VIBRANT: [meta, fasta] -> [sample_id, fasta]
    vibrant_input = samples.map { meta, fasta -> [meta.id, fasta] }

    // Run phage analysis
    PHAGE_ANALYSIS(vibrant_input)

    // Combine all results
    COMBINE_RESULTS(
        AMR_ANALYSIS.out.results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.vibrant_results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.diamond_results.map { it[1] }.collect(),
        PHAGE_ANALYSIS.out.checkv_results.map { it[1] }.collect()
    )

    // Collect all versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(AMR_ANALYSIS.out.versions)
    ch_versions = ch_versions.mix(PHAGE_ANALYSIS.out.versions)
    ch_versions = ch_versions.mix(COMBINE_RESULTS.out.versions)

    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
    amr_results = AMR_ANALYSIS.out.results
    phage_results = PHAGE_ANALYSIS.out.phages
    versions = ch_versions
}
