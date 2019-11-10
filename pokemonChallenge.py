# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import codecs
import sys
import urllib2
import random

__author__ = "Sergi Vila Almenara"

class Pokemon:
	"""
	Structure to store the information of a Pokemon
	"""
	def __init__(self, number, name, types, href, image):
		self.number = int(number)
		self.name = name
		self.types = sorted(types)
		self.href = href
		self.image = image
		self.numTypes = len(self.types)

def readPokemon(row):
	"""
	Returns a Pokemon object from an HTML table row
	"""
	data = row.contents
	number = data[1].find(attrs={"class": "infocard-cell-data"}).get_text()
	href = data[3].find(attrs={"class": "ent-name"}).get("href")
	name = data[3].find(attrs={"class": "ent-name"}).get_text()
	image = data[1].find(attrs={"class": "img-fixed"}).get("data-src")
	types = []
	for typeData in data[4].find_all(attrs={"class": "type-icon"}):
		types.append(typeData.get_text())
	return Pokemon(number, name, types, href, image)

def getPokemonMaps(soup):
	"""
	Reads all the full pokemon list from an HTML table,
	stores all the pokemon that have two types in the pokemonMap,
	and also generates another map, typesMap, classifying the pokemon by both types

	Returns the pokemonMap and the typesMap
	"""
	table = soup.find('table', attrs={'id':'pokedex'})
	table_body = table.find('tbody')
	rows = table_body.find_all('tr')
	pokemonMap = {}
	typesMap = {}
	for row in rows:
		pok = readPokemon(row)
		if pok.numTypes is 2:
			pokemonMap[pok.name] = pok
			typesString = pok.types[0]+"-"+pok.types[1]
			if typesString not in typesMap:
				typesMap[typesString] = []
			typesMap[typesString].append(pok)

	return pokemonMap, typesMap

def getPage(url):
	"""
	Returns the HTML code from an URL
	"""
	hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
	req = urllib2.Request(url, headers=hdr)
	try:
		return urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		print e.fp.read()

def removeUsedTypes(usedTypes, currentTypesMap):
	"""
	Seach in currentTypesMap each type in usedTypes,
	and if one of the types is found, the key is deleted
	from the map
	"""
	for typ in usedTypes:
		for key in currentTypesMap.keys():
			keyValues = key.split("-")
			for keyValue in keyValues:
				if typ == keyValue:
					del currentTypesMap[key]

def getExcluentPairOfTypes(typesMap):
	"""
	Generate a list with all the compatible pair of types using typesMap
	Every time one pair of type is selected, then, the pair of types that
	are used in this pair are deleted from the map to avoid repetition.
	This process is done until no more elements are available.
	This method guarantee two pokemon have not shared types
	If the list contains less than 6 elements, it is discarted and a new
	is generated, until this condition is reached because we need 6 pair
	of types
	"""
	currentTypesMap = typesMap.copy()
	selectedPairs = []
	isCorrect = False

	while not isCorrect and bool(currentTypesMap):
		currentPairOfTypes = random.choice(currentTypesMap.keys())
		selectedPairs.append(currentPairOfTypes)
		removeUsedTypes(currentPairOfTypes.split("-"), currentTypesMap)

		if not bool(currentTypesMap):
			if len(selectedPairs) < 6:
				currentTypesMap = typesMap.copy()
				selectedPairs = []
			else:
				isCorrect = True
	
	return selectedPairs

def chosePokemons(selectedPairs, pokemonMap, typesMap):
	"""
	From pair of types list, 6 elements (pair of types) are chosen
	Then, one pokemon of each value list from typesMap is selected
	And removed from selectedPairs to avoid repetition
	Finally, the team with 6 pokemon is returned
	"""
	team = []
	for i in xrange(6):
		currentTypes = random.choice(selectedPairs)
		team.append(random.choice(typesMap[currentTypes]))
		selectedPairs.remove(currentTypes)
	return team

def allPokemonAreDifferent(team):
	"""
	Check if all pokemon have a different number
	"""
	pokeset = set()
	for pokemon in team:
		pokeset.add(pokemon.number)
	return len(pokeset) == 6

def areRelated(team):
	"""
	Checks if the pokemon of the team have an evolution relation
	First, it is obtained a set with all the related pokemon and then,
	the pokemon of the team are searched on this set.
	If a pokemon is found, the team is not valid
	"""
	root = "https://pokemondb.net"
	relatedPokemons = set()
	for pokemon in team:
		web = root + pokemon.href
		pokeweb = BeautifulSoup(getPage(web), 'html.parser')
		evolist = pokeweb.find('div', attrs={'class':'infocard-list-evo'})
		if evolist is None:
			continue
		infocards = evolist.find_all('span', attrs={'class': 'infocard-lg-data'})
		for card in infocards:
			number = int(card.find('small').get_text()[1:])
			if number != pokemon.number:
				relatedPokemons.add(number)
	
	for pokemon in team:
		if pokemon.number in relatedPokemons:
			return True
	return False


def getTeam(pokemonMap, typesMap):
	"""
	Returns the final team from the map of pokemon and types
	A new team will be generated until it reaches the condition
	that all pokemons are different and they are not related
	by evolution
	"""
	selectedPairs = getExcluentPairOfTypes(typesMap)
	team = chosePokemons(selectedPairs, pokemonMap, typesMap)
	while(not allPokemonAreDifferent(team) or areRelated(team)):
		team = chosePokemons(selectedPairs, pokemonMap, typesMap)
	return team

def generateHTML(team):
	"""
	Creates an html document called "team.html" that shows the team generated
	"""
	output = open("team.html", "w")
	output.write("<!DOCTYPE html> \
	<html> \
	<head> \
	<title>Pokemon team</title> \
	<link rel=\"preconnect\" href=\"https://fonts.gstatic.com\"> \
<link rel=\"preconnect\" href=\"https://img.pokemondb.net\"> \
<link rel=\"stylesheet\" href=\"https://pokemondb.net/static/css/pokemondb-e614e67e0f.css\"> \
	<style> \
table { \
  font-family: arial, sans-serif; \
  border-collapse: collapse; \
  width: auto; \
} \
\
td, th { \
  border: 1px solid #dddddd; \
  text-align: left; \
  padding: 8px; \
  align: center; \
  text-align: center; \
} \
\
</style> \
	</head> \
	<body> \
\
	<h2 align=\"center\">Pokemon team</h2> \
\
	<table align=\"center\" bgcolor = \"#FFFFFF\"> \
	  <tr> \
	    <th>#</th> \
	    <th>Name</th> \
	    <th>Types</th> \
	  </tr>")
	for pokemon in team:
		output.write("<tr>\n");
		output.write('<td><img src="' + pokemon.image + '" height=30 width=40></img>' + str(pokemon.number).zfill(3)+'</td>\n')
		output.write("<td class=\"cell-name\">\n<a class=\"ent-name\" href=\"https://pokemondb.net"+ pokemon.href + '">' + pokemon.name + "</td>\n")
		output.write("<td>");
		output.write('<a class="type-icon type-' + pokemon.types[0].lower() + '" href="https://pokemondb.net/type/' + pokemon.types[0].lower() + '">' + pokemon.types[0] + '</a>\n')
		output.write("<br>\n");
		output.write('<a class="type-icon type-' + pokemon.types[1].lower() + '" href="https://pokemondb.net/type/' + pokemon.types[1].lower() + '">' + pokemon.types[1] + '</a>\n')
		output.write("</td>\n</tr>\n");
	output.write("</table> \
\
	</body>")
	output.close()

if __name__ == "__main__":
	"""
	Main function to solve the challenge
	"""
	reload(sys)
	sys.setdefaultencoding('utf-8') # Necessary to work with unicode
	soup = BeautifulSoup(getPage("https://pokemondb.net/pokedex/all"), 'html.parser')
	pokemonMap, typesMap = getPokemonMaps(soup)
	team = getTeam(pokemonMap, typesMap)
	generateHTML(team)
