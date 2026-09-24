/*
 * PHAGE ANALYSIS SUBWORKFLOW
 * Handles prophage detection, annotation, and characterization
 */

include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { PHANOTATE } from '../modules/phanotate'
include { GENOMAD_PROPHAGE } from '../modules/genomad_prophage'

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

    // Run VIBRANT for prophage detection (includes quality assessment)
    VIBRANT(vibrant_input)

    // Run downstream phage analyses
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    PHANOTATE(VIBRANT.out.phages)

    // Run geNomad on VIBRANT-extracted prophage FASTAs for ICTV taxonomy
    // Empty FASTAs (no prophages detected) are handled gracefully inside the module
    ch_genomad_results = Channel.empty()
    ch_genomad_summaries = Channel.empty()
    if (!params.skip_genomad_prophage) {
        GENOMAD_PROPHAGE(VIBRANT.out.phages)
        ch_genomad_results = GENOMAD_PROPHAGE.out.results
        ch_genomad_summaries = GENOMAD_PROPHAGE.out.virus_summary
    }

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(VIBRANT.out.versions.first())
    ch_versions = ch_versions.mix(DIAMOND_PROPHAGE.out.versions.first())
    ch_versions = ch_versions.mix(PHANOTATE.out.versions.first())
    if (!params.skip_genomad_prophage) {
        ch_versions = ch_versions.mix(GENOMAD_PROPHAGE.out.versions.first())
    }

    emit:
    vibrant_results = VIBRANT.out.results           // channel: [sample_id, results]
    diamond_results = DIAMOND_PROPHAGE.out.results  // channel: [sample_id, results]
    phanotate_results = PHANOTATE.out.results       // channel: [sample_id, results]
    phage_contigs = VIBRANT.out.phages              // channel: [sample_id, fasta]
    genomad_results = ch_genomad_results            // channel: [sample_id, genomad_dir], optional
    genomad_summaries = ch_genomad_summaries        // channel: [sample_id, virus_summary.tsv], optional
    versions = ch_versions
}
