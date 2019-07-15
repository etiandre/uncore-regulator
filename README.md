# Uncore regulator
`uncore-regulator` is a program that tries to maximise CPU performance by regulating the uncore frequency.
It also meters various CPU statistics and logs them for analysis.
## Installation
~~~~
$ apt install likwid python3 python3-pip
$ pip3 install https://github.com/etiandre/uncore-regulator
~~~~
Before use, insert the msr kernel module:
~~~~
# modprobe msr
~~~~

## Usage
~~~~
$ uncore-regulator [-h] [-o LOGFILE] [-r REGULATOR] cores sockets
~~~~
### Required arguments:
 - `cores` :                 list of physical core ids from which flop/s and memory usage will be metered
 - `sockets` :               list of physical sockets ids from which uncore frequency and power will be metered

These can be obtained using `hwloc-ls`. You can specify a comma-separated list of IDs, or a range such as 0-15, or any combination of the two.

### Options:
You should at least specify one of these two options, or else the program will happily do nothing:
 - `-o OUTFILE, --logfile OUTFILE`
Specify a file where the meters will be logged (tab-separated).
 - `-r REGULATOR, --regulator REGULATOR`
Regulator to use. Availiable regulators are in the uncore_regulators/regulators folder.

## Examples
Meter cores 0 to 15 and on the 2 first sockets and log results to `test.tsv`. Do not perform any regulation.

`$ uncore-regulator 0-15 0,1 -o test.tsv`

Meter cores all the cores on the first socket of a double-socket, 14-core-per-socket machine, log results, and regulate.

`$ uncore-regulator 0,2,4,6,8,10,12,14,16,18,20,22,24,26 0 -o pouet.tsv -r SimpleRegulator`

## Troubleshooting
If you get : 
`ERROR: The selected register UBOXFIX is in use. Please run likwid with force option (-f, --force) to overwrite settings`,
set LIKWID_FORCE=1 in your environment, such as :

`$ LIKWID_FORCE=1 uncore-regulator options...`
