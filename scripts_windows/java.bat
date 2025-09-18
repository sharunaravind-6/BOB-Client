@echo off
REM %1 is the bot's filename, e.g., Bot.java
SET BOT_FILENAME=%1
SET BOT_CLASSNAME=%BOT_FILENAME:.java=%
SET JSON_JAR_PATH=..\libs\json.jar

REM Compile the Java file
javac -cp %JSON_JAR_PATH% %BOT_FILENAME%

REM Run the compiled class
java -cp .;%JSON_JAR_PATH% %BOT_CLASSNAME%