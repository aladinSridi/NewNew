# Project Modules
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from datetime import datetime
from django.utils.timezone import make_aware
import json
import re
import pytz
import sys
sys.path.append('../Module - Authenticity Detection')


# Machine Learning Modules
from authenticityDetector import authenticityDetector
from isAuthentic import isAuthentic
import pandas as pd
import itertools
import numpy as np


# Scrapping Modules
import requests
import urllib3
from django.http import HttpResponse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup as BSoup


# Data Base Modules
from news.models import article
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from ipware import get_client_ip
from urllib.request import urlopen


# Create your views here.
def test(request):
    politics = article.objects.all().filter(category="politics").order_by('-date')
    entertainments = article.objects.all().filter(category="entertainment").order_by('-date')
    sports = article.objects.all().filter(category="sports").order_by('-date')
    health = article.objects.all().filter(category="health").order_by('-date')
    technology = article.objects.all().filter(category="technology").order_by('-date')
    local = article.objects.all().filter(category="local").order_by('-date')

    context = {
        'politics': politics,
        'entertainments': entertainments,
        'sports': sports,
        'technology': technology,
        'health': health,
        'local': local,
    }

    return render(request, "test.html", context)


def home(request):
    # Recent Articles
    recents = article.objects.all().order_by('-date')[:4]

    # Filter Analysis
    position = ""
    for key, val in request.GET.dict().items():
        if(key == "position"):
            position = val


    context = {
        'recents'  : recents,
        'position' : position,
    }
    
    return render(request, "index.html", context)


def blog(request):
    # Recent Articles
    recents = article.objects.all().order_by('-date')[:4]

    # Filter Analysis
    city =""
    lref = ""
    ip, is_routable = get_client_ip(request)
    if ip is None:
        print("Unable to fetch IP Address")
    else:
        if is_routable:
            print('Public IP Address detected')
            url = 'http://ipinfo.io/'+ip+'/json'
            response = urlopen(url)
            data = json.load(response)
            city = data['city']
        else:
            print('Private IP Address detected')
            city = "Tunisia"                                                    # Private IP Address Location  <-------
    
    if(city == "Tunisia"):
        lref = "alchourouk"
    if(city == "Algeria"):
        lref = "elkhabar"


    checks = {}
    lookup = Q()
    sLocals = False
    if(len(request.GET.dict()) == 0):
        checks['local'] = "on"
        checks['sports'] = "on"
        checks['health'] = "on"
        checks['politics'] = "on"
        checks['technology'] = "on"
        checks['entertainment'] = "on"
        checks['medium'] = "on"
        checks['theonion'] = "on"
        lookup = (Q(reference__in=['medium','theonion',lref]))

    else:
        for key, val in request.GET.dict().items():
            if(key == "keyword"):
                lookup = (Q(title__contains=val) | Q(text__contains=val))
                checks['keyword'] = val

    
            if(key == "category"):
                cats = str(val).split(' ')
                if(cats[0] == ''):
                    cats.pop(0)

                if(lookup is None):
                    lookup = (Q(category__in=cats))
                else:
                    lookup &= (Q(category__in=cats))

                for c in cats:
                    checks[c] = "on"
                    if(c == "local"):
                        if "reference" in request.GET.dict():
                            sLocals = True
                        else:
                            sLocals = True
                            if(lookup is None):
                                lookup = (Q(reference__in=[lref]))
                            else:
                                lookup &= (Q(reference__in=[lref]))


            if(key == "reference"):
                refs = str(val).split(' ')

                if(refs[0] == ''):
                    refs.pop(0)

                if(sLocals):
                    refs.append(lref)
                
                if(lookup is None):
                    lookup = (Q(reference__in=refs))
                else:
                    lookup &= (Q(reference__in=refs))

                for r in refs:
                    checks[r] = "on"


        if  ("reference" not in request.GET.dict()):
            if(not sLocals):
                if(lookup is None):
                    lookup = (Q(reference__in=[]))
                else:
                    lookup &= (Q(reference__in=[]))

        if  ("category" not in request.GET.dict()):
            if(lookup is None):
                lookup = (Q(category__in=[]))
            else:
                lookup &= (Q(category__in=[]))

       

    results = article.objects.filter(lookup).order_by('-date')

    # Article Count
    politicsCount = results.filter(category="politics").count()
    entertainmentsCount = results.filter(category="entertainment").count()
    sportsCount = results.filter(category="sports").count()
    healthCount = results.filter(category="health").count()
    technologyCount = results.filter(category="technology").count()
    localCount = results.filter(category="local").filter(reference=lref).count()


    paginator = Paginator(results, 5)
    page = request.GET.get('page')

    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)




    # Context

    context = {
        'recents': recents,
        'results': results,
        'checks' : checks,
        'politicsCount' : politicsCount,
        'entertainmentsCount'  : entertainmentsCount,
        'sportsCount'  : sportsCount,
        'healthCount'  : healthCount,
        'technologyCount' :  technologyCount,
        'localCount'  : localCount,
    }

    return render(request, "blog.html", context)


def contact(request):
    return render(request, "contact.html")


def scrape(request):
    # Scrapping "www.theonion.com"
    print('\nScrapping "www.theonion.com"')
    theOnionScraper("https://politics.theonion.com")
    theOnionScraper("https://sports.theonion.com")
    theOnionScraper("https://entertainment.theonion.com")
    

    # Scrapping "www.medium.com"
    print('\nScrapping "www.medium.com"')
    mediumScraper("https://medium.com/topic/politics")
    mediumScraper("https://medium.com/topic/technology")
    mediumScraper("https://medium.com/topic/health")
    mediumScraper("https://medium.com/topic/humor")


    # Scrapping local news
    print('\nScrapping Local News')
    tunisiaScraper()
    algeriaScraper()


    # Detecting Authenticity
    authenticityDetection()

    return render(request, "index.html")


def algeriaScraper():
    url = "https://www.elkhabar.com"
    print("\nScraping elkhabar for local news - Please Wait!")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    content = session.get(url, verify=False).content
    
    parsedContent = BSoup(content, "html.parser")
    articleTags = parsedContent.find_all('a', {"class": "main_article highlighted_article"})

    print("[Done]: Detected {} Articles".format(len(articleTags)))
    artNum = 0
    for articleTag in articleTags:
        artNum += 1
        if (artNum > 0):
            print("[Done]: {}/{} Articles Treated".format(artNum, len(articleTags)))

        category = "local" 
        reference = "elkhabar"       
        image_src = ""
        title = ""
        link = ""
        text = ""
        date = ""

        try:
            imageDiv = articleTag.find_all('div', {"class": "thumbnail has_gradient "})[0]
            image_src = str(imageDiv['style'])
            image_src = "https://www.elkhabar.com" + image_src[23:-3] 

            title = articleTag.find_all('div', {"class": "title"})[0].get_text()

            link = "https://www.elkhabar.com" + articleTag['href']

            text = articleTag.find_all('div', {"class": "description"})[0].get_text()

            dateDiv = articleTag.find_all('time', {"class": "relative_time"})[0]
            date = str(dateDiv['datetime'])[:-5]
            date = datetime.strptime(date, "%Y-%m-%dT%H:%M")
            date = pytz.utc.localize(date)
        except:
            break


        if(image_src != "") and (image_src != None) and (title != "") and (title != None) and (link != "") and (link != None) and (date != None) and (text != "") and (text != None):
            if ((article.objects.all().filter(reference=reference).filter(link=link).filter(title=title)).count() == 0):
                new_article = article()
                new_article.reference = reference
                new_article.image_src = image_src
                new_article.title = title
                new_article.link = link
                new_article.text = text
                new_article.date = date
                new_article.category = category
                new_article.save()


def tunisiaScraper():
    url = "http://www.alchourouk.com"
    print("\nScraping alchourouk for local news - Please Wait!")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    content = session.get(url, verify=False).content
    
    parsedContent = BSoup(content, "html.parser")
    articleTags = parsedContent.find_all('div', {"class": "row-article views-row"})
    
    print("[Done]: Detected {} Articles".format(len(articleTags)))
    artNum = 0
    for articleTag in articleTags:
        artNum += 1
        if (artNum > 0):
            print("[Done]: {}/{} Articles Treated".format(artNum, len(articleTags)))

        category = "local" 
        reference = "alchourouk"       
        image_src = ""
        title = ""
        link = ""
        text = ""
        date = ""
        
        try:
            textParent = articleTag.find_all('div', {"class": "views-field views-field-body"})[0]
            text = textParent.find_all('div')[0].string

            dateParent = articleTag.find_all('div', {"class": "views-field views-field-created"})[0]
            date = dateParent.find_all('span')[0].string
            date = datetime.strptime(date, '%H:%M - %Y/%m/%d')
            date = pytz.utc.localize(date)
            
            titleParent = articleTag.find_all('div', {"class": "views-field views-field-title"})[0]
            titleTag = titleParent.find_all('a')[0]
            title = titleTag.string
            link = "http://www.alchourouk.com" + titleTag['href']
            
            imageParent = articleTag.find_all('div', {"class": "views-field views-field-field-image"})[0]
            imageTag = imageParent.find_all('img')[0]
            image_src = "http://www.alchourouk.com" + imageTag['src']
        except:
            break


        if(image_src != "") and (image_src != None) and (title != "") and (title != None) and (link != "") and (link != None) and (date != None) and (text != "") and (text != None):
            if ((article.objects.all().filter(reference=reference).filter(link=link).filter(title=title)).count() == 0):
                new_article = article()
                new_article.reference = reference
                new_article.image_src = image_src
                new_article.title = title
                new_article.link = link
                new_article.text = text
                new_article.date = date
                new_article.category = category
                new_article.save()


def mediumScraper(url):
    print("\nScraping medium for "+re.search('[^\/]+(?=\/$|$)',url).group(0)+" - Please Wait!")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    msession = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    msession.mount('http://', adapter)
    msession.mount('https://', adapter)
    msession.headers = {
            'Cookie': '__cfduid=dd4f7b7d7936c21127eb6d48b4a0ee9001585131688; uid=2dda3e433158; sid=1:qdVvOcFmyNVCQzGnG1EsuBcveYCIhUcDSClwRJveFwhwyDbdI7CLJzT/u7C84cDq; optimizelyEndUserId=2dda3e433158; __cfruid=581a981c177f34e3311a8641339d108e7dbf35b8-1585131688; _ga=GA1.2.2075182282.1585131692; _gid=GA1.2.134750316.1585131692; lightstep_guid/lite-web=76d8b344220f307e; lightstep_session_id=3e330350586d148d; _parsely_visitor={%22id%22:%22pid=c86dbaf3534f84cbbe151b9ece8e2d19%22%2C%22session_count%22:3%2C%22last_session_ts%22:1585160155715}; lightstep_guid/medium-web=e7dd31de6c55f151; sz=1908; pr=1; tz=-60; _parsely_session={%22sid%22:3%2C%22surl%22:%22https://medium.com/topics%22%2C%22sref%22:%22%22%2C%22sts%22:1585160155715%2C%22slts%22:1585135309136}; xsrf=ZR0Ku2CYhMUD'
        }
    mcontent = msession.get(url, verify=False).content

    mParsedContent = BSoup(mcontent, "html.parser")
    mScriptTags = mParsedContent.find_all('script')
    
    for st in mScriptTags:
        try:
            if (len(st.string) > 5000):
                jsstr = st.string
        except:
            continue

    jsfile = json.loads(jsstr[26:])
    jsfile = dict(filter(lambda item: 'Post' in item[0], jsfile.items())) 
    jsfile = dict(filter(lambda item: 'preview' not in item[0].lower(), jsfile.items())) 
    jsfile = dict(filter(lambda item: 'politics' not in item[0].lower(), jsfile.items())) 
    jsfile = dict(filter(lambda item: 'technology' not in item[0].lower(), jsfile.items())) 


    reference = "medium"
    image_src = ""
    title = ""
    link = ""
    text = ""
    date = ""
    category = ""

    print("[Done]: Detected {} Articles".format(len(jsfile)))
    artNum = 0
    for k, v in jsfile.items():
        artNum += 1
        if (artNum > 0):
            print("[Done]: {}/{} Articles Treated".format(artNum, len(jsfile)))


        try:
            title = v['title']
            link = v['mediumUrl']
            date = datetime.fromtimestamp(int(v['firstPublishedAt'])/1000)
            date = pytz.utc.localize(date)
            image_src = "https://miro.medium.com/max/2119/"+v['previewImage']['id'][14:]
        except:
            try:
                title = v['title']
                link = v['mediumUrl']
                date = datetime.fromtimestamp(int(v['updatedAt'])/1000)
                date = pytz.utc.localize(date)
                image_src = "https://miro.medium.com/max/2119/"+v['previewImage']['id'][14:] 
            except:
                title = ""
                link = ""
                date = ""
                image_src = ""
        
        if(image_src != "") and (image_src != None) and (title != "") and (title != None) and (link != "") and (link != None) and (date != None):
                if ((article.objects.all().filter(reference="medium").filter(link=link).filter(title=title)).count() == 0):
                    
                    if(url == "https://medium.com/topic/politics"):
                        category = "politics"

                    if(url == "https://medium.com/topic/technology"):
                        category = "technology"

                    if(url == "https://medium.com/topic/humor"):
                        category = "entertainment"

                    if(url == "https://medium.com/topic/health"):
                        category = "health"

                    articleContent = msession.get(link, verify=False).content
                    parsedAC = BSoup(articleContent, "html.parser")
                    arScriptTags = parsedAC.find_all('script')


                    for ast in arScriptTags:
                        try:
                            if (len(ast.string) > 5000):
                                arjsstr = ast.string
                        except:
                            continue

                    arjsfile = json.loads(arjsstr[26:])
                    arjsfile = dict(filter(lambda item: 'Paragraph' in item[0], arjsfile.items())) 


                    longestDesc = 0
                    for k, v in arjsfile.items():
                        try:
                            if (len(v['text']) > longestDesc):
                                longestDesc = len(v['text'])
                                text = v['text']
                        except:
                            continue
                    

                    if(text != "") and (text != None):      
                        new_article = article()
                        new_article.reference = reference
                        new_article.image_src = image_src
                        new_article.title = title
                        new_article.link = link
                        new_article.text = text
                        new_article.date = date
                        new_article.category = category
                        new_article.save()


def theOnionScraper(url):
    print("\nScraping theonion for "+re.search('(?<=\/\/)(.*?)(?=\.)',url).group(1)+" - Please Wait!")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.headers = {"User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0"}
    content = session.get(url, verify=False).content

    parsedContent = BSoup(content, "html.parser")
    main = parsedContent.find_all('main')[0]
    articleTags = main.find_all('article')

    print("[Done]: Detected {} Articles".format(len(articleTags)))
    artNum = 0
    for articleTag in articleTags:
        artNum += 1
        if (artNum > 0):
            print("[Done]: {}/{} Articles Treated".format(artNum, len(articleTags)))

        reference = "theonion"
        image_src = ""
        title = ""
        link = ""
        text = ""
        date = ""
        category = ""
        
        try:
            dateStr = articleTag.find_all('div', {"class": "sc-3nbvzd-1 VhErj"})[0].string +" "+  articleTag.find_all('div', {"class": "sc-3nbvzd-1 VhErj"})[1].string
            date = datetime.strptime(dateStr, '%m/%d/%y %I:%M %p')
            date = pytz.utc.localize(date)
        except:
            date = None


        aTags = articleTag.find_all('a')
        for a in aTags:
            if len(a.find_all('img')) > 0:
                i = a.find_all('img')[0]
                try:
                    if i['data-srcset']:
                        try:
                            image_src = str(i['data-srcset']).split(" ")[-4]
                        except:
                            image_src = ""

                except KeyError:
                    try:
                        if i['srcset']:
                            try:
                                image_src = str(i['srcset']).split(" ")[-4]
                            except:
                                image_src = ""
                    except KeyError:
                        image_src = ""
           

            if len(a.find_all('h2')) > 0:
                try:
                    if a['href']:
                        try:
                            link = a['href']
                        except:
                            link = ""              
                except KeyError:
                        link = ""

                try:
                    title = a.find_all('h2')[0].string
                except:
                    title = ""
            else:
                title = ""



        if(image_src != "") and (image_src != None) and (title != "") and (title != None) and (link != "") and (link != None) and (date != None):
            if ((article.objects.all().filter(reference="theonion").filter(link=link).filter(title=title)).count() == 0):
                articleContent = session.get(link, verify=False).content
                parsedAC = BSoup(articleContent, "html.parser")
                main = parsedAC.find_all('main')[0]
                
                try:
                    p = main.find_all('p', {"class": "sc-77igqf-0 hJpRRP"})[0]
                    text = p.string
                except:
                    try:
                        figure = main.find_all('figure')[0]
                        if(len(figure.next_sibling.string)>20):
                            text = figure.next_sibling.string
                        else:
                            raise Exception
                    except:
                        try:
                            text = figure.next_sibling.next_sibling.string
                        except:
                            text = ""

                if(text != "") and (text != None):
                    if(url == "https://politics.theonion.com"):
                        category = "politics"

                    if(url == "https://entertainment.theonion.com"):
                        category = "entertainment"                      


                    if(url == "https://sports.theonion.com"):
                        category = "sports"

                    new_article = article()
                    new_article.reference = reference
                    new_article.image_src = image_src
                    new_article.title = title
                    new_article.link = link
                    new_article.text = text
                    new_article.date = date
                    new_article.category = category

                    new_article.save()


def authenticityDetection():
    print('\nStarting -- Detecting Authenticity')

    # Fetching Untested Articles
    testArticles = article.objects.all().filter(category="politics").filter(reference="theonion").filter(label="")
    print("\n[Done]: Deteced {} new articles".format(testArticles.count()))

    if (testArticles.count()>0):
        # Machine Learning
        print("\nMachine is learning - Please wait!")
        tfidf_vectorizer, pac = authenticityDetector()
        print("[Done]: ML Complete")

        # Data Analysis
        print("\nAnalysing your data - Please wait!")
        df = pd.DataFrame()
        textList = testArticles.values_list('text', flat=True)
        df['text'] = np.array(textList)
        results = isAuthentic(tfidf_vectorizer, pac, df)
        results_list = results.tolist()
        print("[Done]: Analysis Complete")

        # Updating database
        print("\nUpdating database - Please wait!")
        i = 0
        for a in testArticles:
            a.label = results_list[i]
            a.save()
            i += 1
        print("[Done]: Update Complete")

    print("\nEnding -- Detecting Authenticity\n")