# Abstract — Build Guide

Extended abstract for the AIMII @ IASEAI'26 workshop. Source is `main.tex`, compiled with [tectonic](https://tectonic-typesetting.github.io/).

## Structure

```
abstract/
  main.tex              # Full paper source
  main.pdf              # Compiled output (regenerate locally)
  context/              # Reference material (notes, prior reports, poster)
```

Figures are pulled from `../results/charts/` (PNG files) — no copies kept here.

## Install

```bash
brew install tectonic
```

Tectonic auto-downloads any required LaTeX packages on first compile (needs internet). Subsequent compiles are fully offline.

## Compile

```bash
cd abstract
tectonic main.tex
```

Output: `main.pdf` in the same directory.

## Making Changes

Edit `main.tex` directly, then recompile. Key locations:

| What | Where in `main.tex` |
|---|---|
| Title / authors | Lines 23–31 |
| Abstract blurb | `\begin{abstract}...\end{abstract}` |
| Section content | `\section{...}` blocks |
| Figures | `\includegraphics{../results/charts/chartN_*.png}` |
| Decomposition table | `tab:decomp` |
| Acknowledgements | `\begin{acks}...\end{acks}` |
| References | `\begin{thebibliography}...\end{thebibliography}` |

**Note on section heading case:** Section titles are written in ALL CAPS in the source (e.g. `\section{RESULTS}`) to match Overleaf/pdflatex rendering, since tectonic uses XeTeX which doesn't auto-uppercase them.
