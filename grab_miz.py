
import argparse

from mizlib import Mizlib



parser = argparse.ArgumentParser()
parser.add_argument('filename')

args = parser.parse_args()

miz = Mizlib(args.filename)


miz.extract_miztxt()