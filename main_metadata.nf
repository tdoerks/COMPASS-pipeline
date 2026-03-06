#!/usr/bin/env nextflow
nextflow.enable.dsl = 2

include { METADATA_TO_RESULTS } from './workflows/metadata_to_results'

workflow {
    METADATA_TO_RESULTS()
}

workflow.onComplete {
    if (params.email) {
        def subject = "COMPASS Pipeline ${workflow.success ? 'Completed' : 'Failed'}: ${workflow.runName}"
        def body = """
Pipeline execution summary:
---------------------------
Run name: ${workflow.runName}
Success: ${workflow.success}
Exit status: ${workflow.exitStatus}
Duration: ${workflow.duration}
Work directory: ${workflow.workDir}
Results directory: ${params.outdir}

Command line: ${workflow.commandLine}
"""
        sendMail(
            to: params.email,
            subject: subject,
            body: body
        )
    }
}
