# Program written by Andrew Bell
# Used to add manual climbs (when Strava wasn't used) 

from datetime import datetime
from Database import Database

class ManualBag:

    def __init__(self, userID):
        self.userID = userID

    def searchForFell(self, search):
        with Database() as db:
            fells = db.SearchForFells(search)

        if len(fells) == 0:
            print(f'The search: "{search}" came up with no results')
        else:
            ManualBag.printFells(fells)
            choice = ManualBag.getChoice(len(fells))
            # return fellID if they choose a valid result
            if choice != -1:
                return fells[choice]
        return None

    @staticmethod
    def getChoice(n):
        if n == 1:
            choice = input('Enter 1 for the mountain shown, or 0 to exit: ')
        else:
            choice = input(f'Enter your choice, 1-{n}, or 0 to exit: ')

        while not choice.isdigit() or int(choice) < 0 or int(choice) > n:
            choice = input(f'That was not between 0 and {n}, please enter a valid number: ')

        # change into an index
        return int(choice) - 1
            

    @staticmethod
    def printFells(allFells):
        with Database() as db:
            wainwrights = db.GetFellsForClassification(8)
            outliers = db.GetFellsForClassification(9)
        for n, fellInfo in enumerate(allFells):
            extraText = ''
            for fell in wainwrights:
                if fell[0] == fellInfo[0]:
                    extraText = ' (is a wainwright)'
            for fell in outliers:
                if fell[0] == fellInfo[0]:
                    extraText = ' (is an outlier)'

            print(f'{n+1}) {fellInfo[1]} ({fellInfo[2]}m) in {fellInfo[3]}{extraText}')

    @staticmethod
    def manualBagMain(userID):
        
        manual = ManualBag(userID)

        while True:
            search = input('\nEnter your fell search ("quit" to exit): ')
            if search == 'quit':
                break

            fell = manual.searchForFell(search)

            if fell != None:
                print(f'You selected: "{fell[1]}"')

                correctDate = False
                dateStr = input(f'Please enter the date you bagged this fell, in the format YYYY-mm-dd: ')
                dateFormat = '%Y-%m-%d'
                
                while not correctDate:
                    try:
                        date = datetime.strptime(dateStr, dateFormat)
                        correctDate = True
                    except Exception as e:
                        dateStr = input(f'Incorrect format, please enter it in the format YYYY-mm-dd: ')

                with Database() as db:
                    # cannot add the same fell for the same user on the same day
                    if db.BagExists(fell[0], userID, date.strftime('%Y-%m-%d')):
                        print(f"A bag for {fell[1]} already exists on {date.strftime('%Y-%m-%d')}. Not added new bag")
                        
                    else:
                        db.AddBag(fell[0], userID, None, date.strftime('%Y-%m-%d'))
                        print(f"Manual bag added for {fell[1]} on {date.strftime('%Y-%m-%d')}")

