# io
A flexible code-running bot, inspired by [lunarmagpie/io](https://github.com/lunarmagpie/io). Click [here](https://discord.com/api/oauth2/authorize?client_id=1073771658906701954&permissions=346176&scope=bot) to invite the bot.

## Usage
Use `io/run` or `io/asm` in the message to execute or compile code blocks. You can also use the menu command (right-click > apps > create instance) to create an instance from any message.

## Hosting
Copy `.env.example` to a new file called `.env`. Fill out the environment variables.
The bot can then be run with these commands:
```sh
poetry install
poetry run python -m bot
```

## Credits
Most of the credit goes to [lunarmagpie/io](https://github.com/lunarmagpie/io), as this bot was inspired and heavily based on it.
