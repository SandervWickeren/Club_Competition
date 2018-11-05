#https://badmintonnederland.toernooi.nl/sport/draw.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73
#https://badmintonnederland.toernooi.nl/sport/drawmatches.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73

import urllib.request
from bs4 import BeautifulSoup
import html
import json
import re
import time

# Turns weblink into beautifulsoup format.
def get_webpage(link):

    req = urllib.request.urlopen(link)
    bytes = req.read()

    string = bytes.decode('utf8')
    req.close()

    return BeautifulSoup(string, 'html.parser')

# Retrieves all matches from a soup.
def get_matches(soup):

    # Get the rows containing the information
    rows = soup.table.findAll('tr')

    matches = []
    for row in rows[1:]:
        matches.append(strip_match_col(row))

    return {"matches": matches}

# Retrieves ranking from a soup.
def get_ranking(soup):

    rows = soup.find('table', {"class": "ruler"}).findAll('tr')
    division = " ".join(soup.findAll("div", {"class":"title"})[0].get_text().split()[:2])


    ranking = []
    for row in rows[1:]:
        ranking.append(strip_rank_col(row))

    return {"division": division, "table": ranking}

# strips the match cols into a list of items.
def strip_match_col(rows):
    time = rows.find('td', {"class":"plannedtime"}).get_text()
    home = rows.findAll('a', {"class":"teamname"})[0].get_text()
    away = rows.findAll('a', {"class":"teamname"})[1].get_text()
    
    # Retrieves location id
    location_link = rows.findAll('a')[-1]['href']
    regexl = re.search("lid=[\d]+", str(location_link))
    locID = regexl.group().split("=")[-1]
    
    # Retrieves game id
    regex = re.search("match=[\d]+", str(rows))
    gameID = regex.group().split("=")[-1]

    try:
        score = rows.find('span', {"class":"score"}).get_text()
    except:
        score = ""

    return {"time": time, "home": home,"away": away, "score": score,"locationid": locID, "gameid":gameID}

def strip_rank_col(rows):
    rank = rows.find('td', {"class":"standingsrank"}).get_text()
    team = rows.find('a').get_text()
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
        info = player.get_text(" ").split(" ")[1:-1]
        
        # Discard player if not a regular player
        if info[-1] == "Ja":
            
            # Retrieve only the surname.
            name = list(reversed(info[0:-2]))[0]
            names.append(name)

    return ", ".join(names)

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
            result.append(dictionary)
    
    return result[-1]

def get_next_game(json):
    """
    Takes as input json matches. Outputs the information
    from the next game.
    """
    result = []
    
    for dictionary in get_games(json, "hillegom"):
        if dictionary["score"] == "":
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
                
            # Process the temp list
            if "D" in temp[0]:
                game = [temp[0]] + temp[2:4] + temp[-3:]
            else:
                game = [temp[0], temp[2]] + temp[-2:]
            
            # Calculate winner per match
            game.append(who_wins(temp[-1]))
            
            games.append(game)
    return games


def who_wins(points):
    games = points.split(" ")
    
    if int(games[-1].split("-")[0]) > int(games[-1].split("-")[1]):
        return "home"
    else:
        return "away"
   

def match():
    link = "https://badmintonnederland.toernooi.nl/sport/drawmatches.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73"
    soup = get_webpage(link)
    return get_matches(soup)

def rank():
    link = "https://badmintonnederland.toernooi.nl/sport/draw.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73"
    soup = get_webpage(link)
    return get_ranking(soup)

def players():
    link = "https://badmintonnederland.toernooi.nl/sport/teamplayers.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&tid=505"
    soup = get_webpage(link)
    return get_players(soup)

def game(gameid):
    """
    Takes as input a gameid, crafts a link and Retrieves
    information about the game in a list:
    [["MD", "player 1", "player 2", "enemy 1", "enemey 2", sets, winner]]
    """
    link = craftGameLink("teammatch", seasonID, gameid)
    soup = get_webpage(link)
    return get_game_info(soup)


def createFile(name, string):
    with open(name, 'w') as jsonfile:
        json.dump(string, jsonfile, ensure_ascii=False, indent=4)


def dumpjson():
    combined_dict = {**rank(), **match()}
    data = ({"Team 7": [combined_dict]})
    jstr = json.dumps(data, indent=4)
    createFile("data.json", data)
    print("Succes!")

def init_data():
    ranking = rank()
    matches = match()
    next_match = {"next":get_next_game(matches)}
    previous_match = get_last_game(matches)
    previous_match["games"] = game(previous_match["gameid"])
    last_match = {"last": previous_match}
    p = {"players": players()}

    combined_dict = {**rank(), **next_match, **last_match, **p}
    data = ({"Team 7": [combined_dict]})
    jstr = json.dumps(data, indent=4)
    createFile("data.json", data)
    return "Succes!"


#dumpjson()

# Todo:
#  Lowercase except first letter
#  Lookup every team
#  Automically move json file to github
#  Daily checks.
#  What if no internet connection?

# https://badmintonnederland.toernooi.nl/sport/teamplayers.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&tid=505
# https://badmintonnederland.toernooi.nl/sport/teamplayers.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&tid=504
# https://badmintonnederland.toernooi.nl/sport/teamplayers.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&tid=499
# https://badmintonnederland.toernooi.nl/sport/team.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&team=499

teamID = [505, 504, 499]
seasonID = "F3C6D619-32F6-4C2A-8506-798D7493D668"
baseLink = "https://badmintonnederland.toernooi.nl/sport/"

def craftTeamLink(info, seasonID, teamID):
    baseLink = "https://badmintonnederland.toernooi.nl/sport/"
    link = baseLink + info + ".aspx?id=" + seasonID + "&tid=" + str(teamID)
    return link

def craftGameLink(info, seasonID, gameID):
    baseLink = "https://badmintonnederland.toernooi.nl/sport/"
    link = baseLink + info + ".aspx?id=" + seasonID + "&match=" + str(gameID)
    return link

#print(game(4644))
#print(get_last_game(match())["gameid"])
start_time = time.clock()
print(init_data())
print(time.clock() - start_time, "seconds")


