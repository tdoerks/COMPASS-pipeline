/*
 * ASSEMBLY SUBWORKFLOW
 * Handles genome assembly from sequencing reads
 */

include { ASSEMBLE_SPADES } from '../modules/assembly'

workflow ASSEMBLY {
    take:
    reads      // channel: [sample_id, reads]
    metadata   // channel: [sample_id, organism] (optional, can be empty)

    main:
    // Assemble genomes
    ASSEMBLE_SPADES(reads)

    // Create meta channel for downstream processes
    // If metadata is provided, join with assemblies
    // Otherwise, create a basic meta map
    if (metadata) {
        assembly_with_meta = ASSEMBLE_SPADES.out.assembly
            .join(metadata)
            .map { sample_id, fasta, organism ->
                def meta = [:]
                meta.id = sample_id
                meta.organism = organism
                [meta, fasta]
            }
    } else {
        assembly_with_meta = ASSEMBLE_SPADES.out.assembly
            .map { sample_id, fasta ->
                def meta = [:]
                meta.id = sample_id
                meta.organism = "Unknown"
                [meta, fasta]
            }
    }

    emit:
    assemblies = assembly_with_meta  // channel: [meta, fasta]
    raw_assemblies = ASSEMBLE_SPADES.out.assembly  // channel: [sample_id, fasta]
    versions = ASSEMBLE_SPADES.out.versions
}
