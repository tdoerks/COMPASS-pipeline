#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

/*
 * ========================================================================================
 *  COMPASS: COmprehensive Mobile element & Pathogen ASsessment Suite
 * ========================================================================================
 *  Main entry point using modular subworkflow structure
 */

include { COMPASS } from './workflows/compass'

workflow {
    // Read the sample sheet
    // Expected columns: sample, organism, fasta
    Channel
        .fromPath(params.input)
        .splitCsv(header:true)
        .map { row ->
            def meta = [:]
            meta.id = row.sample
            meta.organism = row.organism
            return [meta, file(row.fasta)]
        }
        .set { ch_samples }

    COMPASS(ch_samples)
}
