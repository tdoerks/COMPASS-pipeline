/*
 * TYPING SUBWORKFLOW
 * Handles strain typing and characterization
 */

include { MLST } from '../modules/mlst'
include { SISTR } from '../modules/sistr'

workflow TYPING {
    take:
    assemblies  // channel: [meta, fasta] or [sample_id, fasta]

    main:
    // Transform channel for typing tools: handle both meta and non-meta input formats
    typing_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            // Input is [meta, fasta] -> [sample_id, fasta, organism]
            return [item[0].id, item[1], item[0].organism ?: "Unknown"]
        } else {
            // Input is already [sample_id, fasta] -> add Unknown organism
            return [item[0], item[1], "Unknown"]
        }
    }

    // Run MLST for strain typing (all organisms)
    mlst_input = typing_input.map { sample_id, fasta, organism -> [sample_id, fasta] }
    MLST(mlst_input)

    // Run SISTR for Salmonella serotyping (conditional on organism)
    SISTR(typing_input)

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(MLST.out.versions.first())
    ch_versions = ch_versions.mix(SISTR.out.versions.first().ifEmpty([]))

    emit:
    mlst_results = MLST.out.results      // channel: [sample_id, tsv]
    sistr_results = SISTR.out.results    // channel: [sample_id, tsv]
    versions = ch_versions
}
