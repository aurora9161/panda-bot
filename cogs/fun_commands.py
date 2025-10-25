import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
import logging
from utils.constants import TRIVIA_BANK, PANDA_NAMES

logger = logging.getLogger(__name__)

class FunCommands(commands.Cog):
    """Fun panda commands - trivia, names, polls, etc."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="pandatrivia", description="Answer a panda trivia question")
    async def pandatrivia_cmd(self, interaction: discord.Interaction):
        try:
            q = random.choice(TRIVIA_BANK)
            options_txt = "\n".join([f"{idx+1}. {opt}" for idx, opt in enumerate(q["options"])])
            embed = discord.Embed(title="🧠 Panda Trivia", description=q["q"], color=0xe74c3c)
            embed.add_field(name="Options", value=options_txt, inline=False)
            embed.set_footer(text="React 1/2/3/4 below to answer! You have 20 seconds.")
            await interaction.response.send_message(embed=embed)
            sent = await interaction.original_response()
            emoji_map = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            
            for i in range(len(q["options"])):
                try:
                    await sent.add_reaction(emoji_map[i])
                except Exception:
                    pass

            def check(reaction: discord.Reaction, user: discord.User | discord.Member):
                return (
                    reaction.message.id == sent.id
                    and str(reaction.emoji) in emoji_map[:len(q["options"])]
                    and user.id != self.bot.user.id
                )

            correct_index = q["answer"]
            try:
                while True:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=20.0, check=check)
                    chosen_index = emoji_map.index(str(reaction.emoji))
                    if chosen_index == correct_index:
                        await sent.reply(f"✅ {user.mention} got it right! Answer: **{q['options'][correct_index]}**\n*{q['explain']}*")
                        break
                    else:
                        continue
            except asyncio.TimeoutError:
                await sent.reply(f"⏰ Time's up! Correct answer was **{q['options'][correct_index]}**\n*{q['explain']}*")
        except Exception as e:
            logger.error(f"/pandatrivia error: {e}")
            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message("Unexpected error occurred.")
                else:
                    await interaction.followup.send("Unexpected error occurred.")
            except Exception:
                pass
    
    @app_commands.command(name="pandaname", description="Get a random cute panda name")
    async def pandaname_cmd(self, interaction: discord.Interaction):
        try:
            name = random.choice(PANDA_NAMES)
            await interaction.response.send_message(f"🍼 Your panda name is: **{name}**")
        except Exception as e:
            logger.error(f"/pandaname error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")
    
    @app_commands.command(name="pandamash", description="Mash up two panda names into one fun name")
    async def pandamash_cmd(self, interaction: discord.Interaction):
        try:
            a, b = random.sample(PANDA_NAMES, 2)
            mash = a[: len(a)//2] + b[len(b)//2 :]
            await interaction.response.send_message(f"🧪 Panda mash: **{mash}** (from {a} + {b})")
        except Exception as e:
            logger.error(f"/pandamash error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")
    
    @app_commands.command(name="pandapoll", description="Create a quick bamboo poll with thumbs reactions")
    @app_commands.describe(question="Poll question")
    async def pandapoll_cmd(self, interaction: discord.Interaction, question: str):
        try:
            embed = discord.Embed(title="🎋 Bamboo Poll", description=question, color=0x27ae60)
            await interaction.response.send_message(embed=embed)
            msg = await interaction.original_response()
            for emoji in ("👍", "👎"):
                try:
                    await msg.add_reaction(emoji)
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"/pandapoll error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")
    
    @app_commands.command(name="pandaping", description="Check bot latency the panda way")
    async def pandaping_cmd(self, interaction: discord.Interaction):
        try:
            ms = round(self.bot.latency * 1000)
            await interaction.response.send_message(f"🐾 Bamboo speed: **{ms} ms**")
        except Exception as e:
            logger.error(f"/pandaping error: {e}")
            await interaction.response.send_message("Unexpected error occurred.")

async def setup(bot):
    await bot.add_cog(FunCommands(bot))