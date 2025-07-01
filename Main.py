from UpdateFells import UpdateFells
from ManualBag import ManualBag
from Analysis import Analysis
from RecheckActivity import RecheckActivity

if __name__ == '__main__':
    userID = 1

    UpdateFells(userID)

    while True:
        print('*'*100)

        choice = input('Enter "1" to manually bag fells, "2" for analysis, "3" to re-check an activity, or anything else to quit: ')
        if choice == '1':
            ManualBag.manualBagMain(userID)
        elif choice == '2':
            Analysis(userID)
        elif choice == '3':
            RecheckActivity.recheckMain(userID)
        else:
            break