---
name: licenta-checker
description: Review a LaTeX thesis against its assignment brief, Python codebase, and bibliography. Use whenever the user mentions thesis review, uncited references, citation validation, code-thesis alignment, or writing style issues.
argument-hint: <thesis-folder-path>
allowed-tools: Read, Write, Glob, Grep, Bash, WebSearch
---

# Thesis Checker

Systematically review all thesis materials in `$ARGUMENTS` across four areas: unused bibliography entries, citation accuracy, code–thesis alignment, and writing style.

## Expected Structure

```
$ARGUMENTS/
├── *.tex                  # main LaTeX source
├── *.bib                  # bibliography
├── raw_idea/
│   └── licenta_title.txt  # original assignment brief
└── src/                   # Python project code
    └── *.py
```

Abort with a clear message if `.tex`, `.bib`, or `raw_idea/licenta_title.txt` are missing.

## Procedure

### 1. Scan

```bash
find $ARGUMENTS -name "*.tex" -o -name "*.bib" -o -name "*.py" | grep -v __pycache__
cat $ARGUMENTS/raw_idea/licenta_title.txt
```

Read all `.tex` and `.bib` files fully. For Python files, read class/function definitions and imports.

---

### 2. Unused References

Extract every `@type{key, ...}` from `.bib`. Check each key against `\cite{key}`, `\citep{key}`, `\citet{key}`, and multi-key `\cite{key1, key2}` patterns across all `.tex` files.

**Output:**

```
📚 UNUSED REFERENCES — safe to delete from .bib
• smith2019ml — "Machine Learning Fundamentals", Smith et al.
• jones2021 — "Deep Learning", Jones
```

If none: `✅ All .bib entries are cited in the text.`

---

### 3. Unsupported Claims

Scan the `.tex` text for factual or technical claims that have no `\cite{}` nearby (within the same sentence or the one before). Ignore obvious definitions, the student's own contributions, and results sections where the student describes their own experiments.

For each unsupported claim, search online for a suitable reference and suggest it.

**Output:**

```
⚠️  Unsupported claim (§2.3): "BERT outperforms previous models on most NLP benchmarks."
    No citation found in the surrounding text.
    Suggested reference: Devlin et al., 2019 — "BERT: Pre-training of Deep Bidirectional
    Transformers for Language Understanding." https://arxiv.org/abs/1810.04805
```

---

### 4. Citation Accuracy

For each cited key, identify the claim made in the surrounding sentence. Search the source online (Google Scholar, arXiv, Semantic Scholar) using the title and authors from `.bib`. Check whether the claim is supported by the abstract or conclusions.

**Output per citation:**

```
✅ \cite{lecun1998} — claim matches source content.

⚠️  \cite{smith2020nlp} — source not found online. Verify title/author in .bib.

❌ \cite{jones2019} — claim says "exclusively depends on data quality";
   source treats it as one of several factors.
   Fix: "depends largely on data quality \cite{jones2019}."
```

Never fabricate source content. If a source cannot be found, say so explicitly.

---

### 4. Code–Thesis Alignment

Collect all named entities from `.tex`: class names, function names, module names, libraries, and behavioral claims ("the system detects X", "module Y handles Z").

```bash
grep -rn "^class \|^def \|^    def " $ARGUMENTS/src/ --include="*.py"
grep -rn "^import \|^from " $ARGUMENTS/src/ --include="*.py" | sort -u
```

Compare against what the thesis describes.

**Output:**

```
✅ Preprocessing module described in §3.2 → found: src/preprocessing.py, preprocess_text()
✅ Transformer architecture → found: import torch.nn.Transformer in src/model.py

⚠️  "The system includes a caching layer" (§4, p.23)
    → No caching found in code (no Redis, no @lru_cache, no local cache).
    Either implement it or remove the claim.

❌ "Custom DataLoader class manages batching" (§3)
    → Only torch.utils.data.DataLoader used; no subclass found.
    Fix: "PyTorch's DataLoader handles batching."
```

---

### 5. Writing Style

Flag passages with these issues:

| Issue | Example |
|-------|---------|
| Informal voice | "we did", "we put", "we said" |
| Vague language | "various methods", "some results", "better" |
| Redundancy | "in conclusion, we can conclude that" |
| Literal translation | "makes sense", "at the end of the day", "in terms of" |
| Overly long sentence | >50 words with no logical break |

**Output per issue:**

```
✍️  §2.1, paragraph 3:
  Original:  "We implemented a system that does various things related to
              text processing and we got good results."
  Issue:     Informal + vague ("various things", "good results").
  Suggested: "The system performs tokenisation, normalisation, and
              vectorisation, achieving an F1 score of 0.87 on the test set."
```

---

### 6. Summary

```
═══════════════════════════════════════════
THESIS REVIEW SUMMARY
═══════════════════════════════════════════
📚 Unused references:      X to delete
🔍 Citation issues:        X / Y checked
🔗 Code mismatches:        X found
✍️  Style issues:           X passages

High priority:
  1. ...
Medium priority:
  1. ...
```

## Notes

- Never edit files directly. Suggestions only.
- If a section is clean, say so briefly — don't list every passing check.
- Prioritise accuracy issues (wrong citations, missing code) over style issues.
- If the thesis is in Romanian, keep all suggestions in Romanian.
