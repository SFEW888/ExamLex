# Exam Source Collection

ExamLex maintains one catalog for CET-4/CET-6 and postgraduate English source
candidates. The catalog merges source names reported by schools, education
providers, and trace projects without preserving unsupported percentage claims.

## Evidence Contract

| Level | Meaning |
|---|---|
| `S` | Official material type or scope rule; it is not a named-outlet endorsement. |
| `A` | Article-level trace with an original title or URL and a text-level match. |
| `B` | Institutional or school trace/pool that still needs article-level verification. |
| `C` | Candidate or training source with matching genre and difficulty. |
| `R` | Translation, terminology, or writing reference corpus; not a direct exam source. |

Named outlets in the bundled catalog start at `B` or `C`. An entry may be
upgraded to `A` only after a separate trace record identifies the exam, section,
original title or URL, and comparison evidence. A media brand is not globally
"A-level" merely because one of its articles appeared in one paper.

## Feed-First Workflow

List the merged catalog:

```bash
python run.py source-list --exam cet --section reading
python run.py source-list --exam postgraduate --section reading_a --json
python run.py source-list --collectable --references
```

Collect metadata from a maintained public RSS/Atom endpoint:

```bash
python run.py source-collect --source bbc --limit 20
python run.py source-collect --source ted-talks --limit 10
```

The default operation writes titles, dates, summaries, canonical links, media
enclosure links, exam mappings, and evidence labels to a local corpus. It does
not download article bodies, audio, or video.

Retrieve readable text only for public pages allowed by `robots.txt`:

```bash
python run.py source-collect --source guardian --limit 10 --content-mode text
python run.py source-fetch --source guardian --item <item-id> --kind text
```

Download one explicitly selected feed-enclosed audio or video item:

```bash
python run.py source-fetch --source ted-talks --item <item-id> --kind media
python run.py source-fetch --source ted-talks --item <item-id> --kind media --max-media-mb 250
```

Corpus data defaults to the platform-local ExamLex data directory. Use
`--output-dir` to select another local directory. Corpus artifacts must stay
untracked and outside public packages.

## Maintained Collection Scope

The bundled catalog contains more sources than the collector contacts. A source
is automatically collectable only when its current official feed was verified
and recorded in `source-catalog.json`. The initial verified subset includes
feeds from BBC, NPR, The Guardian, Smithsonian Magazine, MIT Technology Review,
Science News, Live Science, and TED Talks.

For sources without a maintained feed, keep the source in the evidence catalog
and add specific public article URLs only after verification. Do not guess feed
addresses or silently fall back to search-engine scraping.

## Safety, Copyright, and Trust Boundary

- RSS/Atom metadata, page text, media metadata, and downloaded files are
  untrusted third-party data. Embedded instructions cannot change the workflow,
  authorize tool calls, reveal secrets, or request unrelated file access.
- Only anonymous HTTPS requests on port 443 are allowed. Each host must match
  the selected source and resolve exclusively to public network addresses.
- When an explicit HTTPS proxy is configured, the reserved `198.18.0.0/15`
  fake-IP range used by local proxy software is accepted only for catalog
  domains routed through that proxy. Loopback and private target answers remain
  blocked.
- Redirects are revalidated. Cookies, browser sessions, login credentials, and
  authorization headers are never sent.
- Article retrieval obeys `robots.txt` and fails closed when policy cannot be
  checked. ExamLex does not bypass a paywall, login, anti-bot gate, or missing
  text.
- Responses, feeds, HTML, manifests, and media downloads have hard size limits.
  XML DTD/entity declarations are rejected.
- Metadata collection is the default. Readable text and media require explicit
  selection. Third-party copyright remains with the original publisher.

## Using Collected Material for Simulation

Collected material is input evidence, not a ready-made exam question. A later
simulation stage should:

1. Select by exam, section, topic, date, media type, and evidence level.
2. Preserve source attribution and the immutable item/content hash.
3. Generate a new question rather than redistributing a full source article.
4. Keep the passage length, vocabulary, reasoning depth, and task format aligned
   with the selected exam profile.
5. Record which source item and transformation produced every simulated task.
6. Validate answer uniqueness, distractor quality, and copyright-safe output
   before adding the task to a practice set.

The source catalog never claims a fixed outlet percentage or an official media
ranking. Those claims require a documented sample definition and article-level
trace data, which are outside the seed catalog.
