import discord
client = discord.Client()
import json, urllib.parse, http.cookies
http.cookies._is_legal_key = lambda _: True
import requests as _requests
import manifest as _manifest
from fractions import Fraction

BASE_ROUTE = "https://www.bungie.net/Platform"

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
    
    def get_weapon_socket(self, hash):
        weapon_data = self.manifest._decode_hash(hash, "DestinyInventoryItemDefinition", "en")
        perk_data_list = []
        for weapon_socket_data in weapon_data["sockets"]["socketCategories"]:
            print(self.manifest._decode_hash(weapon_socket_data["socketCategoryHash"], "DestinySocketCategoryDefinition", "en"))

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
    
    def get_perk(self, hash):
        perk_data = self.manifest._decode_hash(hash, "DestinyInventoryItemDefinition", "en")
        return perk_data
    
    def get_mod_desc(self, hash):
        mod_data = self.get_perk(hash)
        for perk_hash in mod_data["perks"]:
            mod_display_data = self.manifest._decode_hash(perk_hash["perkHash"], "DestinySandboxPerkDefinition", "en")["displayProperties"]["description"]
        return mod_display_data

class Variables:
    def __init__(self):
        pass

storage = Variables()

def refresh_database():
    storage.weapons = {}
    storage.perks = {}
    storage.mods = {}
    hash_category_conversion_table = {}
    for x in storage.m.manifest._query_all("DestinyInventoryItemDefinition", "en"):
        try:
            x = json.loads(x[0])
            for y in x["itemCategoryHashes"]:
                if y not in hash_category_conversion_table.keys():
                    hash_category_conversion_table[y] = storage.m.manifest._decode_hash(y, "DestinyItemCategoryDefinition", "en")["displayProperties"]["name"]
            if 1 in x["itemCategoryHashes"] or 20 in x["itemCategoryHashes"]: ## weapons + armour
                hashes = []
                for hash in x["itemCategoryHashes"]:
                    hashes.append(hash_category_conversion_table[hash])
                storage.weapons[x["displayProperties"]["name"].lower()] =  [x["hash"], hashes]
            if 610365472 in x["itemCategoryHashes"] and 1052191496 not in x["itemCategoryHashes"]: ## perks
                stats = []
                for stat_entry in x["investmentStats"]:
                    stats.append( storage.m.manifest._decode_hash(stat_entry["statTypeHash"], "DestinyStatDefinition", "en")["displayProperties"]["name"] + ": " + str(stat_entry["value"]))
                storage.perks[x["displayProperties"]["name"].lower()] = [x["hash"], stats]
            if 1052191496 in x["itemCategoryHashes"] or 4062965806 in x["itemCategoryHashes"]: ## mods
                slot_item = "a weapon." if 1052191496 in x["itemCategoryHashes"] and 4062965806 not in x["itemCategoryHashes"] else "a piece of armour."
                stats = []
                for stat_entry in x["investmentStats"]:
                    stats.append( storage.m.manifest._decode_hash(stat_entry["statTypeHash"], "DestinyStatDefinition", "en")["displayProperties"]["name"] + ": " + str(stat_entry["value"]))
                storage.mods[x["displayProperties"]["name"].lower()] = [x["hash"], stats, slot_item]
        except Exception as ex:
            pass

@client.event
async def on_ready():
    storage.m = Manifest_Handler()
    refresh_database()


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
            zz = "\n".join(column)
            embed.add_field(name="Perk Column", value=zz)
        await client.send_message(message.channel, embed=embed)

    if message.content.lower().startswith("!perk"):
        chosen_perk = message.content.lower()[6:]
        if storage.perks.get(chosen_perk, False) == False: return await client.send_message(message.channel, "Perk not found. Perhaps you misspelt it or it is classified?")
        perk_roll_data = storage.m.get_perk(storage.perks[chosen_perk][0])
        embed = discord.Embed()
        embed.set_footer(text="Made By TheTimebike#2349")
        if perk_roll_data["displayProperties"]["description"] == "":
            print(perk_roll_data)
        embed.add_field(name="Perk Description", value=perk_roll_data["displayProperties"]["description"] if perk_roll_data["displayProperties"]["description"] != "" else "Error")
        embed.set_author(name=message.content[6:].title(), icon_url="https://www.bungie.net" + perk_roll_data["displayProperties"]["icon"])
        joined_str = "\n".join(storage.perks[chosen_perk][1])
        if joined_str != "":
            embed.add_field(name="Perk Stats", value=joined_str)
        await client.send_message(message.channel, embed=embed) 

    if message.content.lower().startswith("!mod"):
        chosen_mod = message.content.lower()[5:]
        if storage.mods.get(chosen_mod, False) == False: return await client.send_message(message.channel, "Mod not found. Perhaps you misspelt it or it is classified?")
        mod_roll_data = storage.m.get_perk(storage.mods[chosen_mod][0])
        mod_description = storage.m.get_mod_desc(storage.mods[chosen_mod][0])
        embed = discord.Embed()
        embed.set_footer(text="Made By TheTimebike#2349")
        embed.add_field(name="Mod Description", value=mod_description)
        embed.set_author(name=message.content[5:].title(), icon_url="https://www.bungie.net" + mod_roll_data["displayProperties"]["icon"])
        joined_str = "\n".join(storage.mods[chosen_mod][1])
        if joined_str != "":
            embed.add_field(name="Mod Stats", value=joined_str)
        await client.send_message(message.channel, embed=embed) 
    
