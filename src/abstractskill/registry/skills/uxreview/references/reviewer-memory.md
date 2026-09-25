# UX Reviewer Memory

Use this file as compact shared memory for the `uxreview` skill. Read it when
the task turns on labels, workflow clarity, accessibility, source distinctions,
or approval decisions. Update it only during skill-maintenance work.

## Distilled Principles

- Favor recognition over recall. Show the choice, consequence, and next step in
  the interface instead of making users remember them.
  Source: NN/g usability heuristics and recognition-vs-recall guidance.
  https://www.nngroup.com/articles/ten-usability-heuristics/
  https://www.nngroup.com/articles/recognition-and-recall/
- Use plain visible labels and keep them close to the control they describe.
  Hidden/internal names are a usability risk, not just a copy problem.
  Source: GOV.UK text input and writing guidance.
  https://design-system.service.gov.uk/components/text-input/
  https://www.gov.uk/service-manual/design/writing-for-user-interfaces
- Error states must explain what went wrong and how to recover. Do not rely on
  color alone or vague failure text.
  Source: GOV.UK error-message guidance.
  https://design-system.service.gov.uk/components/error-message/
- Keyboard focus, semantic roles, and tab behavior are part of the product, not
  optional polish.
  Source: W3C WAI-ARIA Authoring Practices.
  https://www.w3.org/WAI/ARIA/apg/
  https://www.w3.org/WAI/ARIA/apg/patterns/tabs/
  https://www.w3.org/WAI/ARIA/apg/practices/keyboard-interface/

## Durable Lessons

- Naive users are harmed first by raw ids, ambiguous source/origin labels, and
  hidden consequences.
- Intermediate users lose confidence when similar things have different names or
  when workflow steps change meaning across screens.
- Expert users still need plain language. Their extra need is provenance,
  scale, and override clarity, not more jargon.
- Duplicate choices with slightly different wording are usually a design bug,
  not an advanced feature.
