process DOWNLOAD_NARMS_METADATA {
    tag "metadata_download"
    publishDir "${params.outdir}/metadata", mode: 'copy'
    container = 'quay.io/biocontainers/entrez-direct:16.2--he881be0_1'

    output:
    path "*.csv", emit: metadata
    path "versions.yml", emit: versions

    script:
    def bioproject = params.bioproject
    def species = params.species
    def all_bacterial = params.all_bacterial

    // Default NARMS BioProjects if nothing specified
    def narms_bioprojects = [
        'PRJNA292664': 'campylobacter',
        'PRJNA292661': 'salmonella',
        'PRJNA292663': 'ecoli'
    ]

    if (bioproject) {
        // User-specified BioProject(s)
        def projects = bioproject.split(',').collect { it.trim() }
        def queries = projects.collect { bp ->
            // Map known NARMS BioProjects to pathogen names for file naming
            def name_map = [
                'PRJNA292664': 'campylobacter',
                'PRJNA292661': 'salmonella',
                'PRJNA292663': 'ecoli'
            ]
            def name = name_map.get(bp, bp.replaceAll('PRJNA', 'bp'))
            "esearch -db sra -query \"${bp}[BioProject]\" | efetch -format runinfo > ${name}_metadata.csv"
        }.join('\n    ')

        """
        echo "Downloading metadata for BioProject(s): ${bioproject}..."
        ${queries}
        echo '"DOWNLOAD_NARMS_METADATA": {"entrez-direct": "16.2"}' > versions.yml
        """
    } else if (species) {
        // Species-based query
        """
        echo "Downloading metadata for species: ${species}..."
        esearch -db sra -query "${species}[Organism] AND bacteria[Filter]" | \
        efetch -format runinfo > ${species.toLowerCase().replaceAll(' ', '_')}_metadata.csv
        echo '"DOWNLOAD_NARMS_METADATA": {"entrez-direct": "16.2"}' > versions.yml
        """
    } else if (all_bacterial) {
        // All bacterial samples (use with caution!)
        """
        echo "WARNING: Downloading ALL bacterial SRA metadata - this may be very large!"
        esearch -db sra -query "bacteria[Filter]" | \
        efetch -format runinfo > all_bacteria_metadata.csv
        echo '"DOWNLOAD_NARMS_METADATA": {"entrez-direct": "16.2"}' > versions.yml
        """
    } else {
        // Default: NARMS BioProjects
        """
        echo "Downloading NARMS BioProject metadata (default)..."

        # Campylobacter
        esearch -db sra -query "PRJNA292664[BioProject]" | \
        efetch -format runinfo > campylobacter_metadata.csv

        # Salmonella
        esearch -db sra -query "PRJNA292661[BioProject]" | \
        efetch -format runinfo > salmonella_metadata.csv

        # E. coli
        esearch -db sra -query "PRJNA292663[BioProject]" | \
        efetch -format runinfo > ecoli_metadata.csv

        echo '"DOWNLOAD_NARMS_METADATA": {"entrez-direct": "16.2"}' > versions.yml
        """
    }
}

process FILTER_NARMS_SAMPLES {
    tag "filter_${params.filter_state}"
    publishDir "${params.outdir}/filtered_samples", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'
    
    input:
    path metadata_files
    
    output:
    path "filtered_samples.csv", emit: filtered
    path "srr_accessions.txt", emit: srr_list
    path "*_srr_list.txt", emit: pathogen_lists
    path "versions.yml", emit: versions
    
    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    from pathlib import Path
    
    metadata_files = "${metadata_files}".split()
    
    all_samples = []
    pathogen_map = {
        'campylobacter': 'Campylobacter',
        'salmonella': 'Salmonella',
        'ecoli': 'Escherichia'
    }
    
    for mfile in metadata_files:
        pathogen = None
        for key in pathogen_map.keys():
            if key in mfile:
                pathogen = key
                break
        
        if not pathogen:
            continue
            
        df = pd.read_csv(mfile)
        print(f"Processing {pathogen}: {len(df)} samples")

        mask = pd.Series([True] * len(df))

        # Filter by platform (Illumina only - pipeline designed for short reads)
        platform_filter = "${params.filter_platform}"
        if platform_filter and platform_filter != "null":
            if 'Platform' in df.columns:
                platform_mask = df['Platform'].astype(str).str.upper() == platform_filter.upper()
                mask &= platform_mask
                print(f"  After platform filter ({platform_filter}): {mask.sum()}")
            else:
                print(f"  WARNING: 'Platform' column not found in metadata - skipping platform filter")

        # Filter by library source (GENOMIC = isolates only, excludes metagenomic/environmental)
        library_source_filter = "${params.filter_library_source}"
        if library_source_filter and library_source_filter != "null":
            if 'LibrarySource' in df.columns:
                library_source_mask = df['LibrarySource'].astype(str).str.upper() == library_source_filter.upper()
                mask &= library_source_mask
                print(f"  After library source filter ({library_source_filter}): {mask.sum()}")
            else:
                print(f"  WARNING: 'LibrarySource' column not found in metadata - skipping library source filter")

        # Filter by state (in sample name)
        state_filter = "${params.filter_state}"
        if state_filter and state_filter != "null":
            state_mask = pd.Series([False] * len(df))
            sample_cols = [col for col in df.columns if 'sample' in col.lower() or 'library' in col.lower()]

            for col in sample_cols:
                if col in df.columns:
                    # Pattern: STATE code followed by digits (e.g., 25KS08, 19KS07, KS-123)
                    # This matches both old format (19KS07) and new format (25KS08)
                    pattern = f'{state_filter}\\\\d'
                    state_mask |= df[col].astype(str).str.contains(pattern, case=False, na=False, regex=True)

            mask &= state_mask
            print(f"  After state filter ({state_filter}): {mask.sum()}")
        
        # Filter by year range
        year_start = "${params.filter_year_start}"
        year_end = "${params.filter_year_end}"
        
        if (year_start and year_start != "null") or (year_end and year_end != "null"):
            if 'ReleaseDate' in df.columns:
                df['Year'] = pd.to_datetime(df['ReleaseDate'], errors='coerce').dt.year
                
                if year_start and year_start != "null":
                    mask &= df['Year'] >= int(year_start)
                    print(f"  After year start filter (>={year_start}): {mask.sum()}")
                
                if year_end and year_end != "null":
                    mask &= df['Year'] <= int(year_end)
                    print(f"  After year end filter (<={year_end}): {mask.sum()}")
        
        # Filter by source
        source_filter = "${params.filter_source}"
        if source_filter and source_filter != "null":
            source_mask = pd.Series([False] * len(df))
            source_cols = ['isolation_source', 'Sample Name', 'LibraryName', 'host']
            
            for col in source_cols:
                if col in df.columns:
                    source_mask |= df[col].astype(str).str.contains(source_filter, case=False, na=False)
            
            mask &= source_mask
            print(f"  After source filter ({source_filter}): {mask.sum()}")
        
        if mask.sum() == 0:
            print(f"  WARNING: No samples passed filters for {pathogen}")
            continue
        
        filtered = df[mask].copy()
        filtered['organism'] = pathogen_map[pathogen]
        all_samples.append(filtered)
    
    if not all_samples:
        print("\\nERROR: No samples passed all filters!")
        # Create empty CSV with proper headers to avoid Nextflow parsing error
        empty_df = pd.DataFrame(columns=['Run', 'organism'])
        empty_df.to_csv('filtered_samples.csv', index=False)
        open('srr_accessions.txt', 'w').close()
        for org in pathogen_map.values():
            open(f"{org.lower()}_srr_list.txt", 'w').close()
    else:
        combined = pd.concat(all_samples, ignore_index=True)
        print(f"\\nTotal filtered samples before max limit: {len(combined)}")

        # Apply max_samples limit
        max_samples = "${params.max_samples}"
        if max_samples and max_samples != "null":
            max_samples = int(max_samples)
            print(f"  max_samples parameter: {max_samples}")
            print(f"  Current sample count: {len(combined)}")
            if len(combined) > max_samples:
                print(f"  Applying .head({max_samples}) to limit samples")
                combined = combined.head(max_samples)
                print(f"  After .head(): {len(combined)} samples")
            else:
                print(f"  No limiting needed ({len(combined)} <= {max_samples})")

        print(f"\\nFinal sample count before writing: {len(combined)}")
        for org in combined['organism'].unique():
            count = len(combined[combined['organism'] == org])
            print(f"  {org}: {count}")

        combined.to_csv('filtered_samples.csv', index=False)
        print(f"CSV written with {len(combined)} data rows")

        with open('srr_accessions.txt', 'w') as f:
            for srr in combined['Run']:
                f.write(f"{srr}\\n")

        for pathogen in combined['organism'].unique():
            subset = combined[combined['organism'] == pathogen]
            filename = f"{pathogen.lower()}_srr_list.txt"
            with open(filename, 'w') as f:
                for srr in subset['Run']:
                    f.write(f"{srr}\\n")
    
    with open('versions.yml', 'w') as f:
        f.write('"FILTER_NARMS_SAMPLES": {"pandas": "1.5.2"}\\n')
    """
}
