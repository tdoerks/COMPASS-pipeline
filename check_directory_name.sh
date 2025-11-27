#!/bin/bash
#SBATCH --job-name=check_dirs
#SBATCH --output=/fastscratch/tylerdoe/check_dirs_%j.out
#SBATCH --error=/fastscratch/tylerdoe/check_dirs_%j.err
#SBATCH --time=00:02:00
#SBATCH --mem=100M

echo "=========================================="
echo "Directory Name Check"
echo "=========================================="

echo "Current working directory when job starts:"
pwd

echo ""
echo "Checking for COMPASS-pipeline (uppercase):"
ls -ld /fastscratch/tylerdoe/COMPASS-pipeline 2>&1

echo ""
echo "Checking for compass-pipeline (lowercase):"
ls -ld /fastscratch/tylerdoe/compass-pipeline 2>&1

echo ""
echo "Listing all directories in /fastscratch/tylerdoe/ containing 'compass':"
ls -ld /fastscratch/tylerdoe/*compass* 2>&1

echo ""
echo "Checking /bulk/tylerdoe/ as well:"
ls -ld /bulk/tylerdoe/*compass* 2>&1 || echo "No compass directories in /bulk yet"

echo "=========================================="
