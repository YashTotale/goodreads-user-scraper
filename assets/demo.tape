# demo.tape — sleek terminal demo of goodreads-user-scraper.
# Render from the repo root:  vhs assets/demo.tape   (writes assets/demo.gif — Output is relative to where vhs runs, NOT the cd below).
# The scrape runs from ~/Desktop (repo cookie copied there) so the CLI's "📁 Saved to …" line shows a clean ~/Desktop path
# rather than the repo/Conductor workspace path; the data + cookie copy are removed afterward.

Output assets/demo.gif

Require uvx

# --- look & feel ---
Set Theme "Catppuccin Mocha"
Set FontFamily "MesloLGL Nerd Font"   # installed locally; emoji fall back to Apple Color Emoji
Set FontSize 22
Set Width 1280
Set Height 460
Set Padding 40
Set Margin 24
Set MarginFill "#1e1e2e"
Set BorderRadius 14
Set WindowBar Colorful
Set TypingSpeed 45ms

# --- setup (not recorded): cd to ~/Desktop (clean 'Saved to' path, cookie copied alongside), and force uvx to the latest
# PUBLISHED version by clearing its cache + warming it here — plain `uvx <pkg>` otherwise reuses a stale cached env, and a
# `--refresh` run from the repo gets hijacked by the local project. Doing it from ~/Desktop after cd avoids both. Warm is hidden.
Hide
Type "REPO=$PWD && cd ~/Desktop && cp $REPO/.goodreads-cookie . && rm -rf goodreads-data && uv cache clean goodreads-user-scraper >/dev/null 2>&1 && uvx goodreads-user-scraper --help >/dev/null 2>&1 && clear"
Enter
Sleep 10s
Show

# --- the demo: full scrape end to end (output_dir defaults to ./goodreads-data = ~/Desktop/goodreads-data) ---
# Flow: 'Finding user…' spinner -> 👤 profile -> 'Finding shelves'/'Scraping books' bars -> 📚 shelves -> 📖 books -> 📁 Saved to.
Type "uvx goodreads-user-scraper --user_id 54739262 --cookie_file .goodreads-cookie"
Enter

# Ends on the 📁 summary — nothing typed after (VHS's Wait can't match rich output, and typing mid-scrape garbles it).
# Tune to ~(scrape time + 4s): too low cuts off mid-scrape (re-render), too high leaves a short static tail. Never garbles.
Sleep 20s

# --- cleanup (not recorded): remove the scraped data and the copied cookie from the Desktop (absolute paths = safe) ---
Hide
Type "rm -rf ~/Desktop/goodreads-data ~/Desktop/.goodreads-cookie"
Enter
Sleep 500ms
