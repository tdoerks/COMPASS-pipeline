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
    path "filter_summary.txt", emit: summary
    path "versions.yml", emit: versions

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    from pathlib import Path
    import re

    metadata_files = "${metadata_files}".split()

    all_samples = []
    pathogen_map = {
        'campylobacter': 'Campylobacter',
        'salmonella': 'Salmonella',
        'ecoli': 'Escherichia'
    }

    # Summary tracking
    filter_summary = []

    for mfile in metadata_files:
        pathogen = None
        for key in pathogen_map.keys():
            if key in mfile:
                pathogen = key
                break

        if not pathogen:
            continue

        df = pd.read_csv(mfile)
        initial_count = len(df)
        print(f"Processing {pathogen}: {initial_count} samples")
        filter_summary.append(f"\\n{pathogen_map[pathogen]} ({pathogen}):")
        filter_summary.append(f"  Initial samples: {initial_count}")

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
            filter_summary.append(f"  State filter ({state_filter}): {mask.sum()} samples")

        # Filter by year range
        year_start = "${params.filter_year_start}"
        year_end = "${params.filter_year_end}"

        if (year_start and year_start != "null") or (year_end and year_end != "null"):
            if 'ReleaseDate' in df.columns:
                df['Year'] = pd.to_datetime(df['ReleaseDate'], errors='coerce').dt.year

                if year_start and year_start != "null":
                    mask &= df['Year'] >= int(year_start)
                    print(f"  After year start filter (>={year_start}): {mask.sum()}")
                    filter_summary.append(f"  Year >= {year_start}: {mask.sum()} samples")

                if year_end and year_end != "null":
                    mask &= df['Year'] <= int(year_end)
                    print(f"  After year end filter (<={year_end}): {mask.sum()}")
                    filter_summary.append(f"  Year <= {year_end}: {mask.sum()} samples")

        # Filter by host (new enhanced filtering)
        host_filter = "${params.filter_host}"
        if host_filter and host_filter != "null":
            host_mask = pd.Series([False] * len(df))
            host_cols = ['host', 'Host', 'host_subject_id']

            # Support multiple hosts separated by comma
            hosts = [h.strip() for h in host_filter.split(',')]

            for col in host_cols:
                if col in df.columns:
                    for host in hosts:
                        host_mask |= df[col].astype(str).str.contains(host, case=False, na=False)

            mask &= host_mask
            print(f"  After host filter ({host_filter}): {mask.sum()}")
            filter_summary.append(f"  Host filter ({host_filter}): {mask.sum()} samples")

        # Filter by isolation source (enhanced with multiple patterns)
        source_filter = "${params.filter_isolation_source}"
        if source_filter and source_filter != "null":
            source_mask = pd.Series([False] * len(df))
            source_cols = ['isolation_source', 'Isolation_source', 'Sample Name', 'LibraryName']

            # Support multiple sources separated by comma
            sources = [s.strip() for s in source_filter.split(',')]

            for col in source_cols:
                if col in df.columns:
                    for source in sources:
                        source_mask |= df[col].astype(str).str.contains(source, case=False, na=False)

            mask &= source_mask
            print(f"  After isolation source filter ({source_filter}): {mask.sum()}")
            filter_summary.append(f"  Isolation source filter ({source_filter}): {mask.sum()} samples")

        # Filter by general source (backward compatibility)
        general_source = "${params.filter_source}"
        if general_source and general_source != "null" and (source_filter == "null" or not source_filter):
            source_mask = pd.Series([False] * len(df))
            source_cols = ['isolation_source', 'Sample Name', 'LibraryName', 'host']

            for col in source_cols:
                if col in df.columns:
                    source_mask |= df[col].astype(str).str.contains(general_source, case=False, na=False)

            mask &= source_mask
            print(f"  After source filter ({general_source}): {mask.sum()}")
            filter_summary.append(f"  Source filter ({general_source}): {mask.sum()} samples")

        # Filter by geography/location
        geo_filter = "${params.filter_geography}"
        if geo_filter and geo_filter != "null":
            geo_mask = pd.Series([False] * len(df))
            geo_cols = ['geo_loc_name', 'geographic_location', 'collection_location', 'Sample Name', 'LibraryName']

            # Support multiple locations separated by comma
            locations = [loc.strip() for loc in geo_filter.split(',')]

            for col in geo_cols:
                if col in df.columns:
                    for location in locations:
                        geo_mask |= df[col].astype(str).str.contains(location, case=False, na=False)

            mask &= geo_mask
            print(f"  After geography filter ({geo_filter}): {mask.sum()}")
            filter_summary.append(f"  Geography filter ({geo_filter}): {mask.sum()} samples")

        # Filter by sample type
        sample_type_filter = "${params.filter_sample_type}"
        if sample_type_filter and sample_type_filter != "null":
            type_mask = pd.Series([False] * len(df))
            type_cols = ['sample_type', 'SampleType', 'Sample Name', 'LibraryName']

            # Support multiple types separated by comma
            types = [t.strip() for t in sample_type_filter.split(',')]

            for col in type_cols:
                if col in df.columns:
                    for stype in types:
                        type_mask |= df[col].astype(str).str.contains(stype, case=False, na=False)

            mask &= type_mask
            print(f"  After sample type filter ({sample_type_filter}): {mask.sum()}")
            filter_summary.append(f"  Sample type filter ({sample_type_filter}): {mask.sum()} samples")

        final_count = mask.sum()
        filter_summary.append(f"  Final: {final_count} samples ({100*final_count/initial_count:.1f}% retained)")

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

        # Write summary even if no samples
        with open('filter_summary.txt', 'w') as f:
            f.write("NARMS Metadata Filtering Summary\\n")
            f.write("=" * 60 + "\\n\\n")
            f.write("\\n".join(filter_summary))
            f.write("\\n\\nERROR: No samples passed all applied filters!\\n")
    else:
        combined = pd.concat(all_samples, ignore_index=True)
        print(f"\\nTotal filtered samples: {len(combined)}")
        filter_summary.append("\\n" + "=" * 60)
        filter_summary.append(f"\\nTOTAL FILTERED SAMPLES: {len(combined)}")

        for org in combined['organism'].unique():
            count = len(combined[combined['organism'] == org])
            print(f"  {org}: {count}")
            filter_summary.append(f"  {org}: {count}")

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

        # Write filter summary
        with open('filter_summary.txt', 'w') as f:
            f.write("NARMS Metadata Filtering Summary\\n")
            f.write("=" * 60 + "\\n")

            # Applied filters section
            f.write("\\nApplied Filters:\\n")
            f.write("-" * 60 + "\\n")
            if "${params.filter_state}" != "null" and "${params.filter_state}":
                f.write(f"  State: ${params.filter_state}\\n")
            if "${params.filter_year_start}" != "null" and "${params.filter_year_start}":
                f.write(f"  Year start: ${params.filter_year_start}\\n")
            if "${params.filter_year_end}" != "null" and "${params.filter_year_end}":
                f.write(f"  Year end: ${params.filter_year_end}\\n")
            if "${params.filter_host}" != "null" and "${params.filter_host}":
                f.write(f"  Host: ${params.filter_host}\\n")
            if "${params.filter_isolation_source}" != "null" and "${params.filter_isolation_source}":
                f.write(f"  Isolation source: ${params.filter_isolation_source}\\n")
            if "${params.filter_source}" != "null" and "${params.filter_source}":
                f.write(f"  Source (general): ${params.filter_source}\\n")
            if "${params.filter_geography}" != "null" and "${params.filter_geography}":
                f.write(f"  Geography: ${params.filter_geography}\\n")
            if "${params.filter_sample_type}" != "null" and "${params.filter_sample_type}":
                f.write(f"  Sample type: ${params.filter_sample_type}\\n")

            # Results by organism
            f.write("\\n" + "\\n".join(filter_summary))

    with open('versions.yml', 'w') as f:
        f.write('"FILTER_NARMS_SAMPLES": {"pandas": "1.5.2"}\\n')
    """
}
