#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { METADATA_TO_RESULTS } from './workflows/metadata_to_results'

workflow {
    METADATA_TO_RESULTS()
}
