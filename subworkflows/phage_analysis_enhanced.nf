/*
 * Enhanced Phage Analysis Subworkflow
 *
 * Includes multiple prophage detection approaches:
 * 1. VIBRANT - Quick prophage prediction (existing)
 * 2. PHASTER/PhiSpy - More accurate prophage boundaries
 * 3. viralFlye - De novo viral genome assembly from reads
 * 4. viralVerify - Viral contig classification
 */

include { VIBRANT } from '../modules/vibrant'
include { PHASTER } from '../modules/phaster'
include { VIRALFLYE; VIRALVERIFY; EXTRACT_VIRAL_CONTIGS } from '../modules/viralflye'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'

workflow PHAGE_ANALYSIS_ENHANCED {
    take:
    assemblies  // Channel: [sample_id, assembly.fasta]
    reads       // Channel: [sample_id, reads.fastq] - for viralFlye

    main:
    // Download databases
    DOWNLOAD_PROPHAGE_DB()

    // Transform channel for VIBRANT
    vibrant_input = assemblies.map { item ->
        if (item[0] instanceof Map) {
            [item[0].id, item[1]]
        } else {
            item
        }
    }

    // === Approach 1: VIBRANT (existing, fast) ===
    VIBRANT(vibrant_input)

    // === Approach 2: PHASTER/PhiSpy (more accurate from assemblies) ===
    if (params.run_phaster) {
        PHASTER(vibrant_input)
    }

    // === Approach 3: viralFlye (de novo viral assembly from reads) ===
    if (params.run_viralflye) {
        // Transform reads channel if needed
        viral_reads = reads.map { item ->
            if (item[0] instanceof Map) {
                [item[0].id, item[1]]
            } else {
                item
            }
        }

        VIRALFLYE(viral_reads)
        VIRALVERIFY(VIRALFLYE.out.assembly)

        // Combine assembly and viralVerify results
        combined = VIRALFLYE.out.assembly
            .join(VIRALVERIFY.out.results)

        EXTRACT_VIRAL_CONTIGS(combined)
    }

    // Run DIAMOND prophage analysis on VIBRANT results
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)

    emit:
    vibrant_results = VIBRANT.out.results
    vibrant_phages = VIBRANT.out.phages
    phaster_results = params.run_phaster ? PHASTER.out.results : Channel.empty()
    viralflye_results = params.run_viralflye ? VIRALFLYE.out.results : Channel.empty()
    viral_contigs = params.run_viralflye ? EXTRACT_VIRAL_CONTIGS.out.viral_contigs : Channel.empty()
}
