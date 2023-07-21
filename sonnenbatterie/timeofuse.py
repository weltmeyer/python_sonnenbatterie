"""Process the time of use schedule stuff"""
from datetime import time, datetime

ATTR_TOU_START="start"
ATTR_TOU_STOP="stop"
ATTR_TOU_MAX_POWER="threshold_p_max"
TIME_FORMAT="%H:%M"

MIDNIGHT=time()

class timeofuse:
    def __init__(self, start_time, stop_time, max_power=20000):
        self.start_time = start_time
        # for comparisson reasons we can't have the stop time be midnight as thaty's actually the earliest possible time
        # so if it is provided as midnight make it the latest possible time
        if (stop_time == MIDNIGHT):
            stop_time = time.max
        self.stop_time = stop_time
        self.max_power = max_power

    def get_as_tou(self):
        start_string = self.start_time.strftime(TIME_FORMAT)
        tmp_stop_time = self.stop_time
        # previously we had to munge midnight as an stop time to 23:59:59.999999
        # if that was done now undo it
        if (tmp_stop_time == time.max):
            tmp_stop_time = MIDNIGHT

        stop_string=tmp_stop_time.strftime(TIME_FORMAT)
        max_power_string = str(self.max_power)
        return {ATTR_TOU_START:start_string, ATTR_TOU_STOP:stop_string, ATTR_TOU_MAX_POWER:max_power_string}
    
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
        self.schedule_entries = []

    # adds the entry ensureing that it does not overlap with an existing entry
    def _add_entry(self, entry):
        if (entry.stop_time < entry.start_time):
            raise Exception("End time cannot be before start time")
        for i in self.schedule_entries:
            if (i.is_overlapping(entry)):
                raise Exception("Unable to add entry, overlaps with exisitngv entry")
        self.schedule_entries.append(entry)
        # maintains this as a sotred list based on the start time
        self.schedule_entries = sorted(self.schedule_entries, key=lambda entry: entry.start_time)
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
        self.schedule_entries.pop(entry_number)
        return self.get_as_tou_schedule()
    # removes and exisitng entry and adds a new one , this is really just a convenience
    # If the new entry is rejected due to overlap then the deleted one IS NOT REPLACED
    # Note that the change may result in a modified list order, so callers should AWAYS
    # use the returned list or get a new one as that will reflect the current state of
    # afairs
    def remove_and_replace_entry(self, old_entry_nuber, new_entry):
        self.schedule_entries.pop(old_entry_nuber)
        return self.add_entry(new_entry)

    def get_as_tou_schedule(self):
        schedules = []
        for i in self.schedule_entries :
            schedules.append(i.get_as_tou())
        return schedules
    
    def load_tou_schedule(self, schedule):
        self.schedule_entries = []
        for entry in schedule:
            tou_entry = timeofuse.from_tou(entry)
            self.add_entry(tou_entry)