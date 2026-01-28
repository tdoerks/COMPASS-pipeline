/*
 * AMRFinderPlus on Prophage Sequences
 *
 * Runs AMRFinderPlus directly on prophage sequences identified by VIBRANT
 * to detect antimicrobial resistance genes carried by prophages.
 *
 * This complements whole-genome AMR analysis by specifically identifying
 * which AMR genes are located within prophage regions.
 */

process AMRFINDER_PROPHAGE {
    tag "$sample_id"
    publishDir "${params.outdir}/amrfinder_prophage", mode: 'copy'
    container = 'staphb/ncbi-amrfinderplus:latest'

    input:
    tuple val(sample_id), path(prophage_fasta)
    path(amrfinder_db)

    output:
    tuple val(sample_id), path("${sample_id}_prophage_amr.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    # Check if prophage file contains sequences
    if [ -s ${prophage_fasta} ] && grep -q '^>' ${prophage_fasta}; then
        # Run AMRFinderPlus on prophage sequences
        amrfinder \\
            --nucleotide ${prophage_fasta} \\
            --database ${amrfinder_db} \\
            --output ${sample_id}_prophage_amr.tsv \\
            --threads ${task.cpus} \\
            --plus
    else
        # No prophages found - create empty results file with AMRFinder header
        echo -e "Protein identifier\\tContig id\\tStart\\tStop\\tStrand\\tGene symbol\\tSequence name\\tScope\\tElement type\\tElement subtype\\tClass\\tSubclass\\tMethod\\tTarget length\\tReference sequence length\\t% Coverage of reference sequence\\t% Identity to reference sequence\\tAlignment length\\tAccession of closest sequence\\tName of closest sequence\\tHMM id\\tHMM description" > ${sample_id}_prophage_amr.tsv
    fi

    # Create versions file
    echo '"AMRFINDER_PROPHAGE": {"version": "ncbi-amrfinderplus-latest"}' > versions.yml
    """
}
