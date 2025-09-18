@echo off
REM %1 is the bot's filename, e.g., bot.c
SET BOT_FILENAME=%1

REM Compile the C file, linking Jansson
gcc -std=c11 %BOT_FILENAME% -o bot -ljansson

REM Run the compiled bot
bot.exe