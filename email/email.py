from redbot.core import commands
from email.message import EmailMessage

class Email(commands.Cog):

    @commands.command()
    async def newrequest(self, ctx, *, body):
        user = ctx.message.author.id
        message = EmailMessage()
        message["From"] = "admin@skys.fun"
        message["To"] = "support@mewbot.zohodesk.com"
        message["Subject"] = "f{user} created a request"
        message.set_content(f"{body}/n{user}")

        await aiosmtplib.send(message, hostname="a2plcpnl0218.prod.iad2.secureserver.net", port=465, username="admin@skys.fun", password="liger666", use_tls=True)
        await ctx.send("New request created.")

