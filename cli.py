import sys
import os

import main

if len(sys.argv) < 3:
    print("Usage: define [word]")
    exit()

pd = main.PyDictionary() 
pd.define_word(sys.argv[2])

