# PYCODE SIMILAR BATCH
Simple python plagiarism tool that can compare any number of python files for similar code
Based on [pycode_similar](https://github.com/fyrestone/pycode_similar)

## Instructions
1. Modify any necessary variables in the `makefile`
2. `make`

## Usage
```
usage: pycode_similar_batch.py [-h] [-c C] [-l L] [-p P] [-o O] [-d]
                               files [files ...]

Checks for similarity in code

positional arguments:
  files       The input files

optional arguments:
  -h, --help  show this help message and exit
  -c C        The total plagiarism cutoff percent (default: 0.5)
  -l L        if AST line of the function >= value then output detail
              (default: 4)
  -p P        if plagiarism percentage of the function >= value then output
              detail (default: 0.5)
  -o O        File where results will be output (default: ./results.out)
  -d          Turn debug mode on
```
 
