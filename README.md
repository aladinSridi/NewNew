# NewNew 
**NewNew is a web platform for serving news accompanied by a machine learning algorithm to detect authenticity.**


[Module - Authenticity Detection]
---
- This is where the machine learning algorithm resides.
- The algorithm itself is devided to two sub-modules:
    + authenticityDetector.py : Responsible for the learning process returning a tfidf_vectorizer and a Passive Aggressive Classifier(PAC)
    + isAuthentic.py : Responsible for the prediction process taking the vectorizer, the PAC and the testing set and returning the predictions as an ndarray 
- The training set is a csv file:
    + Named trainingSet.csv
    + With 4 columns: id - title - text - label
    + The label being one of two values: "REAL" or "FAKE"
    + And resides in the ressources directory of this module
    + It wasn't uploaded because of it's large size. Contact me if needed.


[News_Aggregarot_Website]
---
- This is where the website resides
- Backend:
    + Python v3
    + Django v2
    + SQLITE v3
- Frontend:
    + Django templates


[Local Set Up]
---
- Clone the repositry
- cd News_Aggregarot_Website
- python3 manage.py runserver


[Remote Hosting Service]
---
- visit: https://aladinsridi.pythonanywhere.com/


[Usage]
---
- /home     : Initial Page
- /blog     : Aggregation Page
- /contact  : Contact Page
- /scrape   : Does website scraping and authenticity detection
- /test     : Light Testing Page for the scraping process
