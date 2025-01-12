# Magic The Gathering Lookup Bot

A Discord bot that displays MTG card information including Oracle text, pictures, mana cost, and format legalities. I created this discord bot due to many of my friends playing Magic The Gathering regularly and introducing me to the game so I decided to apply some of my coding skills to help them with their games and so here we are.
Future I will try to add mana symbols instead of just having text.
Currently the bot is invite-only due to the cost of me hosting it 24/7 I wish more people could use it.
## Features

- Card image display
- Oracle text lookup
- Mana cost information
- Format legalities (Commander and Standard)
- Support for transform/double-faced cards
- Price information
## beta 5/13/24
- Calls API and shows text legalities and interactions

## fixing 8/11/24
- Made the image printing so they are together with pillow library and fused the images if there is a transformation ie(two-sided card)

## Commands (! commands have been removed for slash)

* `/card [card name]`
  * Displays card information including mana cost, oracle text, and price
  * Example: `!card Lightning Bolt`

* `/random`
  * Fetches a random MTG card from Scryfall
  * Example: `!random`

* `/roll [number of players]`
  * Rolls two d20 dice for each player and sorts results
  * Example: `!roll 4`

* `/help`
  * Displays all available commands and their usage
  * Example: `!help`

## Installation

1. Clone this repository
2. Create a `.env` file with your Discord bot token:
3. Use your guild id for testing the shared bot will the restrction removed

## Exmaple Bot Calls
![image](https://github.com/user-attachments/assets/bfd51caa-9790-4478-8f39-306dab1a9e9a)
![image](https://github.com/user-attachments/assets/6c4ec72f-9c80-4bcc-ad65-dd2bd12aab70)

