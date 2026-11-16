# Language models inside the game

Patterns for games where characters talk through a language model or speech is generated, as
opposed to agents that build the game.

## Contents

- Facts belong to the game
- Optional, bounded, offline-capable
- Latency
- Speech
- Safety and rules

## Facts belong to the game

The model acts; the game decides. A rules engine in C++ or data owns every fact: who was where,
what the clue is, what the player has done, what an NPC knows. The model receives the facts it may
use and returns lines, or a structured intent the game validates:

```
intent: none | move | pose | refuse | ready
target: one of the ids listed in the prompt
mood:   one of a fixed set
```

The game checks every field against what is allowed in the current state and ignores or retries
anything else. Nothing the model says changes the world unless the game accepts it. This keeps a
model from inventing clues, granting items or contradicting the plot, and it makes the game
testable with the model replaced by a scripted stub.

## Optional, bounded, offline-capable

- The game must work with no model: scripted lines or button-driven event prompts as the default
  path, the model as an enhancement.
- If players bring their own API key, never bundle one, cap calls per session, and validate every
  response before use. Scan the shipped files for keys before release.
- Local models (llama.cpp and similar) keep play offline and private. Ship or document the model,
  its size and memory needs, and degrade gracefully when the backend is missing or slow.
- Camera, microphone and face data stay on the player's machine; say so on the store page.

## Latency

Model replies take hundreds of milliseconds to seconds. Hide it in the design: countdowns,
thinking animations, a line of fixed text first. Never put a model call on a timing-critical path
(a shutter, a jump, a hit).

## Speech

- Local text-to-speech can voice every line of a large cast. Check each clip by machine (speech
  recognition against the script, a speaker-similarity score against the casting reference) and
  have a human listen to a sample.
- Tie each clip to the text it was recorded from. When text changes, the clip must be re-recorded
  or rejected; count rejected clips and fail the build above a small threshold, or a data mistake
  silences the game while every test passes.

## Safety and rules

- Jam and platform rules may restrict LLM use, trademarks and data collection; read them first.
- Keep prompts in the repository, versioned, and declare them.
- Write content limits into the prompts (for example no medical or legal advice, nothing outside
  the game's rating) and never try to get around the provider's safety systems.
