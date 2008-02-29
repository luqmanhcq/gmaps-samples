#!/usr/bin/env python

# makepolys.py

import math
import os
import random
import shutil
import stat
import sys
import time

#from geo import Geo
import shpUtils
import states

keysep = '|'
states.statesByNumber = {}
useTowns = [ 'New Hampshire', 'Vermont' ]

def loadshapefile( filename ):
	print 'Loading shapefile %s' % filename
	t1 = time.time()
	shapefile = shpUtils.loadShapefile( filename )
	t2 = time.time()
	print '%0.3f seconds load time' %( t2 - t1 )
	return shapefile
	
#def randomColor():
#	def hh(): return '%02X' %( random.random() *128 + 96 )
#	return hh() + hh() + hh()

featuresByName = {}
def featureByName( feature ):
	info = feature['info']
	name = info['NAME']
	if name not in featuresByName:
		featuresByName[name] = {
			'feature': feature #,
			#'color': randomColor()
		}
	return featuresByName[name]

def filterCONUS( features ):
	result = []
	for feature in features:
		shape = feature['shape']
		if shape['type'] != 5: continue
		info = feature['info']
		state = int(info['STATE'])
		if state == 2: continue  # Alaska
		if state == 15: continue  # Hawaii
		if state == 72: continue  # Puerto Rico
		result.append( feature )
	return result

#def featuresBounds( features ):
#	bounds = [ [ 180.0, 90.0 ], [ -180.0, -90.0 ] ]
#	for feature in features:
#		shape = feature['shape']
#		if shape['type'] == 5:
#			for part in shape['parts']:
#				bounds = geo.extendBounds( bounds, part['bounds'] )
#	return bounds

def writeFile( filename, data ):
	f = open( filename, 'wb' )
	f.write( data )
	f.close()

def readShapefile( filename ):
	print '----------------------------------------'
	print 'Loading %s' % filename
	
	shapefile = loadshapefile( filename )
	features = shapefile['features']
	print '%d features' % len(features)
	
	#stateFeatures = filterCONUS( stateFeatures )
	#print '%d features in CONUS states' % len(stateFeatures)
	
	#writeFile( 'features.csv', shpUtils.dumpFeatureInfo(features) )
	
	nPoints = nPolys = 0
	places = {}
	for feature in features:
		shape = feature['shape']
		if shape['type'] != 5: continue
		info = feature['info']
		name = info['NAME']
		state = info['STATE']
		key = name + keysep + state
		if key not in places:
			places[key] = {
				'name': name,
				'state': state,
				'shapes': []
			}
		place = places[key]
		shapes = place['shapes']
		for part in shape['parts']:
			nPolys += 1
			points = part['points']
			n = len(points) - 1
			nPoints += n
			pts = []
			area = part['area']
			if area == 0: continue
			bounds = part['bounds']
			center = part['center']
			centroid = part['centroid']
			points = part['points']
			for j in xrange(n):
				point = points[j]
				pts.append( '[%s,%s]' %( point[0], point[1] ) )
			shapes.append( '{area:%.8f,bounds:[[%.8f,%.8f],[%.8f,%.8f]],center:[%.8f,%.8f],centroid:[%.8f,%.8f],points:[%s]}' %(
				area,
				bounds[0][0], bounds[0][1], 
				bounds[1][0], bounds[1][1], 
				center[0], center[1],
				centroid[0], centroid[1],
				','.join(pts)
			) )
	print '%d points in %d places' %( nPoints, len(places) )
	return shapefile, places

def writeUS( places ):
	json = []
	keys = places.keys()
	keys.sort()
	for key in keys:
		json.append( '{name:"%s",shapes:[%s]}' %(
			#reader.fixCountyName( name ),
			key.split(keysep)[0],
			','.join(places[key]['shapes'])
		) )
	writeFile( 'json/us.js', '''
States = States || {};
States.us = {
	places: [%s]
};
''' %( ','.join(json) ) )

def writeStates( places ):
	keys = places.keys()
	keys.sort()
	for key in keys:
		name, number = key.split(keysep)
		state = states.statesByNumber[number]
		state['json'].append( '{name:"%s",shapes:[%s]}' %(
			#reader.fixCountyName( name ),
			name,
			','.join(places[key]['shapes'])
		) )
	for state in states.states:
		abbr = state['abbr'].lower()
		writeFile(
			'json/%s.js' % abbr,
			'''
States = States || {};
States.%s = {
	places: [%s]
};
''' %( abbr, ','.join(state['json']) ) )

def generateStates():
	shapefile, places = readShapefile( 'states/st99_d00_shp-90/st99_d00.shp' )
	for key in places:
		name, number = key.split(keysep)
		state = states.statesByName[name]
		state['json'] = []
		state['counties'] = []
		state['number'] = number
		states.statesByNumber[number] = state
	writeUS( places )

def generateCounties():
	shapefile, places = readShapefile( 'counties/co99_d00_shp-90/co99_d00.shp' )
	for key, place in places.iteritems():
		name, number = key.split(keysep)
		if True: # name not in useTowns:
			state = states.statesByNumber[number]
			state['counties'].append( place )
	#shapefile, places = readShapefile( 'towns/co99_d00_shp-90/co99_d00.shp' )
	#for key, place in places.iterItems():
	#	name, number = key.split(keysep)
	#	if name not in useTowns:
	#		state = states.statesByNumber[number]
	#		state['counties'].append( place )
	writeStates( places )

generateStates()
generateCounties()

print 'Done!'
