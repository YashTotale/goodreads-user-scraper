# demo-invalid-cookie.tape — 👤 profile, then ❌ invalid-cookie error on the first shelf fetch. NON-DETERMINISTIC. Render via scripts/render_demos.sh.
Source assets/_demo-common.tape

Output assets/demo-invalid-cookie.gif

# Run from ~/Desktop (it writes user.json before failing); cleaned up after.
Hide
Type "cd ~/Desktop && rm -rf goodreads-data && clear"
Enter
Sleep 1s
Show

Type 'uvx goodreads-user-scraper --user_id 54739262 --cookie "invalid"'
Enter

# Wait for the ❌ error, then a short tail.
Wait+Screen@30s /invalid or expired/
Sleep 1.5s

Hide
Type "rm -rf ~/Desktop/goodreads-data"
Enter
Sleep 500ms
