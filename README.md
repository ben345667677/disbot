# Monster Bot

A Discord bot with AI chat, giveaways, tickets, verification, and more.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file (see `.env.example`):
   ```
   DISCORD_TOKEN=your_token_here
   OPENAI_API_KEY=your_key_here
   ```

3. Run the bot:
   ```bash
   python bot.py
   ```

   Or use the GUI launcher:
   ```bash
   python launcher.py
   ```

## Project Structure

```
├── bot.py              # Main bot entry point
├── launcher.py         # GUI launcher (CustomTkinter)
├── requirements.txt    # Python dependencies
├── cogs/               # Bot extensions
│   ├── ai_chat.py      # AI chat integration
│   ├── giveaway.py     # Giveaway system
│   ├── info.py         # Info commands
│   ├── oauth.py        # OAuth / user database
│   ├── security.py     # Security features
│   ├── tickets.py      # Ticket system
│   ├── verification.py # User verification
│   └── welcome.py      # Welcome messages
├── data/               # Runtime data (git-ignored)
│   └── users.db        # SQLite user database
└── scripts/            # Deployment scripts
    ├── setup.sh        # EC2 setup
    └── deploy.sh       # Deploy & restart
```

## Deployment

See `scripts/setup.sh` for first-time server setup and `scripts/deploy.sh` for deploying updates.
