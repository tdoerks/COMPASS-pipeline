/*
 * ========================================================================================
 *  ANTIMICROBIAL RESISTANCE ANALYSIS SUBWORKFLOW
 * ========================================================================================
 *  Comprehensive AMR detection and characterization
 *  - AMRFinder+ for resistance gene detection
 *  - Point mutation identification
 *  - Database management
 */

include { DOWNLOAD_AMRFINDER_DB; AMRFINDER } from '../modules/amrfinder'

workflow AMR_ANALYSIS {
    take:
    samples  // channel: [meta, fasta]

    main:
    // Download/prepare AMRFinder database
    DOWNLOAD_AMRFINDER_DB()

    // Run AMR analysis
    AMRFINDER(samples, DOWNLOAD_AMRFINDER_DB.out.db)

    emit:
    results = AMRFINDER.out.results
    mutations = AMRFINDER.out.mutations
    versions = DOWNLOAD_AMRFINDER_DB.out.versions
        .mix(AMRFINDER.out.versions)
}
