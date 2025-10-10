/*
 * ========================================================================================
 *  ASSEMBLY & QC SUBWORKFLOW
 * ========================================================================================
 *  Handles genome assembly and quality control
 *  - De novo assembly with SPAdes
 *  - Future: Assembly QC with CheckM/QUAST
 */

include { ASSEMBLE_SPADES } from '../modules/assembly'

workflow ASSEMBLY_QC {
    take:
    reads  // channel: [meta, [reads]]

    main:
    // Assemble genomes
    ASSEMBLE_SPADES(reads)

    // Future: Add assembly QC steps here
    // QUAST(ASSEMBLE_SPADES.out.assembly)
    // CHECKM(ASSEMBLE_SPADES.out.assembly)

    emit:
    assemblies = ASSEMBLE_SPADES.out.assembly
    versions = ASSEMBLE_SPADES.out.versions
}
