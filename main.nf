#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { COMPLETE_PIPELINE } from './workflows/complete_pipeline'

workflow {
    // Determine input mode based on parameters
    def input_mode = params.input_mode ?: 'fasta'  // Options: 'fasta', 'metadata', 'sra_list'

    if (input_mode == 'fasta') {
        // Read the sample sheet for FASTA input
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
            .set { ch_input }

    } else if (input_mode == 'metadata') {
        // NARMS metadata mode - no input channel needed
        ch_input = Channel.empty()

    } else if (input_mode == 'sra_list') {
        // SRA accession list mode
        // Expected: text file with one SRR accession per line
        Channel
            .fromPath(params.input)
            .splitText()
            .map { it.trim() }
            .set { ch_input }
    }

    // Run the complete pipeline
    COMPLETE_PIPELINE(input_mode, ch_input)
}
