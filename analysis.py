import pandas as pd
import os

def time_to_seconds(time_string):
    if ":" in time_string:
        split_on_mins = time_string.split(":")
    else:
        split_on_mins = ["0", time_string]
    mins = int(split_on_mins[0])
    split_on_secs = split_on_mins[1].split(".")
    secs = int(split_on_secs[0])
    hundredths = int(split_on_secs[1])
    return mins * 60 + secs + .01 * hundredths

class Swimmer():
    def __init__(self, name, age_in_2021):
        self.name = name
        self.age_in_2021 = age_in_2021
        # Event -> Age -> Time
        self.times = dict()

    # Time is string formatted
    # Event should be formated "50 FR SCY" (default by USA swimming)
    def add_time(self, event, age, time):
        if type(time) != float:
            time = time_to_seconds(time)
        if event not in self.times:
            self.times[event] = dict()
        if age not in self.times[event]:
            self.times[event][age] = time
        if self.times[event][age] > time:
            self.times[event][age] = time
    
    def get_time(self, event, age):
        if event in self.times and age in self.times[event]:
            return self.times[event][age]
        return None
    
    # Higher is better (i.e., negative difference)
    def get_improvement(self, event, ages):
        if event not in self.times:
            return None
        if ages[0] not in self.times[event]:
            return None
        if ages[1] not in self.times[event]:
            return None
        return self.times[event][ages[0]] - self.times[event][ages[1]]


class Recruit():
    # Events is a list of event strings of form: "50 FR SCY"
    def __init__(self, name, events):
        self.name = name
        self.events = events

filenames = []
folders = ["50FR", "100FR", "200FR", "500FR"]
for folder in folders:
    files = os.listdir(folder)
    files = [x for x in files if x.split(".")[1]=='csv']  # Remove non csvs
    # Expectation is that filenames have year at the beginning with other info followed by underscores
    folder_fnames = [(x, int(x.split("_")[0])) for x in files]
    filenames.extend([(folder + "/" + x, y) for x, y in folder_fnames])

# Hard code recruits
recruits = [
            # Sprint
            Recruit("Wilson, Zarek", ["50 FR SCY", "100 FR SCY", "200 FR SCY", "100 FL SCY"]),
            Recruit("Wang, Sonny", ["50 FR SCY", "100 FR SCY"]),
            Recruit("Duncan, Cade", ["50 FR SCY", "100 FR SCY"]),
            Recruit("Dalbey, Tristan", ["50 FR SCY", "100 FR SCY", "200 FR SCY"]),
            Recruit("Wehbe, Greg", ["50 FR SCY", "100 FR SCY", "200 FR SCY"]),
            Recruit("Pilkinton, Oliver", ["50 FR SCY", "100 FR SCY"]),
            # Mid
            Recruit("McFadden, Henry", ["500 FR SCY", "200 FR SCY", "200 FL SCY"]),
            Recruit("Denbrok, Tristan", ["200 FR SCY", "500 FR SCY"]),
            Recruit("Craft, Sam", ["200 FR SCY", "500 FR SCY"]),
            # Distance
            Recruit("Dunlap, Willi", ["400 IM SCY", "1650 FR SCY", "1000 FR SCY", "500 FR SCY"]),
            # Backstroke
            Recruit("Peterson, Andy", ["200 BK SCY", "200 FL SCY"]),
            Recruit("Beehler, Matthew", ["200 BK SCY"]),
            Recruit("Hagar, Tommy", ["200 BK SCY"]),
            # Fly
            Recruit("Schmitt, David", ["100 FL SCY", "200 FL SCY"]),
            Recruit("Baffico, Felipe", ["100 FL SCY", "200 FL SCY"]),
            Recruit("Pospishil, Jaden", ["100 FL SCY", "50 FR SCY", "100 FR SCY", "100 BK SCY"]),
            # Note: Flanders' time on sheets is LCM
            Recruit("Flanders, George", ["100 FL SCY"]),
            Recruit("Gold, Evan", ["100 FL SCY", "200 FL SCY"]),
            Recruit("Kharun, Ilya", ["100 FL SCY", "200 FL SCY", "50 FR SCY"]),
            ]

swimmers = dict()  # name to swimmer object

for filename, year in filenames:
    # Replace equals signs, first (weird USA swimming thing)
    with open(filename, "r") as fhand:
        text = fhand.read()
    text = text.replace("=", "")
    with open(filename, "w") as fhand:
        fhand.write(text)

    data = pd.read_csv(filename)
    
    for i, row in data.iterrows():
        name = row['full_name']
        age = row['swimmer_age']

        if name not in swimmers:
            age_in_2021 = 2021 - year + age
            swimmers[name] = Swimmer(name, age_in_2021)
        
        swimmers[name].add_time(row['event_desc'], age, row['alt_adj_swim_time_formatted'])

# Hard coded times
swimmers["Wilson, Zarek"].add_time("50 FR SCY", 15, "21.70")  # This is a converted time; original LCM was 24.83

def get_time_list(event, age, reverse=True, top=1000, age_in_2021=None):
    times = []
    for key in swimmers:
        if age_in_2021 is not None and swimmers[key].age_in_2021 != age_in_2021:
            continue
        time = swimmers[key].get_time(event, age)
        if time is not None:
            times.append(time)
    times.sort(reverse=reverse)
    # Only interested in top x number
    if top is not None:
        times = times[-top:]
    if len(times) != top:
        print(f"Warning: not enough people in {age} y/o {event}")
    return times

def get_percentile(mylist, value):
    for i, x in enumerate(mylist):
        if value >= x:
            return i / len(mylist)

def get_rank(mylist, value):
    for i, x in enumerate(mylist):
        if value >= x:
            return len(mylist) - i + 1
    
# Higher is better
def get_improvement_in_percentile(swimmer_obj, ages, event):
    times1 = get_time_list(event, ages[0])
    times2 = get_time_list(event, ages[1])

    time1 = swimmer_obj.get_time(event, ages[0])
    time2 = swimmer_obj.get_time(event, ages[1])
    if time1 is None or time2 is None:
        return None

    percentile1 = get_percentile(times1, time1)
    percentile2 = get_percentile(times2, time2)
    return percentile2 - percentile1

# Higher is better
def get_improvement_in_rank(swimmer_obj, ages, event):
    times1 = get_time_list(event, ages[0])
    times2 = get_time_list(event, ages[1])

    time1 = swimmer_obj.get_time(event, ages[0])
    time2 = swimmer_obj.get_time(event, ages[1])
    if time1 is None or time2 is None:
        return None

    rank1 = get_rank(times1, time1)
    rank2 = get_rank(times2, time2)
    return rank1 - rank2

for recruit in recruits:
    try:
        times = swimmers[recruit.name].times
        print(recruit.name + ": " + str(times))
        """
        imp = get_improvement_in_percentile(swimmers[recruit.name], (15, 16), "50 FR SCY")
        if imp is not None:
            print("Imp Percentile: " + str(round(imp, 3)))
        else:
            print("Imp Percentile: None")
        """
    except KeyError:
        print(f"{recruit.name} not found.")
