# Architecture

> Recap doc — the 10,000ft view of how this system is built, derived from the ADRs in
> `docs/adr/`. Keep it in sync as ADRs are added or superseded. ADRs hold the *why* and the
> discarded options; this doc holds only the **current state**.

## Overview

A small, local-only CLI that archives Substack newsletters you are subscribed to — keeping an
offline copy of paid and free content you already have access to. It does not bypass paywalls.

It has two Python entry points:

- **`login.py`** — a one-time, browser-driven helper that captures an authenticated session.
- **`scraper.py`** — reads Substack's JSON API and writes each post to disk as HTML and/or
  Markdown with images downloaded locally.

Output is organised into per-domain folders that are fully self-contained (post files plus a
local `assets/` image folder), and runs are incremental — each newsletter folder remembers the
newest post it downloaded so re-runs only fetch what is new.

## Key components

- **`scraper.py` — `SubstackScraper`** — wraps a `requests.Session` (desktop User-Agent).
  Fetches the post list from `/api/v1/archive` (newest-first), full posts from
  `/api/v1/posts/{slug}`, downloads inline images, rewrites `<img>` sources to local relative
  paths, and writes `.html` and/or `.md` per post.
- **`scraper.py` — state helpers** — `load_state` / `save_state` / `is_newer` and
  `state_path`, backing incremental resume via a per-folder `.substack_state.json`.
- **`scraper.py` — `main()`** — the argparse CLI: resolves auth source, builds the per-domain
  output path, resolves the resume boundary, and runs the scrape loop.
- **`login.py`** — a Playwright helper that launches the user's installed **Brave** (not a
  bundled Chromium), lets the user log in manually, then dumps cookies, `localStorage`, and the
  User-Agent to a session JSON file.
- **Session files** — `substack_session.json` (standard `*.substack.com`) or
  `substack_session_{domain}.json` (custom domains); a Playwright export the scraper loads.
- **`.substack_state.json`** — per-archive sync state inside each newsletter folder, tracking
  `latest_post_date` and `last_run`.

## Cross-cutting decisions

> No ADRs cover these yet — they record the current state. Backfill an ADR when a decision
> here gains a meaningful alternative worth remembering, and link it from this section.

- **Runtime** — Python 3 in a local `venv`; dependencies pinned by name in `requirements.txt`
  (`requests`, `beautifulsoup4`, `tqdm`, `python-dotenv`, `playwright`, `markdownify`).
- **Auth is cookie-based; the scraper never logs in itself.** Credentials come from (in
  priority order) a `--cookie` flag, a session file produced by `login.py`, or `SUBSTACK_SID`
  in `.env`. The cookie name is domain-aware: `substack.sid` for `*.substack.com`, `connect.sid`
  for custom domains (whose `.substack.com` cookies are not sent).
- **Data comes from Substack's undocumented JSON API**, not HTML scraping of rendered pages —
  archive list plus per-slug post bodies.
- **HTTP via a plain `requests.Session`** with a fixed desktop User-Agent; no API client wrapper.
- **Dual offline output** — every post is saved as styled HTML and/or Markdown, and all inline
  images are downloaded into `assets/` with their references rewritten to relative paths, so an
  archive is fully viewable offline. Markdown is converted from the *image-rewritten* HTML so
  its links also point at the local files.
- **Incremental sync** — the archive API is newest-first, so the scraper stops paging as soon
  as it reaches a post at or older than the resume boundary. Boundary priority:
  `--full` (wipe + re-download all) > `--since DATE` (manual) > saved state (auto-resume).
  `--limit` runs deliberately do **not** advance the saved state, to avoid leaving a permanent
  gap over the older posts they never covered.
- **Login uses the user's real Brave install** (headless off) via Playwright to get past bot
  protection on custom domains; the binary path is auto-detected per OS or overridden with
  `BRAVE_EXECUTABLE_PATH`.
- **100% local** — cookies, sessions, and downloaded content never leave the machine.

## Conventions

- **Per-domain output folders** under `--output-dir` (default `./archive`), e.g.
  `archive/read.substack.com/`. Filenames are `{post_date}_{safe_slug}.{html,md}`, with the
  slug sanitised to alphanumerics, space, `-`, and `_`.
- **Image dedup** — an image already present on disk is not re-downloaded.
- **Politeness** — a `time.sleep(1)` pause between full-post fetches.
- **Auth lookup order** — CLI cookie → domain-specific session file → default session file →
  `.env` `SUBSTACK_SID`.
- **Failure handling** — network/parse failures are logged to stdout (`print`) and the function
  returns an empty list / `None` rather than raising, so one bad post does not abort the run.
