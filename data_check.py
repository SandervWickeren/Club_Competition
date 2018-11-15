# Purpose of the file is to check if its required to refresh some information or not.
# This way we can save requests and thus bandwith.
import os
import glob
import json
import time
from main import *

# Check if there is a history file.
def check_history():
	filenames = glob.glob('history/*')

	if len(filenames) == 0:
		print("Initieer een nieuw bestand!")
		return False
	else:
		latest = max(filenames, key=os.path.getctime)
		return latest

def check_names(team):
	if team["players"] != "":
		return True
	return False

def check_matches(team, today):

	# Only check for rank and match if data is not
	# up to date.
	matchtime = team['upcoming'][0]['time'].split()[1]
	mtime = time.strptime(matchtime, "%d-%m-%Y")

	if today > mtime:
		return False
	return True

def check_last_club_match(team):

	# If the outdated data contains the club
	# hillegom, the game data has to be renewed also.
	if 'hillegom' in team['upcoming'][0]['away'].lower() or 'hillegom' in team['upcoming'][0]["home"].lower():
		return False
	return True

def updated_file(new_data, old_data):

	for team in new_data:
		if len(team) > 0:
			print(new_data.index(team))
			if 'table' in team:
				old_data['Teams'][new_data.index(team)]['table'] = team['table']
			if 'teamrank' in team:
				old_data['Teams'][new_data.index(team)]['teamrank'] = team['teamrank']
			if 'next' in team:
				old_data['Teams'][new_data.index(team)]['next'] = team['next']
			if 'last' in team:
				old_data['Teams'][new_data.index(team)]['last'] = team['last']
			if 'upcoming' in team:
				old_data['Teams'][new_data.index(team)]['upcoming'] = team['upcoming']
			if 'players' in team:
				old_data['Teams'][new_data.index(team)]['players'] = team['players']

	createFile(time.strftime("%d%m%Y") + ".json", old_data)



def check():
	today = time.localtime()
	history = check_history()
	query = {}

	if history != False:
		with open(history) as jsonfile:
			data = json.load(jsonfile)

		for team in data['Teams']:

			query[team['name']] = []

			if not check_names(team):
				query[team['name']].append("name")
			if not check_last_club_match(team):
				query[team['name']].append("game")
			if not check_matches(team, today):
				query[team['name']].append("match")


	# Ask main.py for information from the following lists
	#print(information(query))
		updated_file(information(query), data)

	# Open old json file again in memory

	# Replace old data with new gotten data

	# Save into file with current date.

	# Cleanup history such that there are three files left.

check()