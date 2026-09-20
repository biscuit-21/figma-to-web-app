# Key Indicators

A dashboard for U.S. economic data — inflation, employment, interest rates,
growth, exchange rates, housing and consumer spending — in twenty-two series
across eight categories, refreshed automatically from the Federal Reserve's
FRED database.

**[View the dashboard](https://biscuit-21.github.io/figma-to-web-app/)**

## Run it

Nothing to install. Either open the link above, or clone and open the file:

```sh
git clone https://github.com/biscuit-21/figma-to-web-app.git
```

Then open `web/index.html` in any browser — double-click it, or drag it onto a
browser window. It is one self-contained file. The page makes no network calls of its own beyond loading
its typeface, so it works offline.

**Requirements:** a modern browser.

## What it does

- **Interactive Charts** Hover or drag for the value at any point.
  Ranges from one year to the full history, with recessions shaded.
- **Compare up to four series** on one axis. Mixed units are rebased to 100 at
  the start of the range, so you can put the mortgage rate against the 10-year
  yield, or unemployment against GDP growth.
- **Detail view** for every indicator: high, low and average over the selected
  range, plus what the series actually measures, what distorts it, and what to
  watch for.
- **Pin** the indicators you follow to the sidebar. Search with `/`.
- Dark mode, keyboard navigation, and a layout that works on a phone.

Rising is amber and falling is teal rather than red and green: for inflation
and unemployment a rise is bad news, and a green-means-good palette would
mislead. Colour shows direction only.

## Data

A scheduled workflow pulls every series from the FRED API on weekday mornings,
rebuilds the dashboard, and commits the result only if the numbers moved.
Visitors need no key and no account — whatever they open is already current.

`refresh.py` asks FRED to apply its own transforms — year-over-year
percentages, period changes, monthly aggregation of daily yields — so the
figures are the published ones rather than anything computed here. It touches
only the values; the titles and commentary in `data.json` are left alone. If
any series fails, nothing is written.

Source agencies: Bureau of Labor Statistics, Bureau of Economic Analysis,
Census Bureau, Federal Reserve Board, Freddie Mac, S&P Dow Jones Indices,
University of Michigan. Series identifiers follow FRED.

## Setting up your own copy

Only needed if you fork this or start from scratch. Four steps.

**1. Get a FRED API key.** Free, instant, from
[fredaccount.stlouisfed.org/apikeys](https://fredaccount.stlouisfed.org/apikeys).

**2. Add it as a secret.** Settings → Secrets and variables → Actions → New
repository secret. Name it exactly `FRED_API_KEY`. It stays on GitHub's
servers and never reaches a visitor's browser.

**3. Enable Pages.** Settings → Pages → Source → **GitHub Actions**. Do not
pick a branch; that is the older deployment mode and it conflicts with the
workflow.

**4. Run it once.** Actions → Refresh data → Run workflow. This proves the key
works and publishes the site. After that it runs on its own. You will most likely
need to run 'Deplay to GitHub Pages' manually once. Since there is no previous
data to compare to, data will never be initialized from FRED.

Expect the first successful refresh to produce a large diff: the repository
ships a reconstructed starting snapshot, and that run replaces it wholesale
with published observations.

## Working on it

**Requirements:** Python 3.9 or newer, standard library only. No packages to
install.

`web/index.html` is generated. Edit `tools/template.html`, then rebuild:

```sh
python3 tools/build.py
```

Edits made directly to `web/index.html` are overwritten by the next build, and
`ci.yml` fails if the two drift apart.

To refresh the data by hand:

```sh
export FRED_API_KEY=your_key_here      # Windows: set FRED_API_KEY=your_key_here
python3 tools/refresh.py               # add --force to pull again the same day
python3 tools/build.py
```

```
web/index.html           the dashboard — generated, do not edit by hand
tools/template.html      the source of the dashboard, with a /*__DATA__*/ slot
tools/data.json          the dataset
tools/build.py           template + data -> web/index.html
tools/refresh.py         pull live observations from the FRED API
tools/build_snapshot.py  regenerate the starting snapshot from anchor points
```

## Automation

- `refresh.yml` — pulls from FRED on weekday mornings, rebuilds, commits only
  when the data moved, and redeploys. Also runnable from the Actions tab.
- `pages.yml` — publishes `web/` to GitHub Pages on push to `main`, and when
  `refresh.yml` calls it.
- `ci.yml` — rebuilds `web/index.html` on every push and fails if it differs
  from what `tools/` produces.

## Licence

MIT. Economic data belongs to the issuing agencies and is public domain.
