import math
import os
import re
import time
from Strava import Strava
from Database import Database

RADIUS_EARTH = 6378000

# how close you have to get to the summit to count (meters)
DISTANCE = 100

# so this calculation is only run once
DISTANCE_RADIUS = DISTANCE/RADIUS_EARTH

class UpdateFells:

    def __init__(self, userID=None, checkStrava=True):
        if userID == None:
            self.userID = self.login()
        else:
            self.userID = userID

        if checkStrava:
            strava = Strava(self.userID)
            strava.downloadActivities()

            self.saveBagsFromAllActivities()

    def saveBagsToDB(self, file, activityID, saveToDB=True, newActivity=True):
        print(f'\nChecking activity {file}')

        fellsBagged = UpdateFells.getAllBagsFromFile(file)
        for fell in fellsBagged:
            
            with Database() as db:
                fellName = db.GetFellNameFromID(fell['fellID'])
                # add the bag for the activity
                if saveToDB:
                    db.AddBag(fell['fellID'], self.userID, activityID, fell['date'])

            print(f"Bagged {fellName} on {fell['date']}")
        
        if saveToDB:
            # entire activity has been processed, save that it has been checked, along with metadata about the activity
            with Database() as db:

                if newActivity:
                    db.SetCheckedActivity(self.userID, activityID, UpdateFells.getMetadataFromFile(file))
                # if activity is being rechecked, only set last checked date
                else:
                    db.SetCheckedDate(self.userID, activityID)

        print(f'Successfully checked activity {file} ({len(fellsBagged)} bags)')

    def saveBagsFromAllActivities(self, path='activities'):

        totalTime = 0
        fileCount = 0
        # files checked this run of the program
        currentlyCheckedCount = 0
        # files checked in a previous run of the program
        previouslyCheckedCount = 0

        for root, dirs, files in os.walk(path):
            for file in files:

                startTime = time.time()

                with Database() as db:
                    # remove '.gpx' at the end
                    activityID = file.split('.')[0]
                    
                    # check the activity has not already been checked
                    if not db.ActivityChecked(self.userID, activityID):
                        self.saveBagsToDB(os.path.join(root, file), activityID)
                        currentlyCheckedCount += 1
                        success = True
                    else:
                        previouslyCheckedCount += 1
                        success = False

                    fileCount += 1
                
                totalTime += (time.time() - startTime)
                
                if currentlyCheckedCount > 0:
                    averageTime = totalTime/currentlyCheckedCount
                else:
                    averageTime = 0

                timeLeft = (len(files) - fileCount) * averageTime
                
                hours = int(timeLeft / 3600)
                minutes = int((timeLeft - hours * 3600) / 60)
                seconds = round(timeLeft - (minutes*60) - (hours*3600))

                if success:
                    print(f'Completed {activityID} ({fileCount}/{len(files)}). Avg time: {round(averageTime, 2)}s, est time remaining: {hours}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}')

        
    @staticmethod
    def extractInfoFromTrack(track):
        trackInfo = {'date': None, 'fellIDs': None}

        for line in track.split('\n'):
            line = line.strip()

            # line for datetime
            if line[:6] == '<time>':
                # just getting the date
                trackInfo['date'] = line.split('>')[1][:10]

            # line for lat and lon
            if line[:3] == 'lat':
                info = line.split('"')
                # getting latitude and longitude from each track point in gpx file
                latitude = float(info[1])
                longitude = float(info[3])

                # finding the minimum and maximum latitudes that each point could have a fell in
                d_latitude = DISTANCE_RADIUS * (180 / math.pi)
                min_latitude  = latitude - d_latitude
                max_latitude = latitude + d_latitude

                # finding the minimum and maximum longitudes that each point could have a fell in
                d_longitude = DISTANCE_RADIUS * (180 / math.pi) / math.cos(latitude * math.pi/180)
                min_longitude = longitude - d_longitude
                max_longitude = longitude + d_longitude

                with Database() as db:
                    fells = db.GetFellsInRange(min_latitude, max_latitude, min_longitude, max_longitude)
                
                # add a fell to the list, if one/more was found
                if len(fells) > 0:
                    trackInfo['fellIDs'] = fells

        return trackInfo

    @staticmethod
    def addToBagged(info, baggedFells, bagAndDate):   
        if info['fellIDs'] != None:
            # multiple fells can be close together in one point
            for fellID in info['fellIDs']:

                sizeBefore = len(baggedFells)
                baggedFells.add(fellID[0])

                # if a new fell was added
                if len(baggedFells) != sizeBefore:
                    bagAndDate.append({'date': info['date'], 'fellID': fellID[0]})

    @staticmethod
    def getAllBagsFromFile(file, skipPoint=5):
        # all fells bagged in this activity
        baggedFells = set()
        bagAndDate = []

        with open(file, 'r', encoding='utf-8') as r:
            tracks = '\n'.join(r.readlines()).split('<trkpt')

            pointCount = 1

            for track in tracks:
                # don't check every point in the .gpx file
                if pointCount == skipPoint:
                    info = UpdateFells.extractInfoFromTrack(track)
                    UpdateFells.addToBagged(info, baggedFells, bagAndDate)

                    # reset the counter
                    pointCount = 1
                else:
                    pointCount += 1

        return bagAndDate
    
    @staticmethod
    def getMetadataFromFile(file):
        metadata = {}

        with open(file, 'r', encoding='utf-8') as r:
            data = '\n'.join(r.readlines()).split('metadata')
        
        # checking through all metadata
        for line in data[1].split('\n'):
            info = re.split('[<>]', line.strip('<> '))
            if len(info) == 3:
                metadata[info[0]] = info[1]
        
        return metadata
    
    @staticmethod
    def login():    
        # ignore case
        username = input('Enter your username: ')
        with Database() as db:
            userID = db.GetUserIDFromUsername(username)

        while userID == None:
            username = input('Incorrect username. Please enter your username: ')
            with Database() as db:
                userID = db.GetUserIDFromUsername(username)

        return userID
