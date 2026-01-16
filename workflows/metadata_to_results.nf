include { DOWNLOAD_NARMS_METADATA; FILTER_NARMS_SAMPLES } from '../modules/metadata_filtering'
include { DOWNLOAD_SRA } from '../modules/sra_download'
include { ASSEMBLE_SPADES } from '../modules/assembly'
include { ASSEMBLY_QC } from '../modules/assembly_qc'
include { QC_SUMMARY } from '../modules/qc_summary'
include { BUSCO; DOWNLOAD_BUSCO_LINEAGE } from '../modules/busco'
include { BUSCO_QC } from '../modules/busco_qc'
include { BUSCO_QC_SUMMARY } from '../modules/busco_qc_summary'
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

    // Assembly QC (check N50, contigs, length, N content)
    ASSEMBLY_QC(ASSEMBLE_SPADES.out.assembly)

    // BUSCO analysis (genome completeness and contamination detection)
    if (!params.skip_busco) {
        // Download BUSCO lineage if needed
        DOWNLOAD_BUSCO_LINEAGE()

        // Run BUSCO on assemblies that passed initial QC
        BUSCO(ASSEMBLY_QC.out.qc_pass.map { sample_id, assembly, qc_json -> [sample_id, assembly] })

        // BUSCO QC (contamination detection via duplication)
        BUSCO_QC(BUSCO.out.summary.map { summary ->
            def sample_id = summary.getBaseName().replaceAll('_busco.*', '')
            [sample_id, summary]
        })

        // Generate BUSCO QC summary reports
        BUSCO_QC_SUMMARY(BUSCO_QC.out.qc_metrics.collect())

        // Only pass samples that passed BOTH assembly QC and BUSCO QC
        qc_passed_assemblies = ASSEMBLY_QC.out.qc_pass
            .map { sample_id, assembly, qc_json -> [sample_id, assembly] }
            .join(BUSCO_QC.out.qc_pass.map { sample_id, qc_json -> [sample_id, qc_json] })
            .map { sample_id, assembly, busco_qc_json -> [sample_id, assembly] }
    } else {
        // If BUSCO is skipped, only use assembly QC
        qc_passed_assemblies = ASSEMBLY_QC.out.qc_pass
            .map { sample_id, assembly, qc_json -> [sample_id, assembly] }
    }

    // Generate Assembly QC summary reports
    QC_SUMMARY(ASSEMBLY_QC.out.qc_metrics.collect())

    // Join QC-passed assemblies with organism metadata
    assembly_with_meta = qc_passed_assemblies
        .join(filtered_metadata)
        .map { srr, fasta, organism ->
            def meta = [:]
            meta.id = srr
            meta.organism = organism
            [meta, fasta]
        }

    // Run integrated AMR + Phage analysis on clean samples only
    AMR_PHAGE_ANALYSIS(assembly_with_meta)
    
    emit:
    summary = AMR_PHAGE_ANALYSIS.out.summary
    report = AMR_PHAGE_ANALYSIS.out.report
    versions = AMR_PHAGE_ANALYSIS.out.versions
}
