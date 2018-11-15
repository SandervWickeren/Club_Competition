import urllib.request
from bs4 import BeautifulSoup
import html
import json
import re
import time

### Season Info ###
seasonID = "F3C6D619-32F6-4C2A-8506-798D7493D668"
teamInfo = [[499, 23], [500, 22], [501, 44], [502, 43], [503, 42], [504, 74],
            [505, 73], [506, 89], [507, 135], [508, 153]]    
teamDict = {"Hillegom BC 1": [499, 23],
            "Hillegom BC 2": [500, 22],
            "Hillegom BC 3": [501, 44],
            "Hillegom BC 4": [502, 43],
            "Hillegom BC 5": [503, 42],
            "Hillegom BC 6": [504, 74],
            "Hillegom BC 7": [505, 73],
            "Hillegom BC 8": [506, 89],
            "Hillegom BC 9": [507, 135],
            "Hillegom BC 10": [508, 153]}   
#teamInfo = [[499, 23]]   
### Season Info ###
Requests = 0

def get_webpage(link):
    """ 
    Takes as input a weblink link and returns
    a BeautifulSoup object.
    """
    req = urllib.request.urlopen(link)
    bytes = req.read()

    string = bytes.decode('utf8')
    req.close()

    global Requests 
    Requests += 1
    return BeautifulSoup(string, 'html.parser')


def get_matches(soup):
    """
    Takes as input a BeautifulSoup object and Retrieves
    all matches found in the object in a dictionary.
    """

    # Get the rows containing the information
    rows = soup.table.findAll('tr')
    matches = []

    # For each row strip the important information.
    for row in rows[1:]:
        matches.append(strip_match_col(row))

    return {"matches": matches}

# Retrieves ranking from a soup.
def get_ranking(soup):
    """
    Takes as input a BeautifulSoup object and Retrieves
    the ranking found in the object in a dictionary.
    """

    # Find all rows that represent the ranking.
    rows = soup.find('table', {"class": "ruler"}).findAll('tr')
    division = " ".join(soup.findAll("div", {"class":"title"})[0].get_text().split()[:2])

    teamname = ""
    teamrank = ""
    ranking = []

    # Loop trough every row and strip the right information.
    for row in rows[1:]:
        r = strip_rank_col(row)
        ranking.append(r)

        if "hillegom" in r['team'].lower():
            teamname = prettify_teamname(r['team'])
            teamrank = r['rank']

    return {"division": division, "name": teamname, "table": ranking, 'teamrank': teamrank}


def strip_match_col(rows):
    """
    Takes as input a match row and Retrieves the information. Output
    is a dictionary which contains the information ordered.
    """

    time = rows.find('td', {"class":"plannedtime"}).get_text()
    home = lower_layout(rows.findAll('a', {"class":"teamname"})[0].get_text())
    away = lower_layout(rows.findAll('a', {"class":"teamname"})[1].get_text())
    
    # Retrieves location id
    location_link = rows.findAll('a')[2]['href']
    locID = 0
    
    # Because comments can screw up the format of the match row,
    # there are two possible situations.
    try:
        regexl = re.search("lid=[\d]+", str(location_link))
        locID = regexl.group().split("=")[-1]
    except:
        location_link = rows.findAll('a')[-2]['href']
        regexl = re.search("lid=[\d]+", str(location_link))
        locID = regexl.group().split("=")[-1]
    
    # Retrieves game id
    regex = re.search("match=[\d]+", str(rows))
    gameID = regex.group().split("=")[-1]

    # Tries to find a score, if there ain't any, keep it empty.
    try:
        score = rows.find('span', {"class":"score"}).get_text()
    except:
        score = ""

    return {"time": time, "home": home,"away": away,
            "score": score,"locationid": locID, "gameid":gameID}


def strip_rank_col(rows):
    """
    Takes as input a rank row and Retrieves the information. Output
    is a dictionary which contains the information ordered.
    """
    rank = rows.find('td', {"class":"standingsrank"}).get_text()
    team = lower_layout(rows.find('a').get_text())
    scores = rows.findAll('td', {"align":"center"})
    points = scores[0].get_text()
    played = scores[1].get_text()

    return {"rank": rank,"team": team,"points": points,"played": played}


def get_players(soup):
    """
    Takes soup of a player page as input and gives a list
    of surnames as output.
    (teamplayers.aspx)
    """
    players = soup.table.tr.findAll("tr")
    names = []

    for player in players:

        # Gets basic info for every person in a list
        info = player.get_text(" ").split(",")[-1].split(" ")[1:-1]
        
        # Discard player if not a regular player
        if info[-1] == "Ja":
            
            # Retrieve only the surname.
            name = info[0]
            names.append(name)

    return {"players": ", ".join(names)}


def get_games(json, team):
    """ 
    Takes as input json matches and teamname.
    Outputs all the home and away games from
    the given team.
    """
    result = []
    
    for dictionary in json['matches']:
        if team in dictionary["home"].lower() or team in dictionary["away"].lower():
            result.append(dictionary)
            
    return result


def get_last_game(json): 
    """
    Takes as input json matches. Outputs the information
    from the last game.
    """
    result = []
    
    for dictionary in get_games(json, "hillegom"):
        if dictionary["score"] != "":

            # Remove teamnumber
            dictionary["home"] = teamname_only(dictionary["home"])
            dictionary["away"] = teamname_only(dictionary["away"])

            result.append(dictionary)
    
    return result[-1]

def next_x_games(json, x):
    result = []
    
    for dictionary in json['matches']:
        if dictionary["score"] == "":

            # Remove teamnumber
            dictionary["home"] = teamname_only(dictionary["home"])
            dictionary["away"] = teamname_only(dictionary["away"])

            result.append(dictionary)
    
    return result[:x]


def get_next_game(json):
    """
    Takes as input json matches. Outputs the information
    from the next game.
    """
    result = []
    
    for dictionary in get_games(json, "hillegom"):
        if dictionary["score"] == "":

            # Remove teamnumber
            dictionary["home"] = teamname_only(dictionary["home"])
            dictionary["away"] = teamname_only(dictionary["away"])

            return dictionary


def get_game_info(soup):
    s = soup.find("table", {"class":"ruler matches"}).findAll("tbody")
    games = []
    
    for x in s[0]:
        
        # Ignore whitespaces
        if len(x) > 2:
            
            # Make temporary list of information
            temp = []
            
            # Get every game played in the match
            for y in x.findAll("td"):
                temp.append(y.get_text())
                
            # Process the temp list. Make diffence between double and single.
            if "D" in temp[0]:
                game = [temp[0]] + temp[2:4] + temp[-3:]
            else:
                game = [temp[0], temp[2]] + temp[-2:]
            
            # Calculate winner per match
            try:
                game.append(who_wins(temp[-1]))
            except:
                game.append("undecided")
            
            games.append(game)
    return games


def who_wins(points):
    """
    Takes as input a string containing sets. Outputs home if
    the left side wins and away if the right side wins.
    """
    games = points.split(" ")
    
    if int(games[-1].split("-")[0]) > int(games[-1].split("-")[1]):
        return "home"
    else:
        return "away"

def lower_layout(string):
    """
    Takes as input an uppercase string and returns a string with
    only the first letter in uppercase.

    EXAMPLE -> Example.
    """
    end = string[1:].lower()
    return string[0] + end

def teamname_only(string):
    """
    Takes as input a full teamname and returns only the
    base.

    Team BC 5 -> Team.
    """
    return string.split(" ")[0]

def prettify_teamname(string):
    """
    Team bc 7 -> Team BC 7.
    """
    spl = string.split(" ")
    return spl[0] + " " + spl[1].upper() + " " + spl[2]

   
def match(team):
    """
    Helper returns soup from given matchlink, calling
    the correct function.
    """
    link = craftLink("drawmatches", seasonID, "&draw=", team[1])
    soup = get_webpage(link)
    return get_matches(soup)

def rank(team):
    """
    Helper returns soup from given ranklink, calling
    the correct function.
    """
    link = craftLink("draw", seasonID, "&draw=", team[1])
    soup = get_webpage(link)
    return get_ranking(soup)

def players(team):
    """
    Helper returns soup from given playerlink, calling
    the correct function.
    """
    link = craftLink("teamplayers", seasonID, "&tid=", team[0])
    soup = get_webpage(link)
    return get_players(soup)

def game(gameid):
    """
    Takes as input a gameid, crafts a link and Retrieves
    information about the game in a list:
    [["MD", "player 1", "player 2", "enemy 1", "enemey 2", sets, winner]]
    """
    link = craftLink("teammatch", seasonID, "&match=", gameid)
    soup = get_webpage(link)
    return get_game_info(soup)

def craftLink(info, seasonID, compare, cid):
    """
    Takes as input the information, seasonid, compare text 
    and id. Outputs a correct structured link.

    """
    baseLink = "https://badmintonnederland.toernooi.nl/sport/"
    link = baseLink + info + ".aspx?id=" + seasonID + compare + str(cid)
    return link

def createFile(name, string):
    """
    Takes as input filename and a jsonstring,
    outputs the json into the filename.
    """
    with open(name, 'w', encoding='utf8') as jsonfile:
        json.dump(string, jsonfile, ensure_ascii=False, indent=4)


# Todo
# Make the functions modulair.

def init_data(team):
    """
    Crafts dictionary with all information for one specific team.
    A team has the form of [teamID, drawID].
    """
    # Online requests
    ranking = rank(team)
    matches = match(team)
    members = players(team)

    # Other calculations
    next_match = {"next":get_next_game(matches)}
    upcoming = {"upcoming":next_x_games(matches, 4)}
    previous_match = get_last_game(matches)
    previous_match["games"] = game(previous_match["gameid"])
    last_match = {"last": previous_match}

    combined_dict = {**ranking, **next_match, **last_match, **upcoming, **members}

    return combined_dict

# Todo:
#  Lookup every team
#  Automically move json file to github
#  Daily checks.
#  What if no internet connection?
#  Next match based on time, not on where score = ''
#  Scrape ID's and draw automatically.


def start(teamInfo):
    """
    Launches the program, and scrapes all information for the 
    given team in list teamInfo. It dumps the result into data.json.
    """
    start_time = time.clock()
    total = []

    for team in teamInfo:
        print("Busy with team: %s --" % team, round(time.clock() - start_time, 2), "seconds passed so far.")
        teamdata = init_data(team)
        total.append(teamdata)

    print("Dumping into json file..")
    data = ({"Teams": total})
    jstr = json.dumps(data, indent=4)
    createFile("data.json", data)

def information(query):
    result = []
    global teamDict

    for teamname, values in query.items():
        init = {}
        if 'match' in values:
            ranking = rank(teamDict[teamname])
            matches = match(teamDict[teamname])

            # Calculations based on matches
            next_match = {"next":get_next_game(matches)}
            upcoming = {"upcoming":next_x_games(matches, 4)}

            # Only new information is possible if there has been played
            # a new game.
            if 'game' in values:
                previous_match = get_last_game(matches)

                previous_match["games"] = game(previous_match["gameid"])
                last_match = {"last": previous_match}

                init = {**init, **ranking, **next_match, **last_match, ** upcoming}
            else:
                init = {**init, **ranking, **next_match, **upcoming}

        if 'name' in values:
            members = players(teamDict[teamname])

            init = {**init, **members}

        result.append(init)
    return result


# Timing information
# start_time = time.clock()
# start(teamInfo)
# print("Finished in", round(time.clock() - start_time, 2), "seconds")
# print("In", Requests, "Requests")