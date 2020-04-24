from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse

from .models import Greeting

import numpy as np
import scipy.spatial.distance as dis
import scipy
import sqlite3
from sqlite3 import Error

# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


def db(request):
    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})

def country(request):
    return render(request, "country.html")

def info(request):
	return render(request, "info.html")


# returns the ids of objects, given the desired country and date range
# to be used in findFreq
def getIDS_URLS(values):
	ids = []
	urls = []

	conn = sqlite3.connect('puam.db')
	c = conn.cursor()
	query = ''' SELECT ID
				FROM OBJECTS
				WHERE COUNTRY = ? AND DATE BETWEEN ? AND ?'''
	c.execute(query, values)

	
	for idext in c.fetchall():
		ids.append(idext[0])

	query2 = ''' SELECT IMAGE
				FROM OBJECTS
				WHERE COUNTRY = ? AND DATE BETWEEN ? AND ?'''
	c.execute(query2, values)

	for urlsext in c.fetchall():
		urls.append(urlsext[0])

	conn.close();


	return ids, urls


def rgb2xyz(rgb):
	m = [[0.41239080, 0.35758434, 0.18048079],[0.21263901, 0.71516868, 0.07219232],[0.01933082, 0.11919478, 0.95053215]]
	xyz = np.matmul(m, rgb)
	return xyz


def xyz2lab(xyz):
	RefX = 100
	RefY = 100
	RefZ = 100
	var_X = xyz[0] / RefX
	var_Y = xyz[1] / RefY
	var_Z = xyz[2] / RefZ
  
	if( var_X > 0.008856 ):
	  var_X = var_X **( 1/3 )
	else:
	  var_X = ( 7.787 * var_X ) + ( 4 / 29 )
	if( var_Y > 0.008856 ):
	  var_Y = var_Y **( 1/3 )
	else:
	  var_Y = ( 7.787 * var_Y ) + ( 4 / 29)
	if( var_Z > 0.008856 ):
	  var_Z = var_Z **( 1/3 )
	else:
	  var_Z = ( 7.787 * var_Z ) + ( 4 / 29 )

	L = (116 * var_Y ) - 16
	a = 500 * (var_X - var_Y)
	b = 200 * (var_Y - var_Z)

	return (L, a, b)

def deltE(lab1, lab2):
	dL = lab1[0] - lab2[0]
	c1 = np.sqrt(lab1[1]**2 + lab1[2]**2)
	c2 = np.sqrt(lab2[1]**2 + lab2[2]**2)
	dC = c1 - c2
	dE = dis.euclidean(lab1, lab2)
	dH = np.sqrt(dE**2 - dL**2 - dC**2)
	sL = 1 
	sC = 1 + 0.045 * c1
	sH = 1 + 0.014 * c1
	a = (dL/sL)**2
	b = (dC/sC)**2
	c = (dH/sH)**2
	delt = np.sqrt(a + b + c)

	return delt
# given two colors, determine if the colors are a 'match' using euclidean distance
def isMatch(searchRGB, imageRGB):
	isMatch = False
	xyz1 = rgb2xyz(searchRGB)
	xyz2 = rgb2xyz(imageRGB)
	lab1 = xyz2lab(xyz1)
	lab2 = xyz2lab(xyz2)
	delt = deltE(lab1, lab2)

	if (delt <= 10):
		isMatch = True
	return isMatch

# finds the count / frequency of objects given a specific search query (date, country, color)
def findFreq(searchRGB, values):
	count = 0
	objectIDs = []
	imageURLs = []

	#conn = sqlite3.connect('mini-puam.db')
	conn = sqlite3.connect('puam.db')
	c = conn.cursor()

	query = ''' SELECT COLOR1R, COLOR1G, COLOR1B, 
	COLOR2R, COLOR2G, COLOR2B, 
	COLOR3R, COLOR3G, COLOR3B, 
	COLOR4R, COLOR4G, COLOR4B, 
	COLOR5R, COLOR5G, COLOR5B
				FROM OBJECTS
				WHERE COUNTRY = ? AND DATE BETWEEN ? AND ?'''

	c.execute(query, values)
	palettes= c.fetchall();
	ids, urls = getIDS_URLS(values);

	i = 0;
	for palette in palettes:

		rgb1 = (palette[0], palette[1], palette[2])
		rgb2 = (palette[3], palette[4], palette[5])
		rgb3 = (palette[6], palette[7], palette[8])
		rgb4 = (palette[9], palette[10], palette[11])
		rgb5 = (palette[12], palette[13], palette[14])


		if (isMatch(searchRGB, rgb1) or isMatch(searchRGB, rgb2) or isMatch(searchRGB, rgb3) or isMatch(searchRGB, rgb4) or isMatch(searchRGB, rgb5)):
			count = count + 1
			objectIDs.append(ids[i])
			imageURLs.append(urls[i])

		i = i+1

	conn.close();

	return count, objectIDs, imageURLs

def colorSearch(request):
	if request.method == 'GET':
		data = []
		searchCounts = []
		searchObjectIDs = []
		searchImageURLs = []

		getrgb = request.GET['searchRGB']
		rgb_str = getrgb.split(',')
		searchRGB = (int(rgb_str[0]), int(rgb_str[1]), int(rgb_str[2]))

		getmapids = request.GET['mapIDs']
		mapids = getmapids.split(',')

		getdates = request.GET['dateRange']
		dates_str = getdates.split(',')
		dates = [int(dates_str[0]), int(dates_str[1])]

		for i in range (len(mapids)):
			country = mapids[i].replace("_", " ")
			values = (country, dates[0], dates[1])
			count, objectIDs, imageURLs = findFreq(searchRGB, values)
			searchCounts.append(count)
			searchObjectIDs.append(objectIDs)
			searchImageURLs.append(imageURLs)

		data.append(searchCounts)
		data.append(searchObjectIDs)
		data.append(searchImageURLs)
	return JsonResponse(data, safe=False)



