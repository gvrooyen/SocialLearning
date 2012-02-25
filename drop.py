import pymongo
import argparse

parser = argparse.ArgumentParser(description="Drop a collection from the local SocialLearning database")
parser.add_argument('deme', type=str, default='default', help="The name of the genetic programming deme")
args = parser.parse_args()

conn = pymongo.Connection()
db = conn.SocialLearning
db.drop_collection(args.deme)
