# Thoughtful AI - Challenge

Robot to parse page ```https://apnews.com/`` employing some [parameters](api/constants.py) and extracting:
- URL: news link
- Title: news title
- Description: news description (when available)
- Image: news image filename (when available). The downloaded image file is in `IMGS` folder
- DateTime: news publication date and hour (some promoted news may have this field missing)
- #Search Phrase Matches: quantity of occurrence of the search keyword in the news title and/or description
- Contains Money: True or False informing if the news title and/or description contains monetary information

## Running

#### VS Code
1. Get [Robocorp Code](https://robocorp.com/docs/developer-tools/visual-studio-code/extension-features) -extension for VS Code.
1. You'll get an easy-to-use side panel and powerful command-palette commands for running, debugging, code completion, docs, etc.

#### Command line

1. [Get RCC](https://github.com/robocorp/rcc?tab=readme-ov-file#getting-started)
1. Use the command: `rcc run`

## Results

🚀 After running the bot, check out the `log.html` under the `output` -folder.