import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

# Rate limiting dictionary
rate_limits = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

async def create_card_embed(card_data, ctx):
    embed = discord.Embed(
        title=card_data.get('name'),
        url=card_data.get('scryfall_uri'),
        color=0x00ff00,
        timestamp=datetime.now(timezone.utc)
    )

    card_layout = card_data.get('layout')
    
    # Handle double-faced cards
    if card_layout in ['transform', 'modal_dfc', 'double_faced_token']:
        card_faces = card_data.get('card_faces', [])
        if len(card_faces) >= 2:
            # Front face
            front_face = card_faces[0]
            embed.add_field(
                name=f"Front Face - {front_face.get('name')}",
                value=f"**Mana Cost:** {front_face.get('mana_cost', 'N/A')}\n"
                      f"**Type:** {front_face.get('type_line', 'N/A')}\n"
                      f"**Oracle Text:** {front_face.get('oracle_text', 'N/A')}",
                inline=False
            )
            embed.set_thumbnail(url=front_face.get('image_uris', {}).get('normal'))

            # Back face
            back_face = card_faces[1]
            embed.add_field(
                name=f"Back Face - {back_face.get('name')}",
                value=f"**Type:** {back_face.get('type_line', 'N/A')}\n"
                      f"**Oracle Text:** {back_face.get('oracle_text', 'N/A')}",
                inline=False
            )
            embed.set_image(url=back_face.get('image_uris', {}).get('normal'))
    else:
        # Regular single-faced card
        embed.add_field(
            name="Card Details",
            value=f"**Mana Cost:** {card_data.get('mana_cost', 'N/A')}\n"
                  f"**Type:** {card_data.get('type_line', 'N/A')}\n"
                  f"**Oracle Text:** {card_data.get('oracle_text', 'N/A')}",
            inline=False
        )
        embed.set_image(url=card_data.get('image_uris', {}).get('normal'))

    # Add price information
    prices = card_data.get('prices', {})
    if prices:
        price_text = f"USD: ${prices.get('usd', 'N/A')}\n"
        price_text += f"USD Foil: ${prices.get('usd_foil', 'N/A')}"
        embed.add_field(name="Prices", value=price_text, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.name}")
    return embed

@bot.command(name='card', help='Looks up a Magic: The Gathering card by name.')
@commands.cooldown(1, 3, commands.BucketType.user)
async def card_lookup(ctx, *, card_name: str):
    user_id = ctx.author.id
    if user_id in rate_limits:
        if datetime.now() < rate_limits[user_id]:
            remaining_time = (rate_limits[user_id] - datetime.now()).seconds
            await ctx.send(f"Please wait {remaining_time} seconds before making another request.")
            return

    loading_message = await ctx.send("Searching for card...")

    try:
        query = card_name.replace(' ', '+')
        url = f'https://api.scryfall.com/cards/named?fuzzy={query}'
        
        response = requests.get(url)
        response.raise_for_status()
        
        card_data = response.json()
        from discord.errors import NotFound

        embed = await create_card_embed(card_data, ctx)
        
        try:
            await loading_message.delete()
        except NotFound:
            # Ignore if loading message was already deleted
            pass
        
        await ctx.send(embed=embed)
        
        rate_limits[user_id] = datetime.now() + timedelta(seconds=3)

    except requests.exceptions.RequestException as e:
        try:
            await loading_message.delete()
        except NotFound:
            pass
        await ctx.send(f"Error fetching card data: {str(e)}")
    except Exception as e:
        try:
            await loading_message.delete()
        except NotFound:
            pass
        await ctx.send(f"An unexpected error occurred: {str(e)}")

@card_lookup.error
async def card_lookup_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

bot.run(TOKEN)
