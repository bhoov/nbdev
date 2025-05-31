#!/usr/bin/env python

import os
import shutil
import re
from pathlib import Path
from execnb.nbio import read_nb, dict2nb
from nbdev.process import read_qmd, write_qmd, read_nb_or_qmd
from fastcore.script import call_parse


@call_parse
def convert_notebooks(
    source_folder: str,  # Source folder containing .ipynb files
    dest_folder: str  # Destination folder for .qmd files and copied items
):
    """
    Converts .ipynb files from source_folder to .qmd files in dest_folder.
    Other files are copied directly. Replicates directory structure.
    """
    source_dir = Path(source_folder)
    dest_dir = Path(dest_folder)

    if not source_dir.is_dir():
        print(f"Error: Source directory '{source_dir.resolve()}' does not exist or is not a directory.")
        return

    print(f"Source directory: {source_dir.resolve()}")
    print(f"Destination directory: {dest_dir.resolve()}")
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured destination directory exists: {dest_dir}")

    total_files_processed = 0
    notebooks_converted = 0
    files_copied = 0
    errors_encountered = 0

    for root, _, files in os.walk(source_dir):
        current_source_dir = Path(root)
        # Calculate path relative to the initial source_dir
        # to replicate the structure in dest_dir
        relative_subdir_path = current_source_dir.relative_to(source_dir)
        current_dest_dir = dest_dir / relative_subdir_path
        
        # Ensure the subdirectory structure exists in the destination
        # (os.walk guarantees `root` exists, so mkdir for current_dest_dir is usually fine)
        current_dest_dir.mkdir(parents=True, exist_ok=True)

        for filename in files:
            total_files_processed += 1
            source_file_path = current_source_dir / filename
            
            if source_file_path.name.startswith('.'): # Skip hidden files like .DS_Store
                print(f"Skipping hidden file: {source_file_path}")
                # Decrement count as we are not "processing" it in terms of conversion/copy
                total_files_processed -=1 
                continue

            if source_file_path.is_dir(): # Should not happen with os.walk's `files` list, but as a safeguard
                print(f"Skipping directory listed as file: {source_file_path}")
                total_files_processed -=1
                continue

            if source_file_path.suffix == ".ipynb":
                # Prepare destination path for .qmd file
                dest_qmd_filename = source_file_path.stem + ".qmd"
                dest_file_path = current_dest_dir / dest_qmd_filename
                
                print(f"Processing for conversion: {source_file_path} -> {dest_file_path}")
                try:
                    # For .ipynb, read_nb_or_qmd will use read_nb from execnb
                    notebook_object = read_nb_or_qmd(source_file_path)
                    write_qmd(notebook_object, dest_file_path)
                    print(f"  Successfully converted '{source_file_path.name}' to '{dest_file_path.name}'")
                    notebooks_converted +=1
                except Exception as e:
                    print(f"  Error converting {source_file_path}: {e}")
                    errors_encountered +=1
            else:
                # For any other file type, copy it directly
                dest_file_path = current_dest_dir / filename
                print(f"Copying: {source_file_path} -> {dest_file_path}")
                try:
                    shutil.copy2(source_file_path, dest_file_path) # copy2 preserves metadata
                    print(f"  Successfully copied '{source_file_path.name}'")
                    files_copied += 1
                except Exception as e:
                    print(f"  Error copying {source_file_path}: {e}")
                    errors_encountered +=1
    
    print(f"\n--- Conversion Summary ---")
    print(f"Total items scanned in source: {total_files_processed}")
    print(f"Notebooks converted to .qmd: {notebooks_converted}")
    print(f"Other files copied: {files_copied}")
    if errors_encountered > 0:
        print(f"Errors encountered: {errors_encountered}")
    print(f"Output located in: {dest_dir.resolve()}") 