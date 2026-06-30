import numpy as np
import argparse
import os


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description = "Params explanation of [concat-volreg]"
    )

    parser.add_argument(
        '-V', '--volreg',
        dest='volreg_files', action='append',
        required=True,
        help='Volreg file (using multiple times: -V file1 -V file2 ...)'
    )

    parser.add_argument(
        '-O', '--output',
        dest='output_file',
        default=None,
        help='Output filename (optional)'
    )

    args = parser.parse_args()

    volreg_files = args.volreg_files

    total = []
    
    print(f"[Debug-python]: Enterin python script")
    
    print(f"[Debug-python]: Check input files:{volreg_files}")

    for volreg_file in volreg_files:
        print(f"[Info-python]: current work file:{volreg_file}")

        with open(volreg_file, mode='r', encoding='utf-8') as f:
            c = f.read()
            print(f"[Debug-python]: current workfile content:\n{c}")

            total.append(c)
    
    print(f"[Debug-python]: Check total list:\n{total}")

    content = "".join(total)
    
    print(f"[Info]: Check content write-able:\n{content}")

    if args.output_file:
        filepath = args.output_file
        print(f"[Debug-python]: write into:{filepath}")
    else:
        filename = os.path.basename(volreg_files[0]).split('.1D')[0].split(".run")[0] + 'Allvol' + '.1D'
        filepath = os.path.join(os.path.dirname(volreg_files[0]), filename)

    with open(filepath, mode='w+', encoding='utf-8') as F:
        F.write(content)
    
