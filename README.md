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
