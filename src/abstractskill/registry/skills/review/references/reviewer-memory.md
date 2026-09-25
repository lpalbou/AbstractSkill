# Review Skill Memory

Use this file as compact shared memory for the `review` skill. Read it when a
review spans code, UX, architecture, or operations. Update it only during
skill-maintenance work.

## Distilled Principles

- Evidence beats intuition. Reviews should cite observed artifacts, not vibes.
- Ownership and language boundaries matter. Mixed models and fuzzy boundaries
  create long-term confusion and bugs.
  Source: Martin Fowler on bounded contexts.
  https://martinfowler.com/bliki/BoundedContext.html
- Important platform decisions should retain explicit context and consequences.
  Source: Martin Fowler on ADRs.
  https://martinfowler.com/bliki/ArchitectureDecisionRecord.html
- Operability is part of design quality: observability, recovery, and support
  burden should be reviewed with feature behavior.
  Source: AWS Well-Architected operational excellence and Google SRE guidance.
  https://docs.aws.amazon.com/wellarchitected/latest/framework/operational-excellence.html
  https://sre.google/sre-book/monitoring-distributed-systems/

## Durable Lessons

- A review without a verdict becomes advisory noise.
- A UI review without a visible artifact is weaker than a UI review with one;
  say that explicitly.
- Architecture-fit failures often surface first as terminology drift or
  duplicated concepts in the product.
- If no reviewer can name the strongest opposing argument, the review is too
  shallow.
