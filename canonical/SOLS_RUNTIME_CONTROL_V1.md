# SOLS RUNTIME CONTROL V1

SOLS = Self Optimization Layer System.

This file defines usable runtime control rules extracted from older patent-style notes and master-room memory.
Unsafe wording has been removed.
This layer does not modify the base AI model.
This layer does not claim perfect persona fixation.
This layer does not allow DONE without evidence.

## Purpose
Prevent AI work from drifting away from canonical files and real evidence.

## Correct runtime model

```text
new task
  -> create temporary task correction context
  -> force canonical read
  -> run drift / response / evidence gates
  -> execute only after gates pass
  -> write ledger and evidence
  -> discard temporary task context
```

## 1. Temporary correction context lifecycle
For each task, create a temporary correction context.
It may contain:

- current user instruction
- immutable canonical summary
- dynamic canonical state
- current blocker
- expected evidence
- allowed next action

It must not contain:

- emotional residue
- outdated assumptions
- unverified completion claims
- archive-only ideas treated as current facts

Lifecycle:

```text
CREATE -> FORCE_CANONICAL_READ -> EXECUTE_GATE -> EVIDENCE_CHECK -> LEDGER_WRITE -> DISCARD
```

If evidence is missing, the context ends as HOLD, not DONE.

## 2. Resonance threshold replacement
Old wording such as "persona fixation" or "100% output" is not allowed.
Use this operational replacement:

```text
Emotion + Direction + Decision
  -> increase strictness
  -> reduce prose
  -> force canonical read
  -> require executable output or evidence request
```

The AI does not become perfect.
The system becomes stricter.

## 3. Independent sync model
Cloud AI is compute only.
Canonical files, ledger, and evidence are the recoverable memory.

```text
Cloud AI output loses
GitHub canonical wins
Execution ledger wins
Reality evidence wins
NORI-san final judgment wins
```

The same answer must be reproducible from:

- immutable canonical
- dynamic canonical
- execution ledger
- evidence logs
- current real endpoint state

## 4. Segmentation gate
Archive and idea sources must not be treated as current implementation.

Blocked as current truth unless explicitly re-promoted:

- archive thoughts
- rough notes
- old screenshots
- old API paths
- old model names
- unverified local copies

Allowed current sources:

- canonical files
- execution ledger
- live Cloud Run describe output
- curl responses
- tests
- file hashes
- explicit NORI-san instruction

## 5. TTL / INVALID rule
Tasks expire if they do not reach real evidence.

Default TTL:

```text
ENGINE_DESIGNED: 24h
TASK_BUILT: 12h
REALITY_VERIFIED: 6h
```

If TTL expires without evidence:

```text
HOLD -> INVALID
```

INVALID means:

- do not continue from memory
- re-read canonical
- re-check files and live endpoints
- create a new ledger record

## 6. Status states
Use only:

- HOLD
- STOP
- INVALID
- LOCAL_PASS
- LIVE_PASS
- RELEASE_READY
- GO_CANDIDATE

DONE is not an AI decision word.

## 7. Required evidence before promotion

LOCAL_PASS requires:

- file exists
- syntax/test passed
- hash or line evidence exists

LIVE_PASS requires:

- live endpoint or deployed service evidence
- status/body marker evidence
- timestamp or revision evidence

RELEASE_READY requires:

- LIVE_PASS
- payment path checked if release touches revenue
- cancellation/legal path checked if user-facing
- ORE / NORI-san approval

## 8. Short form
Create a temporary correction context.
Force canonical read.
Block archive drift.
Expire unproven work.
Write ledger.
Require reality evidence.
Discard context after task.
