/*
 * AMR ANALYSIS SUBWORKFLOW
 * Handles antimicrobial resistance gene detection
 */

include { AMRFINDER; DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'
include { ABRICATE; ABRICATE_SUMMARY } from '../modules/abricate'

workflow AMR_ANALYSIS {
    take:
    assemblies  // channel: [meta, fasta]

    main:
    // Download/prepare AMRFinder database
    DOWNLOAD_AMRFINDER_DB()

    // Run AMRFinder
    AMRFINDER(assemblies, DOWNLOAD_AMRFINDER_DB.out.db)

    // Transform channel for ABRicate: [meta, fasta] -> [sample_id, fasta]
    abricate_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            return [item[0].id, item[1]]
        } else {
            return item
        }
    }

    // Run ABRicate against multiple databases
    db_list = params.abricate_dbs.split(',').collect { it.trim() }
    ABRICATE(abricate_input, db_list)

    // Create summary across all databases
    ABRICATE_SUMMARY(ABRICATE.out.results.map { it[2] }.collect())

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(AMRFINDER.out.versions.first())
    ch_versions = ch_versions.mix(ABRICATE.out.versions.first())

    emit:
    amrfinder_results = AMRFINDER.out.results       // channel: [meta, results]
    abricate_results = ABRICATE.out.results         // channel: [sample_id, db, results]
    abricate_summary = ABRICATE_SUMMARY.out.summary // channel: path(summary)
    results = AMRFINDER.out.results                 // Maintain backward compatibility
    versions = ch_versions
}
