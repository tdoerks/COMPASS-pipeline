/*
 * PHAGE ANALYSIS SUBWORKFLOW
 * Handles prophage detection, annotation, and characterization
 */

include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { PHANOTATE } from '../modules/phanotate'
include { AMRFINDER_PROPHAGE } from '../modules/amrfinder_prophage'
include { DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'

workflow PHAGE_ANALYSIS {
    take:
    assemblies  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Download databases
    DOWNLOAD_PROPHAGE_DB()
    DOWNLOAD_AMRFINDER_DB()

    // Transform channel for VIBRANT: [meta, fasta] -> [sample_id, fasta]
    // Handle both meta and non-meta input formats
    vibrant_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            // Input is [meta, fasta]
            return [item[0].id, item[1]]
        } else {
            // Input is already [sample_id, fasta]
            return item
        }
    }

    // Run VIBRANT for prophage detection (includes quality assessment)
    VIBRANT(vibrant_input)

    // Run downstream phage analyses
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    PHANOTATE(VIBRANT.out.phages)
    AMRFINDER_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_AMRFINDER_DB.out.db)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(VIBRANT.out.versions.first())
    ch_versions = ch_versions.mix(DIAMOND_PROPHAGE.out.versions.first())
    ch_versions = ch_versions.mix(PHANOTATE.out.versions.first())
    ch_versions = ch_versions.mix(AMRFINDER_PROPHAGE.out.versions.first())

    emit:
    vibrant_results = VIBRANT.out.results           // channel: [sample_id, results]
    diamond_results = DIAMOND_PROPHAGE.out.results  // channel: [sample_id, results]
    phanotate_results = PHANOTATE.out.results       // channel: [sample_id, results]
    prophage_amr_results = AMRFINDER_PROPHAGE.out.results  // channel: [sample_id, results]
    phage_contigs = VIBRANT.out.phages              // channel: [sample_id, fasta]
    versions = ch_versions
}
