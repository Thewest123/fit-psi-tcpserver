#!/bin/bash
# Merges all .py files to one single file

OUTPUT_FILE="MERGE.py"
FILES=$(ls | grep -E '.*\.py$' | grep -v "$OUTPUT_FILE")
FILE_COUNT=$(echo "$FILES" | wc -l)

echo "# ================== MERGE ==================" > $OUTPUT_FILE
echo "# This is a merge of $FILE_COUNT files" >> $OUTPUT_FILE
echo "# Author: cernyj87 (Jan Černý)" >> $OUTPUT_FILE
echo "# Merged on: $(date +%F)" >> $OUTPUT_FILE
echo "# ===========================================" >> $OUTPUT_FILE

i=1
for file in $FILES; do
    
    printf "Merging %s (%d/%d)\n" $file $i $FILE_COUNT
    file=$(echo $file | tr -d '\n')

    printf "\n\n" >> $OUTPUT_FILE
    echo "# =============[ Part ]==============" >> $OUTPUT_FILE
    echo "# Name: ${file}" >> $OUTPUT_FILE
    echo "# Part: $i / $FILE_COUNT " >> $OUTPUT_FILE
    printf "\n" >> $OUTPUT_FILE
    cat $file >> $OUTPUT_FILE
    printf "\n" >> $OUTPUT_FILE
    echo "# ==============[ end ]==============" >> $OUTPUT_FILE
    i=$((i+1))

done