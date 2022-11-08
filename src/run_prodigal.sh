#!/bin/bash
tmpfolder="$2"
cpus=$4
mkdir -p $tmpfolder
function check_prodigal_input () {
    base_name=$(basename -s .fna "$1")
    prodigal -i "$1" -o "$tmpfolder/$base_name.genes" -a "$tmpfolder/$base_name.faa"
}
export -f check_prodigal_input
export tmpfolder

echo "Start prodigal gene prediction"
if [ -d "$1" ]; then
    filename=$(find "$1" -name "*.fna")
    filecount=$(echo "$filename" | wc -w)
    echo "$filename" | xargs -n 1 -I {} -P $cpus bash -c 'check_prodigal_input {}'
    # for file in $filename
    # do
    #     count=$((count+1))
    #     echo -ne "Progress: $count/$filecount\r"
    #     base_name=$(basename -s .fna "$file")
    #     prodigal -i "$file" -o "$tmpfolder/$base_name.genes" -a "$tmpfolder/$base_name.faa" 2> /dev/null
    # done
elif [ -f "$1" ]; then
    base_name=$(basename -s .fna "$1")
    prodigal -i "$1" -o "$tmpfolder/$base_name.genes" -a "$tmpfolder/$base_name.faa" 2> /dev/null
else
    echo "Invalid input"
fi
echo "Finish prodigal gene prediction"

unset check_prodigal_input
unset tmpfolder
