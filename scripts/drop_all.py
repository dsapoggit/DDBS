import pandas as pd
from pymongo import InsertOne, MongoClient
import numpy as np
import json
from time import time

TEST_RUN = 0
GROUP_SIZE = 20

def db():
    return MongoClient('localhost', 30000).ddbs

if __name__ == '__main__':
    db().region_b.drop()
    db().region_h.drop()

    db().category_s.drop()
    db().category_t.drop()

    db().read_b.drop()
    db().read_h.drop()

    db().read_cat_s.drop()
    db().read_cat_t.drop()

    db().popular_d.drop()
    db().popular_w.drop()
    db().popular_m.drop()