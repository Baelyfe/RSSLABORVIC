# Victorian Labor News → RSS

Generates an RSS feed from https://www.viclabor.org.au/news, which has no
built-in feed. Runs entirely on GitHub's free tier (Actions + Pages) —
no trial period, no paid plan required, ever.

## One-time setup (~5 minutes)

1. Create a free GitHub account if you don't have one: https://github.com/signup
2. Create a new **public** repository (any name, e.g. `viclabor-rss`).
3. Upload all the files in this folder to that repository (drag-and-drop
   on the GitHub web UI works fine, or `git push` if you're comfortable
   with git).
4. In the repo, go to **Settings → Actions → General → Workflow
   permissions** and select **"Read and write permissions"**, then Save.
   (This lets the scheduled job commit the updated feed back to the repo.)
5. Go to the **Actions** tab, open "Update RSS feed", and click
   **"Run workflow"** once to generate the first `feed.xml`.
6. Go to **Settings → Pages**, set **Source** to "Deploy from a branch",
   branch `main`, folder `/ (root)`, and Save.
7. Wait a minute, then your feed is live at:

   `https://<your-github-username>.github.io/<repo-name>/feed.xml`

Share that URL with anyone, or add it to any RSS reader.

## How it stays up to date

`.github/workflows/update-feed.yml` runs `scrape_feed.py` every 3 hours
(you can change the cron schedule in that file), regenerates `feed.xml`,
and commits it if anything changed. GitHub Pages then serves the updated
file automatically — nothing else to do.

## If titles or dates look wrong after the first real run

`scrape_feed.py` was written and tested against a mocked-up copy of the
page's structure (the site couldn't be fetched directly while writing
this), so it's a best guess at the real markup. If the first generated
`feed.xml` has garbled titles, missing dates, or missing/extra items,
open an Actions run's log (it prints each item it found) or share
`feed.xml` and I can adjust `extract_items()` in `scrape_feed.py`
accordingly — it's a small, self-contained function.

## Files

- `scrape_feed.py` — fetches the page, extracts news items, writes `feed.xml`
- `requirements.txt` — Python dependencies (requests, beautifulsoup4)
- `.github/workflows/update-feed.yml` — the scheduled GitHub Action
- `.nojekyll` — tells GitHub Pages not to run this through Jekyll
