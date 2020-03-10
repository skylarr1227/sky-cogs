import discord
from redbot.core import commands, checks
from redbot.core.config import Config
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

class SkyImgInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def skyinfo(ctx, user: discord.Member):
        img = Image.open('/root/.local/share/Red-DiscordBot/cogs/CogManager/cogs/skyimginfo/infoimgimg.png') 
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("/root/.local/share/Red-DiscordBot/cogs/CogManager/cogs/skyimginfo/Modern_Sans_Light.otf", 100)
        fontbig = ImageFont.truetype("/root/.local/share/Red-DiscordBot/cogs/CogManager/cogs/skyimginfo/Fitamint Script.ttf", 400)
        #    (x,y)::↓ ↓ ↓ (text)::↓ ↓     (r,g,b)::↓ ↓ ↓
        draw.text((200, 0), "Information:", (255, 255, 255), font=fontbig) 
        draw.text((50, 500), "Username: {}".format(user.display_name), (255, 255, 255), font=font)
        draw.text((50, 700), "ID:  {}".format(user.id), (255, 255, 255), font=font) 
        draw.text((50, 900), "User Status:{}".format(user.status), (255, 255, 255), font=font)
        draw.text((50, 1100), "Account created: {}".format(user.created_at), (255, 255, 255), font=font) 
        draw.text((50, 1300), "Nickname:{}".format(user.display_name), (255, 255, 255), font=font) 
        draw.text((50, 1500), "Users' Top Role:{}".format(user.top_role), (255, 255, 255), font=font) 
        draw.text((50, 1700), "User Joined:{}".format(user.joined_at), (255, 255, 255), font=font)
        img.save('infoimg2.png')
        await ctx.upload("infoimg2.png")
    
    

    
 
