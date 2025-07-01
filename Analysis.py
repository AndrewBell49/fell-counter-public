# Program written by Andrew Bell
# Used to analyse fell climbing data in the database

from datetime import datetime, timedelta

from Database import Database
import matplotlib.pyplot as plt

class Analysis:

    def __init__(self, userID):

        # options the user has for analysis
        allFunctions = [{'function': self.GetMostPopularBags, 'text': 'Show your most popular bags'}, 
                        {'function': self.GetBigBagActivities, 'text': 'Show the activities you picked up the most bags on'},
                        {'function': self.GetHighestBags, 'text': 'Show the highest mountains you have climbed'},
                        {'function': self.GraphBags, 'text': 'Graph how you have climbed mountains over time'},
                        {'function': self.PieChartCounties, 'text': 'Show a pie chart of how many bags you have per country'},
                        {'function': self.GetGroupStats, 'text': 'Get stats on classification groups of mountains'},
                        {'function': self.GetGeneralStats, 'text': 'Get general statistics for you'}]

        self.userID = userID
        with Database() as db:
            self.username = db.GetCredentials(self.userID)['username']
            
        self.classificationCount = self.GetClassificationCount()

        self.GetGeneralStats()

        choice = ''
        while choice != '0':

            for i, func in enumerate(allFunctions, 1):
                print(f"{i}) {func['text']}")
            
            choice = input('Enter which option you would like to view, or 0 to quit: ')
            while not choice.isdigit() or int(choice) < 0 or int(choice) > len(allFunctions):
                choice = input(f'That was not between 0 and {len(allFunctions)}, please enter a valid number: ')

            # run function if not exiting
            if choice != '0':
                allFunctions[int(choice)-1]['function']()

    # General statistics for the user
    def GetGeneralStats(self):
        print(f'\nGeneral stats for {self.username}:')

        with Database() as db:
            baggedFellCount = len(db.GetAllBaggedActivityFells(self.userID))
            baggedActivityFellCount = len(db.GetAllBaggedActivityFells(self.userID, manual=False))

            bagCount = len(db.GetAllBags(self.userID))

            nullNameBags = len(db.GetNullBags(self.userID, nullName=True, nullElevation=False))
            nullElevationBags = len(db.GetNullBags(self.userID, nullName=False, nullElevation=True))
            nullBothBags = len(db.GetNullBags(self.userID, nullName=True, nullElevation=True))

            activityCount = len(db.GetAllActivities(self.userID))

        text = f'Bagged {baggedFellCount} different fells'
        # no manually bagged activities
        if baggedActivityFellCount == baggedFellCount:
            text += '.'
        else:
            text += f' ({baggedActivityFellCount} from Strava activities).'
        print(text)

        print(f'Climbed {bagCount} fells from {activityCount} activities.')

        text = ''
        addComma = False

        if nullNameBags > 0:
            text += f'{nullNameBags} fells had no name but elevation'
            addComma = True

        if nullElevationBags > 0:
            if addComma:
                text += ', '
            else:
                addComma = True
            text += f'{nullElevationBags} fells had no elevation but a name'

        if nullBothBags > 0:
            if addComma:
                text += ', '
            text += f'{nullBothBags} fells had both no elevation and name'

        print(text)

        self.BoxPlotHeights()

        print()            

    # function for generalising the functionality of finding the 
    # N most common items in the database, returned from a particular function
    def GetNMostX(self, lst, func, n = 10):
        itemAndCount = []
        for item in lst:
            count = func(self.userID, item[0])
            itemAndCount.append({'id': item[0], 'count': count})

        sortedItems = sorted(itemAndCount, key=lambda d: d['count'], reverse=True)

        if n > len(sortedItems):
            n = len(sortedItems)

        return sortedItems[:n]    

    # activities with the most mountains bagged on
    def GetBigBagActivities(self, n = 5):
        with Database() as db:
            activities = self.GetNMostX(db.GetAllBaggingActivities(self.userID), db.GetBagsForActivity, n)
        
        print(f'\nThe top {len(activities)} activities with the most bags for {self.username}:')

        # keep showing this until the user quits
        choice = -1
        while choice != 0:

            with Database() as db:
                for x in range(len(activities)):
                    activityInfo = db.GetActivityInfoFromID(self.userID, activities[x]['id'])
                    time = activityInfo[3]
                    hours = int(time/3600)
                    minutes = int((time - (hours*3600))/60)
                    seconds = int(time - (hours*3600 + minutes*60))
                    print(f"{x+1}) {activityInfo[0]}, {activityInfo[4]}ing {activityInfo[1]}km ({activityInfo[2]}m elevation gain) in {hours}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)} (bagging {activities[x]['count']} fells)")

            choice = input('Enter which activity you would like to see the fells of, or 0 to continue: ')
            while not choice.isdigit() or int(choice) < 0 or int(choice) > len(activities):
                choice = input(f'That was not between 0 and {len(activities)}, please enter a valid number: ')

            # user wants to quit
            if choice == '0':
                print()
                return
            
            # showing all fells in that activity
            with Database() as db:
                for i, bag in enumerate(db.GetBagsForActivity(self.userID, activities[int(choice) - 1]['id'], False), 1):
                    print(f'{i}) {bag[0]} ({bag[1]})')
            input('\nEnter to continue')

    # mountains that user has climbed the most often
    def GetMostPopularBags(self, n = 10):
        with Database() as db:
            bags = self.GetNMostX(db.GetAllBaggedFells(self.userID), 
                                  db.GetCountOfFell, n)
        
        print(f'\nThe top {len(bags)} most popular bags for {self.username}:')
        with Database() as db:
            for x in range(len(bags)):
                print(f"{x+1}) {db.GetFellNameFromID(bags[x]['id'])} (bagged {bags[x]['count']} times)")
        input('\nEnter to continue')

    # tallest mountains the user has climbed
    def GetHighestBags(self, n = 15):
        with Database() as db:
            highBags = self.GetNMostX(db.GetAllBaggedFells(self.userID), 
                                      db.GetFellElevationFromID, n)

        print(f'\nThe top {len(highBags)} highest bags for {self.username}:')
        with Database() as db:
            for x in range(len(highBags)):
                print(f"{x+1}) {db.GetFellNameFromID(highBags[x]['id'])} ({highBags[x]['count']}m)")
        input('\nEnter to continue')

    # getting information for each classification, and how many fells fall into that
    def GetClassificationCount(self):

        classificationAndCount = []
        with Database() as db:
            classifications = db.GetAllClassifications()
        
            for classification in classifications:
                classificationCount = len(db.GetFellsForClassification(classification[0]))

                classificationAndCount.append({'info': classification, 'count': classificationCount})
                
        return classificationAndCount
    
    # how many of each classification the user has bagged
    def GetBaggedClassifications(self, classificationID):
        with Database() as db:
            classificationBags = db.GetBaggedFromClassification(self.userID, classificationID)

        # get info on that particular classification
        info = next(item for item in self.classificationCount if item['info'][0] == classificationID)

        percentBagged = round((len(classificationBags)/info['count']) * 100)

        print(f"\nYou have bagged {len(classificationBags)}/{info['count']} {info['info'][1]}s ({percentBagged}%)\n")
        
        plot = input("Would you like to view a plot of which hills you have and haven't bagged? ").lower()
        if plot == 'yes':
            self.MapClassificationFells(classificationID)
        

    # choice of which classification user wants
    def GetGroupStats(self):
        print()
        for n, classification in enumerate(self.classificationCount):
            print(f"{n+1}) {classification['info'][1]} ({classification['info'][2]})")

        group = input('\nEnter the number of the group you would like to view (0 to exit): ')

        while not group.isdigit() or int(group) < 0 or int(group) > len(self.classificationCount):
            group = input('That was not in the range specified')

        if group != '0':
            self.GetBaggedClassifications(self.classificationCount[int(group) - 1]['info'][0])

    def MapClassificationFells(self, classificationID):
        with Database() as db:
            fells = db.GetFellsForClassification(classificationID)
            classificationName = db.GetClassificationNameFromID(classificationID)

        self.MapBags(fells, f'Plot of the fells in the classification: {classificationName}')

    def MapBags(self, allFells, title):
        baggedX = []
        baggedY = []
        baggedLabels = []

        notBaggedX = []
        notBaggedY = []
        notBaggedLabels = []

        for fell in allFells:
            with Database() as db:
                # getting name, elevation, latitude and longitude
                fellInfo = db.GetFellInfoFromID(fell[0])

                # Y values (latitude) measured from -90 to 90, whereas X (longitude)
                # is measured from -180 to 180. Multiply Y values so it is scaled
                # Plots near the poles will look skewed because of spherical earth
                if db.GetIsFellBagged(self.userID, fell[0]):
                    baggedY.append(fellInfo[2]*2)
                    baggedX.append(fellInfo[3])
                    baggedLabels.append(f'{fellInfo[0]} ({fellInfo[1]}m)')

                else:
                    notBaggedY.append(fellInfo[2]*2)
                    notBaggedX.append(fellInfo[3])
                    notBaggedLabels.append(f'{fellInfo[0]} ({fellInfo[1]}m)')

        labels = baggedLabels + notBaggedLabels
        
        fig = plt.figure()
        plot = fig.add_subplot(111)

        # plot with a triangle
        sctNot = plot.scatter(notBaggedX, notBaggedY, c='red', marker=10)
        sctBag = plot.scatter(baggedX, baggedY, c='green', marker=10)

        plot.axis('scaled')

        # solution got, and edited from https://stackoverflow.com/questions/7908636/how-to-add-hovering-annotations-to-a-plot/47166787#47166787

        annotation = plot.annotate('', xy=(0,0), xytext=(20,20), textcoords='offset points',
                                   bbox=dict(boxstyle='round', fc='w'), arrowprops=dict(arrowstyle='->'))
        annotation.set_visible(False)

        def update_annotation(index):            
            # check if index is within in range of all bagged fells
            if index["ind"][0] < len(baggedLabels):
                pos = sctBag.get_offsets()[index["ind"][0]]
                annotation.set_backgroundcolor('green')
            else:
                # take away len(baggedLabels) to get index in not bagged fells
                pos = sctNot.get_offsets()[index["ind"][0] - len(baggedLabels)]
                annotation.set_backgroundcolor('red')

            annotation.xy = pos
            annotation.set_text(labels[index['ind'][0]])
            annotation.get_bbox_patch().set_alpha(0.4)
            

        def onHover(event):
            vis = annotation.get_visible()
            if event.inaxes == plot:
                cont, index = sctBag.contains(event)
                # if not hovering over the bagged (green), check not bagged (red)
                if not cont:
                    cont, index = sctNot.contains(event)
                    index['ind'] += len(baggedLabels)

                if cont:
                    update_annotation(index)
                    annotation.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    if vis:
                        annotation.set_visible(False)
                        fig.canvas.draw_idle()

        fig.canvas.mpl_connect('motion_notify_event', onHover)

        plot.set_xticks([])
        plot.set_yticks([])
        plot.set_title(title)
        plt.show()

    # show a box plot of the heights of all the mountains the user has bagged
    def BoxPlotHeights(self):

        with Database() as db:
            # only interested in the height (at index 1 in the tuples in the list)
            baggedFellsOrdered = [x[1] for x in db.GetAllBags(self.userID, nullElevation=False)]

        boxPlotData = plt.boxplot(baggedFellsOrdered, vert=False)

        if len(baggedFellsOrdered) < 2:
            return
        
        # general stats about the box plot
        
        maxHeight = baggedFellsOrdered[-1]
        minHeight = baggedFellsOrdered[0]

        median = round(boxPlotData['medians'][0].get_xdata()[0], 1)

        q1 = round(boxPlotData['whiskers'][0].get_xdata()[0], 1)
        plotMax = boxPlotData['whiskers'][0].get_xdata()[1]

        q3 = round(boxPlotData['whiskers'][1].get_xdata()[0], 1)
        plotMin = boxPlotData['whiskers'][1].get_xdata()[1]

        iqr = round((q3 - q1), 1)
        
        # always show general boxplot stats
        print(f'You have bagged hills in a range of {minHeight}m - {maxHeight}m')
        print(f'You have a median bagging height of {median}m')
        print(f'You have an IQR of {iqr}m, from {q1}m - {q3}m')
        print(f'The range excluding outliers is {plotMax}m - {plotMin}m')

        showBoxPlot = input('Would you like to view the full box plot? ').lower()

        # only show the box plot if user wants to
        if showBoxPlot == 'yes':
            plt.title('Box plot of the heights of mountains you have climbed')
            plt.show()
        else:
            plt.close()

    # graph how bagging has changed over time
    def GraphBags(self, fromDate='0000-00-00', toDate=datetime.today().strftime('%Y-%m-%d')):
        with Database() as db:
            bags = db.GetBagsInDateOrder(self.userID, fromDate, toDate)

        dates, dateCount = self.GetDatesAndCount(bags)

        plt.plot(dates, dateCount)
        plt.title('Graph of how number of bags has changed over times')
        plt.show()
        print()

    # counting how many bags are in increments (default is in getPreviousDate method)
    def GetDatesAndCount(self, bags):
        dates = []
        dateCount = []

        # add the first date to the list
        previousDate = Analysis.getPreviousDate(datetime.strptime(bags[0][1], '%Y-%m-%d'))
        dates.append(previousDate)
        dateCount.append(1)

        count = 1

        for bag in bags[1:]:

            count += 1
            date = datetime.strptime(bag[1], '%Y-%m-%d')

            # if the date is within the range, increment the count
            if date >= previousDate:
                dateCount[-1] += 1

            # if the date is within the next increment date in the list
            elif date >= Analysis.getPreviousDate(previousDate):
                previousDate = Analysis.getPreviousDate(previousDate)
                dates.append(previousDate)
                dateCount.append(1)

            # if there are increments of dates with no activities
            elif count < len(bags):
                previousDate = Analysis.getPreviousDate(previousDate)
                # fill in the months with 0 bags
                while date <= previousDate:
                    dates.append(previousDate)
                    dateCount.append(0)
                    previousDate = Analysis.getPreviousDate(previousDate)

                # next one in the list, fill with 1 bag
                dates.append(previousDate)
                dateCount.append(1)

        return dates, dateCount
    
    # How many bags the user has per country
    def PieChartCounties(self):
        with Database('Fells.db') as db:
            dbCountries = db.GetAllBaggingCountries()
        
        totalCounts = []
        distinctCounts = []
        countries = []

        for country in dbCountries:
            countries.append(country[0])
            with Database('Fells.db') as db:
                totalCounts.append(db.GetTotalBagsFromCountry(country[0]))
                distinctCounts.append(db.GetDistinctBagsFromCountry(country[0]))

        plt.subplot(1, 2, 1)
        patches, _ = plt.pie(totalCounts)
        plt.title('Pie chart of the number\nof bags per country')
        plt.legend(patches, countries, loc='center left', bbox_to_anchor=(-0.1, 1.), fontsize=8)

        plt.subplot(1, 2, 2)
        patches, _ = plt.pie(distinctCounts)
        plt.title('Pie chart of the number\nof distinct bags per country')
        plt.legend(patches, countries, loc='center', bbox_to_anchor=(-0.1, 1.), fontsize=8)

        plt.show()

        print()
    
    @staticmethod
    def getPreviousDate(date, nDays=91):
        return date - timedelta(days=nDays)