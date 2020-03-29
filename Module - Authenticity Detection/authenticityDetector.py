import pandas as pd
import itertools
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import PassiveAggressiveClassifier

def authenticityDetector():
    ## Reading Training Data
    trainingSet = pd.read_csv('/home/loudin/Desktop/Mini Projet/Module - Authenticity Detection/ressources/trainingSet.csv')
    labels = trainingSet.label

    ## Initializing a TfidfVectorizer 
    tfidf_vectorizer = TfidfVectorizer(stop_words='english', max_df=0.7)

    ## Vocabulary Extraction
    tfidf_train = tfidf_vectorizer.fit_transform(trainingSet['text'])  

    ## Training the PassiveAggressiveClassifier
    pac = PassiveAggressiveClassifier(max_iter=50)
    pac.fit(tfidf_train, labels)

    return tfidf_vectorizer, pac
