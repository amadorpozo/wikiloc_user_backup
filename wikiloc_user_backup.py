import requests
import mimetypes
from bs4 import BeautifulSoup
from sys import argv
import json
import string

# base USER address of Wikiloc
wikilocUserUrl="http://www.wikiloc.com/wikiloc/user.do?id="

# if no using some headers, wikiloc answers HTML error 503, probably they protect their servers against scrapping
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',}

def scrapTrailList(userUrl):
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
    print( json.dumps(trailInfo,indent=4))
    return trailInfo

def scrapPhoto(photoUrl):
    """Scrap the URL of the slideshow and gets the URL of the photo file"""

    print("Scrapping photo: %s" % photoUrl)
    response=requests.get(photoUrl, headers=headers)
    soup=BeautifulSoup(response.text, "lxml")
    return soup.find("img", class_="photo").get("src")

def downloadPhoto(photoUrl, filename):
    print("Downloading photo: %s" % photoUrl)
    response = requests.get(photoUrl)
    content_type = response.headers['content-type']
    extension = mimetypes.guess_extension(content_type)
    with open(filename+extension, 'wb') as handler:
        handler.write(response.content)

def saveTrail(trailDict, filename):
    #TODO: download and save the photos and GPX. And save the trailDict as json
    pass

def decideTrailFilename(trailInfo):
    trail_filename=""
    trail_filename+=trailInfo["uploaded_date"]["year"]
    trail_filename+=convertMonthNameToNumber(trailInfo["uploaded_date"]["month"])
    trail_filename+="%02d"%int(trailInfo["uploaded_date"]["day"])
    trail_filename+="_"
    trail_filename+=trailInfo["activity"]
    trail_filename+="_"
    trail_filename+=trailInfo["title"]
    #print(trail_filename)
    trail_filename=trail_filename.replace(" ", "-")
    #print(trail_filename)
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
    # if len(argv)>1:
    #     if argv[1].isdigit(): 
    #         url=wikilocUserUrl+argv[1]
    #     else:
    #         print("Wrong user-id")
    #         exit()
    # else:
    #     print("Wrong user-id")
    #     exit()
    # trailUrls=[]
    # while (url):
    #     trailUrlsPerPage,url=scrapTrailList(url)
    #     trailUrls=trailUrls+trailUrlsPerPage
    # print(trailUrls)

    # trailUrls=['https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-3-manana-44421576', 'https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-2-tarde-44421528', 'https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-2-manana-44421514', 'https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-1-tarde-44421502', 'https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-1-manana-44421243', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-trialeras-de-bajada-en-el-taubenberg-43727772', 'https://www.wikiloc.com/walking-trails/ruta-caminando-gmund-a-tegernsee-por-el-hoehenweg-42948718', 'https://www.wikiloc.com/walking-trails/caminata-al-parrizal-de-beceite-41909654', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-con-sillita-de-nino-munich-andechs-por-el-perlacherforst-41908878', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-wiesenalm-zell-am-ziller-41329648', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-desde-brannenburg-pasando-por-el-reindleralm-37645948', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-con-sillita-nino-por-la-parte-este-del-muenchen-radlring-36852149', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-con-sillita-nino-por-la-parte-norte-del-muenchen-radlring-36851960', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-con-sillita-nino-por-la-parte-suroeste-del-muenchen-radlring-35816502', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-con-sillita-nino-por-a-parte-este-del-muenchen-radlring-34518580', 'https://www.wikiloc.com/bicycle-touring-trails/ruta-en-bici-munich-a-grunwald-de-paseo-con-sillita-de-nino-33193895', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-lenggries-seekarkreuz-lenggries-30499138', 'https://www.wikiloc.com/mountain-biking-trails/lenggries-benitrail-30176823', 'https://www.wikiloc.com/mountain-biking-trails/m-wasserweg-tramo-desde-munich-hasta-furth-y-vuelta-por-unterhaching-29593095', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-al-sur-de-holzkirchen-29393665', 'https://www.wikiloc.com/mountain-biking-trails/mtb-lermoos-a-blindsee-y-vuelta-29126035', 'https://www.wikiloc.com/hiking-trails/paseo-a-andechs-28950025', 'https://www.wikiloc.com/mountain-biking-trails/competicion-en-mtb-enduro-one-2018-en-aschau-im-chiemgau-28949316', 'https://www.wikiloc.com/mountain-biking-trails/big-5-de-saalbach-27776670', 'https://www.wikiloc.com/mountain-biking-trails/ruta-mtb-aschau-kampenwand-27370365', 'https://www.wikiloc.com/hiking-trails/paseo-circular-por-el-giessenbachklamm-27370133', 'https://www.wikiloc.com/mountain-biking-trails/fleckalmtrail-via-kitzbuehel-26368460', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-al-ebersbergerforst-25293822', 'https://www.wikiloc.com/mountain-biking-trails/isartrails-completas-de-munich-a-wolfrathausen-rev2-25114969', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-de-los-3-lagos-tegernsee-spitzingsee-schliersee-25091787', 'https://www.wikiloc.com/mountain-biking-trails/holzkirchen-kreuzstrasse-mangfall-taubenberg-24882959', 'https://www.wikiloc.com/with-baby-carriage-trails/excursion-con-carrito-de-fistenau-a-wandberg-24882849', 'https://www.wikiloc.com/mountain-biking-trails/de-lenggries-a-benedikbeuern-20502597', 'https://www.wikiloc.com/hiking-trails/ruta-circular-tergernseerhutte-buchsteinhutte-19162583', 'https://www.wikiloc.com/mountain-biking-trails/garmisch-esterbergalm-finzbachal-gschwandtnerbauer-18289010', 'https://www.wikiloc.com/hiking-trails/dienten-maria-alm-18243516', 'https://www.wikiloc.com/bicycle-touring-trails/gauting-wurmtal-meisingerbach-andechs-herrsching-am-ammersee-18100903', 'https://www.wikiloc.com/bicycle-touring-trails/visita-al-walderlebniszentrum-de-grunwald-17979359', 'https://www.wikiloc.com/hiking-trails/wanderung-raquetas-hasta-rotwandhaus-16761857', 'https://www.wikiloc.com/mountain-biking-trails/andechs-munich-por-asfalto-16739081', 'https://www.wikiloc.com/mountain-biking-trails/munich-hasta-andechs-por-caminos-y-trialeras-16739063', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-al-ammersee-16646941', 'https://www.wikiloc.com/mountain-biking-trails/munich-gauting-starnbergsee-schaftlarn-munich-16550862', 'https://www.wikiloc.com/mountain-biking-trails/klais-barmsee-kruneralm-wallgaueralm-trails-s2-15355293', 'https://www.wikiloc.com/hiking-trails/kaerlingerhaus-saugasse-stbartholomae-eiskapelle-stbartholomae-14876826', 'https://www.wikiloc.com/hiking-trails/salet-kaerlingerhaus-feldkogel-kaerlingerhaus-14876596', 'https://www.wikiloc.com/mountain-biking-trails/lenggries-roerhtmoosalm-hirschberg-tegernsee-repetida-14638590', 'https://www.wikiloc.com/mountain-biking-trails/isartrails-completas-de-munich-a-wolfrathausen-13968070', 'https://www.wikiloc.com/with-baby-carriage-trails/wanderung-con-kinderwagen-a-rachalm-13682393', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-alrededor-del-zwiesel-hochstaufer-13468849', 'https://www.wikiloc.com/mountain-biking-trails/zoo-grunwald-forstenrieder-park-wurmtal-stanberg-munich-12631737', 'https://www.wikiloc.com/snowshoeing-trails/raquetas-klamm-kreuth-hacia-schildenstein-12201631', 'https://www.wikiloc.com/mountain-biking-trails/isartails-version-n-11692222', 'https://www.wikiloc.com/mountain-biking-trails/lenggries-roerhtmoosalm-hirschberg-tegernsee-11317944', 'https://www.wikiloc.com/hiking-trails/wanderung-partnachklamm-eckbauer-11285637', 'https://www.wikiloc.com/mountain-biking-trails/lenggries-aueralm-schwarzentennalm-11285620', 'https://www.wikiloc.com/hiking-trails/paseo-a-schwarzentennalm-con-kinderwagen-11285586', 'https://www.wikiloc.com/mountain-biking-trails/munich-hasta-stanberg-via-wurmtal-11285583', 'https://www.wikiloc.com/mountain-biking-trails/trialeras-desde-el-zoo-a-wolftrathausen-9855959', 'https://www.wikiloc.com/mountain-biking-trails/ruta-de-bosques-forstenrieder-y-perlacherfrost-9359363', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-por-perlacher-frost-9044593', 'https://www.wikiloc.com/snowshoeing-trails/pequeno-paseo-agg-oberaudof-8828501', 'https://www.wikiloc.com/mountain-biking-trails/isartrails-de-paseo-8164877', 'https://www.wikiloc.com/mountain-biking-trails/drei-seerunde-intentofallido-8119157', 'https://www.wikiloc.com/mountain-biking-trails/garmisch-enningalm-garmisch-8055009', 'https://www.wikiloc.com/mountain-biking-trails/kochelsee-a-herzogstand-7949246', 'https://www.wikiloc.com/mountain-biking-trails/munich-freising-munich-7869248', 'https://www.wikiloc.com/mountain-biking-trails/ruta-por-asturias-dia-4-7869245', 'https://www.wikiloc.com/mountain-biking-trails/ruta-por-asturias-dias-1-2-y-3-7869233', 'https://www.wikiloc.com/mountain-biking-trails/isar-hacia-el-norte-7509710', 'https://www.wikiloc.com/mountain-biking-trails/de-gilching-a-munich-por-carretera-7509703', 'https://www.wikiloc.com/mountain-biking-trails/munich-forstrieder-park-stanberg-andechs-herrsching-7509661', 'https://www.wikiloc.com/mountain-biking-trails/munich-isartrails-wolfrathausen-isartrails-munich-7417130', 'https://www.wikiloc.com/hiking-trails/obergurgl-ramolhaus-langtalereckhutte-obergurgl-7252129', 'https://www.wikiloc.com/hiking-trails/jachenau-wasserfall-7184047', 'https://www.wikiloc.com/mountain-biking-trails/excursion-en-bici-por-el-englischer-garten-7169588', 'https://www.wikiloc.com/mountain-biking-trails/osterhausen-soinsee-rotwandhaus-spitzingsee-neuhaus-7169415', 'https://www.wikiloc.com/mountain-biking-trails/muenchen-isar-trail-forstenrieder-gauting-wurmtal-starnberg-7052145', 'https://www.wikiloc.com/hiking-trails/excursion-junto-al-kuhlbach-desde-graswang-hasta-pista-forestal-6937328', 'https://www.wikiloc.com/mountain-biking-trails/recorrido-por-forstenried-hasta-schaftlarn-y-vuelta-por-el-isar-6937099', 'https://www.wikiloc.com/mountain-biking-trails/100-isar-trails-vuelta-corta-6765343', 'https://www.wikiloc.com/mountain-biking-trails/munich-perlacher-frost-isar-trails-munich-6549090', 'https://www.wikiloc.com/mountain-biking-trails/trialeras-del-isar-2-6403650', 'https://www.wikiloc.com/mountain-biking-trails/bici-por-el-isar-6288256', 'https://www.wikiloc.com/mountain-biking-trails/trialeras-del-isar-6203758', 'https://www.wikiloc.com/hiking-trails/intento-fallido-de-walchensee-hasta-jochberg-6147127', 'https://www.wikiloc.com/mountain-biking-trails/munich-perlacher-frost-isarufer-munich-6062099', 'https://www.wikiloc.com/mountain-biking-trails/excursion-bici-por-el-isar-hacia-el-norte-5984410', 'https://www.wikiloc.com/mountain-biking-trails/paseo-por-el-isar-5959996', 'https://www.wikiloc.com/mountain-biking-trails/trialeras-por-el-isar-hacia-el-sur-intento-1-5959981', 'https://www.wikiloc.com/mountain-biking-trails/ruta-madrid-a-la-bola-del-mundo-siguiendo-el-camino-de-santiago-5162562', 'https://www.wikiloc.com/mountain-biking-trails/vuelta-a-la-casa-de-campo-madrid-en-sentido-anti-horario-5135911', 'https://www.wikiloc.com/mountain-biking-trails/20130811-colmenar-morcuera-canencia-colmenar-5012300', 'https://www.wikiloc.com/hiking-trails/20130804-andando-fuenfria-carretera-republica-miradores-balcon-schmidt-4964738', 'https://www.wikiloc.com/mountain-biking-trails/cercedilla-fuenfria-cotos-cercedilla-4804633', 'https://www.wikiloc.com/mountain-biking-trails/20130427-madrid-a-segovia-por-la-fuenfria-4791254', 'https://www.wikiloc.com/mountain-biking-trails/20130504-vuelta-hoya-y-morcuera-by-aalto-4791239', 'https://www.wikiloc.com/mountain-biking-trails/ruta-sube-y-baja-por-el-pardo-4791236', 'https://www.wikiloc.com/bicycle-touring-trails/4-cno-santiago-bici-morga-bilbao-4791235', 'https://www.wikiloc.com/bicycle-touring-trails/3-cno-santiago-bici-markina-morga-4791233',
    # 'https://www.wikiloc.com/bicycle-touring-trails/2-cno-santigo-bici-zumaia-markina-4791224', 'https://www.wikiloc.com/bicycle-touring-trails/1-cno-santiago-bici-donostia-a-zumaia-4791221']
    
    trailUrls=['https://www.wikiloc.com/mountain-biking-trails/finale-ligure-enduro-mtb-dec-2019-dia-3-manana-44421576']
    trailUrls+=['https://www.wikiloc.com/walking-trails/caminata-al-parrizal-de-beceite-41909654']
    for url in trailUrls:
        trailInfo=scrapTrailInfo(url)
        trail_filename=decideTrailFilename(trailInfo)
        print(trail_filename)


if __name__ == "__main__":
    main()