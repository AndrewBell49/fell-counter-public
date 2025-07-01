# data got from https://download.geofabrik.de
# download the .osm.bz2 file, then extract it to the /Data folder

from Database import Database

# def saveFellToDB(fellID, name, ele, lat, lon, country):


with Database() as db:
    fellID = db.GetLastFellID() + 1

# comment out which files you want to search, or add a new one in the same format
allFiles = [
            {'file': 'Data/liechtenstein-latest.osm', 'country': 'Liechtenstein'}]
            # {'file': 'Data/slovenia-latest.osm', 'country': 'Slovenia'},
            # {'file': 'Data/france-latest.osm', 'country': 'France'},
            # {'file': 'Data/germany-latest.osm', 'country': 'Germany'},
            # {'file': 'Data/norway-latest.osm', 'country': 'Norway'},
            # {'file': 'Data/poland-latest.osm', 'country': 'Poland'},
            # {'file': 'Data/czech-republic-latest.osm', 'country': 'Czech Republic'},
            # {'file': 'Data/switzerland-latest.osm', 'country': 'Switzerland'},

lineNum = 1

for file in allFiles:
    with open(file['file'], encoding='utf8') as r:
        previousNode = ""

        # files are too large for xml tree solutions, so using good old fashioned loop through every line
        for line in r:

            line = line.strip()

            # all nodes are at the beginning, after that is not useful data for this program
            # break when all nodes are viewed to speed up process
            if line[:4] == '<way':
                break

            if line[:5] == '<node':
                previousNode = line

                ele = None
                name = None
                lat = None
                lon = None

            elif line[:4] == '<tag':
                tags = line.split()

                # tags we are interested in
                if len(tags) >= 3:

                    # elevation tag
                    if tags[1] == 'k="ele"':
                        ele = tags[2].split('"')[1]

                    # name tag
                    elif tags[1] == 'k="name"':
                        nameTag = ' '.join(tags[2:])
                        name = ' '.join(nameTag.split('"')[1:-1])

                    # final tag that we are interested
                    # this shows that the node is a peak, and save data (useful data comes before this tag)
                    elif tags[1] == 'k="natural"' and tags[2] == 'v="peak"/>':
                        nodeSplit = previousNode.split()

                        for att in nodeSplit:
                            values = att.split('=')

                            # finding latitude and longitude of the node
                            if len(values) == 2:
                                if values[0] == 'lat':
                                    lat = values[1].replace('"', '')
                                elif values[0] == 'lon':
                                    lon = values[1].replace('"', '').replace('>', '')

                        # each fell needs a latitude and longitude
                        # some elevations and names can be None, these are still saved to the database
                        if lat != None and lon != None:
                            # save fell and change fellID
                            with Database() as db:
                                if not db.FellAlreadyInDB(name, ele, lat, lon):
                                    db.AddFellToDB(fellID, name, ele, lat, lon, file['country'])
                                    fellID += 1
                                                            
                        else:
                            print(f"Error with node: {previousNode}. Got data: {name, ele, lat, lon, file['country']}")

    print(f"Completed {file['country']}")