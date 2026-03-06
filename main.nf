#!/usr/bin/env nextflow

nextflow.enable.dsl = 2

include { COMPLETE_PIPELINE } from './workflows/complete_pipeline'

// Parameter validation
def validateParameters() {
    def valid = true
    def errors = []

    // Validate input mode
    def valid_modes = ['fasta', 'metadata', 'sra_list']
    def input_mode = params.input_mode ?: 'fasta'
    if (!(input_mode in valid_modes)) {
        errors << "Invalid input_mode '${input_mode}'. Must be one of: ${valid_modes.join(', ')}"
        valid = false
    }

    // Validate input file exists (for fasta and sra_list modes)
    if (input_mode in ['fasta', 'sra_list']) {
        if (!params.input) {
            errors << "Parameter --input is required for ${input_mode} mode"
            valid = false
        } else if (!file(params.input).exists()) {
            errors << "Input file not found: ${params.input}"
            valid = false
        }
    }

    // Validate output directory parameter exists
    if (!params.outdir) {
        errors << "Parameter --outdir is required"
        valid = false
    }

    // Print errors and exit if validation failed
    if (!valid) {
        log.error "Parameter validation failed:"
        errors.each { log.error "  - ${it}" }
        System.exit(1)
    }
}

workflow {
    // Validate parameters before starting
    validateParameters()

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
