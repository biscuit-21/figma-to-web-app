# Key Indicators

A dashboard for U.S. economic data — inflation, employment, interest rates,
growth, exchange rates, housing and consumer spending — in twenty-two series
across eight categories.

It runs as a single executable with nothing to install: the dashboard is
compiled into the binary, which serves it on localhost and opens your browser.
It is also a plain HTML file, so you can open it directly or host it anywhere
static.


## Run it

**Download a binary.** Grab the one for your platform from
[Releases](../../releases), then:

```sh
chmod +x key-indicators-darwin-arm64     # macOS and Linux only
./key-indicators-darwin-arm64
```

On Windows, double-click the `.exe`. macOS will refuse an unsigned download the
first time — right-click the file and pick Open, or run
`xattr -d com.apple.quarantine key-indicators-darwin-arm64`.

**Or skip the binary entirely.** `web/index.html` is self-contained. Open it in
a browser and everything works.

**Or build from source.** Requires Go 1.22 or newer:

```sh
git clone https://github.com/your-username/key-indicators.git
cd key-indicators
make run
```

### Options

```
-port 7331      port to listen on; 0 picks any free port
-host 127.0.0.1 bind address; use 0.0.0.0 to reach it from other machines
-open=false     don't launch a browser
-version        print the version
```

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

The repository ships a **bundled snapshot**. The latest reading of every series
matches the agency release it claims; earlier history is reconstructed from
published figures and interpolated between them, so the shapes are right but
individual mid-series months are approximations rather than exact prints.

To replace it with live data, get a free API key from the
[St. Louis Fed](https://fredaccount.stlouisfed.org/apikeys) and run:

```sh
export FRED_API_KEY=your_key_here
python3 tools/refresh.py     # pulls every series from the FRED API
python3 tools/build.py       # rebuilds web/index.html
```

`refresh.py` asks FRED to apply its own transforms — year-over-year percentages,
period changes, monthly aggregation of daily yields — so the refreshed numbers
are the published ones rather than anything computed here. It touches only the
values; the titles and commentary in `data.json` are left alone. If any series
fails, nothing is written.

Source agencies: Bureau of Labor Statistics, Bureau of Economic Analysis,
Census Bureau, Federal Reserve Board, Freddie Mac, S&P Dow Jones Indices,
University of Michigan. Series identifiers follow FRED.

## Layout

```
main.go              embeds web/ and serves it
web/index.html       the dashboard — self-contained, no runtime fetches
tools/template.html  the same file with a /*__DATA__*/ placeholder
tools/data.json      the dataset
tools/build.py       template + data -> web/index.html
tools/refresh.py     pull live observations from the FRED API
tools/build_snapshot.py  regenerate the bundled snapshot from anchor points
```

`web/index.html` is generated. Edit `tools/template.html` and run
`python3 tools/build.py`; CI fails if the two drift apart.

## Make targets

```
make build   compile for this machine
make run     build and start
make data    rebuild web/index.html from tools/
make check   go vet and a compile check
make dist    cross-compile all platforms into dist/ with checksums
```

## Automation

- `ci.yml` — vets and compiles on every push, and fails if `web/index.html`
  is out of date with `tools/`.
- `pages.yml` — publishes `web/` to GitHub Pages on push to `main`.
- `release.yml` — on a `v*` tag, cross-compiles Linux, macOS and Windows
  binaries, generates `SHA256SUMS`, and attaches everything to the release.

## Licence

MIT. Economic data belongs to the issuing agencies and is public domain.
