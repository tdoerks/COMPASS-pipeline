#!/bin/bash
#SBATCH -J checkm2-db-dl
#SBATCH -t 1:00:00
#SBATCH -p batch.q
#SBATCH --mem=4G
#SBATCH -o /fastscratch/tylerdoe/checkm2_db_dl_%j.log

IMG=docker://quay.io/biocontainers/checkm2:1.0.2--pyh7cba7a3_0
DB=/fastscratch/tylerdoe/databases/checkm2_db

mkdir -p "$DB"
apptainer exec "$IMG" checkm2 database --download --path "$DB"
echo "Done. DB at: $DB/CheckM2_database/uniref100.KO.1.dmnd"
