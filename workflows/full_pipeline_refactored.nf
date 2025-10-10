/*
 * ========================================================================================
 *  COMPASS: Full Pipeline Workflow (Refactored)
 * ========================================================================================
 *  Complete workflow from NARMS metadata to final results using subworkflows
 *  Includes data acquisition, assembly, AMR, and phage analysis
 */

include { DATA_ACQUISITION } from '../subworkflows/data_acquisition'
include { ASSEMBLY_QC } from '../subworkflows/assembly_qc'
include { COMPASS } from './compass'

workflow FULL_PIPELINE_REFACTORED {
    main:
    // Download and filter NARMS data
    DATA_ACQUISITION()

    // Assemble genomes
    ASSEMBLY_QC(DATA_ACQUISITION.out.reads)

    // Run integrated AMR and phage analysis
    COMPASS(ASSEMBLY_QC.out.assemblies)

    // Collect all versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(DATA_ACQUISITION.out.versions)
    ch_versions = ch_versions.mix(ASSEMBLY_QC.out.versions)
    ch_versions = ch_versions.mix(COMPASS.out.versions)

    emit:
    summary = COMPASS.out.summary
    report = COMPASS.out.report
    versions = ch_versions
}
