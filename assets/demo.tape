# demo.tape — terminal demo of goodreads-user-scraper. Render from the repo root: vhs assets/demo.tape

Output assets/demo.gif

Require uvx

# --- look & feel ---
Set Theme "Catppuccin Mocha"
Set FontFamily "MesloLGL Nerd Font"   # any installed Nerd Font; emoji via system fallback
Set FontSize 22
Set Width 1280
Set Height 460
Set Padding 40
Set Margin 24
Set MarginFill "#1e1e2e"
Set BorderRadius 14
Set WindowBar Colorful
Set TypingSpeed 45ms

# Setup (hidden): run from ~/Desktop (clean "Saved to" path, cookie copied) and clear uvx's cache so the run uses the latest published version, not a stale one.
Hide
Type "REPO=$PWD && cd ~/Desktop && cp $REPO/.goodreads-cookie . && rm -rf goodreads-data && uv cache clean goodreads-user-scraper >/dev/null 2>&1 && uvx goodreads-user-scraper --help >/dev/null 2>&1 && clear"
Enter
Sleep 10s
Show

Type "uvx goodreads-user-scraper --user_id 54739262 --cookie_file .goodreads-cookie"
Enter

# Sleep must outlast the scrape (~scrape time + 4s); nothing is typed after, so it can't garble.
Sleep 20s

# Cleanup (hidden).
Hide
Type "rm -rf ~/Desktop/goodreads-data ~/Desktop/.goodreads-cookie"
Enter
Sleep 500ms
