/*
 * AMR ANALYSIS SUBWORKFLOW
 * Handles antimicrobial resistance gene detection
 */

include { AMRFINDER; DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'

workflow AMR_ANALYSIS {
    take:
    assemblies  // channel: [meta, fasta]

    main:
    // Download/prepare AMRFinder database
    DOWNLOAD_AMRFINDER_DB()

    // Run AMR analysis
    AMRFINDER(assemblies, DOWNLOAD_AMRFINDER_DB.out.db)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(AMRFINDER.out.versions.first())

    emit:
    results = AMRFINDER.out.results    // channel: [meta, results]
    versions = ch_versions
}
