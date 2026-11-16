# Jam production

Shipping an Unreal game in a few days with agents. Most of it applies to any deadline.

## Contents

- Before the jam
- The first day
- Gates and the cut ladder
- The devlog
- Submission checklist
- Sources

## Before the jam

Allowed preparation is usually tools only. Prove the whole chain on a throwaway project:

1. The engine installs and a C++ module compiles (Visual Studio toolset, Windows SDK and .NET
   Framework SDK as the engine's release notes list them).
2. An agent connects over MCP, makes one change, captures a picture of it, and saves.
3. The empty project packages in Shipping and the packaged build launches and takes a screenshot.
4. The zip is weighed against the jam's limit.
5. Video capture works at the required resolution, with game audio, on an unlocked desktop.

Read the official rules in full (eligibility, AI and asset rules, logo rules, video length and
resolution, size limits, who must submit). Write the rules that change how you work into a file
agents read. Declare everything made before the start (agent rule files, scripts, pipelines).

## The first day

- Make the first commit at the start time, so history shows the start.
- Build the hardest or riskiest system first, with real content, not a toy version. A system that
  works in a ten-minute test can fail with the real game on day three.
- Package and upload a draft build the same day. It finds cook errors, size problems and
  platform gaps while there is time.
- Set a frame cap, a self-play mode and a screenshot mode in the first builds.

## Gates and the cut ladder

Write gates in local time with what must be true at each, for example:

| Gate | Must be true |
|---|---|
| Day 1 evening | One full loop of the core mechanic plays in a packaged build |
| Day 2 | Every system in, rough; draft build uploaded |
| Day 3 evening | Feature freeze |
| Final day, early | Release candidate packaged, tested from the zip, video recorded from it |
| Final day, hours before the deadline | Submitted |

Write the cut ladder before you need it: the ordered list of features to drop when a gate slips by
more than an hour. Apply the next cut without debate. A submitted build without a feature beats a
complete build that missed the deadline. Every optional feature ships behind a switch so a late
failure is a config change, not a code change.

Estimates from agents run short. Count remaining work against remaining hours several times a
day, and read the clock rather than trusting anyone's sense of time.

## The devlog

Write it as you go, with real timestamps from the clock or commits. Record who decided what (human
or agent), what each tool made, what failed and the wrong first diagnosis, what was cut and why,
and what no human has checked. That list is honest and it is what readers and judges find most
useful. Provenance and cost ledgers make it cheap to write.

## Submission checklist

- [ ] Shipping build, zipped, under the size limit; unzipped and played from an empty folder.
- [ ] Windows build tested on Windows if any player or judge uses Windows.
- [ ] Web build (if any) passes the browser sweep; `index.html` at the zip root.
- [ ] Gameplay video at the required resolution and length, gameplay in the first seconds,
      recorded from the release build.
- [ ] Credits in the game match the asset and tool ledgers; licences checked; no logos the rules
      forbid.
- [ ] Third-party assets and AI tools listed; pre-jam work declared.
- [ ] A human played the release build start to finish, with sound on.
- [ ] The human submits; agents do not accept terms or submit on anyone's behalf.

## Sources

Field reports from the 2026 Epic AI MegaJam that shaped this skill:

- SkyCut: https://d-kol.itch.io/skycut/devlog/1782355/2026-epic-ai-megajam
- Reel Fleet: https://peterkoevariqa.itch.io/reel-fleet/devlog/1779775/reel-fleet-dev-log-four-days-one-developer-and-an-ai-coding-agent
- Forest Barrier: https://etherealexperiences.itch.io/forest-barrier/devlog/1781901/2026-epic-ai-megajam-devlog
- STILL: https://cosmintrica.itch.io/still/devlog/1782189/still-day-1-one-developer-a-team-of-ai-agents-and-an-unreal-editor-driven-through-mcp
- FIX IT YOURSELF!: https://e1-bomba.itch.io/fix-it-yourself/devlog/1781945/how-i-built-fix-it-yourself-in-4-days-with-ai-agents-epic-ai-megajam-2026
- Director's Blueprint: https://himdib-tech.itch.io/directors-blueprint/devlog/1782626/how-a-director-and-claude-code-built-directors-blueprint-in-unreal-engine-59-epic-ai-megajam-devlog
- Stunt Launch: https://gotagamee.itch.io/stunt-launch/devlog/1781541/how-stunt-launch-was-made-one-person-24-ai-sessions-one-weekend
- The Last Plan: https://mrv777.itch.io/the-last-plan/devlog/1781975/how-the-last-plan-was-built-and-where-the-tests-lied-glass-box-dev-log
- UE 5.9 MegaJam Preview known issues: https://forums.unrealengine.com/t/unreal-engine-5-9-megajam-preview/2852840
- Epic's Unreal skills plugin for Claude Code: https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin
