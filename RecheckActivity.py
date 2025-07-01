# Program written by Andrew Bell
# Used to recheck a particular activity

from datetime import datetime
import time
from Database import Database
from UpdateFells import UpdateFells

class RecheckActivity:

    def __init__(self, userID):
        self.userID = userID

    def searchForActivity(self, search):
        with Database() as db:
            activities = db.SearchForActivity(self.userID, search)

        if len(activities) == 0:
            print(f'The search: "{search}" came up with no results')
        else:
            RecheckActivity.printActivities(activities)
            choice = RecheckActivity.getChoice(len(activities))

            # return the activity if they choose a valid result
            if choice != -1:
                return activities[choice]
        return None

    @staticmethod
    def getChoice(n):
        print()
        if n == 1:
            choice = input('Enter 1 for the activity shown, or 0 to exit: ')
        else:
            choice = input(f'Enter your choice, 1-{n}, or 0 to exit: ')

        while not choice.isdigit() or int(choice) < 0 or int(choice) > n:
            choice = input(f'That was not between 0 and {n}, please enter a valid number')

        # change into an index
        return int(choice) - 1
            

    @staticmethod
    def printActivities(allActivities):
        for n, activityInfo in enumerate(allActivities):
            hours = int(activityInfo[3]/3600)
            minutes = int((activityInfo[3] - (hours*3600))/60)
            seconds = int(activityInfo[3] - (hours*3600 + minutes*60))

            print(f'{n+1}) {activityInfo[1]} ({activityInfo[2]}km, {activityInfo[4]}m, ' + 
                  f'{hours}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}). Last checked: {activityInfo[5]}')

    @staticmethod
    def recheckMain(userID):
        
        recheck = RecheckActivity(userID)

        while True:
            search = input('\nEnter your search for an activity ("quit" to exit): ')
            if search == 'quit':
                break

            activity = recheck.searchForActivity(search)

            if activity != None:
                print(f'You selected: "{activity[1]}"')
                save = input('Would you like to save the output to the database? ').lower()
                print()

                update = UpdateFells(userID, False)
                start = time.time()
                
                if save == 'yes':
                    with Database() as db:
                        db.RemoveBagsForActivity(userID, activity[0])

                    update.saveBagsToDB(f'activities/{activity[0]}.gpx', activity[0], True, False)

                else:
                    update.saveBagsToDB(f'activities/{activity[0]}.gpx', activity[0], False)

                print(f'\nThe check took {time.time() - start}s to process\n')