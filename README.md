This is a simple launcher program. That allows you to drop a built executable into a folder with a simple config.json file to target your game files. To create a Steam like experience of selecting from multiple options.

<img width="492" height="400" alt="image" src="https://github.com/user-attachments/assets/b2d6a3d8-046b-43cc-a694-610962a890c4" />

#### Config.json
Here is the example of the config.json from the image above.

    {
      "game_name": "Rune Factory 3 Special",
      "options": [
         {
           "name": "Play Game",
           "path": "Rune Factory 3 Special Launcher.exe",
           "launch_options": [],
           "use_wine": 0
         },
         {
           "name": "Config",
           "path": "Launcher/RF3S_Launcher.exe",
           "launch_options": [],
           "use_wine": 0
         }
      ],
      "umu_commands": {
      "GAMEID": "2243710",
      "PROTONPATH": "GE-Proton10-28",
      "pre_launch": ["GAMEID=2243710", "PROTONPATH=GE-Proton10-28"]
      }
    }

This config uses umu-launcher when running the ".exe" on Linux and the commands are set in advance so when the game runs on Linux it will use the command "GAMEID=2243710 PROTONPATH=GE-Proton10-28 umu-run" before the selected executable.

Wine can be used if set to 1 on "use_wine". These are set per-executable as you could have a situation where you needed Wine to run one and Proton another thing runs better in it.

If you don't need commands for umu you can just do ""umu_commands": {}".

I built this on Linux and have no Windows or Mac computers in my home. So your millage may very on these platforms. If it does not work, and you have a solution to fix it, feel free to fork and test out your variation of the launcher via Windows or Mac. Though hopefully it works out of the box. 
