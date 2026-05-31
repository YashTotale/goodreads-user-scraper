# demo-no-cookie.tape — 👤 profile + 🟡 Skipping shelves warning (no cookie). 1 profile fetch. Render via scripts/render_demos.sh.
Source assets/_demo-common.tape

Output assets/demo-no-cookie.gif
Set Height 740   # override: the cookie warning is ~12 lines, taller than the shared 460

# Run from ~/Desktop so the 📁 path is clean (not the workspace path); cleaned up after.
Hide
Type "cd ~/Desktop && rm -rf goodreads-data && clear"
Enter
Sleep 1s
Show

Type "uvx goodreads-user-scraper --user_id 54739262"
Enter

# Wait for the run to finish (the 📁 line), then a short tail.
Wait+Screen@30s /Saved to/
Sleep 1.5s

Hide
Type "rm -rf ~/Desktop/goodreads-data"
Enter
Sleep 500ms
