import discord
from discord import app_commands
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from PIL import Image
from io import BytesIO

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
intents = discord.Intents.default()
intents.message_content = True
# Initialize bot
bot = commands.Bot(command_prefix='!', intents = intents, help_command=None)

# Rate limiting dictionary
rate_limits = {}

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    try:
        guild = discord.Object(id = GUILD_ID)

        await bot.tree.sync(guild = guild)
        print("Slash commands synced")
    
    except Exception as e:
        print(f"Error is on_ready: {e}")



@bot.tree.command(name="help", description="Lists all available commands")
@app_commands.guilds(discord.Object(id=GUILD_ID))  # Restrict the command to a specific guild use for only testing deploy will be global
async def help(interaction: discord.Interaction):
    # Check if the interaction is from the correct guild
    if interaction.guild.id != GUILD_ID:
        return await interaction.response.send_message("This command is not available in this server.", ephemeral=True)
    
    # Create the embed with command list
    embed = discord.Embed(
        title="Commands",
        description="List of commands",
        color=0x00ff00
    )
    # Iterate over all registered commands
    for command in bot.tree.get_commands():
        embed.add_field(
            name=f"/{command.name}",
            value=command.description or "No description available",
            inline=False
        )
    
    # Send the embed as a response to the interaction
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="roll", description="Rolls two d20 dice for each player.")
@app_commands.describe(player_count="Number of players")
@app_commands.guilds(discord.Object(id=GUILD_ID))
async def roll_command(interaction: discord.Interaction, player_count: int):
    if player_count < 1:
        await interaction.response.send_message("Please specify at least one player.", ephemeral=True)
        return
    import random

    rolls = []
    for i in range(1, player_count + 1):
        die1 = random.randint(1, 20)
        die2 = random.randint(1, 20)
        total = die1 + die2
        rolls.append((f"Player {i}", die1, die2, total))

    # Sort by total descending
    rolls.sort(key=lambda x: x[3], reverse=True)

    # Build the response
    results = []
    position = 1
    for player, d1, d2, total in rolls:
        results.append(f"{position}) {player}: {d1} + {d2} = {total}")
        position += 1
    
    embed = discord.Embed(
        title="Dice Roll Results",
        description="Here are the rolls from highest to lowest total:",
        color=0x00FF00
    )
    embed.add_field(
        name="Results",
        value="\n".join(results),
        inline=False
    )
    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    # Respond to the interaction
    await interaction.response.send_message(embed=embed)


async def create_card_embed(card_data, interaction):
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

    file = None
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

    embed.set_footer(text=f"Requested by {interaction.user.display_name}")
    return embed, None if 'image_uris' in card_data else file


@bot.tree.command(name="card", description="Looks up a Magic: The Gathering card by name.")
@app_commands.guilds(discord.Object(id=GUILD_ID))
@app_commands.describe(card_name="The name of the Magic: The Gathering card to look up.")
async def card_lookup(interaction: discord.interactions, card_name: str):
    user_id = interaction.user.id
    if user_id in rate_limits and datetime.now() < rate_limits[user_id]:
        remaining_time = (rate_limits[user_id] - datetime.now()).seconds
        await interaction.response.send_message(
            f"Please wait {remaining_time} seconds before making another request.", ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        query = card_name.replace(' ', '+')
        url = f'https://api.scryfall.com/cards/named?fuzzy={query}'
        
        response = requests.get(url)
        response.raise_for_status()
        card_data = response.json()

        embed, file = await create_card_embed(card_data, interaction)

        if file:
            await interaction.followup.send(embed=embed, file=file)
        else:
            await interaction.followup.send(embed=embed)

        # Set rate limit for the user
        rate_limits[user_id] = datetime.now() + timedelta(seconds=3)

    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"Error fetching card data: {str(e)}")
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {str(e)}")


@bot.tree.command(name="random", description="Gets a random MTG card from Scryfall.")
@app_commands.guilds(discord.Object(id=GUILD_ID))  # Restrict to specific guild
async def random_card(interaction: discord.Interaction):
    await interaction.response.defer()  # Defer response to show processing
    try:
        # Fetch a random card
        url = "https://api.scryfall.com/cards/random"
        response = requests.get(url)
        response.raise_for_status()
        card_data = response.json()


        embed, file = await create_card_embed(card_data, interaction)

        if file:
            await interaction.followup.send(embed=embed, file = file)
        else:
            await interaction.followup.send(embed=embed)

    except requests.exceptions.RequestException as e:
        await interaction.followup.send(f"Error fetching a random card: {str(e)}")
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {str(e)}")


# Error handling for app commands
@random_card.error
async def random_card_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"This command is on cooldown. Try again in {error.retry_after:.2f} seconds.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"An error occurred: {str(error)}",
            ephemeral=True,
        )


bot.run(TOKEN)
