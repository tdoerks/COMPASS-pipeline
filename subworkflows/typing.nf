/*
 * TYPING SUBWORKFLOW
 * Handles strain typing and characterization
 */

include { MLST } from '../modules/mlst'
include { SISTR } from '../modules/sistr'
include { VALIDATE_SPECIES } from '../modules/validate_species'
include { SUMMARIZE_SPECIES_VALIDATION } from '../modules/summarize_species_validation'

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

    // Validate species: compare metadata organism to MLST scheme
    // Join MLST results with organism metadata
    validation_input = MLST.out.results.join(
        typing_input.map { sample_id, fasta, organism -> [sample_id, organism] }
    )
    VALIDATE_SPECIES(validation_input)

    // Summarize all validation results
    SUMMARIZE_SPECIES_VALIDATION(VALIDATE_SPECIES.out.results.collect())

    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(MLST.out.versions.first())
    ch_versions = ch_versions.mix(SISTR.out.versions.first().ifEmpty([]))
    ch_versions = ch_versions.mix(VALIDATE_SPECIES.out.versions.first().ifEmpty([]))
    ch_versions = ch_versions.mix(SUMMARIZE_SPECIES_VALIDATION.out.versions.first().ifEmpty([]))

    emit:
    mlst_results = MLST.out.results                         // channel: [sample_id, tsv]
    sistr_results = SISTR.out.results                       // channel: [sample_id, tsv]
    species_validation = VALIDATE_SPECIES.out.results       // channel: [sample_id, tsv]
    validation_summary = SUMMARIZE_SPECIES_VALIDATION.out.summary  // path: summary.tsv
    validation_mismatches = SUMMARIZE_SPECIES_VALIDATION.out.mismatches  // path: mismatches.tsv
    versions = ch_versions
}
