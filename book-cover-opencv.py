#this is the version of the book cover app.   it
#is partly derived from the examples from 
#https://www.pyimagesearch.com/practical-python-opencv/?src=sidebar-single-weekend
#and the opecv docs and the public oxford api.
#you need two sets of credentials
# bing  and project oxford.  you can get those easily.

import numpy as np
import argparse
import time
import cv2
import httplib, urllib, urllib2, base64
import json
from picamera.array import PiRGBArray
from picamera import PiCamera


# define the upper and lower boundaries for a color
# to be considered "blue"
#let's make blue white
blueLower = np.array([140, 140, 140], dtype = "uint8")
blueUpper = np.array([255, 255, 255], dtype = "uint8")

def check_rotate(pt):
    newpt = np.array([[0,0],[0,0],[0,0],[0,0]], np.int32)
    if np.linalg.norm(pt[0]-pt[1]) < np.linalg.norm(pt[0]-pt[3]):
        newpt[0]=pt[3]
        newpt[3]=pt[2]
        newpt[2]=pt[1]
        newpt[1]=pt[0]
        return newpt
    else:
        return pt

def bing_search(query, search_type):
    #search_type: Web, Image, News, Video
    key= 'YOUR_API_KEY'
    query = urllib.quote(query)
    # create credential for authentication
    user_agent = 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; FDM; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 1.1.4322)'
    credentials = (':%s' % "your bing credentials here").encode('base64')[:-1]
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
        #str = str+ '<IMG SRC= "image.jpg"  width="500" height="400">'
        str = str+  '<IMG SRC= "rectangle.jpg"  width="500" height="400">'
        str = str+  '<IMG SRC= "rectangle-capture.jpg"  width="500" height="400">'
        f = open("page.html", "wb")
        str = str.encode("ascii", "ignore")
        f.write(str)

def find_info(query):
    w = bing_search(query, 'Web')
    generate_page(query, w)
    s = w[0]["Description"] +" " + w[1]["Description"] +" " + w[2]["Description"]
    return s

#print find_info(" MICHAEL CRICHTON HERS ceoce coo")

time.sleep(1)
camera = PiCamera()
camera.resolution = (2592, 1944)
rawCapture = PiRGBArray(camera)
time.sleep(0.1)

for tries in range(1):
    camera.capture(rawCapture, format="bgr")
    frame = rawCapture.array
    #rawCapture.truncate(0)
    blue = cv2.inRange(frame, blueLower, blueUpper)
    blue = cv2.GaussianBlur(blue, (3, 3), 0)

    # find contours in the image
    x = cv2.findContours(blue.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = x[0]
    # check to see if any contours were found
    dst = None
    if len(cnts) > 0:
        for i in range(0, len(cnts)):
            cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[i]
            orect = np.int32(cv2.cv.BoxPoints(cv2.minAreaRect(cnt)))
            area = cv2.contourArea(cnt)
            print "area("+str(i)+")="+str(area)
            #the following hack is to exclude rectalges that are celling patches
            if  orect[0][0] < 2200 and orect[0][1]> 1000:
               break
        rect = check_rotate(orect)
        #rect = orect
        cv2.drawContours(frame, [rect], -1, (0, 255, 0), 2)
        #pts1 = np.float32([rect[0], rect[1], rect[3], rect[2]])

        pts1 = np.float32([rect[2], rect[3],  rect[1], rect[0]])
        pts2 = np.float32([[0,0],[500,0],[0,300],[500,300]])

        M = cv2.getPerspectiveTransform(pts1,pts2)

        img0 = cv2.warpPerspective(frame, M,(500,300))
        img = img0 #cv2.cvtColor(img0, cv2.COLOR_BGR2GRAY)
        M = cv2.getRotationMatrix2D((350,150),90,1)
        dst = cv2.warpAffine(img,M,(500,500))
        dst = img
    # show the frame and the binary image
    #cv2.imshow("Tracking", frame)
    if dst.any():
        #cv2.imshow("paper", dst)
        cv2.imwrite("rectangle.jpg",frame)
        dst = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY)
        cv2.imwrite("rectangle-capure.jpg", dst)

        break
print rect

#camera.release()

headers1 = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'your oxford key goes here',
}
params3 = urllib.urlencode({
    # Request parameters
    'language': 'en',
    'detectOrientation ': 'true',
})

#better fix this path so it works for you
f = open("/home/pi/rectangle-capure.jpg", "rb")
im = f.read()
try:
    conn = httplib.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/vision/v1/ocr?%s" % params3, im, headers1)
    response = conn.getresponse()
    data = response.read()
    #print(data)
    conn.close()
except Exception as e:
     print(e)
    #print("[Errno {0}] {1}".format(e.errno, e.strerror))

x = json.loads(data)
try:
    ab = x["regions"][0]["lines"]
    st = ""
    for i in range(len(ab)):
        xt = ab[i]["words"]
        for w in xt:
                st = st + " "+ w["text"]
    print st
    print type(st)
    sta = st.encode("ascii","ignore")
    print sta
    print type(sta)
    sta = sta.lower()
    try:
        info = find_info(sta)
    except:
        info = "bad search string"
    print "info ................ "
    print info
except:
    print("failed to see any words")


print("done")
