# Strava authentication got from: https://medium.com/swlh/using-python-to-connect-to-stravas-api-and-analyse-your-activities-dummies-guide-5f49727aac86

# https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all

from datetime import datetime, timedelta
import os
import shutil
import pandas as pd
import gpxpy.gpx
import requests
import time
from Database import Database

CLIENT_ID = 70951
ACTIVITY_TYPES = ["Hike", "RockClimbing", "Run", "TrailRun", "Walk"]


class Strava:

    def __init__(self, userID):

        self.userID = userID

        with Database() as db:
            self.credentials = db.GetCredentials(userID)

        if self.credentials == None:
            print("Error: No user with that user ID exists in the database")
        else:
            try:
                self.updateTokens()
            except Exception as e:
                print(f'Error with getting tokens from Strava: {e}')


    def updateTokens(self):
        if self.credentials['expiresAt'] == None or self.credentials['expiresAt'] == '' or self.credentials['expiresAt'] < time.time():

            # Make Strava auth API call with current refresh token
            response = requests.post(
                                url = 'https://www.strava.com/oauth/token',
                                data = {
                                        'client_id': self.credentials['clientID'],
                                        'client_secret': self.credentials['clientSecret'],
                                        'grant_type': 'refresh_token',
                                        'refresh_token': self.credentials['refreshToken']
                                        }
                            )
            new_strava_tokens = response.json()
            
            with Database() as db:
                db.SaveAccessToken(self.userID, new_strava_tokens['access_token'], new_strava_tokens['expires_at'])
                self.credentials = db.GetCredentials(self.userID)

            print("Successfully updated Strava tokens")

        else:
            print("Access token already valid")

    
    def clearActivities(self):
        print("CLEARING ACTIVITIES")
        sure = input("Are you sure you want to clear all activities? Type 'yes' if you are sure: ")
        if sure == 'yes':
            try:
                shutil.rmtree("./activities")  # remove dir and all contents
                print("Successfully cleared activity GPXs")
            except Exception as e:
                print("Error: " + e)

            # make the directory again
            os.makedirs("./activities")
        else:
            print("Aborted clear")


    def getActivityIDsFromStrava(self, startDate):

        # default to not many activities per page
        perPage = 50

        if startDate == None:
            with Database() as db:
                startDate = db.GetLastUpdate(self.userID)
            if startDate == None or startDate == '':
                # if first time updating the record, have more per page
                perPage = 200


        url = "https://www.strava.com/api/v3/activities"
        page = 1
        endOfActivities = True
        activityIDs = []

        while endOfActivities:

            print(f'Page {page}')

            header = {'Authorization': 'Bearer ' + self.credentials['accessToken']}
            params = {'per_page': perPage, 'page': page}
            
            try:
                # get page of activities from Strava
                r = requests.get(url, headers=header, params=params)
                r = r.json()
            except Exception as e:
                print(f'Error getting activities from Strava: {e}')
                break

            # if no results then exit loop
            if (not r):
                endOfActivities = False
                break
            
            # otherwise add new data to dataframe
            for x in range(len(r)):
                if startDate == None or r[x]['start_date_local'] > startDate:

                    if r[x]['sport_type'] in ACTIVITY_TYPES:
                        # remove comma in the name, as this causes other issues in the program
                        activityIDs.append({'id': r[x]['id'], 'date': r[x]['start_date_local'], 'name': r[x]['name'].replace(',', ' '),
                                            'distance': round((r[x]['distance']/1000), 2), 'time': r[x]['elapsed_time'],
                                            'elevation': r[x]['total_elevation_gain'], 'sport': r[x]['sport_type']})
                    
                else:
                    endOfActivities = False
                    break

            page += 1

        return activityIDs
    
    def getActivityIDsFromFile(self, fileContents):
        activityIDs = []

        for line in fileContents.split('\n'):
            lineSplit = line.split(',')
            if len(lineSplit) == 7:
                activityIDs.insert(0, {'id': lineSplit[0], 'date': lineSplit[1], 'name': lineSplit[2], 'distance': lineSplit[3], 
                                       'time': lineSplit[4], 'elevation': lineSplit[5], 'sport': lineSplit[6]})

        return activityIDs

    def downloadActivities(self, startDate = None):

        with open('activitiesLeft.txt', 'r', encoding='utf-8') as r:
            activityFile = ''.join(r.readlines()).strip()

            # first time the activities have been downloaded
            if activityFile == '':
                activityIDs = self.getActivityIDsFromStrava(startDate)
                self.clearActivities()
            
            else:
                activityIDs = []
                if activityFile == 'None':
                    activityIDs = self.getActivityIDsFromStrava(startDate)
                    if len(activityIDs) == 0:
                        print("All activities are downloaded")
                        return True
                
                # activities still left in the file
                activityIDs.extend(self.getActivityIDsFromFile(activityFile))

        # number of updates per 15 minutes from Strava API is reached
        quotaReached = False

        print(f'There are {len(activityIDs)} activities to download')
        
        for x in range(len(activityIDs) - 1, -1, -1):

            if not quotaReached:
                try:
                    self.downloadGPX(activityIDs[x])

                except Exception as e:
                    print(f'Error: {e}')

                    # first activity to fail (when Strava 15 minute quote is reached), overwrites the file
                    with open('activitiesLeft.txt', 'w', encoding='utf-8') as w:
                        w.write(f"{activityIDs[x]['id']},{activityIDs[x]['date']},{activityIDs[x]['name']},{activityIDs[x]['distance']},{activityIDs[x]['time']},{activityIDs[x]['elevation']},{activityIDs[x]['sport']}")

                    with Database() as db:
                        db.SetLastUpdate(self.userID, activityIDs[x]['date'])
                    quotaReached = True

            # save activity IDs to text file, to store for next time, along with other metadata
            else:
                with open('activitiesLeft.txt', 'a', encoding='utf-8') as a:
                    a.write(f"\n{activityIDs[x]['id']},{activityIDs[x]['date']},{activityIDs[x]['name']},{activityIDs[x]['distance']},{activityIDs[x]['time']},{activityIDs[x]['elevation']},{activityIDs[x]['sport']}")

        if not quotaReached:
            print('All activities downloaded')

            with open('activitiesLeft.txt', 'w', encoding='utf-8') as w:
                w.write('None')

            with Database() as db:
                db.SetLastUpdate(self.userID, activityIDs[0]['date'])
            return True
        
        return False

    def downloadGPX(self, activity):
        id = activity['id']

        url = f"https://www.strava.com/api/v3/activities/{id}/streams"
        header = {'Authorization': 'Bearer ' + self.credentials['accessToken']}
        params = {'keys': 'latlng,time', 'key_by_type': True}

        response = requests.get(url, headers=header, params=params).json()

        latlng = None
        types = ''

        for type in response:
            types += f'{type}, '
            if type == "latlng":
                latlng = response['latlng']['data']
            elif type == "time":
                time_list = response['time']['data']
            
            # make sure an error is thrown, if strava runs out of requests
            elif type == "errors" and len(response['errors']) > 0:
                print(response)
                0/0

        if latlng == None:
            print(f'Activity with id: {id} had no latitude and longitude. Types: {types}')
            return

        # Create dataframe to store data 'neatly'
        data = pd.DataFrame([*latlng], columns=['lat','long'])
        start = datetime.strptime(activity['date'], "%Y-%m-%dT%H:%M:%SZ")
        data['time'] = [(start+timedelta(seconds=t)) for t in time_list]

        gpx = gpxpy.gpx.GPX()

        gpx.name = activity['name']

        # Create first track in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        gpx.tracks.append(gpx_track)

        # Create first segment in our GPX track:
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)

        # Create points:
        for idx in data.index:
            gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(
                        data.loc[idx, 'lat'],
                        data.loc[idx, 'long'],
                        time=data.loc[idx, 'time']
            ))
        # Write data to gpx file
        with open(f'./activities/{id}.gpx', 'w', encoding='utf-8') as f:
            f.write(gpx.to_xml())

        index = -1

        # finding where metadata begins
        with open(f'./activities/{id}.gpx', 'r', encoding='utf-8') as f:
            contents = f.readlines()
            for i, line in enumerate(contents):
                if line.strip()[:6] == '<name>':
                    index = i + 1

        # inserting in new metadata
        if index != -1:
            contents.insert(index, f"    <sport>{activity['sport']}</sport>\n")
            contents.insert(index, f"    <elevation>{activity['elevation']}</elevation>\n")
            contents.insert(index, f"    <time>{activity['time']}</time>\n")
            contents.insert(index, f"    <distance>{activity['distance']}</distance>\n")

            with open(f'./activities/{id}.gpx', 'w', encoding='utf-8') as f:
                contents = "".join(contents)
                f.write(contents)

        print(f'Successfully downloaded activity: {id}')