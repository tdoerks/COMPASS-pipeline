/*
 * PHAGE ANALYSIS SUBWORKFLOW
 * Handles prophage detection, annotation, and characterization
 */

include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { CHECKV } from '../modules/checkv'
include { PHANOTATE } from '../modules/phanotate'

workflow PHAGE_ANALYSIS {
    take:
    assemblies  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Download prophage database
    DOWNLOAD_PROPHAGE_DB()

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

    // Run VIBRANT for prophage detection
    VIBRANT(vibrant_input)

    // Run downstream phage analyses
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    CHECKV(VIBRANT.out.phages)
    PHANOTATE(VIBRANT.out.phages)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(VIBRANT.out.versions.first())
    ch_versions = ch_versions.mix(DIAMOND_PROPHAGE.out.versions.first())
    ch_versions = ch_versions.mix(CHECKV.out.versions.first())
    ch_versions = ch_versions.mix(PHANOTATE.out.versions.first())

    emit:
    vibrant_results = VIBRANT.out.results           // channel: [sample_id, results]
    diamond_results = DIAMOND_PROPHAGE.out.results  // channel: [sample_id, results]
    checkv_results = CHECKV.out.results             // channel: [sample_id, results]
    phanotate_results = PHANOTATE.out.results       // channel: [sample_id, results]
    phage_contigs = VIBRANT.out.phages              // channel: [sample_id, fasta]
    versions = ch_versions
}
