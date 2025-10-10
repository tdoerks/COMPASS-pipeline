/*
 * ========================================================================================
 *  PHAGE ANALYSIS SUBWORKFLOW
 * ========================================================================================
 *  Comprehensive phage and prophage characterization
 *  - Phage identification with VIBRANT
 *  - Prophage database comparison with DIAMOND
 *  - Quality assessment with CheckV
 *  - Gene prediction with PHANOTATE
 */

include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { CHECKV } from '../modules/checkv'
include { PHANOTATE } from '../modules/phanotate'

workflow PHAGE_ANALYSIS {
    take:
    samples  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Download/prepare prophage database
    DOWNLOAD_PROPHAGE_DB()

    // Prepare CheckV database path as channel
    checkv_db_path = Channel.fromPath(params.checkv_db, checkIfExists: true)

    // Run phage identification
    VIBRANT(samples)

    // Run downstream phage analyses
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    CHECKV(VIBRANT.out.phages, checkv_db_path.collect())
    PHANOTATE(VIBRANT.out.phages)

    emit:
    vibrant_results = VIBRANT.out.results
    phages = VIBRANT.out.phages
    diamond_results = DIAMOND_PROPHAGE.out.results
    checkv_results = CHECKV.out.results
    phanotate_results = PHANOTATE.out.results
    versions = DOWNLOAD_PROPHAGE_DB.out.versions
        .mix(VIBRANT.out.versions)
        .mix(DIAMOND_PROPHAGE.out.versions)
        .mix(CHECKV.out.versions)
        .mix(PHANOTATE.out.versions)
}
