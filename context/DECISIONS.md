# DECISIONS LOG — Multimodal Fake News Detection

> Record important project decisions and rationale here.
> Format: Date, Decision, Rationale, Decided By

---

## D001 — 2026-09-07 — Dataset Selection: Fakeddit

**Decision:** Use Fakeddit as the primary dataset.

**Rationale:**
- Over 1 million multimodal samples (text + image)
- Supports 2-way, 3-way, and 6-way classification
- Publicly available with clear usage guidelines
- Established benchmark with published baselines (LREC 2020)
- Includes `has_image` column for filtering multimodal samples
- Active research community using this dataset

**Decided By:** Team (project specification)

---

## D002 — 2026-09-07 — Initial Modality Scope: Text + Image Only

**Decision:** Restrict initial implementation to text + image modality only.

**Rationale:**
- Aligns with Fakeddit's core multimodal design
- Keeps the project manageable within 3–5 months
- Video, AI-generated content, and other modalities are future extensions only
- The original Fakeddit paper's experiments used text + image

**Decided By:** Team (project specification)

---

## D003 — 2026-09-07 — Baseline-First Approach

**Decision:** Establish text-only, image-only, and text+image baselines before attempting any improvement.

**Rationale:**
- Cannot identify genuine research gaps without understanding baseline performance
- Need to analyze where the baseline fails before proposing improvements
- Prevents premature optimization or unfounded claims
- Standard scientific methodology

**Decided By:** Team (project specification)

---

## D004 — 2026-09-07 — Project Structure and Shared Context System

**Decision:** Use `context/` directory with PROJECT_CONTEXT.md, DECISIONS.md, and EXPERIMENT_LOG.md as shared memory across all AI agents and team members.

**Rationale:**
- Multiple AI tools (Claude Code, Codex, Antigravity, etc.) may be used
- Need a single source of truth that any agent can read
- Prevents conflicting information or duplicated work
- Standard practice for multi-agent collaboration

**Decided By:** Team (project specification)

---

## D005 — 2026-09-07 — Do Not Download Full Images Immediately

**Decision:** First inspect TSV metadata to determine multimodal sample counts and storage requirements before downloading the full image archive.

**Rationale:**
- Full image archive could be very large (tens of GB)
- MacBook Air has only 512 GB total storage
- May only need a subset for initial baselines
- Need to understand data characteristics before committing storage

**Decided By:** Team (project specification)

---

## D006 — 2026-09-07 — Use Public Dataset Only

**Decision:** Use only the public train/validate/test splits. Do NOT use private test sets.

**Rationale:**
- Private test sets have no labels — useless for our experiments
- Following official dataset guidelines
- Academic integrity requirement

**Decided By:** Team (project specification)

## D007 — 2026-09-07 — First Baseline Image Subset

**Decision:** We will use a smaller subset (e.g. 50k-100k samples) of the multimodal dataset for the initial baseline rather than the full ~771k usable samples.

**Rationale:**
- The full image dataset for multimodal samples is estimated to be ~29.44 GB.
- While manageable on a 512 GB MacBook Air, training on ~771k images for initial baselines would be slow and computationally expensive.
- A balanced subset allows for faster iteration and debugging of the text+image pipeline.
- We will download only the required images for the chosen subset using the `image_url` column, or extract them from the archive later if needed.

**Decided By:** Antigravity (Data Strategy)

---
