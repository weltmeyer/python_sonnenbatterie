"""Process the time of use schedule stuff"""
from datetime import time, datetime
from typing import List


ATTR_TOU_START="start"
ATTR_TOU_STOP="stop"
ATTR_TOU_MAX_POWER="threshold_p_max"
TIME_FORMAT="%H:%M"

MIDNIGHT=time()

class timeofuse:
    def __init__(self, start_time:time, stop_time:time, max_power=20000):
        self.start_time = start_time
        # for comparisson reasons we can't have the stop time be midnight as thaty's actually the earliest possible time
        # so if it is provided as midnight make it the latest possible time
        if (stop_time == MIDNIGHT):
            stop_time = time.max
        self.stop_time = stop_time
        self.max_power = max_power

    def __eq__(self, other) -> bool :
        if not isinstance(other, type(self)):
            return False
        return (self.start_time == other.start_time) and (self.stop_time == other.stop_time) and (self.max_power == other.max_power) 

    def __hash__(self) -> int:
        return hash(self.start_time) ^ hash(self.stop_time) ^ hash(self.max_power)

    def get_as_tou(self):
        start_string = self.get_start_time_as_string()
        tmp_stop_time = self.stop_time
        # previously we had to munge midnight as an stop time to 23:59:59.999999
        # if that was done now undo it
        if (tmp_stop_time == time.max):
            tmp_stop_time = MIDNIGHT

        stop_string=tmp_stop_time.strftime(TIME_FORMAT)
        max_power_string = str(self.max_power)
        return {ATTR_TOU_START:start_string, ATTR_TOU_STOP:stop_string, ATTR_TOU_MAX_POWER:max_power_string}
    
    def get_as_string(self) -> str:
        resp = "Start "+self.get_start_time_as_string()+", End "+self.get_stop_time_as_string(), "Max allowable power "+str(self.get_max_power())
        return resp 

    def get_start_time_as_string(self) -> str:
        return self._get_time_as_string(self.start_time)
    
    def get_stop_time_as_string(self) -> str:
        tmp_stop_time = self.stop_time
        # previously we had to munge midnight as an stop time to 23:59:59.999999
        # if that was done now undo it
        if (tmp_stop_time == time.max):
            tmp_stop_time = MIDNIGHT
        return self._get_time_as_string(tmp_stop_time)
    
    def _get_time_as_string(self, timeobj:time) -> str:
        return timeobj.strftime(TIME_FORMAT)
    
    def get_max_power(self) -> int:
        return self.max_power
    
    def from_tou(tou):
        # parse it out
        start_time = datetime.strptime(tou.get(ATTR_TOU_START), TIME_FORMAT).time()
        stop_time = datetime.strptime(tou.get(ATTR_TOU_STOP), TIME_FORMAT).time()
        max_power= int(tou.get(ATTR_TOU_MAX_POWER))
        # build the resulting object
        return timeofuse(start_time, stop_time, max_power)
    
    def is_overlapping(self, other):
        # is our start time within the others time window ?
        if (self.start_time>= other.start_time) and (self.start_time<= other.stop_time):
            return True
        
        # is our end time within the others time window ?
        if (self.stop_time>= other.start_time) and (self.stop_time<= other.stop_time):
            return True
        

        # is it's start time within the out time window ?
        if (other.start_time>= self.start_time) and (other.start_time<= self.stop_time):
            return True
        
        # is it's end time within the out time window ?
        if (other.stop_time>= self.start_time) and (other.stop_time<= self.stop_time):
            return True
        
        # no overlap
        return False
    
    def create_time_of_use_entry(start_hour=23, start_min=30, stop_hour=5, stop_min=30, max_power=20000):
        start_time = time(hour=start_hour, minute=start_min)
        stop_time = time(hour=stop_hour, minute=stop_min) 
        return timeofuse(start_time, stop_time, int(max_power))
    
class timeofuseschedule:
    def __init__(self):
        self._schedule_entries = []

    # adds the entry ensureing that it does not overlap with an existing entry
    def _add_entry(self, entry):
        if (entry.stop_time < entry.start_time):
            raise Exception("End time cannot be before start time")
        for i in self._schedule_entries:
            if (i.is_overlapping(entry)):
                raise Exception("Unable to add entry, overlaps with exisitngv entry")
        self._schedule_entries.append(entry)
        # maintains this as a sotred list based on the start time, this lets us compare properly
        self._schedule_entries = sorted(self._schedule_entries, key=lambda entry: entry.start_time)

    # Add an entry, if it spans midnight split it into a before midnight and after midnight section
    # Note that this IS NOT reversed on retrieving the saved entries
    # Note that the change may result in a modified list order, so callers should AWAYS
    # use the returned list or get a new one as that will reflect the current state of
    # afairs
    def add_entry(self, entry):
        if (entry.start_time > entry.stop_time):
            # this is a over midnight situation
            self._add_entry(timeofuse(entry.start_time, time.max, entry.max_power))
            self._add_entry(timeofuse(time.min, entry.stop_time,entry.max_power))
        else:
            self._add_entry(entry)
        return self.get_as_tou_schedule()

    # Note that the change may result in a modified list order, so callers should AWAYS
    # use the returned list or get a new one as that will reflect the current state of
    # afairs
    def delete_entry(self, entry_number):
        self._schedule_entries.pop(entry_number)
        return self.get_as_tou_schedule()
    # removes and exisitng entry and adds a new one , this is really just a convenience
    # If the new entry is rejected due to overlap then the deleted one IS NOT REPLACED
    # Note that the change may result in a modified list order, so callers should AWAYS
    # use the returned list or get a new one as that will reflect the current state of
    # afairs
    def remove_and_replace_entry(self, old_entry_nuber, new_entry):
        self._schedule_entries.pop(old_entry_nuber)
        return self.add_entry(new_entry)

    def get_as_tou_schedule(self)-> List[timeofuse]:
        schedules = []
        for i in self._schedule_entries :
            schedules.append(i.get_as_tou())
        return schedules
    
    def get_as_string(self) -> str:
        result = ""
        doneFirst = False 
        for entry in self._schedule_entries :
            if (doneFirst) :
                result = result +","
            else :
                doneFirst = True 
            result = result + str(entry.get_as_string())
        return result 
    
    # retained fore compatibility purposed, is not just a wrapper roung  def load_tou_schedule
    def load_tou_schedule(self, schedcule):
        self.load_tou_schedule_from_json(schedcule)

    # replace the current tou schedule data with the new dicitonary data
    def load_tou_schedule_from_json(self, json_schedule):
        self._schedule_entries = []
        for entry in json_schedule:
            tou_entry = timeofuse.from_tou(entry)
            self.add_entry(tou_entry)

    # create a new timeofuseschedule with the provided array ofdictionary data
    def build_from_json(json_schedule) :
        tous = timeofuseschedule()
        for entry in json_schedule:
            tou_entry = timeofuse.from_tou(entry)
            tous.add_entry(tou_entry)
        return tous
    
    def entry_count(self) -> int:
        return len(self._schedule_entries)

    
    def get_tou_entry_count(self) -> int:
        return len(self._schedule_entries)
    
    def get_tou_entry(self, i:int) -> timeofuse:
        entrties = self.get_tou_entry_count()
        if (i > entrties):
            return None
        else:
            return self._schedule_entries[i]

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        myEntryCount = self.entry_count() 
        otherEntryCount = other.entry_count()
        # if there both zero length by definition they are equal
        if (myEntryCount == 0) and (otherEntryCount==0):
            return True
        # different numbers of entries means different scheduled
        if (myEntryCount != otherEntryCount):
            return False
        # for each entry
        for i in range(0, myEntryCount):
            myTou = self.get_tou_entry(i)
            otherTou = other.get_tou_entry(i)
            if (myTou != otherTou):
                return False
        # got to the end of the individual timeofuse entries and they arew all equal so ...
        return True
    
    def __hash__(self) -> int:
        myHash = 0
        myEntryCount = self.entry_count() 
        for i in range(0, myEntryCount):
            myTou = self.get_tou_entry(i)
            myTouHash = hash(myTou) 
            # adjust the hash based on the position in the order to allow for things in a differing order
            myHash = myHash ^ (myTouHash + i)
        return myHash