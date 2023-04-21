import disnake
from disnake.ext import commands

class OnReady(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Bot {self.bot.user} is ready to work!")
        await self.bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.watching, name='on Tickets'))

def setup(bot):
    bot.add_cog(OnReady(bot))
