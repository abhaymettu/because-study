# How runs are isolated, and how we know

A study of instruction following is void if the agent also sees the operator's own instructions. Every run here uses a
subscription login on a working developer machine, which is the hardest case, so isolation is measured, not assumed.

## What each run gets

| Surface | Control |
|---|---|
| User `CLAUDE.md` | `claudeMdExcludes` over the home directory. `--setting-sources project` alone does not remove it. |
| User settings and hooks | `--setting-sources project`, `disableAllHooks` |
| Memory | `autoMemoryEnabled: false`, `--no-session-persistence` |
| MCP servers and connectors | `--strict-mcp-config --mcp-config '{"mcpServers":{}}'`. `--tools` alone leaves them live. |
| Skills | No `Skill` tool in Study 1, and its 40 kept captures hold no skill listing. Studies 2, 2b and 2c use a library built inside the run's repo, listed with the CLI's bundled skills. |
| Environment | Started from an empty environment with a short allowlist. Study 2c rows with a raised budget add one variable, `SLASH_COMMAND_TOOL_CHAR_BUDGET`, through `run_agent`'s `env` option. |
| Shell profile | The Bash tool sources the user's profile, so aliases and functions reach the agent. A wrapper shell gives tool calls an empty `HOME`. The CLI keeps the real `HOME` because the login needs it. |
| Git identity | Repo-level `Dev` identity, and `GIT_CONFIG_GLOBAL=/dev/null` |
| Account identity | The CLI puts the login's email in the prompt and `ls -l` prints the OS user. The capture proxy rewrites both before the request leaves. |
| Working directory | A fresh directory under the run root, with no instruction files in any ancestor. The run root is `/private/tmp/wk`. `BECAUSE_RUN_ROOT` overrides it, and it falls back to `/tmp/wk` where `/private/tmp` does not exist. `TMPDIR` is the run root's parent. |

Pilots found three of these by looking at captured requests and transcripts: the email, the git user, and the shell
profile, which showed up as a directory listing in the format of a user's `ls` alias. All three were fixed before the
preregistration.

## Proof

`make isolation` sends one prompt twice through the capture proxy, once isolated and once as a plain `claude -p`, then
looks in the outgoing requests for lines of the operator's own instruction files and memory index, and for their skill
names. Only counts are written. One machine, 2026-11-01:

| | Isolated | Plain `claude -p` |
|---|---|---|
| Instruction and memory lines found, of 231 | 0 | 219 |
| Skill names found, of 85 | 1 | 73 |
| Tools offered | 6 | 181 |
| MCP tools offered | 0 | 150 |

The one skill name found in the isolated run is the ordinary word "research", in Claude Code's default system prompt. It
is not a skill listing. The plain column is the negative control: the same scan fires when the setup is present.

During the study, every request of every run goes through a scan for identity and setup strings
(`harness/agent_run.py`). A run that trips it is excluded and counted.

## What remains

Runs on one account share its `skillUsage`, because the login needs the real config. A Skill call promotes that name in later runs' listings, so runs in Studies 2 and 2b are not fully independent (`docs/LISTING-MECHANISM.md`). Target names are unique per run, so this reaches only distractors.

Claude Code's own default system prompt and its preamble around the instruction file are part of the treatment
environment, on purpose. Those are what every user gets. The study's tool list is shorter than the default, which changes
the system prompt somewhat from what an interactive user sees. The system prompt hash is logged per run.

## Rechecked and not rechecked

Rechecked on 2026-11-02 by reading `harness/agent_run.py`, with no agent started. Every row of the table above matches the code. The proof in `results/isolation.json` was run at `/private/tmp/wk` before the first freeze, and that is still the default run root on a Mac. Nothing named `CLAUDE.md`, `AGENTS.md` or `.claude` exists in `/private/tmp/wk`, `/private/tmp`, `/private` or `/` on this machine.

Not rechecked, since it needs an agent run:

- The counts in the proof table have not been measured again since 2026-11-01.
- `make isolation` has not been run at a `BECAUSE_RUN_ROOT` other than the default, or on Linux.
- `make isolation` does not cover a raised budget, or the `Skill` tool, since its run offers six tools. The per-request scan does cover those rows.
- The Haiku batch and Study 2c were running during this recheck, and this recheck read neither.
