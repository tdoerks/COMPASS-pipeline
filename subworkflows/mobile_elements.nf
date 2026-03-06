/*
 * MOBILE ELEMENTS SUBWORKFLOW
 * Handles plasmid detection and mobile genetic element analysis
 */

include { MOBSUITE_RECON } from '../modules/mobsuite'

workflow MOBILE_ELEMENTS {
    take:
    assemblies  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Transform channel for MOB-suite: handle both meta and non-meta input formats
    mobsuite_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            // Input is [meta, fasta]
            return [item[0].id, item[1]]
        } else {
            // Input is already [sample_id, fasta]
            return item
        }
    }

    // Run MOB-suite for plasmid detection and typing
    MOBSUITE_RECON(mobsuite_input)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(MOBSUITE_RECON.out.versions.first())

    emit:
    mobsuite_results = MOBSUITE_RECON.out.results    // channel: [sample_id, dir]
    plasmids = MOBSUITE_RECON.out.plasmids           // channel: [sample_id, fasta]
    mobtyper = MOBSUITE_RECON.out.mobtyper           // channel: path(txt)
    versions = ch_versions
}
