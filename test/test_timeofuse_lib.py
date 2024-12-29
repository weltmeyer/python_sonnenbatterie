#!/usr/bin/env python3
# I suspect that I haven't got to grips with the way phthon does things, but soppusely this will setup the path to allod for the sonnen batteri moduel to be in a separate location
# To me having to do this for testing seems a horrendous hack
import json
import os
import sys

script_path = os.path.realpath(os.path.dirname(__name__))
os.chdir(script_path)
sys.path.append("..")
from pprint import pprint
from timeofuse.timeofuse import TimeofUseSchedule, create_time_of_use_entry

problemHit = False
problemsList = ""
def do_test(description:str, test, expected_result):
    actual_result = test()
    if expected_result == actual_result:
        print (description+" achieved expected result of "+str(actual_result))
    else :
        global problemHit
        global problemsList
        problemHit = True
        problemstr = description+" did not result in expected result of "+str(expected_result)+" but actually resulted in "+str(actual_result)
        print ("================= PROBLEM ===============")
        print (problemstr)
        print ("================= PROBLEM ===============")
        problemsList = problemsList + "\n"+problemstr

if __name__ == '__main__':
    tous = TimeofUseSchedule()  
    print("\nEmpty schedule")
    pprint(tous.get_as_tou_schedule())
    tou=create_time_of_use_entry()
    print("\nOverlapping midnight schedule")
    pprint(tous.add_entry(tou))
    print ("\nAdding non overlaping entry")
    tou=create_time_of_use_entry(10,0,11,0)
    touTenToEleven = tou
    pprint(tous.add_entry(tou))
    print ("\nAdding fully overlaping entry")
    tou=create_time_of_use_entry(9,0,12,0)
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
    tou=create_time_of_use_entry(9,0,10,30)
    touNineToTenThirty = tou
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding overlaping end entry")
    tou=create_time_of_use_entry(10,30, 11, 30)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, tnis is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nAdding exact match overlaping entry")
    tou=create_time_of_use_entry(10,0,11,0)
    try:
        tous.add_entry(tou)
        print ("\nOpps, no exception, this is a bug")
    except Exception as e:
        print ("\nExpected exception message "+str(e.args))
    pprint(tous.get_as_tou_schedule())

    print ("\nBuilding based on returned entry")
    old_schedule = tous.get_as_tou_schedule()
    tous = TimeofUseSchedule() 
    tous.load_tou_schedule(old_schedule)

    print("\nAfter schedule load")
    pprint(tous.get_as_tou_schedule())
    print("\nAfter deleting index entry")
    pprint(tous.delete_entry(1))
    js = json.dumps(tous.get_as_tou_schedule())
    print("Dumped json data "+js)

    print("Testing timeofuse class hash codes")
    touSecondNineToMidday = create_time_of_use_entry(9,0,12,0)

    touTouTenToElevenMaxPower=create_time_of_use_entry(10,0,11,0, 40000)
    firstNineToMiddayHash = hash(touNineToMidday)
    secondNineToMiddayHash = hash(touSecondNineToMidday)
    tenToElevenHash = hash(touTenToEleven)
    touTouTenToElevenMaxPowerHash = hash (touTouTenToElevenMaxPower)
    print("Hash of first nine to midday "+str(firstNineToMiddayHash))
    print("Hash of second nine to midday "+str(secondNineToMiddayHash))
    print("Hash of ten to eleven "+str(tenToElevenHash))
    print("Hash of ten to eleven max power "+str(touTouTenToElevenMaxPowerHash))
    do_test("Compare hash of first and second nine to midday  ", lambda:firstNineToMiddayHash == secondNineToMiddayHash, True)
    do_test("Compare hash of nine to midday and ten to eleven ", lambda:firstNineToMiddayHash == tenToElevenHash, False)
    do_test("Compare hash of ten to eleven and ten to eleven max power ", lambda:touTouTenToElevenMaxPowerHash == tenToElevenHash, False)

    print("Testing timeofuse class equality")
    touSecondNineToMidday = create_time_of_use_entry(9,0,12,0)
    do_test("Compare first nine to midday with itself ", lambda:touNineToMidday == touNineToMidday, True)
    do_test("Compare first nine to midday with sesond nine to midday ", lambda:touNineToMidday == touSecondNineToMidday, True)
    do_test("Compare second nine to midday with first nine to midday ", lambda:touSecondNineToMidday == touNineToMidday, True)
    do_test("Compare nine to midday with ten to eleven ", lambda:touNineToMidday == touTenToEleven, False)
    do_test("Compare ten to eleven with ten to eleven max power ", lambda: touTenToEleven == touTouTenToElevenMaxPower , False)

    
    firstEmptyTous = TimeofUseSchedule()
    secondEmptyTous = TimeofUseSchedule()

    firstNineToMiddayTous = TimeofUseSchedule()
    firstNineToMiddayTous.add_entry(touNineToMidday)
    firstNineToMiddayTousSameTou = TimeofUseSchedule()
    firstNineToMiddayTousSameTou.add_entry(touNineToMidday)
    secondNineToMiddayTous = TimeofUseSchedule()
    secondNineToMiddayTous.add_entry(touSecondNineToMidday)
    tenToElevenTous = TimeofUseSchedule()
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
    do_test("Compare hash of first empty with itself ", lambda:firstEmptyTousHash == firstEmptyTousHash,True)
    do_test("Compare hash of first and second empty ", lambda:firstEmptyTousHash == secondEmptyTousHash,True)
    do_test("Compare hash of empty and nine to midday ", lambda:firstEmptyTousHash == firstNineToMiddayTousHash,False)
    do_test("Compare hash of first midday with itself ", lambda:firstNineToMiddayTousHash == firstNineToMiddayTousHash,True)
    do_test("Compare hash of first midday with other nine to middat using tame tou  ", lambda:firstNineToMiddayTousHash == firstNineToMiddayTousSameTouHash,True)
    do_test("Compare hash of first and second nine to midday ", lambda:firstNineToMiddayTousHash == secondNineToMiddayTousHash,True)
    do_test("Compare hash of first nine to midday with ten to elevel ", lambda:firstNineToMiddayTousHash == tenToElevelTousHash,False)

    print("Testing single entry time of use schedule class equality")

    do_test("Compare first empty tous with itself ", lambda:firstEmptyTous == firstEmptyTous,True)
    do_test("Compare first empty tous with second empty ", lambda:firstEmptyTous == secondEmptyTous,True)
    do_test("Compare second empty tous with first empty ", lambda:secondEmptyTous==firstEmptyTous,True)
    do_test("Compare first nine to midday tous with itself ", lambda:firstNineToMiddayTous == firstNineToMiddayTous,True)
    do_test("Compare first nine to midday tous with the same using the same Tou ", lambda:firstNineToMiddayTous == firstNineToMiddayTousSameTou,True)
    do_test("Compare first empty tous with first nine to midday ", lambda:firstEmptyTous == firstNineToMiddayTous,False)
    do_test("Compare first nine to midday tous with first empty ", lambda:firstNineToMiddayTous==firstEmptyTous,False)
    do_test("Compare first nine to midday tous with ten to eleven  ", lambda:firstNineToMiddayTous==tenToElevenTous,False)
    do_test("Compare ten to eleven tous with first nine to midday  ", lambda:tenToElevenTous==firstNineToMiddayTous,False)


    print("Testing multiple entry time of use schedule hashes")
    morningTou = create_time_of_use_entry(9,0,10,0)
    afternoonTou = create_time_of_use_entry(13,0,15,0)
    eveningTou = create_time_of_use_entry(21,0,22,0)
    nightTou = create_time_of_use_entry(1,30,3,40)
    overMidnightTou = create_time_of_use_entry(23,30,5,30)
    uptoMidnightTou = create_time_of_use_entry(23,30,0,0)
    afterMidnightTou = create_time_of_use_entry(0,0,5, 30)

    tousMorningAfternoon = TimeofUseSchedule() 
    tousMorningAfternoon.add_entry(morningTou)
    tousMorningAfternoon.add_entry(afternoonTou)
    tousFirstMorningAfternoonEveningNight = TimeofUseSchedule() 
    tousFirstMorningAfternoonEveningNight.add_entry(morningTou)
    tousFirstMorningAfternoonEveningNight.add_entry(afternoonTou)
    tousFirstMorningAfternoonEveningNight.add_entry(eveningTou)
    tousFirstMorningAfternoonEveningNight.add_entry(nightTou)
    tousSecondMorningAfternoonEveningNight = TimeofUseSchedule() 
    tousSecondMorningAfternoonEveningNight.add_entry(morningTou)
    tousSecondMorningAfternoonEveningNight.add_entry(afternoonTou)
    tousSecondMorningAfternoonEveningNight.add_entry(eveningTou)
    tousSecondMorningAfternoonEveningNight.add_entry(nightTou)
    tousAfternoonMorning = TimeofUseSchedule() 
    tousAfternoonMorning.add_entry(afternoonTou)
    tousAfternoonMorning.add_entry(morningTou)
    tousAfternoonEvening = TimeofUseSchedule() 
    tousAfternoonEvening.add_entry(afternoonTou)
    tousAfternoonEvening.add_entry(eveningTou)
    tousOvernight = TimeofUseSchedule() 
    tousOvernight.add_entry(overMidnightTou)
    tousUptoAfterMidnight =  TimeofUseSchedule() 
    tousUptoAfterMidnight.add_entry(uptoMidnightTou)
    tousUptoAfterMidnight.add_entry(afterMidnightTou)

    do_test("Compare hashes for first and second  morning/afternoon/evening/night", lambda:hash(tousFirstMorningAfternoonEveningNight) == hash (tousSecondMorningAfternoonEveningNight), True)
    do_test("Compare hashes for morning / afternoon with first  morning/afternoon/evening/night", lambda:hash(tousMorningAfternoon) == hash (tousSecondMorningAfternoonEveningNight), False)
    do_test("Compare hashes for morning/afternoon with afternoon/morning", lambda:hash(tousMorningAfternoon) == hash (tousAfternoonMorning), True)
    do_test("Compare hashes for  afternoon/morning with morning/afternoon", lambda:hash(tousAfternoonMorning) == hash (tousMorningAfternoon), True)
    do_test("Compare hashes for upto after midnight with overnight", lambda:hash(tousUptoAfterMidnight) == hash (tousOvernight), True)


    print("Testing multiple entry time of use schedule class equality")
    do_test("Comparing single and multiple entry tous (morning / afternoon / evening / night with nine to midday )", lambda: tousFirstMorningAfternoonEveningNight == firstNineToMiddayTous, False )
    do_test("Comparing multiple and single entry tous (nine to midday with morning / afternoon / evening / night  )", lambda: firstNineToMiddayTous == tousFirstMorningAfternoonEveningNight, False )
    do_test("Comparing  morning/afternoon with afternoon/morning )", lambda: tousMorningAfternoon == tousAfternoonMorning, True )
    do_test("Comparing afternoon/morning with   morning/afternoon )", lambda: tousAfternoonMorning == tousMorningAfternoon, True )
    do_test("Comparing overnight with upto / after midnight )", lambda: tousOvernight == tousUptoAfterMidnight, True )
    do_test("Comparing  upto / after midnight with overnight)", lambda: tousUptoAfterMidnight==tousOvernight, True )


    if problemHit:
        print ("=========== WARNING, WARNING, WARNING ===========")
        print (problemsList)
        print ("=========== WARNING, WARNING, WARNING ===========")
    else:
        print("All worked fine")
