import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from PIL import Image
from io import BytesIO

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

    # Format prices
    prices = card_data.get('prices', {})
    price_text = ""
    if prices.get('usd'):
        price_text += f"USD: ${prices['usd']}\n"
    if prices.get('usd_foil'):
        price_text += f"USD Foil: ${prices['usd_foil']}"

    # Handle double-sided cards
    if 'card_faces' in card_data and len(card_data['card_faces']) > 1:
        face1_url = card_data['card_faces'][0].get('image_uris', {}).get('normal')
        face2_url = card_data['card_faces'][1].get('image_uris', {}).get('normal')
        
        if face1_url and face2_url:
            # Create combined image
            face1_response = requests.get(face1_url)
            face2_response = requests.get(face2_url)
            
            img1 = Image.open(BytesIO(face1_response.content))
            img2 = Image.open(BytesIO(face2_response.content))
            
            total_width = img1.width + img2.width
            max_height = max(img1.height, img2.height)
            combined_img = Image.new('RGB', (total_width, max_height))
            
            combined_img.paste(img1, (0, 0))
            combined_img.paste(img2, (img1.width, 0))
            
            combined_bytes = BytesIO()
            combined_img.save(combined_bytes, format='PNG')
            combined_bytes.seek(0)
            
            file = discord.File(combined_bytes, filename="card.png")
            embed.set_image(url="attachment://card.png")

            # Front face information
            face1 = card_data['card_faces'][0]
            front_text = f"**Front Face - {face1.get('name')}**\n"
            if 'mana_cost' in face1:
                front_text += f"Mana Cost: {face1['mana_cost']}\n"
            if 'type_line' in face1:
                front_text += f"Type: {face1['type_line']}\n"
            if 'oracle_text' in face1:
                front_text += f"Oracle Text: {face1['oracle_text']}\n"
            
            embed.add_field(name="Front Side", value=front_text, inline=False)

            # Back face information
            face2 = card_data['card_faces'][1]
            back_text = f"**Back Face - {face2.get('name')}**\n"
            if 'type_line' in face2:
                back_text += f"Type: {face2['type_line']}\n"
            if 'oracle_text' in face2:
                back_text += f"Oracle Text: {face2['oracle_text']}\n"
            
            embed.add_field(name="Back Side", value=back_text, inline=False)

    else:
        # Single-sided card
        if 'image_uris' in card_data:
            embed.set_image(url=card_data['image_uris'].get('normal'))
        
        card_text = ""
        if 'mana_cost' in card_data:
            card_text += f"Mana Cost: {card_data['mana_cost']}\n"
        if 'type_line' in card_data:
            card_text += f"Type: {card_data['type_line']}\n"
        if 'oracle_text' in card_data:
            card_text += f"Oracle Text: {card_data['oracle_text']}\n"
        
        embed.add_field(name="Card Information", value=card_text, inline=False)

    # Add prices
    if price_text:
        embed.add_field(name="Prices", value=price_text, inline=False)

    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
    return embed, None if 'image_uris' in card_data else file

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

        embed, file = await create_card_embed(card_data, ctx)
        
        try:
            await loading_message.delete()
        except NotFound:
            # Ignore if loading message was already deleted
            pass
        
        if file:
            await ctx.send(embed=embed, file=file)
        else:
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
