#!/bin/bash
#SBATCH --job-name=check_databases
#SBATCH --output=/fastscratch/tylerdoe/check_databases_%j.out
#SBATCH --error=/fastscratch/tylerdoe/check_databases_%j.err
#SBATCH --time=00:02:00
#SBATCH --mem=100M

echo "=========================================="
echo "Database Location Check"
echo "=========================================="

echo "Checking /homes/tylerdoe/databases/:"
ls -lh /homes/tylerdoe/databases/ 2>&1

echo ""
echo "Checking /fastscratch/tylerdoe/databases/:"
ls -lh /fastscratch/tylerdoe/databases/ 2>&1

echo ""
echo "Checking /bulk/tylerdoe/databases/ (if exists):"
ls -lh /bulk/tylerdoe/databases/ 2>&1 || echo "Directory doesn't exist yet"

echo ""
echo "=========================================="
echo "Key Database Files:"
echo "=========================================="

echo ""
echo "Prophage database (.dmnd):"
find /homes/tylerdoe/databases /fastscratch/tylerdoe/databases /bulk/tylerdoe/databases -name "*.dmnd" 2>/dev/null

echo ""
echo "BUSCO downloads:"
find /homes/tylerdoe/databases /fastscratch/tylerdoe/databases /bulk/tylerdoe/databases -type d -name "busco_downloads" 2>/dev/null

echo "=========================================="
