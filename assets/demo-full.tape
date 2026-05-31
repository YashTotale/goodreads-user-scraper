# demo-full.tape — full scrape (the hero demo). Render via scripts/render_demos.sh.
Source assets/_demo-common.tape

Output assets/demo-full.gif

# Setup (hidden): run from ~/Desktop for a clean "Saved to" path, with the cookie copied into cwd.
Hide
Type "REPO=$PWD && cd ~/Desktop && cp $REPO/.goodreads-cookie . && rm -rf goodreads-data && clear"
Enter
Sleep 1s
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
