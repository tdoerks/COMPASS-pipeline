/*
 * ========================================================================================
 *  DATA ACQUISITION SUBWORKFLOW
 * ========================================================================================
 *  Handles downloading and filtering of samples from public databases
 *  - NARMS metadata filtering
 *  - SRA data download
 */

include { DOWNLOAD_NARMS_METADATA; FILTER_NARMS_SAMPLES } from '../modules/metadata_filtering'
include { DOWNLOAD_SRA } from '../modules/sra_download'

workflow DATA_ACQUISITION {
    take:
    // No input - uses params for filtering

    main:
    // Download and filter NARMS metadata
    DOWNLOAD_NARMS_METADATA()
    FILTER_NARMS_SAMPLES(DOWNLOAD_NARMS_METADATA.out.metadata)

    // Download SRA data for filtered samples
    DOWNLOAD_SRA(FILTER_NARMS_SAMPLES.out.srr_list)

    emit:
    reads = DOWNLOAD_SRA.out.reads
    filtered_samples = FILTER_NARMS_SAMPLES.out.filtered_csv
    versions = DOWNLOAD_NARMS_METADATA.out.versions
        .mix(FILTER_NARMS_SAMPLES.out.versions)
        .mix(DOWNLOAD_SRA.out.versions)
}
