import argparse
import logging
from src.daemon import Daemon

parser = argparse.ArgumentParser()
parser.add_argument("-o",
                    "--logfile",
                    type=str,
                    help="output file")
parser.add_argument("cores", type=str, help="comma-separated list of cores")
args = parser.parse_args()
cores = [int(item) for item in args.cores.split(',')]

logging.basicConfig(level=logging.DEBUG)
d = Daemon(cores=cores, logfile=args.logfile)
d.run()
