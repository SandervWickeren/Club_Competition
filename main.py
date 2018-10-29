#https://badmintonnederland.toernooi.nl/sport/draw.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73
#https://badmintonnederland.toernooi.nl/sport/drawmatches.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73

import urllib.request
from bs4 import BeautifulSoup
import html
import json

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
    location_link = rows.findAll('a')[-1]['href']

    try:
        score = rows.find('span', {"class":"score"}).get_text()
    except:
        score = ""

    return {"time": time, "home": home,"away": away, "score": score,"location": location_link}

def strip_rank_col(rows):
    rank = rows.find('td', {"class":"standingsrank"}).get_text()
    team = rows.find('a').get_text()
    scores = rows.findAll('td', {"align":"center"})
    points = scores[0].get_text()
    played = scores[1].get_text()

    return {"rank": rank,"team": team,"points": points,"played": played}
   

def match():
    link = "https://badmintonnederland.toernooi.nl/sport/drawmatches.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73"
    soup = get_webpage(link)
    return get_matches(soup)

def rank():
    link = "https://badmintonnederland.toernooi.nl/sport/draw.aspx?id=F3C6D619-32F6-4C2A-8506-798D7493D668&draw=73"
    soup = get_webpage(link)
    return get_ranking(soup)

def dumpjson():
    combined_dict = {**rank(), **match()}
    data = ({"Team 7": [combined_dict]})
    jstr = json.dumps(data, indent=4)
    print(jstr)

dumpjson()




