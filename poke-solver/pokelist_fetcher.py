import json, requests

def fetch():
    nameslist = []
    url = 'https://pokeapi.co/api/v2/pokemon/?offset=0&limit=807'
    response = requests.get(url)
    data = response.json()

    for pokemon in data['results']:
        nameslist.append(pokemon['name'])

    with open('nameslist.txt', 'w') as list_file:
        list_file.writelines("%s\n" % name for name in nameslist)
