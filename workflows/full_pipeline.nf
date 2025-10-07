include { DOWNLOAD_SRA } from '../modules/sra_download'
include { ASSEMBLE_SPADES } from '../modules/assembly'
include { AMRFINDER; DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'
include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { CHECKV } from '../modules/checkv'
include { PHANOTATE } from '../modules/phanotate'
include { COMBINE_RESULTS } from '../modules/combine_results'

workflow FULL_PIPELINE {
    take:
    srr_accessions  // channel: val(srr_id)

    main:
    // Download databases
    DOWNLOAD_AMRFINDER_DB()
    DOWNLOAD_PROPHAGE_DB()

    // Download reads from SRA
    DOWNLOAD_SRA(srr_accessions)

    // Assemble genomes
    ASSEMBLE_SPADES(DOWNLOAD_SRA.out.reads)

    // Create meta channel for downstream processes
    // Add organism info (you'll need to determine this from metadata)
    assembly_meta = ASSEMBLE_SPADES.out.assembly
        .map { srr, fasta -> 
            def meta = [:]
            meta.id = srr
            meta.organism = "Salmonella"  // TODO: get from metadata
            [meta, fasta]
        }

    // Run AMR analysis
    AMRFINDER(assembly_meta, DOWNLOAD_AMRFINDER_DB.out.db)

    // Run Phage analysis
    VIBRANT(ASSEMBLE_SPADES.out.assembly)
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    CHECKV(VIBRANT.out.phages)
    PHANOTATE(VIBRANT.out.phages)

    // Combine results
    COMBINE_RESULTS(
        VIBRANT.out.results.map { it[1] }.collect(),
        DIAMOND_PROPHAGE.out.results.map { it[1] }.collect()
    )

    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
}
