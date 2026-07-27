# Skill seat — accumulated lessons and standing disciplines

## Writing discipline (operator-critical, 2026-07-26, commons c5798)

Laurent's critical room-wide instruction, binding on every post and
especially anything a human will read: write in clear, concise,
human-readable language. No invented shorthand ("door leg",
"seat-swept"), no receipts written as dense token strings. If a term
of art is genuinely needed, define it in the same sentence. This
applies to hub posts, commit messages, docs, and code comments alike.

Note: the entity-facing teaching surfaces (capability map, SKILL.md
registers) already follow a stronger version of this rule — plain
words in the entity's own register, no machinery jargon. The gap was
hub coordination posts; close it there.

## Hub operations

- The hub CLI occasionally wedges on a first call (hangs >30s where
  normal is <10s). Reliable workaround: kill the process and retry —
  the retry lands instantly. Seen repeatedly 2026-07-23/24.
- Addresseeless OPEN messages pin every member's unread view past
  their ack cursor (hub quirk, reported by tui 2026-07-24). Rows that
  keep re-rendering after acks are usually this, not unacked debt.
- Before answering an addressed ask, read the channel since the last
  known position — another session of the same seat, or a crossing
  post, may have already discharged it (the double-posting class).
- Ask-discharge is machine-checked on reply threading: a reply that
  names a message in TEXT but replies to a sibling id leaves the
  original row counted as unanswered. Discharge with a direct
  reply-to when the counter matters.

## Design-position discipline

- Every design position posted to the hub gets at least one fable5
  adversarial review first (seat floor; made room-wide unconditional
  by the operator 2026-07-21). The adversary regularly overturns
  load-bearing claims — treat "verify the citations against the tree"
  as the review's core job.
- Before parking work on "awaiting the operator's word", search
  whether the word was already given (2026-07-23 lesson: the identity
  build gate was already satisfied by prior rulings; re-asking angered
  the operator).
- Completion claims for UI work require an operator-posture
  walkthrough, full-page screenshots at realistic sizes, and a
  naive-user pass (operator done-rule, 2026-07-23). Plumbing proofs
  alone never count as done.
