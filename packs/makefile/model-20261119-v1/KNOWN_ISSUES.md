# Makefile optimized known issues

- Fresh exact-span F1 is **93.79% on 16 files**; the unchanged exposed
  17-file cohort improves **89.14% → 92.87%**. Fresh validation is
  **83.03% on 14 other files**, legacy validation 90.44%. Small bounded cohorts
  do not certify every project, source style or dialect.
- Visible displays improve to 96.90%, but strict Golden regresses
  from 29/46 to **26/46**, with 86.24% base-span F1. Short uncommon directives,
  prefix values, BOM/Unicode comments, define bodies and modifiers remain weaker;
  Unicode and define visible examples regress slightly. Previous bundles remain
  available for reproducible comparison and rollback.
- Long/distant Shell state, quotes, nested substitutions, multiline defines and
  comments remain limited by 512-byte context. A Helm validation source with
  distant custom SHELL remains around 53% under conservative opacity semantics.
  No text is lost or executed even when prediction roles/boundaries are wrong.
- Scope remains common bounded GNU Make. Some `:::=`, static patterns with
  order-only prerequisites, computed names/nested defines and recipe here-docs
  are outside the unchanged offline oracle. Foreign/computed SHELL is opaque;
  only literal unconditional one-character recipe prefixes/reset are supervised.
  Complete BSD make, NMake, CMake, Automake input and arbitrary Windows shells
  are not guaranteed.
- Joint BIO decoding uses neural logits and training-fitted matrices only;
  canonical union joins touching equal strings without bridging whitespace gaps.
  No source spelling, parser, regex, included-file loading, variable expansion,
  dependency resolution or execution repairs inference. Browser/native parity
  establishes consistency, not semantic perfection or complete Markdown composition.
