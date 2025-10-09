/*
 * DATA ACQUISITION SUBWORKFLOW
 * Handles metadata filtering and SRA download
 */

include { DOWNLOAD_NARMS_METADATA; FILTER_NARMS_SAMPLES } from '../modules/metadata_filtering'
include { DOWNLOAD_SRA } from '../modules/sra_download'

workflow DATA_ACQUISITION {
    take:
    mode  // val: 'metadata' or 'sra_list'
    input_ch  // channel: null (for metadata mode) or val(srr_id) for sra_list mode

    main:
    ch_reads = Channel.empty()
    ch_metadata = Channel.empty()
    ch_versions = Channel.empty()

    if (mode == 'metadata') {
        // Download and filter NARMS metadata
        DOWNLOAD_NARMS_METADATA()
        FILTER_NARMS_SAMPLES(DOWNLOAD_NARMS_METADATA.out.metadata)

        // Create metadata map
        ch_metadata = FILTER_NARMS_SAMPLES.out.filtered
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
        ch_reads = DOWNLOAD_SRA.out.reads

        ch_versions = ch_versions.mix(DOWNLOAD_SRA.out.versions.first())
    } else if (mode == 'sra_list') {
        // Direct SRA download from provided list
        DOWNLOAD_SRA(input_ch)
        ch_reads = DOWNLOAD_SRA.out.reads

        ch_versions = ch_versions.mix(DOWNLOAD_SRA.out.versions.first())
    }

    emit:
    reads = ch_reads           // channel: [sample_id, reads]
    metadata = ch_metadata     // channel: [sample_id, organism]
    versions = ch_versions
}
