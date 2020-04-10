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
def getIDS(values):
	conn = sqlite3.connect('mini-puam.db')
	c = conn.cursor()
	query = ''' SELECT ID
				FROM OBJECTS
				WHERE COUNTRY = ? AND DATE BETWEEN ? AND ?'''
	c.execute(query, values)

	ids = []
	for idext in c.fetchall():
		ids.append(idext[0])

	conn.close();

	return ids

# given two colors, determine if the colors are a 'match' using euclidean distance
def isMatch(searchRGB, imageRGB):
	dist = dis.euclidean(searchRGB, imageRGB)
	isMatch = False
	if (dist <= 80): 
		isMatch = True
	return isMatch

# finds the count / frequency of objects given a specific search query (date, country, color)
def findFreq(searchRGB, values):
	count = 0
	objectIDs = []

	conn = sqlite3.connect('mini-puam.db')
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
	ids = getIDS(values);

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
		i = i+1

	conn.close();

	return count, objectIDs

def colorSearch(request):
	if request.method == 'GET':
		data = []

		getrgb = request.GET['searchRGB']
		searchRGB_str = getrgb.split('/')
		searchRGB = (int(searchRGB_str[0]), int(searchRGB_str[1]), int(searchRGB_str[2]))

		getvals = request.GET['vals']
		values_str =  getvals.split('/')
		values = (values_str[0], int(values_str[1]), int(values_str[2]))

		count, objectIDs = findFreq(searchRGB, values)

		data.append(count)
		data.append(objectIDs)
	return JsonResponse(data, safe=False)



