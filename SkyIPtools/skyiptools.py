import requests
import discord
#from discord.ext import commands
import socket
import json
import re
from redbot.core.config import Config
from redbot.core import commands, checks
from .config import lapi_key




def lookup_ip(ip_address):
	response = requests.get(f'https://api.ipdata.co/{ip_address}?api-key={lapi_key}')
	response_json = json.loads(response.text)
	return f'''
```
IP: {str(response_json['ip'])}
IP LOCATION INFO
City: {str(response_json['city'])}
Region: {str(response_json['region'])}
Region code: {str(response_json['region_code'])}
Country: {str(response_json['country_name'])}
Country code: {str(response_json['country_code'])}
Flag: {str(response_json['emoji_flag'])}
Continent: {str(response_json['continent_name'])}
Continent code: {str(response_json['continent_code'])}
Postal code: {str(response_json['postal'])}
Latitude: {str(response_json['latitude'])}
Longitude: {str(response_json['longitude'])}
Calling code: {str(response_json['calling_code'])}
Time zone: {str(response_json['time_zone']['name'])}
Time zone current time: {str(response_json['time_zone']['current_time'])}
Currency: {str(response_json['currency']['name'])}
Currency code: {str(response_json['currency']['code'])}
Currency symbol: {str(response_json['currency']['symbol'])}
Language: {str(response_json['languages'][0]['name'])}
Native language: {str(response_json['languages'][0]['native'])}
BASIC INFO
asn: {str(response_json['asn']['asn'])}
Name: {str(response_json['asn']['name'])}
Domain: {str(response_json['asn']['domain'])}
Route: {str(response_json['asn']['route'])}
Type: {str(response_json['asn']['type'])}
EXTRA INFO
TOR: {str(response_json['threat']['is_tor'])}
Proxy: {str(response_json['threat']['is_proxy'])}
Anonymous: {str(response_json['threat']['is_anonymous'])}
Abuser: {str(response_json['threat']['is_known_abuser'])}
Threat: {str(response_json['threat']['is_threat'])}
Bogon: {str(response_json['threat']['is_bogon'])}```'''

class SkyIP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



    @commands.command(name='pong')
    async def ponger(ctx):
        """Sends bot's pong"""
        await ctx.send(f'It took roughly {round(bot.latency * 1000)}ms for this pong to reach the server-satisfied?')



    @commands.command(name='geo', aliases=['ip'])
    async def geo(ctx, *, ip):
        """looks up an ip address"""
        try:
            ip_address = socket.gethostbyname(ip)
            await ctx.send(lookup_ip(ip_address))
        except socket.gaierror:
            await ctx.send('Hey dipshit, there is no ip or domain matching your input')
        except:
            await ctx.send('Oh fuck... error has occured!')
            print('Error has occured!')