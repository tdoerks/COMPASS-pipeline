process VALIDATE_SPECIES {
    tag "$sample_id"
    publishDir "${params.outdir}/species_validation", mode: 'copy'
    container = 'quay.io/biocontainers/pandas:1.5.2'

    input:
    tuple val(sample_id), path(mlst_file), val(expected_organism)

    output:
    tuple val(sample_id), path("${sample_id}_species_check.tsv"), emit: results
    path "versions.yml", emit: versions

    script:
    """
    #!/usr/bin/env python3
    import sys

    # Expected organism from metadata
    expected = "${expected_organism}".lower()

    # Read MLST result
    with open("${mlst_file}") as f:
        mlst_line = f.readlines()[-1].strip()  # Last line has the result

    parts = mlst_line.split('\\t')
    if len(parts) < 2:
        mlst_scheme = "UNKNOWN"
    else:
        mlst_scheme = parts[1]  # Column 2 is SCHEME

    # Map MLST schemes to organisms
    scheme_to_organism = {
        'ecoli': 'Escherichia',
        'ecoli_achtman': 'Escherichia',
        'ecoli_2': 'Escherichia',
        'senterica': 'Salmonella',
        'senterica_achtman': 'Salmonella',
        'campylobacter': 'Campylobacter',
        'campylobacter_nonjejuni': 'Campylobacter',
        'cjejuni': 'Campylobacter',
        'ccoli': 'Campylobacter',
    }

    # Determine detected organism from MLST
    detected_organism = "UNKNOWN"
    for scheme, org in scheme_to_organism.items():
        if mlst_scheme.lower().startswith(scheme):
            detected_organism = org
            break

    # Check if they match
    match_status = "MATCH"
    if mlst_scheme == "-" or mlst_scheme == "UNKNOWN":
        match_status = "NO_MLST_HIT"
    elif detected_organism == "UNKNOWN":
        match_status = "UNKNOWN_SCHEME"
    elif expected.startswith('escherichia') and detected_organism == 'Escherichia':
        match_status = "MATCH"
    elif expected.startswith('salmonella') and detected_organism == 'Salmonella':
        match_status = "MATCH"
    elif expected.startswith('campylobacter') and detected_organism == 'Campylobacter':
        match_status = "MATCH"
    else:
        match_status = "MISMATCH"

    # Write output
    with open("${sample_id}_species_check.tsv", 'w') as out:
        out.write("sample_id\\texpected_organism\\tmlst_scheme\\tdetected_organism\\tmatch_status\\n")
        out.write(f"${sample_id}\\t${expected_organism}\\t{mlst_scheme}\\t{detected_organism}\\t{match_status}\\n")

    # Print warning if mismatch
    if match_status == "MISMATCH":
        print(f"⚠️  WARNING: Species mismatch for ${sample_id}!", file=sys.stderr)
        print(f"    Expected: ${expected_organism}", file=sys.stderr)
        print(f"    MLST detected: {detected_organism} (scheme: {mlst_scheme})", file=sys.stderr)
        print(f"    This sample may be mislabeled in NARMS metadata!", file=sys.stderr)

    with open('versions.yml', 'w') as f:
        f.write('"VALIDATE_SPECIES": {"python": "3.10"}\\n')
    """
}
