#!/bin/bash

read -p "WARNING!
This script will run multiple combinations of pipeline parameters with both the gpt-3.5-turbo and gpt-4o model.
Estimated cost is \$10-\$12, but check the OpenAI pricing models. Do you want to proceed? (y/n): " confirm

if [[ $confirm != [yY] ]]; then
    echo "Operation cancelled."
    exit 1
fi

source ./init_shell.sh

source_paths=("data/sources" "data_decompile_eval/sources")
strip_flags=("" "-s")
disassemblers=("objdump" "r2")

for source_path in "${source_paths[@]}"; do
    for strip_flag in "${strip_flags[@]}"; do
        for disassembler in "${disassemblers[@]}"; do
            echo "Running with source_path=$source_path, strip_flag=$strip_flag, disassembler=$disassembler"
            python main.py full-run -a -m gpt-3.5-turbo gpt-4o -i "$source_path" $strip_flag -x "$disassembler"
        done
    done
done
