## Figuring out which hash decodes into which type/category is literal hell, because you cant read the manifest itself.
## To find out what a hash means, you need to write code to decode it with its specific definition, which is a pain in my
## ass.

## Manifest definition breakdown:
## DestinyInventoryItemDefinition - definition for decoding items that slot into inventory buckets.
## DestinySandboxPerkDefinition - definition for getting a mod's displayProperties, e.g. description, name.
## DestinyStatDefinition - definition for getting the stat bonus a mod or perk gives.

## Manifest hash breakdown:
## 1 - weapon
## 20 - armour
## 610365472 - perk
## 1052191496 - weapon mod
## 4062965806 - armour mod

import discord
import json, urllib.parse, http.cookies
http.cookies._is_legal_key = lambda _: True
import requests as _requests
import manifest as _manifest
from fractions import Fraction

BASE_ROUTE = "https://www.bungie.net/Platform"
client = discord.Client()

class Requests:
    def __init__(self, api_token=None):
        self.api_token = api_token
        self.headers = {"X-API-Key": self.api_token}

    def get(self, request):
        self._requestData = _requests.get(urllib.parse.quote(request, safe=':/?&=,.'), headers=self.headers).json()
        if self._requestData.get("Response", False) == False:
            print(self._requestData)
        return self._requestData


class Manifest_Handler:
    def __init__(self):
        self.manifest = _manifest.Manifest("./", {})
    
    def get_weapon_perks(self, hash):
        weapon_data, perk_data_list = self.manifest._decode_hash(hash, "DestinyInventoryItemDefinition", "en"), []
        if weapon_data.get("sockets", False) == False: return None
        for weapon_socket_data in weapon_data["sockets"]["socketEntries"]:
            if weapon_socket_data["randomizedPlugItems"] == []: continue
            perk_data_list.append([])
            for random_socket_data in weapon_socket_data["randomizedPlugItems"]:
                perk_data = self.manifest._decode_hash(random_socket_data["plugItemHash"], "DestinyInventoryItemDefinition", "en")
                perk_data_list[-1].append(perk_data["displayProperties"]["name"])
        return perk_data_list
    
    def get_mod_desc(self, hash):
        mod_data =  self.manifest._decode_hash(hash, "DestinyInventoryItemDefinition", "en")
        mod_display_data = self.manifest._decode_hash(mod_data[0]["perkHash"], "DestinySandboxPerkDefinition", "en")["displayProperties"]["description"]
        return mod_display_data

class Variables:
    def __init__(self):
        pass

storage = Variables()

def refresh_database():
    storage.weapons, storage.perks, storage.mods, hash_category_conversion_table = {}, {}, {}, {}
    for manifest_entry in storage.m.manifest._query_all("DestinyInventoryItemDefinition", "en"):
        try:
            manifest_entry = json.loads(manifest_entry[0])
            
            ## Create conversion table between enum hashes and decoded values.
            for entry_hash in manifest_entry["itemCategoryHashes"]:
                if entry_hash not in hash_category_conversion_table.keys():
                    hash_category_conversion_table[entry_hash] = storage.m.manifest._decode_hash(entry_hash, "DestinyItemCategoryDefinition", "en")["displayProperties"]["name"]
            
            ## Check if weapon hash (1) or armour hash (20) is in the hash array. TL:DR checking if item is weap or armour
            if any(elim in [1, 20] for elim in manifest_entry["itemCategoryHashes"]):
                hashes = []
                for hash in manifest_entry["itemCategoryHashes"]:
                    hashes.append(hash_category_conversion_table[hash])
                storage.weapons[manifest_entry["displayProperties"]["name"].lower()] =  [manifest_entry["hash"], hashes]
                
            ## Check if perk hash (610365472) is in hash array, that weapon mod hash and armour mod hash (1052191496) are not.
            if 610365472 in manifest_entry["itemCategoryHashes"] and not any(elim in [1052191496, 4062965806] for elim in manifest_entry["itemCategoryHashes"]):
                stats = []
                for stat_entry in manifest_entry["investmentStats"]:
                    stats.append( storage.m.manifest._decode_hash(stat_entry["statTypeHash"], "DestinyStatDefinition", "en")["displayProperties"]["name"] + ": " + str(stat_entry["value"]))
                storage.perks[manifest_entry["displayProperties"]["name"].lower()] = [manifest_entry["hash"], stats]
                
            ## Check if weapon mod hash (1052191496) or armour mod hash (4062965806)
            if any(elim in [1052191496, 4062965806] for elim in manifest_entry["itemCategoryHashes"]):
                stats = []
                for stat_entry in manifest_entry["investmentStats"]:
                    stats.append( storage.m.manifest._decode_hash(stat_entry["statTypeHash"], "DestinyStatDefinition", "en")["displayProperties"]["name"] + ": " + str(stat_entry["value"]))
                storage.mods[manifest_entry["displayProperties"]["name"].lower()] = [manifest_entry["hash"], stats]
                
        except Exception as ex:
            pass

@client.event
async def on_ready():
    while True:
        try:
            storage.m = Manifest_Handler()
            refresh_database()
            break
        except KeyError as ex:
            pass

           
@client.event
async def on_message(message):
    if message.content.lower().startswith("!reload"):
        refresh_database()
        await client.send_message(message.channel, "Database Refreshed!")

    if message.content.lower().startswith("!roll"):
        chosen_weapon = message.content.lower()[6:]
        if storage.weapons.get(chosen_weapon, False) == False: return await client.send_message(message.channel, "Weapon not found. Perhaps you misspelt it or it is classified?")
        weapon_roll_data = storage.m.get_weapon_perks(storage.weapons[chosen_weapon][0])
        embed = discord.Embed(title="Rolls for " + message.content[6:].title())
        embed.set_footer(text="Made By TheTimebike#2349")
        for column in weapon_roll_data:
            column_data = "\n".join(column)
            embed.add_field(name="Perk Column", value=column_data)
        await client.send_message(message.channel, embed=embed)

    if message.content.lower().startswith("!perk"):
        chosen_perk = message.content.lower()[6:]
        if storage.perks.get(chosen_perk, False) == False: return await client.send_message(message.channel, "Perk not found. Perhaps you misspelt it or it is classified?")
        perk_roll_data = storage.m.self.manifest._decode_hash(storage.perks[chosen_perk][0], "DestinyInventoryItemDefinition", "en")
        embed = discord.Embed()
        embed.set_footer(text="Made By TheTimebike#2349")
        embed.add_field(name="Perk Description", value=perk_roll_data["displayProperties"]["description"] if perk_roll_data["displayProperties"]["description"] != "" else "Error")
        embed.set_author(name=message.content[6:].title(), icon_url="https://www.bungie.net" + perk_roll_data["displayProperties"]["icon"])
        joined_str = "\n".join(storage.perks[chosen_perk][1])
        if joined_str != "":
            embed.add_field(name="Perk Stats", value=joined_str)
        await client.send_message(message.channel, embed=embed) 

    if message.content.lower().startswith("!mod"):
        chosen_mod = message.content.lower()[5:]
        if storage.mods.get(chosen_mod, False) == False: return await client.send_message(message.channel, "Mod not found. Perhaps you misspelt it or it is classified?")
        mod_roll_data = storage.m.self.manifest._decode_hash(storage.mods[chosen_mod][0])
        mod_description = storage.m.get_mod_desc(storage.mods[chosen_mod][0],"DestinyInventoryItemDefinition", "en")
        embed = discord.Embed()
        embed.set_footer(text="Made By TheTimebike#2349")
        embed.add_field(name="Mod Description", value=mod_description)
        embed.set_author(name=message.content[5:].title(), icon_url="https://www.bungie.net" + mod_roll_data["displayProperties"]["icon"])
        joined_str = "\n".join(storage.mods[chosen_mod][1])
        if joined_str != "":
            embed.add_field(name="Mod Stats", value=joined_str)
        await client.send_message(message.channel, embed=embed) 
    
