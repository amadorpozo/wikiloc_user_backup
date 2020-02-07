import requests
import mimetypes
from bs4 import BeautifulSoup
from sys import argv
import json
import string
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


# base USER address of Wikiloc
wikilocBaseUrl="http://www.wikiloc.com/wikiloc/"

# if no using some headers, wikiloc answers HTML error 503, probably they protect their servers against scrapping
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',}

def scrapTrailListPage(userUrl):
    """Scrap all the trails of a certain user""" 

    trailUrls=[]
    print("Scrapping trail list %s" % userUrl)
    response=requests.get(userUrl, headers=headers)
    soup=BeautifulSoup(response.text, "lxml")

    trailUrlList = soup.find_all("a", class_="trail-title")
    for trailUrl in trailUrlList:
        trailUrls.append(trailUrl.get("href"))

    # searching next page
    nextA = soup.find("a", class_="next")
    if nextA!=None:
        nextUrl=nextA.get("href")
        return trailUrls, nextUrl
    else:
        print("Scrapping done")
        return trailUrls, None

def scrapTrailListAllPages(startUrl):
    trailUrls=[]
    nextPage=startUrl
    while (nextPage):
        trailUrlsPerPage,nextPage=scrapTrailListPage(nextPage)
        trailUrls=trailUrls+trailUrlsPerPage
    #print(trailUrls)
    return trailUrls

def scrapUsername(userUrl):
    """Scrap username""" 
    response=requests.get(userUrl, headers=headers)
    soup=BeautifulSoup(response.text, "lxml")
    username=soup.find("h1", class_="profile").text
    print("Scrapping %s for username=%s" % (userUrl, username))
    return username

def scrapTrailInfo(trailUrl):
    """Scrap all information of a single trail, like
    GPX track, title, photos, description or dates""" 

    print("Scrapping trail: %s" % trailUrl)
    response=requests.get(trailUrl, headers=headers)
    soup=BeautifulSoup(response.text, "lxml")
    #for debugging offline
    # with open("Wikiloc_example.htm","r", encoding='utf-8') as file: 
    #     response=file.read()
    #     soup=BeautifulSoup(response, "lxml")
    trailInfo={}
    # Trail activity, title, date and description
    trailInfo["author"]= soup.find("div", class_="user-info").find("a").text
    
    trailInfo["activity"]= soup.find("div", class_="trail-title clearfix").find("a").get("title")
    trailInfo["title"] = soup.find("h1").text.strip()
    for i in soup.find_all("h4"):
        if i.text.startswith("Recorded"):
            date=i.text.split()
            trailInfo["recorded_date"]={}
            trailInfo["recorded_date"]["month"]=date[1]
            trailInfo["recorded_date"]["year"]=date[2]
        if i.text.startswith("Uploaded"):
            date=i.text.split()
            trailInfo["uploaded_date"]={}
            trailInfo["uploaded_date"]["month"]=date[1]
            trailInfo["uploaded_date"]["day"]=date[2].split(",")[0]
            trailInfo["uploaded_date"]["year"]=date[3]
    trailInfo["description"]=soup.find("div", class_="description dont-break-out").text
    # Photos
    trailInfo["photos"]=[]
    # step 1: get link to photo slideshow
    photoUrls=[]
    for photo in soup.find_all("a", class_="trail-photo"):
        photoUrls.append("https://www.wikiloc.com"+photo.get("href"))
    #print(photoUrls)
    # step 2: get image URL for downloading
    for photoUrl in photoUrls:
        trailInfo["photos"].append(scrapPhoto(photoUrl))
    # GPX track
    trailInfo["gpxDownloadUrl"]=soup.find("a", class_="btn btn-lg btn-success btn-download").get("href")
    #print(trailInfo)
    return trailInfo

def scrapPhoto(photoUrl):
    """Scrap the URL of the slideshow and gets the URL of the photo file"""

    print("Scrapping photo: %s" % photoUrl)
    response=requests.get(photoUrl, headers=headers)
    soup=BeautifulSoup(response.text, "lxml")
    return soup.find("img", class_="photo").get("src")

def downloadPhoto(photoUrl, filename):
    print("Downloading photo: %s" % photoUrl, end="")
    response = requests.get(photoUrl, headers=headers)
    content_type = response.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    with open(filename+extension, 'wb') as handler:
        handler.write(response.content)
    print(", saved in %s"%filename+extension)

def downloadGpxTrack(url, filename):
    """Get the download page and "navigate" with Selenium to get the GPX track"""
    print("Downloading GPX track: %s" % url, end="")
    driver = webdriver.Firefox()
    driver.get(url)
    assert "Wikiloc" in driver.title
    elem = driver.find_element_by_name("q")
    elem.clear()
    elem.send_keys("pycon")
    elem.send_keys(Keys.RETURN)
    assert "No results found." not in driver.page_source
    driver.close()
    
    extension=".gpx"
    # content_type = response.headers['content-type']
    # extension = mimetypes.guess_extension(content_type)
    # with open(filename+extension, 'wb') as handler:
    #     handler.write(response.content)
    print(", saved in %s"%filename+extension)

def downloadTrail(trailDict, username, dir_suffix):
    """ download and save the photos and GPX. And save the trail info as json"""
    filename=decideTrailFilename(trailDict)
    backup_dir="wikiloc_backup_"+username+dir_suffix
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    trail_dir=backup_dir+"/"+filename+"/"
    if not os.path.exists(trail_dir):
        os.makedirs(trail_dir)
    print("Saving %s in folder %s" % (trailDict["title"], trail_dir))

    with open(trail_dir+"trailInfo.json", "w+") as file:
        file.write(json.dumps(trailDict,indent=4))
    downloadPhoto(trailDict["gpxDownloadUrl"], trail_dir+"gps_track")
    for i,photo in enumerate(trailDict["photos"],start=1):
        downloadPhoto(photo, trail_dir+"photo"+str(i))


def decideTrailFilename(trailInfo):
    trail_filename=""
    trail_filename+=trailInfo["uploaded_date"]["year"]
    trail_filename+=convertMonthNameToNumber(trailInfo["uploaded_date"]["month"])
    trail_filename+="%02d"%int(trailInfo["uploaded_date"]["day"])
    trail_filename+="_"
    trail_filename+=trailInfo["activity"]
    trail_filename+="_"
    trail_filename+=trailInfo["title"]
    trail_filename=trail_filename.replace(" ", "-")
    valid_chars = "-_%s%s" % (string.ascii_letters, string.digits)
    trail_filename=''.join(c for c in trail_filename if c in valid_chars)
    return trail_filename[0:100] #up to 100 chars, just in case

def convertMonthNameToNumber(MonthName):
    MonthNameToNumberDict={"january":"01", 
                        "february":"02", 
                        "march":"03", 
                        "april":"04", 
                        "may":"05", 
                        "june":"06", 
                        "july":"07", 
                        "august":"08", 
                        "september":"09", 
                        "october":"10", 
                        "november":"11", 
                        "december":"12"}
    return MonthNameToNumberDict[MonthName.lower()]

def main():
    downloadGpxTrack("https://www.wikiloc.com/wikiloc/download.do?id=41909654", "test")

    exit()
    if len(argv)>1:
        if argv[1].isdigit(): 
            url=wikilocBaseUrl+"user.do?id="+argv[1]
        else:
            url=wikilocBaseUrl+"user.do?name="+argv[1]

    else:
        print("Please enter your Wikiloc Username or User-ID")
        exit()

    # get username for backup folder
    username=scrapUsername(url)
    #TODO: check for logged-in? maybe not needed
    print(username)

    exit()

    myTrailUrls=scrapTrailListAllPages(url)
    print(myTrailUrls)
    # myTrailUrls=['https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-3-manana-44421576']
    # myTrailUrls+=['https://www.wikiloc.com/walking-trails/caminata-al-parrizal-de-beceite-41909654']
    for url in myTrailUrls:
        trailInfo=scrapTrailInfo(url)
        downloadTrail(trailInfo, username, "_own_trails")
    
    participatedTrailUrls=scrapTrailListAllPages(url+"&event=trails")
    print(participatedTrailUrls)
    for url in participatedTrailUrls:
        trailInfo=scrapTrailInfo(url)
        downloadTrail(trailInfo, username, "_participated_trails")

    favoritedTrailUrls=scrapTrailListAllPages(url+"&event=listfavorites")
    print(favoritedTrailUrls)
    for url in favoritedTrailUrls:
        trailInfo=scrapTrailInfo(url)
        downloadTrail(trailInfo, username, "_favorited_trails")


if __name__ == "__main__":
    main()