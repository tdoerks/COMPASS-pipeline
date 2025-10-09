include { AMRFINDER; DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'
include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { CHECKV } from '../modules/checkv'  // COMMENTED OUT FOR TESTING
include { PHANOTATE } from '../modules/phanotate'
include { COMBINE_RESULTS } from '../modules/combine_results'

workflow AMR_PHAGE_ANALYSIS {
    take:
    samples  // channel: [meta, fasta]

    main:
    // Download/prepare databases
    DOWNLOAD_AMRFINDER_DB()
    DOWNLOAD_PROPHAGE_DB()

    // Run AMR analysis
    AMRFINDER(samples, DOWNLOAD_AMRFINDER_DB.out.db)

    // Transform channel for VIBRANT: [meta, fasta] -> [sample_id, fasta]
    vibrant_input = samples.map { meta, fasta -> [meta.id, fasta] }

    // Run Phage analysis
    VIBRANT(vibrant_input)
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    CHECKV(VIBRANT.out.phages)  // COMMENTED OUT FOR TESTING
    PHANOTATE(VIBRANT.out.phages)

    // Combine all results (without CheckV for now)
    COMBINE_RESULTS(
        AMRFINDER.out.results.map { it[1] }.collect(),
        VIBRANT.out.results.map { it[1] }.collect(),
        DIAMOND_PROPHAGE.out.results.map { it[1] }.collect()
    )

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(AMRFINDER.out.versions.first())
    ch_versions = ch_versions.mix(VIBRANT.out.versions.first())
    ch_versions = ch_versions.mix(DIAMOND_PROPHAGE.out.versions.first())
    ch_versions = ch_versions.mix(CHECKV.out.versions.first())  // COMMENTED OUT
    ch_versions = ch_versions.mix(PHANOTATE.out.versions.first())
    ch_versions = ch_versions.mix(COMBINE_RESULTS.out.versions)

    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
    versions = ch_versions
}
