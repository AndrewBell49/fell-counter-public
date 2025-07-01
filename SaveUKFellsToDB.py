# data got from www.hill-bagging.co.uk
# UK fells have classifications (as shown below) included

import re
from Database import Database

# I only downloaded these classifications, more were available
classifications = {
    'Ma': 'Marilyn',
    'Hu': 'Hump',
    'Sim': 'Simm',
    'M': 'Munro',
    'C': 'Corbett',
    'D': 'Donald',
    'N': 'Nuttall',
    'W': 'Wainwright',
    'WO': 'Wainwright Outlying Fell',
    'B': 'Birkett',
    'E': 'Ethel',
    'CoH': 'Historic County Top (pre-1974)'
}

with Database() as db:
    fellID = db.GetLastFellID()

with open('Data/UKFellsDownload.gpx', 'r') as r:
    for line in r.readlines():
        data = re.split('[<>]', line.strip('<>'))

        if len(data) != 24:
            continue

        latLon = data[0].split('"')
        latitude = latLon[1]
        longitude = latLon[3]

        try:
            elevation = float(data[3])
        except Exception as e:
            print('Error converting elevation: ' + e)

        name = ' '.join(data[7].split()[1:])


        # if that fell is already in the database, don't add a duplicate
        with Database() as db:
            if db.FellAlreadyInDB(name, elevation, latitude, longitude):
                continue

        with Database() as db:
            fellID += 1
            db.AddFellToDB(fellID, name, elevation, latitude, longitude, 'UK')
            print(f'Added {name} to database')

        allClassifications = data[15]

        for classification in allClassifications.split(','):
            try:
                with Database() as db:
                    classificationID = db.GetClassificationIDFromName(classifications[classification])
                    db.AddNewFellClassification(fellID, classificationID)

            # ignore classifications not in the database
            except KeyError as e:
                pass