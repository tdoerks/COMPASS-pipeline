include { AMRFINDER; DOWNLOAD_AMRFINDER_DB } from '../modules/amrfinder'
include { VIBRANT } from '../modules/vibrant'
include { DOWNLOAD_PROPHAGE_DB; DIAMOND_PROPHAGE } from '../modules/diamond_prophage'
include { CHECKV } from '../modules/checkv'
include { PHANOTATE } from '../modules/phanotate'
include { COMBINE_RESULTS } from '../modules/combine_results'

workflow AMR_PHAGE_ANALYSIS {
    take:
    samples  // channel: [meta, fasta]
    
    main:
    // Download/prepare databases
    DOWNLOAD_AMRFINDER_DB()
    DOWNLOAD_PROPHAGE_DB()
    
    // Run AMR analysis
    AMRFINDER(samples, DOWNLOAD_AMRFINDER_DB.out.db)
    
    // Run Phage analysis
    VIBRANT(samples)
    DIAMOND_PROPHAGE(VIBRANT.out.phages, DOWNLOAD_PROPHAGE_DB.out.db)
    CHECKV(VIBRANT.out.phages)
    PHANOTATE(VIBRANT.out.phages)
    
    // Prepare report script
    report_script = file("${projectDir}/bin/generate_compass_report.py")
    
    // Combine all results with enhanced reporting
    COMBINE_RESULTS(
        AMRFINDER.out.results.map { it[1] }.collect(),
        VIBRANT.out.results.map { it[1] }.collect(),
        DIAMOND_PROPHAGE.out.results.map { it[1] }.collect(),
        PHANOTATE.out.results.map { it[1] }.collect(),
        report_script
    )
    
    // Collect versions
    ch_versions = Channel.empty()
    ch_versions = ch_versions.mix(AMRFINDER.out.versions.first())
    ch_versions = ch_versions.mix(VIBRANT.out.versions.first())
    ch_versions = ch_versions.mix(DIAMOND_PROPHAGE.out.versions.first())
    ch_versions = ch_versions.mix(CHECKV.out.versions.first())
    ch_versions = ch_versions.mix(PHANOTATE.out.versions.first())
    ch_versions = ch_versions.mix(COMBINE_RESULTS.out.versions)
    
    emit:
    summary = COMBINE_RESULTS.out.summary
    report = COMBINE_RESULTS.out.report
    phage_summary = COMBINE_RESULTS.out.phage_summary
    versions = ch_versions
}