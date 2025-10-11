/*
 * ASSEMBLY SUBWORKFLOW
 * Handles genome assembly from sequencing reads
 */

include { FASTQC } from '../modules/fastqc'
include { FASTP } from '../modules/fastp'
include { ASSEMBLE_SPADES } from '../modules/assembly'
include { BUSCO } from '../modules/busco'

workflow ASSEMBLY {
    take:
    reads      // channel: [sample_id, reads]
    metadata   // channel: [sample_id, organism] (optional, can be empty)

    main:
    // Quality assessment of raw reads with FastQC
    FASTQC(reads)

    // Quality trim reads with fastp
    FASTP(reads)

    // Assemble genomes using trimmed reads
    ASSEMBLE_SPADES(FASTP.out.reads)

    // Quality assessment of assemblies with BUSCO
    BUSCO(ASSEMBLE_SPADES.out.assembly)

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
    fastqc_html = FASTQC.out.html  // channel: path(html)
    fastqc_zip = FASTQC.out.zip  // channel: path(zip)
    fastp_json = FASTP.out.json  // channel: path(json)
    fastp_html = FASTP.out.html  // channel: path(html)
    busco_results = BUSCO.out.results  // channel: path(busco_dir)
    busco_summary = BUSCO.out.summary  // channel: path(summary.txt)
    versions = FASTQC.out.versions.mix(FASTP.out.versions).mix(ASSEMBLE_SPADES.out.versions).mix(BUSCO.out.versions)
}
