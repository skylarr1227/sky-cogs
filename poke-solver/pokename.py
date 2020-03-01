import pokelist_fetcher

def find_anagrams(name, pokemon_list):
    results = []
    new_name = ''
    remainings = ''
    for pokemon in pokemon_list:
        split_name = list(name.lower())
        pkm_name_length = len(pokemon)
        for poke_letter in pokemon:
            if poke_letter in split_name:
                new_name+=poke_letter
                split_name.remove(poke_letter)
        new_name+=' '
        if new_name[:pkm_name_length] == pokemon:
            remainings = ''.join(split_name)
            more_names, remainings = find_anagrams(remainings, pokemon_list)
            if not more_names:
                results.append(new_name+remainings)
            else:
                for item in more_names:
                    results.append(new_name+item)
        else:
            remainings = name
        new_name = ''        
    return results, remainings

def read_list(extra_items=[]):
    with open('nameslist.txt') as list_file:
        pokemon_file = list_file.readlines()
        for line in pokemon_file:
            pokemon = line[:-1]
            pokemon_names_list.append(pokemon)
        for item in extra_items:
            pokemon_names_list.append(item)

pokemon_names_list = []
try:
    read_list(['pokemon'])
except IOError:
    pokelist_fetcher.fetch()
    read_list(['pokemon'])

#pokemon_names_list = ['bulbasaur', 'pikachu', 'hypno']

name_string = input('Type the name you want to test: ')
print('testing...')

pokenames, leftover = find_anagrams(name_string, pokemon_names_list)

print('results:')
for pokename in pokenames:
    print(pokename)
