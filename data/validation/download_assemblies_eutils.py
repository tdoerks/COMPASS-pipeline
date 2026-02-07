#!/usr/bin/env python3
"""
Download validation assemblies using NCBI E-utilities
Alternative to ncbi-datasets CLI for environments with TLS timeout issues.

Uses E-utilities efetch to download assembly FASTA files directly from NCBI.
Works on Beocat where ncbi-datasets fails with TLS handshake timeouts.
"""

import csv
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

# NCBI E-utilities configuration
ENTREZ_EMAIL = "tdoerks@vet.k-state.edu"
ENTREZ_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

def download_assembly(accession, output_path, max_retries=3):
    """
    Download assembly FASTA using NCBI E-utilities.

    Strategy:
    1. Use efetch with nucleotide database (more reliable than assembly db)
    2. Query by assembly accession to get genomic sequence
    3. Retry on failures with exponential backoff
    """

    print(f"Downloading {accession}...", end=" ", flush=True)

    for attempt in range(1, max_retries + 1):
        try:
            # Construct efetch URL for nucleotide database
            # Use assembly accession with [ACCN] tag
            params = {
                'db': 'nuccore',
                'id': accession,
                'rettype': 'fasta',
                'retmode': 'text',
                'email': ENTREZ_EMAIL
            }

            # Build URL manually to avoid encoding issues
            param_str = '&'.join([f'{k}={v}' for k, v in params.items()])
            url = f"{ENTREZ_BASE}/efetch.fcgi?{param_str}"

            # Download with timeout
            with urllib.request.urlopen(url, timeout=60) as response:
                fasta_content = response.read().decode('utf-8')

            # Check if we got valid FASTA
            if not fasta_content.startswith('>'):
                raise ValueError(f"Invalid FASTA content (no header)")

            if len(fasta_content) < 1000:
                raise ValueError(f"FASTA too small ({len(fasta_content)} bytes), likely incomplete")

            # Write to file
            with open(output_path, 'w') as f:
                f.write(fasta_content)

            # Verify file was written
            if output_path.exists() and output_path.stat().st_size > 1000:
                print(f"✓ ({output_path.stat().st_size:,} bytes)")
                return True
            else:
                raise ValueError(f"Output file too small or missing")

        except urllib.error.HTTPError as e:
            if e.code == 400:
                # Bad request - accession might not exist in nuccore
                # Try alternative approach: search assembly db first
                print(f"⚠ HTTP 400, trying alternative method...", end=" ", flush=True)

                try:
                    # Search assembly database for this accession
                    search_url = f"{ENTREZ_BASE}/esearch.fcgi?db=assembly&term={accession}[Assembly Accession]&email={ENTREZ_EMAIL}"
                    with urllib.request.urlopen(search_url, timeout=30) as response:
                        search_result = response.read().decode('utf-8')

                    # Extract assembly UID
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(search_result)
                    id_elem = root.find('.//Id')

                    if id_elem is None:
                        raise ValueError(f"Assembly not found in NCBI")

                    assembly_uid = id_elem.text

                    # Now fetch using assembly UID and docsum to get FTP path
                    # Actually, let's try efetch with the UID
                    time.sleep(0.5)

                    fetch_url = f"{ENTREZ_BASE}/efetch.fcgi?db=assembly&id={assembly_uid}&rettype=fasta&retmode=text&email={ENTREZ_EMAIL}"

                    with urllib.request.urlopen(fetch_url, timeout=60) as response:
                        fasta_content = response.read().decode('utf-8')

                    if fasta_content.startswith('>'):
                        with open(output_path, 'w') as f:
                            f.write(fasta_content)
                        print(f"✓ ({output_path.stat().st_size:,} bytes)")
                        return True

                except Exception as alt_error:
                    print(f"✗ Alternative method failed: {alt_error}")

            print(f"✗ HTTP {e.code}: {e.reason}")

        except urllib.error.URLError as e:
            print(f"✗ Network error (attempt {attempt}/{max_retries}): {e.reason}")

        except Exception as e:
            print(f"✗ Error (attempt {attempt}/{max_retries}): {e}")

        # Retry with exponential backoff
        if attempt < max_retries:
            wait_time = 2 ** attempt  # 2, 4, 8 seconds
            print(f"  Retrying in {wait_time}s...", end=" ", flush=True)
            time.sleep(wait_time)

    # All retries failed
    print(f"✗ FAILED after {max_retries} attempts")
    return False

def main():
    """Main execution."""
    print("="*70)
    print("COMPASS Validation - Assembly Download via E-utilities")
    print("="*70)
    print()

    # File paths
    script_dir = Path(__file__).parent
    samplesheet_path = script_dir / "validation_samplesheet.csv"
    output_dir = script_dir / "assemblies"

    # Check samplesheet exists
    if not samplesheet_path.exists():
        print(f"ERROR: Samplesheet not found: {samplesheet_path}", file=sys.stderr)
        print("Expected location: data/validation/validation_samplesheet.csv")
        sys.exit(1)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Samplesheet: {samplesheet_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Read samplesheet
    samples = []
    with open(samplesheet_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            samples.append({
                'sample': row['sample'],
                'organism': row['organism'],
                'accession': row['assembly_accession']
            })

    print(f"Total samples to download: {len(samples)}")
    print()

    # Download assemblies
    success_count = 0
    failed_count = 0
    skipped_count = 0
    failed_accessions = []

    start_time = time.time()

    for i, sample in enumerate(samples, 1):
        sample_name = sample['sample']
        accession = sample['accession']
        output_path = output_dir / f"{sample_name}.fasta"

        print(f"[{i}/{len(samples)}] {sample_name} ({accession}): ", end="")

        # Check if already downloaded
        if output_path.exists() and output_path.stat().st_size > 1000:
            print(f"✓ Already exists ({output_path.stat().st_size:,} bytes)")
            skipped_count += 1
            continue

        # Download
        success = download_assembly(accession, output_path)

        if success:
            success_count += 1
        else:
            failed_count += 1
            failed_accessions.append((sample_name, accession))

        # Rate limiting - be nice to NCBI
        if i < len(samples):  # Don't sleep after last one
            time.sleep(0.5)

    elapsed_time = time.time() - start_time

    # Summary
    print()
    print("="*70)
    print("DOWNLOAD COMPLETE")
    print("="*70)
    print(f"Total samples: {len(samples)}")
    print(f"✓ Successfully downloaded: {success_count}")
    print(f"⊙ Already existed (skipped): {skipped_count}")
    print(f"✗ Failed: {failed_count}")
    print()
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    print(f"Average: {elapsed_time/len(samples):.1f} seconds per sample")
    print()

    if failed_accessions:
        print("Failed downloads:")
        for sample_name, accession in failed_accessions:
            print(f"  {sample_name}: {accession}")
        print()

    print(f"Assemblies saved to: {output_dir}")
    print()

    if failed_count == 0:
        print("✅ All assemblies downloaded successfully!")
        print()
        print("Next steps:")
        print("  1. Edit run_compass_validation.sh:")
        print("     Change: --input_mode assembly")
        print("     To:     --input_mode fasta")
        print()
        print("  2. Submit validation run:")
        print("     sbatch data/validation/run_compass_validation.sh")
    else:
        print(f"⚠ {failed_count} assemblies failed to download")
        print("You can:")
        print("  1. Re-run this script (will skip already downloaded files)")
        print("  2. Manually download failed accessions")
        print("  3. Or proceed with partial dataset")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
