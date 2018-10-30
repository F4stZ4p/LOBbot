import discord
import asyncio
import datetime
from aiohttp import ClientSession
from discord.ext import commands
import os, sys

class SpectateMotor:
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=self.bot.loop)
        self.map = None
        self.bots = []
        self.turns = 0
        self.latest = {}
        self.update_task = None

    async def interrupt_spectating(self):
        await self.map.delete()
        self.update_task.cancel()
        self.update_task = None

    async def do_restart(self, ctx, reason):
        counter = await ctx.send(f':warning: | **Initialized restart due to {reason}**')
        try:
            await self.interrupt_spectating()
            self.interrupt_variables()
        except:
            pass
        async for m in self.bot.get_channel(505815417269518346).history(limit=1000):
            try:
                if m.id != counter.id:
                    await m.delete()
            except:
                continue
        await asyncio.sleep(1)
        for count in range(5):
            await counter.edit(content=f':warning: | **Restarting in {abs(count - 5)}s**')
            await asyncio.sleep(1)

        await counter.delete()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def update_turns(self):
        self.turns += 1

    def interrupt_variables(self):
        self.bots = []
        self.turns = 0
        self.latest = {}

    async def updater(self, channel):
        await self.bot.wait_until_ready()
        self.map = await self.bot.get_channel(channel).send('Loading...')
        while not self.bot.is_closed():
            await asyncio.sleep(3)
            print(f'Getting map...\n----------')
            async with self.session.get("https://league.travitia.xyz/map") as r:
                map = await r.json()
            if map == self.latest:
                continue

            self.latest = map
            out = ""

            try:
                for row in map:
                    out = f"{out}\n{''.join(['█' if not i else i['name'][0] for i in row])}"
                print('Getting bots alive...\n----------')
                async with self.session.get("https://league.travitia.xyz/bots") as bots:
                    self.bots = self.bots = sorted((await bots.json()), key=lambda d: -d['hp'])
            except:
                print(f'Game end. Ended in {self.turns} Generations...\n----------')
                await self.map.edit(content=f"```fix\n---GAME ENDED---\n{map['text'].capitalize()}\nTotal Generations: {self.turns}\nThis Game Took: ~{datetime.timedelta(seconds=self.turns * 3)}```")
                return self.interrupt_variables()

            self.update_turns()
            hp = '\n'.join([f"{bot['name']}: {bot['hp']} HP" for bot in self.bots])
            await self.map.edit(content=f'```fix\n{out}\n\n{hp}\n\nGeneration {self.turns}```')

    @commands.command()
    async def spectate(self, ctx):
        """Spectate The Game in LIVE Mode"""
        _ = await ctx.send('Trying to connect... Check <#505815417269518346>')
        if self.update_task is None:
            self.update_task = self.bot.loop.create_task(self.updater(505815417269518346))
            await _.edit(content="🔴 **NOW LIVE!** Check <#505815417269518346>")
        else:
            await _.edit(content='Already spectating... Check <#505815417269518346>')

    @commands.command()
    async def stop(self, ctx):
        """Stop Spectating The Game"""
        if self.update_task is None:
            await ctx.send('Not spectating...')
        else:
            try:
                await self.interrupt_spectating()
                self.interrupt_variables()
            except:
                pass
            await ctx.send('Stopped spectating...')

    @commands.command(aliases=['newgame'])
    async def new(self, ctx):
        """Starts a New Game"""
        async with self.session.get("https://league.travitia.xyz/new") as req:
            req = await req.json()
            if req["status"] == "error":
                await ctx.send("Game already running... you can't start new...")
            else:
                await ctx.send("New game successfully created...")

    @commands.is_owner()
    @commands.command(hidden=True)
    async def restart(self, ctx, reason: str = "some reason"):
        """Restarts The Bot"""
        await self.do_restart(ctx, reason)

class Updater(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or("/"), description="A Bot Made for League of Bots")

    def run(self):
        self.add_cog(SpectateMotor(self))
        super().run(os.getenv("TOKEN"))

    async def on_ready(self):
        await self.wait_until_ready()
        await self.change_presence(status=discord.Status.dnd, activity=discord.Activity(type=discord.ActivityType.watching, name="epic Bot Battles"))
        print("Ready to serve League of Bots!")

if __name__ == "__main__":
    Updater().run()
