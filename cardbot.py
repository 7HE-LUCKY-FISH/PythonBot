import discord
from discord.ext import commands
import requests
from dotenv import load_dotenv
import os
# Replace 'YOUR_BOT_TOKEN' with your bot's tokenp
load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='card', help='Looks up a Magic: The Gathering card by name.')
async def card_lookup(ctx, *, card_name: str):
    # Replace spaces with '+' for the query string
    query = card_name.replace(' ', '+')
    url = f'https://api.scryfall.com/cards/named?fuzzy={query}'

    response = requests.get(url)
    if response.status_code == 200:
        card_data = response.json()
        card_layout = card_data.get('layout')
        embed = discord.Embed(color=0x00ff00)

        if card_layout in ['split', 'flip', 'transform', 'double_faced_token']:
            for face in card_data.get('card_faces', []):
                face_name = face.get('name')
                face_image = face.get('image_uris', {}).get('normal')
                face_mana_cost = face.get('mana_cost', 'N/A')
                face_type_line = face.get('type_line', 'N/A')
                face_oracle_text = face.get('oracle_text', 'N/A')

                embed.add_field(name=f'Name: {face_name}', value=f'Type: {face_type_line}\nMana Cost: {face_mana_cost}\nOracle Text: {face_oracle_text}', inline=False)
                embed.set_image(url=face_image)

        else:
            card_name = card_data.get('name')
            card_image = card_data.get('image_uris', {}).get('normal')
            card_mana_cost = card_data.get('mana_cost', 'N/A')
            card_type_line = card_data.get('type_line', 'N/A')
            card_oracle_text = card_data.get('oracle_text', 'N/A')

            embed.title = card_name
            embed.description = card_type_line
            embed.set_image(url=card_image)
            embed.add_field(name='Mana Cost', value=card_mana_cost, inline=False)
            embed.add_field(name='Oracle Text', value=card_oracle_text, inline=False)

        card_legalities = card_data.get('legalities', {}).get('standard', 'N/A')
        commander_legality = card_data.get('legalities', {}).get('commander', 'N/A')
        embed.add_field(name='Standard Legality', value=card_legalities.capitalize(), inline=False)
        embed.add_field(name='Commander Legality', value=commander_legality.capitalize(), inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f'Could not find card: {card_name}')

bot.run(TOKEN)
