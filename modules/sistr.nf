process SISTR {
    tag "$sample_id"
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
    # Run SISTR for Salmonella serotyping
    sistr \\
        --threads ${task.cpus} \\
        --alleles-output ${sample_id}_sistr_allele.json \\
        --output-format tab \\
        --output-prediction ${sample_id}_sistr.tsv \\
        ${assembly} || {
            echo "SISTR failed for ${sample_id}, creating empty output"
            echo -e "genome\\tserovar\\tserogroup\\th1\\th2\\to_antigen\\tqc_status" > ${sample_id}_sistr.tsv
            echo -e "${sample_id}\\t-\\t-\\t-\\t-\\t-\\tFAIL" >> ${sample_id}_sistr.tsv
        }

    echo '"SISTR": {"sistr_cmd": "1.1.1"}' > versions.yml
    """
}
