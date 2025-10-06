process DOWNLOAD_NARMS_METADATA {
    tag "narms_metadata"
    publishDir "${params.outdir}/metadata", mode: 'copy'
    container = 'quay.io/biocontainers/entrez-direct:16.2--he881be0_1'
    
    output:
    path "*.csv", emit: metadata
    path "versions.yml", emit: versions
    
    script:
    """
    echo "Downloading NARMS BioProject metadata..."
    
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
        
        # Filter by state (in sample name)
        state_filter = "${params.filter_state}"
        if state_filter and state_filter != "null":
            state_mask = pd.Series([False] * len(df))
            sample_cols = [col for col in df.columns if 'sample' in col.lower() or 'library' in col.lower()]
            
            for col in sample_cols:
                if col in df.columns:
                    # Pattern: digits + STATE + digits (e.g., 19KS07)
                    pattern = f'\\\\d{{2}}{state_filter}\\\\d{{2}}'
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
        pd.DataFrame().to_csv('filtered_samples.csv', index=False)
        open('srr_accessions.txt', 'w').close()
        for org in pathogen_map.values():
            open(f"{org.lower()}_srr_list.txt", 'w').close()
    else:
        combined = pd.concat(all_samples, ignore_index=True)
        print(f"\\nTotal filtered samples: {len(combined)}")
        for org in combined['organism'].unique():
            count = len(combined[combined['organism'] == org])
            print(f"  {org}: {count}")
        
        combined.to_csv('filtered_samples.csv', index=False)
        
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
