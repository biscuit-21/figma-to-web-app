# How this was built

A record of the prompts and the working process behind this repository. Built
in one session with Claude, from a Figma file to a deployed, self-updating site.

## The prompts

Ten instructions, in order. Each is roughly verbatim.

| # | Prompt | What it produced |
|---|---|---|
| 1 | *"Create a web app based off of this figma model. You have freedom to make choices about the app so do whatever you think is best or most useful (features wise)."* (with `key-indicators.fig` attached) | The dashboard |
| 2 | *"how can i put this into a github repo with an executable?"* | Repo scaffold, Go binary, three workflows |
| 3 | *"I want to push it to an empty repo that I already have cloned locally"* | Git instructions |
| 4 | *"how do i edit go.mod? file explorer sees it as a video file"* | Windows `.mod` file association fix |
| 5 | *"how can someone run it if they clone the repo?"* | Surfaced that no binary existed |
| 6 | *"there is no .exe file, to run the app you open the .html file"* | Decision point: drop the Go path |
| 7 | *"Can you make the changes to drop it?"* | Static-site repo |
| 8 | *"can you make a dedicated run script that refreshes and then builds?"* → *"just build the one that can be used by all visitors"* | Scheduled refresh workflow |
| 9 | Pasted CI error logs (×3) | Path and Pages-enablement fixes |
| 10 | *"can you confirm that the README is concise and explains the requirements, setup process, and how to run the project?"* | README audit and rewrite |

## What the agent did unprompted

The first prompt was deliberately open — "do whatever you think is best" — and
most of the work came out of that latitude rather than out of instruction.

**Read the Figma file directly.** A `.fig` is a ZIP archive. Unzipping it
exposed `thumbnail.png`, ten embedded screenshots, and `canvas.fig` in Figma's
kiwi binary format, which decompressed with zlib. The design turned out to be a
FRED dashboard rendered in an error state, so the layout and navigation were
legible but the charts were static images.

**Checked its own knowledge was current.** The model's training cutoff predates
the session, so it web-searched the September 2026 releases — CPI, the jobs
report, the FOMC decision, GDP — and anchored every series to published
figures rather than to memory.

**Tested without a browser.** No browser was available in the sandbox, so it
wrote a Node DOM stub and exercised the app headlessly: every series against
every time range, every category, both sort orders, the compare view with
matched and mixed units, and the detail panel for all 22 series. A separate
geometry pass asserted that no chart coordinate escaped its viewBox and that
the y-axis wasn't inverted. Both suites ran again after every change.

**Flagged its own limitations.** It volunteered that the bundled history was
interpolated rather than exact, that a published page cannot call the FRED API,
and — when asked for a launcher script — that the design would force every
visitor to register their own API key.

## Where the work turned

Three moments changed the shape of the project.

**The executable was the wrong answer.** Prompt 2 asked for a binary and got
one: a Go program embedding the HTML, with cross-compilation and a release
workflow. It was only at prompt 5–6 that the obvious surfaced — the dashboard
is a single self-contained HTML file, so a server that does nothing but hand
that file to a browser is ceremony. Deleting `main.go`, `go.mod`, `Makefile`
and `release.yml` made the project simpler and honest about what it is.

**The launcher would have broken the thing it was meant to fix.** The request
was a script that refreshes data before opening the site. Building it would
have made a FRED API key a precondition for every visitor. Moving the refresh
to a scheduled workflow put the key in repo secrets once and left visitors with
nothing to configure.

**A workflow commit does not trigger other workflows.** GitHub suppresses that
to prevent loops, so the refresh job's commit would never have redeployed the
site. `pages.yml` became a reusable workflow that `refresh.yml` calls directly.

## What went wrong

Worth recording, since none of it was visible until it ran on GitHub.

- Files landed one directory too deep, so `tools/refresh.py` was missing at the
  path the workflow expected. Exit code 2 rather than 1 was the tell.
- GitHub Pages has to be switched on manually, with Source set to *GitHub
  Actions* rather than a branch. The workflow cannot enable it.
- Windows treats `.mod` as a music format and hides known extensions, which
  makes editing `go.mod` from Explorer needlessly hard.
- The README still contained a placeholder clone URL and never mentioned
  enabling Pages — caught only by asking for an explicit audit at the end.

## Takeaway

The prompts that produced the most were the open one at the start and the
corrective ones in the middle. Stating the goal and leaving the approach free
produced a better dashboard than a specification would have; saying plainly
that the executable was pointless produced a better repository than defending
it would have.
