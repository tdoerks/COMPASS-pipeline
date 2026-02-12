# PowerShell Script to Download 8 ETEC Reference Genomes
# From: Long-read-sequenced reference genomes of the seven major lineages of ETEC
# DOI: 10.1038/s41598-021-88316-2
#
# Downloads chromosome + plasmids from ENA and concatenates into single FASTA per strain
#
# Usage:
#   .\download_etec_reference_genomes.ps1
#
# Output: 8 FASTA files (E925.fasta, E1649.fasta, etc.)

Write-Host "=========================================="
Write-Host "Downloading 8 ETEC Reference Genomes"
Write-Host "From: doi.org/10.1038/s41598-021-88316-2"
Write-Host "=========================================="
Write-Host ""

# Create output directory
$outputDir = "ETEC_reference_genomes"
if (!(Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir | Out-Null
}
Set-Location $outputDir

# Function to download and concatenate genome
function Download-ETECGenome {
    param (
        [string]$strain,
        [string]$chromosome,
        [string[]]$plasmids
    )

    Write-Host "Downloading $strain..."

    # Download chromosome
    $chrFile = "${strain}_chr.fasta"
    Write-Host "  - Chromosome: $chromosome"
    curl.exe -s "https://www.ebi.ac.uk/ena/browser/api/fasta/$chromosome" -o $chrFile

    # Download plasmids
    $plasmidFiles = @()
    $plasmidNum = 1
    foreach ($plasmid in $plasmids) {
        $plasmidFile = "${strain}_p${plasmidNum}.fasta"
        Write-Host "  - Plasmid ${plasmidNum}: $plasmid"
        curl.exe -s "https://www.ebi.ac.uk/ena/browser/api/fasta/$plasmid" -o $plasmidFile
        $plasmidFiles += $plasmidFile
        $plasmidNum++
    }

    # Concatenate chromosome + plasmids
    $finalFile = "${strain}.fasta"
    Get-Content $chrFile, $plasmidFiles | Set-Content $finalFile

    # Clean up individual files
    Remove-Item $chrFile
    foreach ($file in $plasmidFiles) {
        Remove-Item $file
    }

    Write-Host "  -> Created: $finalFile"
    Write-Host ""
}

# Download all 8 ETEC strains
# Format: Download-ETECGenome "StrainName" "ChromosomeAccession" @("Plasmid1", "Plasmid2", ...)

# E925 (Lineage L1) - 1 chr + 4 plasmids
Download-ETECGenome "E925" "LR883050" @("LR883051", "LR883052", "LR883053", "LR883054")

# E1649 (Lineage L2) - 1 chr + 4 plasmids
Download-ETECGenome "E1649" "LR882973" @("LR882976", "LR882977", "LR882974", "LR882975")

# E36 (Lineage L3) - 1 chr + 2 plasmids
Download-ETECGenome "E36" "LR882997" @("LR882998", "LR882999")

# E2980 (Lineage L3) - 1 chr + 3 plasmids
Download-ETECGenome "E2980" "LR882978" @("LR882979", "LR882980", "LR882981")

# E1441 (Lineage L4) - 1 chr + 2 plasmids
Download-ETECGenome "E1441" "LR883012" @("LR883013", "LR883014")

# E1779 (Lineage L5) - 1 chr + 4 plasmids
Download-ETECGenome "E1779" "LR883006" @("LR883008", "LR883009", "LR883010", "LR883011")

# E562 (Lineage L6) - 1 chr + 5 plasmids
Download-ETECGenome "E562" "LR883000" @("LR883001", "LR883002", "LR883003", "LR883004", "LR883005")

# E1373 (Lineage L7) - 1 chr + 2 plasmids
Download-ETECGenome "E1373" "LR882990" @("LR882991", "LR882992")

# Summary
Write-Host "=========================================="
Write-Host "Download Complete!"
Write-Host "=========================================="
Write-Host ""
Write-Host "Downloaded 8 ETEC reference genomes:"
Get-ChildItem -Filter "*.fasta" | ForEach-Object {
    $size = [math]::Round($_.Length / 1MB, 2)
    Write-Host "  $($_.Name) - ${size} MB"
}
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Upload these 8 FASTA files to Beocat"
Write-Host "2. Create samplesheet pointing to these files"
Write-Host "3. Run COMPASS pipeline"
Write-Host "4. Validate results against expected features"
Write-Host ""
Write-Host "Expected features (from paper):"
Write-Host "  E925:   4 plasmids, LT+STh toxins, CS1+CS3+CS21"
Write-Host "  E1649:  4 plasmids, LT+STh toxins, CS2+CS3+CS21"
Write-Host "  E36:    2 plasmids, LT+STh toxins, CFA/I+CS21"
Write-Host "  E2980:  3 plasmids, LT toxin, CS7"
Write-Host "  E1441:  2 plasmids, LT toxin, CS6+CS21"
Write-Host "  E1779:  4 plasmids, LT+STh toxins, CS5+CS6"
Write-Host "  E562:   5 plasmids, STh toxin, CFA/I+CS21"
Write-Host "  E1373:  2 plasmids, STp toxin, CS6"
Write-Host ""
