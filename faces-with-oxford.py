
# This is the project oxford face application.
# it needs a file name for the jpeg input
# and it produces a jpeg file output with the name of the input file with "-out" appended
# the output file is just the input with the colored rectangle around the faces.  black means
# no smile.
# you also need your oxford key
inputfilepath = "path to your jpg file"
import httplib, urllib, base64
import json
import numpy as np
import argparse
import time
import cv2
from IPython.core.display import Image

def show_rbg(image):
    cv2.imwrite("newimage.jpg", image)
    f = open("./newimage.jpg", "rb")
    im = f.read()
    return im


headers = {
    # Request headers
    'Content-Type': 'application/octet-stream',
    'Ocp-Apim-Subscription-Key': 'your oxford key',
}


params = urllib.urlencode({
    # Request parameters
    'returnFaceId': 'true',
    'returnFaceLandmarks': 'false',
    'returnFaceAttributes': 'age,gender,smile',
})


f = open(inputfilepath, "rb")
im = f.read()
image = cv2.imread(inputfilepath)

try:
    conn = httplib.HTTPSConnection('api.projectoxford.ai')
    conn.request("POST", "/face/v1.0/detect?%s" % params, im, headers)
    response = conn.getresponse()
    data = response.read()
    #print(data)
    conn.close()
except Exception as e:
    print("[Errno {0}] {1}".format(e.errno, e.strerror))

datal = json.loads(data)

def getrect(rdict):
    ul = [rdict['left'],rdict['top']]
    ur = [rdict['left']+rdict['height'],rdict['top']]
    lr = [rdict['left']+rdict['height'],rdict['top']+rdict['width']]
    ll = [rdict['left'] ,rdict['top']+rdict['width']]
    return np.array([ul, ur, lr, ll])
    
malecount = 0
maleage = 0
femalecount = 0
femaleage = 0
for d in datal:
    fa = d['faceAttributes']
    if fa['gender'] == 'male':
        malecount += 1
        maleage += fa['age']
        color = (0, 255, 255)
    else:
        femalecount += 1
        femaleage += fa['age']
        color = (255, 0, 0)
    if fa['smile'] < 0.5:
        color = (0, 0, 0)
    r = getrect(d['faceRectangle'])
    cv2.drawContours(image, [r], -1, color, 2)


if femalecount > 0:
    print "average age of " + str(femalecount)+ " females ="+ str(femaleage/femalecount)
if malecount > 0:
    print "average age of " + str(malecount)+ " males ="+ str(maleage/malecount)

cv2.drawContours(image, [r], -1, (0, 255, 0), 2)
k = inputfilepath.find(".jpg")
if k > 0:
    out = inputfilepath[0:k]+"-out.jpg"
else:
    out = inputfilepath+"-out.jpg"
cv2.imwrite(out, image)
