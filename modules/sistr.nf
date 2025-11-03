process SISTR {
    tag "$sample_id ($organism)"
    publishDir "${params.outdir}/sistr", mode: 'copy'
    container = 'quay.io/biocontainers/sistr_cmd:1.1.1--pyh864c0ab_2'

    input:
    tuple val(sample_id), path(assembly), val(organism)

    output:
    tuple val(sample_id), path("${sample_id}_sistr.tsv"), emit: results
    tuple val(sample_id), path("${sample_id}_sistr_allele.json"), optional: true, emit: alleles
    path "versions.yml", emit: versions

    when:
    organism =~ /(?i)salmonella/

    script:
    """
    echo "=================================================="
    echo "SISTR Serotyping for Salmonella"
    echo "Sample: ${sample_id}"
    echo "Organism: ${organism}"
    echo "=================================================="

    # Run SISTR for Salmonella serotyping
    # Note: SISTR appends .tab to the output filename
    sistr \\
        --threads ${task.cpus} \\
        --alleles-output ${sample_id}_sistr_allele.json \\
        --output-format tab \\
        --output-prediction ${sample_id}_sistr \\
        ${assembly} || {
            echo "ERROR: SISTR analysis failed for ${sample_id}"
            echo "This is a real failure, not a skip"
            echo "Creating empty output for downstream compatibility"
            echo -e "genome\\tserovar\\tserogroup\\th1\\th2\\to_antigen\\tqc_status" > ${sample_id}_sistr.tsv
            echo -e "${sample_id}\\t-\\t-\\t-\\t-\\t-\\tFAIL" >> ${sample_id}_sistr.tsv
        }

    # SISTR creates .tab extension, rename to .tsv for consistency
    if [ -f "${sample_id}_sistr.tab" ]; then
        mv ${sample_id}_sistr.tab ${sample_id}_sistr.tsv
    fi

    echo '"SISTR": {"sistr_cmd": "1.1.1"}' > versions.yml
    """

    stub:
    """
    echo "SKIPPED: ${sample_id} is ${organism}, not Salmonella"
    echo "This is expected behavior - SISTR only runs on Salmonella samples"

    # Create placeholder for pipeline flow
    echo -e "genome\\tserovar\\tserogroup\\th1\\th2\\to_antigen\\tqc_status" > ${sample_id}_sistr.tsv
    echo -e "${sample_id}\\t-\\t-\\t-\\t-\\t-\\tSKIPPED_NON_SALMONELLA" >> ${sample_id}_sistr.tsv

    echo '"SISTR": {"sistr_cmd": "1.1.1"}' > versions.yml
    """
}
