#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import os, sys, json
script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from login import *
from pprint import pprint
from sonnenbatterie.timeofuse import timeofuse, timeofuseschedule

problemHit = False
problemsList = ""
def doTest(description:str, test, expectedResult):
    actualResult = test() 
    if (expectedResult == actualResult) :
        print (description+" achieved expected result of "+str(actualResult))
    else :
        global problemHit
        global problemsList
        problemHit = True
        problemStr = description+" did not result in expected result of "+str(expectedResult)+" but actually resulted in "+str(actualResult)
        print ("================= PROBLEM ===============")
        print (problemStr)
        print ("================= PROBLEM ===============")
        problemsList = problemsList + "\n"+problemStr

if (__name__ == '__main__'):
    tous = timeofuseschedule()  
    print("\nEmpty schedule")
    pprint(tous.get_as_tou_schedule())
    tou=timeofuse.create_time_of_use_entry()
    print("\nOverlapping midnight schedule")
    pprint(tous.add_entry(tou))
    print ("\nAdding non overlaping entry")
    tou=timeofuse.create_time_of_use_entry(10,0,11,0)
    touTenToEleven = tou
    pprint(tous.add_entry(tou))
    print ("\nAdding fully overlaping entry")
    tou=timeofuse.create_time_of_use_entry(9,0,12,0)
    touNineToMidday = tou
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))

    pprint(tous.get_as_tou_schedule())

    print("Getting as string")
    print(tous.get_as_string())

    print ("\nAdding overlaping start entry")
    tou=timeofuse.create_time_of_use_entry(9,0,10,30)
    touNineToTenThirty = tou
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding overlaping end entry")
    tou=timeofuse.create_time_of_use_entry(10,30, 11, 30)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding exacty match overlaping entry")
    tou=timeofuse.create_time_of_use_entry(10,0,11,0)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\Building based on returned entry")
    old_schedule = tous.get_as_tou_schedule()
    tous = timeofuseschedule() 
    tous.load_tou_schedule(old_schedule)

    print("\nAfter schedule load")
    pprint(tous.get_as_tou_schedule())
    print("\nAfter deleting index entry")
    pprint(tous.delete_entry(1))
    js = json.dumps(tous.get_as_tou_schedule())
    print("Dumped json data "+js)

    print("Testing timeofuse class hash codes")
    touSecondNineToMidday = timeofuse.create_time_of_use_entry(9,0,12,0)

    touTouTenToElevenMaxPower=timeofuse.create_time_of_use_entry(10,0,11,0, 40000)
    firstNineToMiddayHash = hash(touNineToMidday)
    secondNineToMiddayHash = hash(touSecondNineToMidday)
    tenToElevenHash = hash(touTenToEleven)
    touTouTenToElevenMaxPowerHash = hash (touTouTenToElevenMaxPower)
    print("Hash of first nine to midday "+str(firstNineToMiddayHash))
    print("Hash of second nine to midday "+str(secondNineToMiddayHash))
    print("Hash of ten to eleven "+str(tenToElevenHash))
    print("Hash of ten to eleven max power "+str(touTouTenToElevenMaxPowerHash))
    doTest("Compare hash of first and second nine to midday  ", lambda:firstNineToMiddayHash == secondNineToMiddayHash, True)
    doTest("Compare hash of nine to midday and ten to eleven ", lambda:firstNineToMiddayHash == tenToElevenHash, False)
    doTest("Compare hash of ten to eleven and ten to eleven max power ", lambda:touTouTenToElevenMaxPowerHash == tenToElevenHash, False)

    print("Testing timeofuse class equality")
    touSecondNineToMidday = timeofuse.create_time_of_use_entry(9,0,12,0)
    doTest("Compare first nine to midday with itself ", lambda:touNineToMidday == touNineToMidday, True)
    doTest("Compare first nine to midday with sesond nine to midday ", lambda:touNineToMidday == touSecondNineToMidday, True)
    doTest("Compare second nine to midday with first nine to midday ", lambda:touSecondNineToMidday == touNineToMidday, True)
    doTest("Compare nine to midday with ten to eleven ", lambda:touNineToMidday == touTenToEleven, False)
    doTest("Compare ten to eleven with ten to eleven max power ", lambda: touTenToEleven == touTouTenToElevenMaxPower , False)

    
    firstEmptyTous = timeofuseschedule()
    secondEmptyTous = timeofuseschedule()

    firstNineToMiddayTous = timeofuseschedule()
    firstNineToMiddayTous.add_entry(touNineToMidday)
    firstNineToMiddayTousSameTou = timeofuseschedule()
    firstNineToMiddayTousSameTou.add_entry(touNineToMidday)
    secondNineToMiddayTous = timeofuseschedule()
    secondNineToMiddayTous.add_entry(touSecondNineToMidday)
    tenToElevenTous = timeofuseschedule()
    tenToElevenTous.add_entry(touTenToEleven)

    print("Testing single entry time of use schedule hashes")
    firstEmptyTousHash = hash(firstEmptyTous)
    secondEmptyTousHash = hash(secondEmptyTous)
    firstNineToMiddayTousHash = hash(firstNineToMiddayTous)
    firstNineToMiddayTousSameTouHash = hash(firstNineToMiddayTousSameTou)
    secondNineToMiddayTousHash = hash(secondNineToMiddayTous)
    tenToElevelTousHash = hash(tenToElevenTous)
    print("Hash of first empty tous "+str(firstEmptyTousHash))
    print("Hash of second empty tous "+str(secondEmptyTousHash))
    print("Hash of first nine to midday tous "+str(firstNineToMiddayTousHash))
    print("Hash of first nine to midday tous with same tou "+str(firstNineToMiddayTousSameTouHash))
    print("Hash of second nine to midday tous "+str(secondNineToMiddayTousHash))
    print("Hash of ten to eleven  tous "+str(tenToElevelTousHash))
    doTest("Compare hash of first empty with itself ", lambda:firstEmptyTousHash == firstEmptyTousHash,True)
    doTest("Compare hash of first and second empty ", lambda:firstEmptyTousHash == secondEmptyTousHash,True)
    doTest("Compare hash of empty and nine to midday ", lambda:firstEmptyTousHash == firstNineToMiddayTousHash,False)
    doTest("Compare hash of first midday with itself ", lambda:firstNineToMiddayTousHash == firstNineToMiddayTousHash,True)
    doTest("Compare hash of first midday with other nine to middat using tame tou  ", lambda:firstNineToMiddayTousHash == firstNineToMiddayTousSameTouHash,True)
    doTest("Compare hash of first and second nine to midday ", lambda:firstNineToMiddayTousHash == secondNineToMiddayTousHash,True)
    doTest("Compare hash of first nine to midday with ten to elevel ", lambda:firstNineToMiddayTousHash == tenToElevelTousHash,False)

    print("Testing single entry time of use schedule class equality")

    doTest("Compare first empty tous with itself ", lambda:firstEmptyTous == firstEmptyTous,True)
    doTest("Compare first empty tous with second empty ", lambda:firstEmptyTous == secondEmptyTous,True)
    doTest("Compare second empty tous with first empty ", lambda:secondEmptyTous==firstEmptyTous,True)
    doTest("Compare first nine to midday tous with itself ", lambda:firstNineToMiddayTous == firstNineToMiddayTous,True)
    doTest("Compare first nine to midday tous with the same using the same Tou ", lambda:firstNineToMiddayTous == firstNineToMiddayTousSameTou,True)
    doTest("Compare first empty tous with first nine to midday ", lambda:firstEmptyTous == firstNineToMiddayTous,False)
    doTest("Compare first nine to midday tous with first empty ", lambda:firstNineToMiddayTous==firstEmptyTous,False)
    doTest("Compare first nine to midday tous with ten to eleven  ", lambda:firstNineToMiddayTous==tenToElevenTous,False)
    doTest("Compare ten to eleven tous with first nine to midday  ", lambda:tenToElevenTous==firstNineToMiddayTous,False)


    print("Testing multiple entry time of use schedule hashes")
    morningTou = timeofuse.create_time_of_use_entry(9,0,10,0) 
    afternoonTou = timeofuse.create_time_of_use_entry(13,0,15,0) 
    eveningTou = timeofuse.create_time_of_use_entry(21,0,22,0) 
    nightTou = timeofuse.create_time_of_use_entry(1,30,3,40) 
    overMidnightTou = timeofuse.create_time_of_use_entry(23,30,5,30)
    uptoMidnightTou = timeofuse.create_time_of_use_entry(23,30,0,0)
    afterMidnightTou = timeofuse.create_time_of_use_entry(0,0,5, 30)

    tousMorningAfternoon = timeofuseschedule() 
    tousMorningAfternoon.add_entry(morningTou)
    tousMorningAfternoon.add_entry(afternoonTou)
    tousFirstMorningAfternoonEveningNight = timeofuseschedule() 
    tousFirstMorningAfternoonEveningNight.add_entry(morningTou)
    tousFirstMorningAfternoonEveningNight.add_entry(afternoonTou)
    tousFirstMorningAfternoonEveningNight.add_entry(eveningTou)
    tousFirstMorningAfternoonEveningNight.add_entry(nightTou)
    tousSecondMorningAfternoonEveningNight = timeofuseschedule() 
    tousSecondMorningAfternoonEveningNight.add_entry(morningTou)
    tousSecondMorningAfternoonEveningNight.add_entry(afternoonTou)
    tousSecondMorningAfternoonEveningNight.add_entry(eveningTou)
    tousSecondMorningAfternoonEveningNight.add_entry(nightTou)
    tousAfternoonMorning = timeofuseschedule() 
    tousAfternoonMorning.add_entry(afternoonTou)
    tousAfternoonMorning.add_entry(morningTou)
    tousAfternoonEvening = timeofuseschedule() 
    tousAfternoonEvening.add_entry(afternoonTou)
    tousAfternoonEvening.add_entry(eveningTou)
    tousOvernight = timeofuseschedule() 
    tousOvernight.add_entry(overMidnightTou)
    tousUptoAfterMidnight =  timeofuseschedule() 
    tousUptoAfterMidnight.add_entry(uptoMidnightTou)
    tousUptoAfterMidnight.add_entry(afterMidnightTou)

    doTest("Compare hashes for first and second  morning/afternoon/evening/night", lambda:hash(tousFirstMorningAfternoonEveningNight) == hash (tousSecondMorningAfternoonEveningNight), True)
    doTest("Compare hashes for morning / afternoon with first  morning/afternoon/evening/night", lambda:hash(tousMorningAfternoon) == hash (tousSecondMorningAfternoonEveningNight), False)
    doTest("Compare hashes for morning/afternoon with afternoon/morning", lambda:hash(tousMorningAfternoon) == hash (tousAfternoonMorning), True)
    doTest("Compare hashes for  afternoon/morning with morning/afternoon", lambda:hash(tousAfternoonMorning) == hash (tousMorningAfternoon), True)
    doTest("Compare hashes for upto after midnight with overnight", lambda:hash(tousUptoAfterMidnight) == hash (tousOvernight), True)


    print("Testing multiple entry time of use schedule class equality")
    doTest("Comparing single and multiple entry tous (morning / afternoon / evening / night with nine to midday )", lambda: tousFirstMorningAfternoonEveningNight == firstNineToMiddayTous, False )
    doTest("Comparing multiple and single entry tous (nine to midday with morning / afternoon / evening / night  )", lambda: firstNineToMiddayTous == tousFirstMorningAfternoonEveningNight, False )
    doTest("Comparing  morning/afternoon with afternoon/morning )", lambda: tousMorningAfternoon == tousAfternoonMorning, True )
    doTest("Comparing afternoon/morning with   morning/afternoon )", lambda: tousAfternoonMorning == tousMorningAfternoon, True )
    doTest("Comparing overnight with upto / after midnight )", lambda: tousOvernight == tousUptoAfterMidnight, True )
    doTest("Comparing  upto / after midnight with overnight)", lambda: tousUptoAfterMidnight==tousOvernight, True )


    if (problemHit):
        print ("=========== WARNING, WARNING, WARNING ===========")
        print (problemsList)
        print ("=========== WARNING, WARNING, WARNING ===========")
    else:
        print("All worked fine")