# Copyright (c) 2012 Stellenbosch University, 2012
# This source code is released under the Academic Free License 3.0
# See https://github.com/gvrooyen/SocialLearning/blob/master/LICENSE for the full text of the license.
# Author: G-J van Rooyen <gvrooyen@sun.ac.za>

"""
Drop a collection from the local SocialLearning MongoDB database.
This script is intended to be run from the command line.
"""

import pymongo
import argparse

parser = argparse.ArgumentParser(description="Drop a collection from the local SocialLearning database")
parser.add_argument('deme', type=str, default='default', help="The name of the genetic programming deme")
args = parser.parse_args()

conn = pymongo.Connection()
db = conn.SocialLearning
db.drop_collection(args.deme)
