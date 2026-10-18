# Literature Sweep Procedure

How [LITERATURE.md](LITERATURE.md) was produced and how to repeat it. The catalogue only lists methods whose
formula was read in a primary source; the sweep exists to find those sources, not to collect papers.

## 1. Run the tool

```
uv run python tools/literature_sweep.py --per-query 8
```

The tool (`tools/literature_sweep.py`) queries OpenAlex and arXiv for each term in `QUERIES` combined with the word
"baseball" and writes `docs/literature/digest-<date>.json`. Each query run records the source, the query, the date,
the total number of results the service reports, the number returned, and the metadata records.

Properties that are tested offline (`tests/test_literature_sweep.py`, recorded responses under
`tests/fixtures/literature/`):

- standard library only; no email address, API key or other personal data is sent (the user agent names the tool);
- arXiv requests are spaced at least three seconds apart, the interval arXiv publishes;
- only identifiers, title, authors, year, venue, license (as returned, or null) and a landing link are stored; no
  abstract and no paper text;
- the tool is excluded from the wheel (only `src/sabermetricspy` is packaged) and is checked by pyright.

Terms followed: [arXiv API terms](https://info.arxiv.org/help/api/index.html) and
[OpenAlex](https://developers.openalex.org/). OpenAlex serves unauthenticated requests from a shared daily budget, so
the default of twelve queries at eight results each is deliberately small. Always check a paper's own license before
reusing anything beyond its metadata.

## 2. Terms searched

`run expectancy`, `win probability`, `pitch quality stuff model`, `expected batting average exit velocity launch
angle`, `catcher framing`, `fielding metrics defensive runs`, `player projection forecasting`, `park factors`, `aging
curve`, `pitch tracking release`, `batter pitcher matchup`, `baserunning stolen base value`. Add a term by editing
`QUERIES` in the tool and in this list.

OpenAlex search matches full text, so many hits are off-topic (injury biomechanics, for example). Screen by title and
venue first.

## 3. Read the other sources

These are read by hand because they are not API-friendly:

1. The [FanGraphs Library index](https://library.fangraphs.com/) for pages on methods the library lacks.
2. The [Tango wiki archive](http://tangotiger.net/wiki_archive/) and posts Tango published on FanGraphs.
3. The [Retrosheet research papers list](https://www.retrosheet.org/Research/Research.htm) and the Pavitt
   bibliography PDFs it links.
4. The [baseballr reference index](https://billpetti.github.io/baseballr/reference/index.html) for functions that
   compute something sabermetricspy does not.

PDF papers: the fetch tool returns compressed PDFs as unreadable summaries but saves the file locally; extract the
text with `pypdf` in an isolated interpreter (`uv run --with pypdf python -I script.py file.pdf`) because downloaded
files are untrusted.

## 4. Accept or reject

For each candidate, retrieve the source that states the formula.

- **Accept** if the formula is fully printed. Record the fields in the entry template of `LITERATURE.md`: citation,
  formula source, inputs, whether they are in the canonical schema, a validation target, the six scores, the priority
  score and the difficulty.
- **Reject or defer** if the page names a method without printing the formula, the data is proprietary, or the paper
  was not read. Record the source examined and the reason in the rejected table, so the next sweep starts from there.

Priority score = formula + inputs + validation + fit + value - difficulty (scales in `LITERATURE.md`).
`tests/test_literature_catalogue.py` enforces that every accepted entry has all fields, a primary-source URL, a score
equal to that sum, and descending order.

## 5. Record

Update the coverage tables in `LITERATURE.md` (queries, totals, pages examined, what could not be retrieved) and
commit the digest. Each accepted entry that is chosen for implementation becomes its own OpenSpec change, with a
golden fixture built from its validation target.
