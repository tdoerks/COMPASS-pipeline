/*
 * TYPING SUBWORKFLOW
 * Handles strain typing and characterization
 */

include { MLST } from '../modules/mlst'

workflow TYPING {
    take:
    assemblies  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Transform channel for MLST: handle both meta and non-meta input formats
    mlst_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            // Input is [meta, fasta]
            return [item[0].id, item[1]]
        } else {
            // Input is already [sample_id, fasta]
            return item
        }
    }

    // Run MLST for strain typing
    MLST(mlst_input)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(MLST.out.versions.first())

    emit:
    mlst_results = MLST.out.results  // channel: [sample_id, tsv]
    versions = ch_versions
}
