# 🐼 Panda Bot - Cogs Structure

A Discord bot focused on pandas with adoption system, economy, and daily content!

## 📦 Project Structure

```
panda-bot/
├── main.py              # Main bot file with cog loading
├── bot.py               # Legacy single-file version (backup)
├── requirements.txt     # Python dependencies
├── config.json          # Bot configuration (auto-generated)
├── adoption_data.json   # Adoption system data (auto-generated)
├── utils/               # Shared utilities
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── constants.py     # Constants and static data
│   ├── http_client.py   # HTTP client for API calls
│   ├── adoption_helpers.py  # Adoption system helpers
│   └── panda_api.py     # Panda API wrapper
└── cogs/                # Command modules (cogs)
    ├── __init__.py
    ├── core_commands.py     # Basic panda commands
    ├── adoption_system.py   # Adoption functionality
    ├── economy_commands.py  # Economy system
    ├── fun_commands.py      # Fun commands & games
    ├── utility_commands.py  # Utility commands
    ├── admin_commands.py    # Admin-only commands
    ├── owner_commands.py    # Owner-only commands
    └── daily_tasks.py       # Automated daily tasks
```

## 🚀 Getting Started

### 1. Setup

```bash
# Clone the repository
git clone https://github.com/aurora9161/panda-bot.git
cd panda-bot

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Edit `main.py` and set your bot token:

```python
BOT_TOKEN = "your_bot_token_here"
BOT_OWNER_ID = your_discord_user_id  # Optional
```

Or use environment variables:
```bash
export DISCORD_TOKEN="your_bot_token_here"
```

### 3. Run the Bot

```bash
# Run with the new cogs structure
python main.py

# Or run the legacy single file (backup)
python bot.py
```

## 📝 Commands Overview

### 📦 Core Commands
- `/panda` - Get a random panda image
- `/pandafact` - Get a panda fact
- `/pandagif` - Get a panda GIF
- `/pandaall` - Image + fact combo
- `/pandaquote` - Inspirational quote
- `/pandajoke` - Random joke
- `/pandacombo` - Image + fact + joke

### 🏠 Adoption System
- `/adoptlist` - View available pandas
- `/adopt <panda_id>` - Adopt a panda
- `/mypandas` - View your adopted pandas
- `/feed <panda_id>` - Feed your panda
- `/play <panda_id>` - Play with your panda

### 💰 Economy
- `/balance` - Check bamboo coin balance
- `/work` - Earn coins by working
- `/daily` - Claim daily bonus

### 🎉 Fun & Games
- `/pandatrivia` - Answer trivia questions
- `/pandaname` - Get a random panda name
- `/pandamash` - Mash panda names together
- `/pandapoll <question>` - Create a poll
- `/pandaping` - Check bot latency

### 🔧 Utility
- `/say <message>` - Make the bot say something
- `/qr <text>` - Generate QR code
- `/pandahelp` - Show all commands

### 🔧 Admin Commands (Administrator Permission)
- `/pandaconfig` - Configure daily pandas
- `/pandastatus` - Check bot status
- `/pandatest` - Send test daily panda

### 👑 Owner Commands (Bot Owner Only)
- `/pandaownerreload` - Reload slash commands
- `/pandaownerset` - Owner configuration
- `/pandaownerstatus` - Detailed status

## ⚙️ Features

### 🐼 Panda Content
- Random panda images and GIFs
- Panda facts from API
- Trivia questions about pandas
- Daily automated panda posts

### 🏠 Adoption System
- Adopt virtual pandas with bamboo coins
- Feed and play with your pandas
- Happiness tracking system
- Cooldown mechanics for realistic care

### 💰 Economy System
- Bamboo coins currency
- Work commands to earn money
- Daily bonuses
- Adoption fees and rewards

### 🔄 Daily Automation
- Configurable daily panda posts
- Admin-controlled scheduling
- UTC time support

## 🐛 Development

### Adding New Commands

1. Choose the appropriate cog file or create a new one
2. Add your command using the `@app_commands.command` decorator
3. Follow the existing pattern for error handling and logging
4. Test your command

### Cog Structure

Each cog follows this pattern:

```python
import discord
from discord.ext import commands
from discord import app_commands

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="mycommand", description="My command")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.send_message("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

## 📜 Migration Notes

The bot has been refactored from a single `bot.py` file into a modular cogs structure:

- **All slash commands preserved** - No functionality lost
- **Improved organization** - Commands grouped by functionality
- **Better maintainability** - Easier to add/modify features
- **Shared utilities** - Common functions moved to utils/
- **Backward compatibility** - Original bot.py kept as backup

## 🚀 Hosting

When hosting, make sure to:

1. Use `main.py` as your entry point
2. Set the `DISCORD_TOKEN` environment variable
3. Ensure all dependencies are installed
4. The bot will create `config.json` and `adoption_data.json` automatically

## 🎆 Credits

Made with ❤️ by aurora

- Uses discord.py for Discord integration
- Panda images from Some Random API
- QR code generation with qrcode library
