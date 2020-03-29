import pandas as pd
import numpy as np
import itertools

def isAuthentic(tfidf_vectorizer, pac, testingSet):
    ## Vocabulary Extraction
    tfidf_test  = tfidf_vectorizer.transform(testingSet['text'])

    ## Testing
    y_pred = pac.predict(tfidf_test)
    
    return y_pred