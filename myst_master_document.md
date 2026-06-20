# myst — Master Document

*The verification layer for earth-observation science.*

**Status:** v0 in development · **Document version:** 1.0 · **Date:** 18 May 2026

This is the single source of truth for what myst is, why it exists, how it works, how it is built, and how it will operate and deploy. It is written to be self-contained: a reader with no prior context — a collaborator, a mentor, a funder, or a future working session — should be able to understand the whole project and continue it from here.

---

## Table of Contents

1. Summary
2. The Problem
3. Why Earth Observation
4. How myst Works
5. Design Principles
6. System Architecture
7. The Codebase
8. Roadmap: Build → Operate → Deploy
9. How myst Scales
10. Go-to-Market & Strategy
11. Risks & Open Problems
12. Continuing the Build
13. Glossary

---

## 1. Summary

When you read "the Amazon lost 12% of its forest cover," that number feels like a fact — but it isn't a lookup. It is the output of a long analysis pipeline full of contestable judgment calls, and almost no claim drawn from satellite data is ever independently checked.

**myst is a verification engine that re-runs any earth-observation claim across every defensible methodology and logs the result to a public record anyone can open — turning "trust me" into "here's the verification."**

The v0 scope is deliberately narrow: one claim type — **forest-cover loss** — verified against established satellite products such as Hansen Global Forest Change. The narrowness is the point. It is a bounded wedge that proves the engine before the scope widens.

---

## 2. The Problem

An earth-observation claim is not a fact retrieved from a database. There is no dataset anywhere that contains "the Amazon lost 12% of its forest cover since 2010." That number is the **output of an analysis pipeline**, and every step of that pipeline is a contestable methodological choice:

- *Which satellite product?* Hansen Global Forest Change, JRC Tropical Moist Forest, ESA WorldCover — each gives different numbers.
- *What canopy density counts as "forest"?* 10%, 25%, 30% — all are used in the literature.
- *What counts as "loss"?* Stand-replacement disturbance, gross loss, net loss including regrowth.
- *What boundary defines the region? What time alignment? What baseline?*

Two competent scientists can analyze the same question, make different defensible choices, and arrive at materially different numbers — both correct. The result is that **satellite data — arguably the most consequential dataset on Earth — is also among the least independently verified.**

The stakes are concrete. Forest-cover claims underpin the **voluntary carbon market**, which has drawn well over $36B in investment and counts a large share of major corporations as buyers. Independent evaluations have found that many forest-carbon projects substantially over-claimed avoided deforestation, wiping significant value from the market. Behind every one of those credits is exactly the kind of forest-loss claim myst v0 is built to verify.

---

## 3. Why Earth Observation

Verification is only worth building where it is both **genuinely needed** and **genuinely possible**. Earth observation is the rare domain where both hold.

- **Needed:** the claims are consequential, contested, and currently unchecked.
- **Possible:** the raw inputs are *public*. Satellite imagery and the major derived products are openly distributed by NASA, ESA, USGS, and others. Unlike financial or medical claims — where the underlying data is private and verification is structurally blocked — an earth-observation claim can be independently re-derived from first principles by anyone with the method and the compute.

This combination is what makes myst feasible. The data is there; what is missing is a systematic, reproducible, public layer that re-derives claims and records the result.

---

## 4. How myst Works

### 4.1 The three-phase model

myst processes a claim in three strictly separated phases. The separation is not a convenience — it is the integrity mechanism.

```
   CLAIM (raw text)
        │
        ▼
┌─────────────────┐
│  1. COMPILE     │  An LLM decomposes the claim. It pins the
│                 │  methodology axes the source explicitly states
│                 │  and grids (varies) the ones it does not.
│                 │  Output: a frozen PipelineSpec. No data seen yet.
└─────────────────┘
        │  ──── freeze wall ────  methodology is now locked
        ▼
┌─────────────────┐
│  2. EXECUTE     │  Runs the methodology grid over real satellite
│                 │  data. The agent may fix plumbing (broken
│                 │  downloads, format bugs) but never methodology.
│                 │  Output: one measured value per grid cell.
└─────────────────┘
        │
        ▼
┌─────────────────┐
│  3. VERDICT +   │  Compares the claim against the spread of grid
│     INDEX       │  results. Emits a verdict, a defensible range,
│                 │  and full provenance — logged to the Index.
└─────────────────┘
        │
        ▼
   THE INDEX (public, versioned record of verifications)
```

The **freeze wall** between Compile and Execute is the defense against bias. Once methodology is locked, no result is visible yet — so the methodology cannot be quietly tuned toward a desired answer. This is what stops the verifier from p-hacking its own verdicts.

### 4.2 The methodology space — the keystone artifact

The compiler does not invent methodology. It selects from a **methodology space**: a curated, versioned, public artifact that enumerates, for one claim type, every recognized axis of methodological choice and every defensible option on each.

It has three nested levels:

- **AxisOption** — one defensible choice on one dimension, with a required citation (e.g. `canopy threshold = 30%`, cited from Hansen et al. 2013). An option without a source cannot exist; the schema enforces it.
- **MethodologyAxis** — one decision point ("what canopy density counts as forest?") plus the full list of its defensible options.
- **MethodologySpace** — all the axes for one claim type, together: the complete space of defensible ways to measure that claim.

The methodology space is **curated by humans from primary sources** — dataset documentation, the peer-reviewed literature, standards bodies — never generated by a model. This is non-negotiable. A methodology space invented by an LLM would be unaccountable, uncitable, and uncontestable, which would reintroduce exactly the bias myst exists to eliminate.

A defensible option is one with **precedent** — a specific value some credible source actually used. Options are discrete, not ranges: defensibility attaches to specific cited values, the grid must be finite to run, and every result must trace to one cited choice. The *range* in myst is an **output** — the spread of grid results — not an input. Discrete in, range out.

### 4.3 Verification as robustness, not reproduction

myst does not attempt strict reproduction — "did the authors, using their exact method, compute the number correctly?" Strict reproduction usually isn't possible, because sources under-specify what they did. (That under-specification *is* the reproducibility crisis.)

Instead, myst tests **robustness**. It runs the whole grid of defensible methodologies and asks: does the claim survive all of them?

- If the claimed number falls **inside** the range produced by every defensible methodology → it is robust. It holds no matter which reasonable choice the original author made.
- If it falls **outside** the entire range → no defensible methodology produces it.

Crucially, *not knowing the original author's methodology is not a flaw in myst — it is the reason the grid exists.* Precisely because the method is unknown, myst runs all of them.

### 4.4 Stated vs gridded

A claim's methodology is never fully known or fully unknown — it is partial. The compiler handles both:

- **Pin** the axes the source explicitly states ("the study used Hansen GFC at 30%").
- **Grid** the axes it does not state — vary them across all defensible options.

The verdict is then conditioned on this split and recorded in the provenance: myst is always explicit about what the source disclosed and what it had to vary.

### 4.5 Verdict semantics

A verdict is one of three values, and the meaning is honest about its own limits:

- **Confirmed** — the claim is robust: it falls within the defensible range.
- **Challenged** — the claim is *not robust*: it falls outside the range of reasonable methodology. This does **not** mean "the authors lied." It means the number depends on a specific, non-obvious, or indefensible choice and warrants scrutiny.
- **Could-not-reproduce** — the claim is too under-specified, or the data unavailable, to construct or run a grid at all.

Every verdict is expressed *relative to a specific version of the methodology space*, and is reproducible against that frozen version.

### 4.6 The Index

The **Index** is myst's public, versioned, permanent record of verifications. Each entry holds the claim, the verdict, the defensible range, and the full frozen pipeline that produced it — so anyone can inspect or re-run it.

The Index is not a feature; it is the compounding asset. The engine produces entries; the Index is where they accumulate into something durable, citable, and impossible for a competitor to clone.

---

## 5. Design Principles

These are the non-negotiable commitments. Every build decision is checked against them.

1. **Determinism and auditability are the product.** Anywhere a choice affects a verdict, that choice must be explicit, frozen, and traceable. The value of myst is not its technology stack; it is that its verdicts can be inspected and reproduced.

2. **Curated, not generated.** The methodology space — the part that decides what is defensible — is a hand-curated artifact from primary sources. It is never the output of a model.

3. **ML lives in perception, never judgment.** Machine learning is welcome for parsing claims (the compiler LLM), cleaning data, and triage. It is forbidden in the judgment layer — the methodology space and the verdict must stay deterministic. myst's own future ML belongs only in the calibration loop, and only once the Index has data.

4. **No RAG in the core.** The methodology space is the deliberate anti-RAG: a curated artifact, not runtime retrieval. Retrieval has narrow, later uses (semantic search over the Index; curation assistance) but never drives a verdict.

5. **Build the part that has to be true, first.** The risky, uncertain, value-bearing question is "can the engine verify a claim correctly?" That is all backend. Front-load the risk.

6. **Backend first.** v0 has no meaningful frontend. The engine *is* the product; its interface is a Python API, a CLI, and a demo notebook. The public Index website is a later phase.

---

## 6. System Architecture

The components, in dependency order:

| Component | Role | Status |
|---|---|---|
| **Claim** | The raw input — claim text, type, value, unit, source. | Built |
| **MethodologySpace** | The curated artifact: axes, options, citations, version. (`AxisOption` / `MethodologyAxis` / `MethodologySpace`.) | Models built; v1.0.0 content to curate |
| **Compiler** | LLM that decomposes a claim into a frozen `PipelineSpec` — pinning stated axes, gridding the rest. | Planned |
| **PipelineSpec** | The frozen, declarative description of the verification to run. | Planned |
| **Executor** | Runs the methodology grid over real satellite data; iterates on plumbing only. | Planned |
| **Verdict** | Compares the claim to the spread of results; emits confirmed / challenged / could-not-reproduce + range. | Planned |
| **The Index** | Public, versioned record of every verification with full provenance. | Planned |
| **Calibration loop** | Accumulated (verification → ground truth) data; the future home of myst's own ML. | Phase 2+ |

**Data flow:** `Claim` → Compiler selects from `MethodologySpace` → frozen `PipelineSpec` → Executor runs the grid over satellite data → measured values → `Verdict` → entry written to the `Index`.

---

## 7. The Codebase

- **Repository:** `myst` (GitHub).
- **Language / environment:** Python 3.13, Windows development, `pip` + `venv` (uv abandoned due to PATH issues).
- **Testing / CI:** `pytest`, GitHub Actions.
- **Layout:** `src/myst/` package layout.

| Layer | Tool | Status |
|---|---|---|
| Data modeling | Pydantic | In use |
| Methodology space format | YAML (`pyyaml`) | In use |
| Testing | pytest | In use |
| CI | GitHub Actions | In use |
| Compiler | Anthropic Claude API | Planned |
| Executor | Geospatial stack (to be selected) | Planned |
| The Index | Public database + website | Planned |

**Current state (end of Phase 1):**

```
src/myst/
    __init__.py
    claim.py                       # Claim model
    methodology/
        __init__.py
        space.py                   # AxisOption, MethodologyAxis, MethodologySpace + YAML loader
        forest_cover_loss.yaml      # STUB only — real v1.0.0 to be curated
tests/
    test_methodology.py
```

Dependencies are deliberately minimal (`pydantic`, `pyyaml`); more are added only as the build reaches the components that need them. The methodology-space schema enforces integrity directly — an `AxisOption` without a citation will not instantiate.

---

## 8. Roadmap: Build → Operate → Deploy

| Phase | Deliverable | Status |
|---|---|---|
| 0 | Repository, CI, toolchain | ✅ Done |
| 1 | Foundation — `Claim` + methodology-space models & loader | ✅ Done |
| 2 | **Methodology space v1.0.0** — curate `forest_cover_loss.yaml` by hand from primary sources | ⏭ Next |
| 3 | **Compiler** — claim → frozen `PipelineSpec` (pins stated axes, grids the rest) | Planned |
| 4 | **Executor** — run the methodology grid over real satellite data | Planned |
| 5 | **Verdict + Index** — verdict logic and the provenance record | Planned |
| 6 | **Demo** — one full, real, end-to-end forest-cover-loss verification | Planned |
| 7 | **Open-source launch** — public repo, README, demo notebook, first announcement | Planned |
| 8+ | The Index website; calibration loop; second methodology space (community-curated); carbon-market offering | Future |

**Build** is Phases 2–6: a working engine that verifies one claim type end-to-end.

**Operate**, once built, means the steady-state loop: claims come in → compiled → executed → verdicted → logged to the Index; the methodology space is maintained and versioned as products and literature evolve; the calibration loop accumulates ground-truth comparisons.

**Deploy** is staged. v0 ships as an open-source Python package — installable, with a clean API, a CLI, and a demo notebook — because the early audience (researchers, grad students, journalists) adopts libraries through code and examples, not a web UI. The public **Index website** follows in a later phase, once the engine has produced verifications worth showing. A paid offering for the carbon-credit ecosystem comes later still, after open-source traction.

---

## 9. How myst Scales

The natural worry is that hand-curating a methodology space per domain doesn't scale to "every kind of satellite claim." The honest answer:

- **The economics are good.** A methodology space is curated once per claim *type* and then verifies every claim of that type forever — fixed cost per type, near-zero marginal cost per claim. Like a compiler: expensive once, cheap thereafter.
- **Claim types are finite.** Consequential earth-observation claims cluster into a few dozen measurement archetypes (forest-cover change, surface-water extent, urban expansion, glacier extent, burned area, and so on). A multi-year roadmap — not an infinite one.
- **The framework is reused.** The methodology-space schema, the compiler, the executor, and the Index are identical across domains. Each new space refills a known template; later spaces are far faster than the first.
- **Curation is a community activity.** The founder builds the framework and curates the first space (forest-cover loss) as the proof. Subsequent spaces are curated by domain experts — exactly myst's user base — because the methodology space is a public, versioned, contestable artifact. The founder owns the framework and the standard; the community fills the content.

**The real scalability test** is not "did myst cover everything." It is: *did someone other than the founder curate methodology space #2?* If outside experts contribute spaces, myst scales. If they never do, it stays a single-domain tool. Phases 7–8 should be engineered explicitly to make outside contribution easy and prestigious.

---

## 10. Go-to-Market & Strategy

- **Open-source first.** The engine is released as open source. The public Index is the credibility and distribution engine — a resource people cite, which is worth more than any marketing.
- **Two audiences, one wedge.** The early *users* are researchers, grad students, and journalists, who value code quality and reproducibility over founder credentials. The eventual *paying customer* is the **carbon-credit ecosystem** — buyers, auditors, and registries — for whom verified forest-loss claims have direct financial stakes. Carbon-credit rating firms already exist, which validates demand; the open gap is a claim-level, reproducible, public verification layer.
- **Funding path.** The founder is a minor, which shapes the approach away from traditional enterprise sales and VC and toward age-appropriate programs — Pioneer.app, Z Fellows, Emergent Ventures, the 1517 Fund, NASA SpaceApps, and similar — alongside open-source community building.
- **Sequencing.** Open-source traction first → the Index as a public good → a hosted/paid tier for the carbon ecosystem once credibility is established.

---

## 11. Risks & Open Problems

An honest accounting. These are real and should be revisited, not buried.

- **Completeness can never be proven.** It is impossible to prove a methodology space contains *every* defensible option. myst does not claim to. The defense is to make the space explicit, versioned, contestable, and conservative (when in doubt, include an option — which makes myst slower to issue a "challenged" verdict). Completeness is approached over time through community scrutiny; it is never certified.
- **Scaling depends on outside contribution.** If domain experts never contribute methodology spaces, myst remains a forest-cover-loss tool. This is the single largest strategic risk.
- **Curation is a real bottleneck.** Building a methodology space is slow, manual, expert-dependent work. It cannot be automated without destroying the property that makes it trustworthy.
- **Methodology extraction is lossy.** The compiler reads messy natural-language sources to find the stated methodology. Papers under-specify; articles specify nothing. myst mitigates this by being explicit about the stated/gridded split, but the imprecision is irreducible.
- **Two-audience tension.** Open-source users and paying carbon-market customers are different groups with different needs; serving both well is not automatic.
- **Social and reputational risk.** A "challenged" verdict may be contested by the parties whose claims are challenged. Verdict language and the Index must be scrupulously honest and defensible to withstand this.
- **Founder constraints.** As a minor, the founder faces real limits on certain funding routes, contracts, and enterprise credibility. The open-source-first strategy is partly a response to this, but the constraint is genuine.
- **Engineering difficulty.** Running real satellite-data pipelines reliably and reproducibly is hard. Phase 4 (the Executor) carries the most technical risk.

---

## 12. Continuing the Build

For whoever picks this up — the founder in a future session, a collaborator, or a new working session — this document plus the repository are the source of truth.

**The immediate next task is Phase 2: curate `forest_cover_loss.yaml` v1.0.0.** This is manual work: gather the documentation of the major forest datasets, one or two dataset-comparison/uncertainty review papers, the FAO forest definition, and relevant carbon-standard methodologies; extract the axes; list every defensible option with a real, verified citation; write the YAML; tag it `version: 1.0.0`; commit.

**Rules that must not be broken:**

- The methodology space is curated from primary sources you have actually read. It is never model-generated. The current `forest_cover_loss.yaml` in the repo is a stub with placeholder citations and exists only to test the loader.
- Build backend first, in roadmap order. Do not build a frontend before the engine works.
- Keep the judgment layer (methodology space, verdict logic) deterministic and auditable. ML and retrieval stay in the perception layer.
- Maintain the compile/execute freeze wall: methodology is locked before any result is visible.
- Every option carries a citation; every verdict is tied to a methodology-space version.

After Phase 2, build the Compiler (Phase 3), which selects from the methodology space to produce a frozen `PipelineSpec` — pinning the axes the source states and gridding the rest.

---

## 13. Glossary

- **Earth-observation claim** — a factual statement derived from satellite data (e.g. a forest-loss percentage).
- **Claim** — myst's data model for a claim as originally stated: raw text, type, value, unit, source.
- **Methodology space** — the curated, versioned artifact enumerating all recognized axes of methodological choice and their defensible options for one claim type.
- **Axis (MethodologyAxis)** — one decision point in an analysis (e.g. canopy-cover threshold), with its list of defensible options.
- **Option (AxisOption)** — one defensible, citation-bound value on an axis.
- **MethodologyChoice** — one fully-specified methodology: exactly one option chosen per axis. One point in the methodology space.
- **Grid** — the set of methodologies to run; the cartesian product of the axes (with stated axes pinned).
- **Compile / Execute wall** — the freeze point: methodology is locked before any data or result is seen, preventing the verifier from tuning toward an answer.
- **PipelineSpec** — the frozen, declarative description of the verification to run.
- **Compiler** — the LLM step that turns a claim into a `PipelineSpec`.
- **Executor** — the step that runs the methodology grid over real satellite data.
- **Reproduction** — re-running an author's exact stated method. Usually impossible due to under-specification; not myst's primary mode.
- **Robustness** — whether a claim survives the whole space of defensible methodologies. myst's actual test.
- **Stated vs gridded** — methodology axes the source disclosed (pinned) versus those it did not (varied).
- **Verdict** — confirmed (robust) / challenged (not robust) / could-not-reproduce (under-specified).
- **Defensible range** — the spread of results across the methodology grid; an output, not an input.
- **The Index** — myst's public, versioned, permanent record of verifications and their provenance.
- **Calibration loop** — the accumulating record of (verification → ground truth) comparisons; the future home of myst's own machine learning.
- **Provenance** — the complete, inspectable trail of how a verdict was produced.

---

*End of document. Keep this in the repository (e.g. as `DESIGN.md` or `docs/master.md`) and update it as the project evolves — it is meant to be living, and to be the first thing a new contributor or working session reads.*
