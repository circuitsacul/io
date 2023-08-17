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
- [@Lunarmagpie](https://github.com/lunarmagpie) for creating the [original io](https://github.com/lunarmagpie/io), which this project was based on
- [@Enderchief](https://github.com/Enderchief) for hosting a [piston fork](https://github.com/Endercheif/piston) with additional languages
- [Compiler Explorer](https://github.com/compiler-explorer/compiler-explorer) and [piston](https://github.com/engineer-man/piston) for creating free-to-use code execution tools
- [@trag1c](https://github.com/trag1c) for coming up with the name
