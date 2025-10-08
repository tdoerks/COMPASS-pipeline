include { DOWNLOAD_NARMS_METADATA; FILTER_NARMS_SAMPLES } from '../modules/metadata_filtering'
include { DOWNLOAD_SRA } from '../modules/sra_download'
include { ASSEMBLE_SPADES } from '../modules/assembly'
include { AMR_PHAGE_ANALYSIS } from './integrated_analysis'

workflow METADATA_TO_RESULTS {
    
    main:
    // Download and filter NARMS metadata
    DOWNLOAD_NARMS_METADATA()
    FILTER_NARMS_SAMPLES(DOWNLOAD_NARMS_METADATA.out.metadata)
    
    // Read filtered metadata to create channel with organism info
    filtered_metadata = FILTER_NARMS_SAMPLES.out.filtered
        .splitCsv(header: true)
        .map { row -> 
            [row.Run, row.organism ?: "Unknown"]
        }
    
    // Convert SRR list to channel
    srr_channel = FILTER_NARMS_SAMPLES.out.srr_list
        .splitText()
        .map { it.trim() }
    
    // Download SRA files
    DOWNLOAD_SRA(srr_channel)
    
    // Assemble genomes
    ASSEMBLE_SPADES(DOWNLOAD_SRA.out.reads)
    
    // Join assembly with organism metadata
    assembly_with_meta = ASSEMBLE_SPADES.out.assembly
        .join(filtered_metadata)
        .map { srr, fasta, organism ->
            def meta = [:]
            meta.id = srr
            meta.organism = organism
            [meta, fasta]
        }
    
    // Run integrated AMR + Phage analysis
    AMR_PHAGE_ANALYSIS(assembly_with_meta)
    
    emit:
    summary = AMR_PHAGE_ANALYSIS.out.summary
    report = AMR_PHAGE_ANALYSIS.out.report
    versions = AMR_PHAGE_ANALYSIS.out.versions
}
