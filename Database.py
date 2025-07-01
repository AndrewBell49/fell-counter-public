from datetime import datetime
import sqlite3

class Database:
    
    def __init__(self, file='Fells.db'):
        self.con = sqlite3.connect(file)
        self.cur = self.con.cursor()

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.con.close() # so the connection is only open while one instance is open

    def GetMostRecentUserID(self):
        userIDs = self.cur.execute("""SELECT userID
                                      FROM users""").fetchall()
        if len(userIDs) == 0:
            return None
        return userIDs[-1][0]
 
    def AddUser(self, username, firstname, surname):
        userID = self.GetMostRecentUserID() + 1
        try: # username is a unique primary key so will error if a username is the same
            self.cur.execute("""INSERT INTO users 
                                (userID, username, firstname, surname, dateSignedUp)
                                VALUES (?, ?, ?, ?, ?)""",
                                (userID, username, firstname, surname, datetime.today().strftime('%Y-%m-%d')))
            self.con.commit()
            return userID
        
        except Exception as e:
            print("Error: " + str(e))
            return None

    def GetCredentials(self, userID):
        user = self.cur.execute("""SELECT userID, username, firstname, surname,
                                   dateSignedUp, clientID, clientSecret, refreshToken,
                                   accessToken, expiresAt, lastUpdate
                                   FROM users
                                   WHERE userID = ?""",
                                   (userID,)).fetchone()
        
        try:
            return {'userID': user[0],
                    'username': user[1],
                    'firstname': user[2],
                    'surname': user[3],
                    'dateSignedUp': user[4],
                    'clientID': user[5],
                    'clientSecret': user[6],
                    'refreshToken': user[7],
                    'accessToken': user[8],
                    'expiresAt': user[9],
                    'lastUpdate': user[10]}
        except Exception:
            return None

    def SaveRefreshToken(self, userID, refreshToken):
        self.cur.execute("""UPDATE users
                            SET refreshToken = ?
                            WHERE userID = ?""",
                            (refreshToken, userID))
        self.con.commit()

    def SaveAccessToken(self, userID, accessToken, expiresAt):
        self.cur.execute("""UPDATE users 
                            SET accessToken = ?, expiresAt = ? 
                            WHERE userID = ?""",
                            (accessToken, expiresAt, userID))
        self.con.commit()
    
    def GetUserIDFromUsername(self, username):
        userID = self.cur.execute("""SELECT userID 
                                     FROM users
                                     WHERE UPPER(username) = ?""",
                                     (username.upper(),)).fetchone()
        if userID == None:
            return -1
        return userID[0]
    
    def SetLastUpdate(self, userID, date): # last time strava was updated
        self.cur.execute("""UPDATE users
                            SET lastUpdate = ?
                            WHERE userID = ?""",
                            (date, userID))
        self.con.commit()
    
    def GetLastUpdate(self, userID):
        lastUpdate = self.cur.execute("""SELECT lastUpdate
                                         FROM users
                                         WHERE userID = ?""",
                                         (userID,)).fetchone()
        if lastUpdate == None:
            return -1
        return lastUpdate[0]
    
    def GetAllUsers(self):
        users = self.cur.execute("""SELECT username
                                    FROM users""").fetchone()
        return users
    
    # all fells in the range of latitude and longitude given
    def GetFellsInRange(self, minLatitude, maxLatitude, minLongitude, maxLongitude):
        fells = self.cur.execute("""SELECT fellID 
                                    FROM fells 
                                    WHERE (latitude BETWEEN ? AND ?) 
                                    AND (longitude BETWEEN ? AND ?)""", 
                                    (minLatitude, maxLatitude, minLongitude, maxLongitude)).fetchall()
        
        return fells
    
    def GetAllFells(self):
        fell = self.cur.execute("""SELECT fellID 
                                   FROM fells""").fetchall()
        return fell
    
    def GetFellNameFromID(self, fellID):
        fellName = self.cur.execute("""SELECT name
                                       FROM fells 
                                       WHERE fellID = ?""",
                                       (fellID,)).fetchone()
        if fellName != None:
            return fellName[0]
        return None
    
    def GetFellElevationFromID(self, _, fellID):
        fellName = self.cur.execute("""SELECT elevation
                                       FROM fells 
                                       WHERE fellID = ?""",
                                       (fellID,)).fetchone()
        if fellName != None:
            return fellName[0]
        return None
    
    def BagExists(self, fellID, userID, bagDate):
        bag = self.cur.execute("""SELECT *
                                  FROM bags
                                  WHERE fellID = ?
                                  AND userID = ?
                                  AND bagDate = ?""",
                                  (fellID, userID, bagDate)).fetchone()
        if bag == None:
            return False
        return True
    
    def AddBag(self, fellID, userID, activityID, bagDate):
        self.cur.execute("""INSERT INTO bags 
                            (fellID, userID, activityID, bagDate) 
                            VALUES (?, ?, ?, ?)""", 
                            (fellID, userID, activityID, bagDate))
        self.con.commit()

    def RemoveBagsForActivity(self, userID, activityID):
        self.cur.execute("""DELETE FROM bags
                            WHERE userID = ?
                            AND activityID = ?""",
                            (userID, activityID))
        self.con.commit()

    # check if the activity has already been checked
    def ActivityChecked(self, userID, activityID):
        checked = self.cur.execute("""SELECT * 
                                      FROM checkedActivities
                                      WHERE userID = ? AND activityID = ?""",
                                      (userID, activityID)).fetchone()
        
        if checked == None:
            return False
        return True


    def SetCheckedActivity(self, userID, activityID, metadata):
        self.cur.execute("""INSERT INTO checkedActivities 
                            (userID, activityID, name, distance, time, elevation, sport, checkedDate) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                            (userID, activityID, metadata['name'], metadata['distance'],
                             metadata['time'], metadata['elevation'], metadata['sport'], 
                             datetime.today().strftime('%Y-%m-%d')))
        self.con.commit()
    
    def SetCheckedDate(self, userID, activityID):
        self.cur.execute("""UPDATE checkedActivities 
                            SET checkedDate = ?
                            WHERE userID = ?
                            AND activityID = ?""", 
                            (datetime.today().strftime('%Y-%m-%d'), userID, activityID))
        self.con.commit()
    
    # all fells that have been bagged by the user
    def GetAllBaggedFells(self, userID):
        fells = self.cur.execute("""SELECT DISTINCT fells.fellID
                                    FROM bags, fells
                                    WHERE bags.fellID = fells.fellID
                                    AND bags.userID = ?
                                    AND fells.elevation IS NOT NULL""",
                                    (userID,)).fetchall()
        
        return fells
    
    # all fells that have been bagged
    # manual specified if to include manual bags in total
    def GetAllBaggedActivityFells(self, userID, manual=True):
        if manual:
            extraText = '\nAND activityID IS NOT NULL'
        else:
            extraText = ''
        fells = self.cur.execute(f"""SELECT DISTINCT fellID
                                     FROM bags
                                     WHERE userID = ? {extraText}""",
                                    (userID,)).fetchall()
        
        return fells
    
    # get everything bagged by the user (including duplicates)
    def GetAllBags(self, userID, nullElevation=True):

        # should fells with null elevation be included
        nullText = ''
        if not nullElevation:
            nullText += '\nAND fells.elevation IS NOT NULL'

        fells = self.cur.execute(f"""SELECT bags.fellID, fells.elevation
                                     FROM bags, fells
                                     WHERE bags.fellID = fells.fellID 
                                     AND bags.userID = ? {nullText}
                                     ORDER BY fells.elevation""",
                                     (userID,)).fetchall()
        
        return fells
    
    def GetNullBags(self, userID, nullName=False, nullElevation=False):

        # parameters determine if null names and elevations should be included
        nullText = ''

        if nullName:
            nullText += '\nAND fells.name IS NULL'
        else:
            nullText += '\nAND fells.name IS NOT NULL'

        if nullElevation:
            nullText += '\nAND fells.elevation IS NULL'
        else:
            nullText += '\nAND fells.elevation IS NOT NULL'

        fells = self.cur.execute(f"""SELECT bags.fellID, fells.elevation
                                     FROM bags, fells
                                     WHERE bags.fellID = fells.fellID 
                                     AND bags.userID = ? {nullText}""",
                                     (userID,)).fetchall()
        
        return fells
    
    def GetAllActivities(self, userID):
        activities = self.cur.execute("""SELECT activityID
                                         FROM checkedActivities
                                         WHERE userID = ?""",
                                         (userID,)).fetchall()
        
        return activities
    
    def GetCountOfFell(self, userID, fellID):
        bags = self.cur.execute("""SELECT *
                                   FROM bags
                                   WHERE userID = ?
                                   AND fellID = ?""",
                                   (userID, fellID)).fetchall()
        return len(bags)
    
    def GetAllBaggingActivities(self, userID):
        activities = self.cur.execute("""SELECT DISTINCT activityID
                                         FROM bags
                                         WHERE userID = ?""",
                                         (userID,)).fetchall()
        
        return activities
    
    # return the length, or the bags
    def GetBagsForActivity(self, userID, activityID, length = True):
        bags = self.cur.execute("""SELECT fells.name, fells.elevation
                                   FROM bags, fells
                                   WHERE bags.fellID = fells.fellID
                                   AND bags.userID = ?
                                   AND bags.activityID = ?
                                   AND fells.elevation IS NOT NULL
                                   AND fells.name IS NOT NULL""",
                                   (userID, activityID)).fetchall()
        if length:
            return len(bags)
        else:
            return bags
    
    def GetActivityInfoFromID(self, userID, activityID):
        info = self.cur.execute("""SELECT name, distance, time, elevation, sport
                                   FROM checkedActivities
                                   WHERE userID = ?
                                   AND activityID = ?""",
                                   (userID, activityID)).fetchone()
        return info
    
    def SearchForFells(self, name):
        fells = self.cur.execute("""SELECT fellID, name, elevation, country
                                    FROM fells
                                    WHERE name LIKE ?""",
                                    (f'%{name}%',)).fetchall()
        return fells
    
    def SearchForActivity(self, userID, search):
        activities = self.cur.execute("""SELECT activityID, name, distance, time, elevation, checkedDate
                                         FROM checkedActivities
                                         WHERE userID = ?
                                         AND (name LIKE ?
                                         OR activityID LIKE ?)""",
                                         (userID, f'%{search}%', f'%{search}%')).fetchall()
        return activities
    
    def GetAllClassifications(self):
        classifications = self.cur.execute("""SELECT classificationID, name, description
                                              FROM classificationInfo""").fetchall()
        
        return classifications
    
    def GetFellsForClassification(self, classificationID):
        fells = self.cur.execute("""SELECT fellID
                                    FROM fellClassification
                                    WHERE classificationID = ?""",
                                    (classificationID,)).fetchall()
        
        return fells
    
    def GetFellsForCountry(self, country):
        fells = self.cur.execute("""SELECT fellID
                                    FROM fells
                                    WHERE country = ?""",
                                    (country,)).fetchall()
        
        return fells
    
    def GetBaggedFromClassification(self, userID, classificationID):
        fells = self.cur.execute("""SELECT DISTINCT bags.fellID
                                    FROM bags, fellClassification
                                    WHERE bags.userID = ?
                                    AND bags.fellID = fellClassification.fellID
                                    AND fellClassification.classificationID = ?""",
                                    (userID, classificationID)).fetchall()
        
        return fells
    
    def GetAllBaggingCountries(self):
        countries = self.cur.execute("""SELECT DISTINCT fells.country
                                        FROM fells, bags
                                        WHERE fells.fellID = bags.fellID""").fetchall()
        return countries
    
    def GetFellInfoFromID(self, fellID):
        info = self.cur.execute("""SELECT name, elevation, latitude, longitude
                                   FROM fells
                                   WHERE fellID = ?""",
                                   (fellID,)).fetchone()
        return info
    
    def GetIsFellBagged(self, userID, fellID):
        bags = self.cur.execute("""SELECT fellID
                                   FROM bags
                                   WHERE fellID = ?
                                   AND userID = ?""",
                                   (fellID, userID)).fetchone()
        if bags == None:
            return False
        return True
    
    def GetTotalBagsFromCountry(self, country):
        bags = self.cur.execute("""SELECT *
                                   FROM bags, fells
                                   WHERE bags.fellID = fells.fellID
                                   AND fells.country = ?""",
                                   (country,)).fetchall()
        return len(bags)
    
    def GetDistinctBagsFromCountry(self, country):
        bags = self.cur.execute("""SELECT DISTINCT fells.fellID
                                   FROM bags, fells
                                   WHERE bags.fellID = fells.fellID
                                   AND fells.country = ?""",
                                   (country,)).fetchall()
        return len(bags)
    
    def GetClassificationIDFromName(self, name):
        classification =  self.cur.execute("""SELECT classificationID 
                                              FROM classificationInfo 
                                              WHERE name = ?""",
                                              (name,)).fetchone()
        return classification[0]
    
    def GetClassificationNameFromID(self, classificationID):
        name =  self.cur.execute("""SELECT name 
                                    FROM classificationInfo 
                                    WHERE classificationID = ?""",
                                    (classificationID,)).fetchone()
        return name[0]
    
    def AddNewFellClassification(self, fellID, classificationID):
        self.cur.execute("""INSERT INTO fellClassification 
                            (fellID, classificationID) 
                            VALUES (?, ?)""", 
                            (fellID, classificationID))
        self.con.commit()
    
    def GetBagsInDateOrder(self, userID, fromDate, toDate):
        bags = self.cur.execute("""SELECT bags.fellID, bags.bagDate
                                   FROM bags, fells
                                   WHERE bags.fellID = fells.fellID
                                   AND bags.userID = ?
                                   AND (bags.bagDate BETWEEN ? AND ?)
                                   AND fells.elevation IS NOT NULL
                                   ORDER BY bagDate DESC""",
                                   (userID, fromDate, toDate)).fetchall()
        
        return bags
    
    def AddFellToDB(self, fellID, name, elevation, latitude, longitude, country):
        self.cur.execute("""INSERT INTO fells 
                            (fellID, name, elevation, latitude, longitude, country) 
                            VALUES (?, ?, ?, ?, ?, ?)""",
                            (fellID, name, elevation, latitude, longitude, country))
        self.con.commit()

    def FellAlreadyInDB(self, name, elevation, latitude, longitude):
        fells = self.cur.execute("""SELECT * 
                                    FROM fells 
                                    WHERE name = ? 
                                    AND elevation = ? 
                                    AND latitude = ? 
                                    AND longitude = ?""",
                                    (name, elevation, latitude, longitude)).fetchone()
        
        if fells == None:
            return False
        return True
        
    def GetLastFellID(self):
        lastFellID = self.cur.execute("""SELECT fellID 
                                         FROM fells 
                                         ORDER BY fellID DESC""").fetchone()
        if lastFellID == None:
            return 0
        return lastFellID[0]