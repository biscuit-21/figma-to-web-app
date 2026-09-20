# Key Indicators

A dashboard for U.S. economic data — inflation, employment, interest rates,
growth, exchange rates, housing and consumer spending — in twenty-two series
across eight categories.

It is a single self-contained HTML file. No build step, no server, no
dependencies: open it and it works.

## Run it

Either use the hosted copy, or clone and open the file:

```sh
git clone https://github.com/your-username/key-indicators.git
```

Then open `web/index.html` in any browser — double-click it, or drag it onto a
browser window. Everything runs locally; the page makes no network calls of its
own beyond loading its typeface.

The data is kept current by a scheduled workflow, so both the hosted copy and a
fresh `git pull` give you the latest published figures without any setup.

## What it does

- **Charts you can interrogate.** Hover or drag for the value at any point.
  Ranges from one year to the full history, with the 2020 recession shaded.
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

The data refreshes itself. A scheduled workflow pulls every series from the
FRED API on weekday mornings, rebuilds the dashboard, and commits the result
only if the numbers actually moved. Visitors need no key, no account and no
setup — whatever they open is already current.

The repository ships a starting snapshot: the latest reading of every series
matches the agency release it claims, while earlier history is reconstructed
from published figures and interpolated between them. The first successful
refresh replaces all of it with published observations.

### Turning the refresh on

Get a free API key from the
[St. Louis Fed](https://fredaccount.stlouisfed.org/apikeys), then add it under
**Settings -> Secrets and variables -> Actions -> New repository secret**, named
`FRED_API_KEY`. Run **Actions -> Refresh data -> Run workflow** once to confirm
it works; after that it runs on its own.

Without the secret the scheduled run fails and the site keeps serving the data
it already has.

To refresh by hand:

```sh
export FRED_API_KEY=your_key_here
python3 tools/refresh.py     # add --force to pull again the same day
python3 tools/build.py
```

Python 3.9 or newer, standard library only.

`refresh.py` asks FRED to apply its own transforms — year-over-year
percentages, period changes, monthly aggregation of daily yields — so the
refreshed numbers are the published ones rather than anything computed here. It
touches only the values; the titles and commentary in `data.json` are left
alone. If any series fails, nothing is written.

Source agencies: Bureau of Labor Statistics, Bureau of Economic Analysis,
Census Bureau, Federal Reserve Board, Freddie Mac, S&P Dow Jones Indices,
University of Michigan. Series identifiers follow FRED.

## Layout

```
web/index.html           the dashboard — generated, do not edit by hand
tools/template.html      the source of the dashboard, with a /*__DATA__*/ slot
tools/data.json          the dataset
tools/build.py           template + data -> web/index.html
tools/refresh.py         pull live observations from the FRED API
tools/build_snapshot.py  regenerate the bundled snapshot from anchor points
```

To change the dashboard itself, edit `tools/template.html` and run
`python3 tools/build.py`. Edits made directly to `web/index.html` are
overwritten by the next build, and CI fails if the two drift apart.

## Automation

- `refresh.yml` — pulls fresh observations from FRED on weekday mornings,
  rebuilds the dashboard, commits only when the data has moved, and redeploys
  the site. Also runnable on demand from the Actions tab.
- `pages.yml` — publishes `web/` to GitHub Pages on push to `main`, and when
  `refresh.yml` calls it.
- `ci.yml` — rebuilds `web/index.html` on every push and fails if it differs
  from what `tools/` produces.

## Licence

MIT. Economic data belongs to the issuing agencies and is public domain.
