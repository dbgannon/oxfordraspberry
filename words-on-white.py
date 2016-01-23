#this is the code that looks for words on a white rectangle.
#it is adapted from code by Adrian Rosebrock and his is book 
# https://www.pyimagesearch.com/practical-python-opencv/?src=sidebar-single-weekend
import numpy as np
import argparse
import time
import cv2
import httplib, urllib, base64
import json
from picamera.array import PiRGBArray
from picamera import PiCamera


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

time.sleep(1)
camera = PiCamera()
camera.resolution = (2592, 1944)
rawCapture = PiRGBArray(camera)
time.sleep(0.1)


camera.capture(rawCapture, format="bgr")
frame = rawCapture.array
rawCapture.truncate(0)
blue = cv2.inRange(frame, blueLower, blueUpper)
blue = cv2.GaussianBlur(blue, (3, 3), 0)

# find contours in the image
x = cv2.findContours(blue.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = x[0]
# check to see if any contours were found
dst = None
if len(cnts) > 0:
    for i in range(len(cnts)):
        cnt = sorted(cnts, key = cv2.contourArea, reverse = True)[i]
        orect = np.int32(cv2.cv.BoxPoints(cv2.minAreaRect(cnt)))
        print "area("+str(i)+")="+str(cv2.contourArea(cnt))
        #this hack is needed to remove large rectangles near the walls at the
        #top of the room.
        if orect[0][0] < 2200 and orect[1][0]> 1000:
            break
    rect = check_rotate(orect)
    cv2.drawContours(frame, [rect], -1, (0, 255, 0), 2)
    
    pts1 = np.float32([rect[2], rect[3],  rect[1], rect[0]])
    pts2 = np.float32([[0,0],[500,0],[0,300],[500,300]])

    M = cv2.getPerspectiveTransform(pts1,pts2)

    dst = cv2.warpPerspective(frame, M,(500,300))
if dst != None:
    #cv2.imshow("paper", dst)
    cv2.imwrite("rectangle.jpg",frame)
    cv2.imwrite("rectangle-capure.jpg", dst)
time.sleep(3)
 
print rect

#camera.release()

headers1 = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'your oxford key here',
}
params3 = urllib.urlencode({
    # Request parameters
    'language': 'unk',
    'detectOrientation ': 'true',
})

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
except:
    print("failed to see any words")


print("done")
