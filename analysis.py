import pandas as pd
import os
import pickle
import statistics

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
    
    def get_oldest_age(self, event):
        if event not in self.times:
            return None
        return max([x[0] for x in self.times[event].items()])

class Recruit():
    # Events is a list of event strings of form: "50 FR SCY"
    def __init__(self, name, events, type):
        self.name = name
        self.events = events
        self.type = type


def save_data(fname="swimmer_data.sav"):

    filenames = []
    folders = ["50FR", "100FR", "200FR", "500FR", "1000FR", "1650FR", "400IM", "100BK", "100FL", "200BK", "200FL"]
    for folder in folders:
        files = os.listdir(folder)
        files = [x for x in files if x.split(".")[1]=='csv']  # Remove non csvs
        # Expectation is that filenames have year at the beginning with other info followed by underscores
        folder_fnames = [(x, int(x.split("_")[0])) for x in files]
        filenames.extend([(folder + "/" + x, y) for x, y in folder_fnames])

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
    swimmers["Gold, Evan"].add_time("100 FL SCY", 15, "52.54")  # Interpolated from April 2019 and April 2021 times
    swimmers["Gold, Evan"].add_time("200 FL SCY", 15, "1:57.5")  # Interpolated from April 2019 and April 2021 times


    pickle.dump(swimmers, open(fname, "wb"))

def get_time_list(event, age, reverse=True, top=1000, age_in_2021=None, top_if_same_class=250):
    times = []
    for key in swimmers:
        if age_in_2021 is not None and swimmers[key].age_in_2021 != age_in_2021:
            continue
        time = swimmers[key].get_time(event, age)
        if time is not None:
            times.append(time)
    times.sort(reverse=reverse)
    # Only interested in top x number
    if top is not None and age_in_2021 is None:
        times = times[-top:]
        if len(times) != top:
            print(f"Warning: not enough people in {age} y/o {event}")
    if top_if_same_class is not None and age_in_2021 is not None:
        times = times[-top_if_same_class:]
        if len(times) != top_if_same_class:
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
def get_improvement_in_percentile(swimmer_obj, ages, event, same_class=False):
    same_age = None
    if same_class:
        same_age = swimmer_obj.age_in_2021
    times1 = get_time_list(event, ages[0], age_in_2021=same_age)
    times2 = get_time_list(event, ages[1], age_in_2021=same_age)

    time1 = swimmer_obj.get_time(event, ages[0])
    time2 = swimmer_obj.get_time(event, ages[1])
    if time1 is None or time2 is None:
        return None

    percentile1 = get_percentile(times1, time1)
    percentile2 = get_percentile(times2, time2)
    return percentile2 - percentile1

# Higher is better
def get_improvement_in_rank(swimmer_obj, ages, event, same_class=False):
    same_age = None
    if same_class:
        same_age = swimmer_obj.age_in_2021
    times1 = get_time_list(event, ages[0], age_in_2021=same_age)
    times2 = get_time_list(event, ages[1], age_in_2021=same_age)

    time1 = swimmer_obj.get_time(event, ages[0])
    time2 = swimmer_obj.get_time(event, ages[1])
    if time1 is None or time2 is None:
        return None

    rank1 = get_rank(times1, time1)
    rank2 = get_rank(times2, time2)
    return rank1 - rank2

# Hard code recruits
recruits = [
            # Sprint
            # Note: Zarek Wilson's times are mostly in LCM because he's really a foreign swimmer
            # Recruit("Wilson, Zarek", ["50 FR SCY", "100 FR SCY", "200 FR SCY", "100 FL SCY"]),
            Recruit("Wang, Sonny", ["50 FR SCY", "100 FR SCY"], "Sprint"),
            Recruit("Duncan, Cade", ["50 FR SCY", "100 FR SCY"], "Sprint"),
            Recruit("Dalbey, Tristan", ["50 FR SCY", "100 FR SCY", "200 FR SCY"], "Sprint"),
            Recruit("Wehbe, Greg", ["50 FR SCY", "100 FR SCY", "200 FR SCY"], "Sprint"),
            Recruit("Pilkinton, Oliver", ["50 FR SCY", "100 FR SCY"], "Sprint"),
            # Mid
            Recruit("McFadden, Henry", ["500 FR SCY", "200 FR SCY", "200 FL SCY"], "Mid"),
            Recruit("Denbrok, Tristan", ["200 FR SCY", "500 FR SCY"], "Mid"),
            Recruit("Craft, Sam", ["200 FR SCY", "500 FR SCY"], "Mid"),
            # Distance
            Recruit("Dunlap, Willi", ["400 IM SCY", "1650 FR SCY", "1000 FR SCY", "500 FR SCY"], "Distance"),
            # Backstroke
            Recruit("Peterson, Andy", ["200 BK SCY", "200 FL SCY"], "Backstroke"),
            Recruit("Beehler, Matt", ["200 BK SCY"], "Backstroke"),
            Recruit("Hagar, Tommy", ["200 BK SCY"], "Backstroke"),
            # Fly
            Recruit("Schmitt, David", ["100 FL SCY", "200 FL SCY"], "Fly"),
            Recruit("Baffico, Felipe", ["100 FL SCY", "200 FL SCY"], "Fly"),
            Recruit("Pospishil, Jaden", ["100 FL SCY", "50 FR SCY", "100 FR SCY", "100 BK SCY"], "Fly"),
            # Note: Flanders' time on sheets is LCM
            Recruit("Flanders, George", ["100 FL SCY"], "Fly"),
            Recruit("Gold, Evan", ["100 FL SCY", "200 FL SCY"], "Fly"),
            Recruit("Kharun, Ilya", ["100 FL SCY", "200 FL SCY", "50 FR SCY"], "Fly"),
            ]

# save_data()

swimmers = pickle.load(open('swimmer_data.sav', 'rb'))

def see_recruits():
    for recruit in recruits:
        try:
            times = swimmers[recruit.name].times
            for event in recruit.events:
                if event not in times:
                    print(f"{event} not found for {recruit.name}")
                else:
                    count = len(times[event])
                    print(f"{count} entries for {event} for {recruit.name}")
        except KeyError:
            print(f"{recruit.name} not found.")

def z_to_letter(z):
    if z > 1.5:
        return "A+"
    elif z > 1:
        return "A"
    elif z > .5:
        return "A-"
    elif z > .25:
        return "B+"
    elif z > 0:
        return "B"
    elif z > -.25:
        return "B-"
    elif z > -.5:
        return "C+"
    elif z > -1:
        return "C"
    elif z > -1.5:
        return "C-"
    else:
        return "D"

kevin_ratings = {
    'Wang, Sonny': 9,
    'Duncan, Cade': 8,
    'Dalbey, Tristan': 9,
    'Wehbe, Greg': 7,
    'Pilkinton, Oliver': 6,
    'McFadden, Henry': 7,
    'Denbrok, Tristan': 7,
    'Craft, Sam': 4,
    'Dunlap, Willi': 6,
    'Peterson, Andy': 7,
    'Beehler, Matt': 6,
    'Hagar, Tommy': 6,
    'Schmitt, David': 7,
    'Baffico, Felipe': 8,
    'Pospishil, Jaden': 7,
    'Flanders, George': 6,
    'Dubovac, Petar': 8,
    'Gold, Evan': 8,
    'Kharun, Ilya': 9
}

def name_to_rec(name):
    for recruit in recruits:
        if recruit.name == name:
            return recruit

def get_rating():

    recruit_scores = dict()

    # Age drop off coefficient for weighting
    age_gamma = .5
    # Event drop off coefficient for weighting
    event_gamma = .5

    for recruit in recruits:
        event_imps = []
        for event in recruit.events:
            imps = []
            for age in range(16,12,-1):
                age1 = age
                age2 = age + 1
                imp = get_improvement_in_percentile(swimmers[recruit.name], (age1, age2), event)
                if imp is not None:
                    imps.append(imp)
            event_imps.append(imps)
        score = 0
        e_weight = 1
        for e in event_imps:
            single = 0
            age_weight = 1
            for a in e:
                single += a * age_weight
                age_weight *= age_gamma
            score += single * e_weight
            e_weight *= event_gamma
        
        recruit_scores[recruit.name] = score
    
    all_scores = [recruit_scores[k] for k in recruit_scores]
    xbar = statistics.mean(all_scores)
    stdev = statistics.stdev(all_scores)
    for rec in recruit_scores:
        recruit_scores[rec] = (recruit_scores[rec] - xbar) / stdev
    
    sorted_scores = dict(sorted(recruit_scores.items(), key=lambda item: item[1], reverse=True))
    for rec in sorted_scores:
        score = z_to_letter(sorted_scores[rec])
        kevin_score = kevin_ratings[rec]
        rec_type = name_to_rec(rec)
        print(f"{rec}: {score} ({kevin_score}), {rec_type.type}")


def get_derivative_rating():
    # Look at most recent time
    # Get list of top x (100?)
    # Get those kids' improvements in time
    # Get rank of improvement
    # Apply same transformation - get z score, etc.

    for recruit in recruits:
        for event in recruit.events:
            swimmer = swimmers[recruit.name]
            age = swimmer.get_oldest_age(event)
            # The following needs to be more of a get swimmer list
            # lst = get_time_list(event, age, top_if_same_class=100, age_in_2021=swimmer.age_in_2021)



get_rating()
