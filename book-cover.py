#this is the version of the book cover webpage generator that
#does not use opencv.   you still need a bing id and a project oxford key.
#both are easy to geth.   
import httplib, urllib, urllib2, base64
import time
import json
import picamera

camera = picamera.PiCamera()
camera.resolution = (2592, 1944)
time.sleep(2)
camera.capture("./image.jpg")

def bing_search(query, search_type):
    #search_type: Web, Image, News, Video
    key= 'YOUR_API_KEY'
    query = urllib.quote(query)
    # create credential for authentication
    user_agent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
    credentials = (':%s' % "your big key here").encode('base64')[:-1]
    auth = 'Basic %s' % credentials
    url = 'https://api.datamarket.azure.com/Data.ashx/Bing/Search/'+search_type+'?Query=%27'+query+'%27&$top=5&$format=json'
    request = urllib2.Request(url)
    request.add_header('Authorization', auth)
    request.add_header('User-Agent', user_agent)
    request_opener = urllib2.build_opener()
    response = request_opener.open(request)
    response_data = response.read()
    json_result = json.loads(response_data)
    result_list = json_result['d']['results']
    #print result_list
    return result_list


def generate_page(oxford_out, bing_list):
        str = '<HEAD> <TITLE>Book Title Reader Output</TITLE> </HEAD> <BODY BGCOLOR="WHITE"> \n'
        str=str+" <CENTER> <H1>Book Title Reader Output</H1> </CENTER> \n"
        str=str+" <H3>The Project Oxford Vision Optical Character Reader produced output </H3>\n"
        str=str+"\n" +  oxford_out + "\n"
        str=str+" <H3>Top 5 Bing results based on this input are </H3>"
        str=str+"<ul> "
        for i in range(len(bing_list)):
                des = bing_list[i]["Description"]
                url = bing_list[i]["Url"]
                str=str+ "<li> "+des + " "+'<a href="'+url+'">'+url+'</a>' +"</li>"
        str = str+"</ul>"
        str = str+"<H3> The image used was </H3> \n "
        str = str+ '<IMG SRC= "image.jpg"  width="500" height="400">'
        f = open("page.html", "wb")
        str = str.encode("ascii", "ignore")
        f.write(str)

def find_info(query):
    w = bing_search(query, 'Web')
    generate_page(query, w)
    for i in range(0, len(w)):
        print w[i]["Url"]
    s = w[0]["Description"] +" " + w[1]["Description"] +" " + w[2]["Description"]
    return s




headers1 = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'your oxford key here',
}

f = open("./image.jpg", "rb")
im = f.read()

params = urllib.urlencode({
    'language': 'en',
    'detectOrientation ': 'true',
})

try:
    conn = httplib.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/vision/v1/ocr?%s" % params, im, headers1)
    response = conn.getresponse()
    data = response.read()
    #print(data)
    conn.close()
except Exception as e:
    print (e)
    #print("[Errno {0}] {1}".format(e.errno, e.strerror))

x = json.loads(data)

#find_info(" michael chriton")

try:
    ab = x["regions"][0]["lines"]
    st = ""
    for i in range(len(ab)):
        xt = ab[i]["words"]
        for w in xt:
                st = st + " "+ w["text"]
    print st
    st = st.encode("ascii", "ignore")
    try:
        info = find_info(st)
    except:
        info = "bad search string"
    print "info ................ "
    print info
except:
    print("failed to see any words")


print("done")
