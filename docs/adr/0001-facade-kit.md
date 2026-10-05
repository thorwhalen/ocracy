# ADR 0001 — The facade kit lives in `ocracy.kit`

- **Status:** accepted, 2026-10-05
- **Issue:** [thorwhalen/ocracy#7](https://github.com/thorwhalen/ocracy/issues/7)
- **Scope:** the param_map translator, the credential chain, install plans

## Context

The fleet has about ten facades: one interface over many providers (ocracy for OCR, scribed for transcription, arioso for music, foley for sound effects, falaw over fal.ai, voxy for speech, illustration, aix, denote…). Each needs the same three mechanisms, and each got them by copying another facade's files and editing them:

| Mechanism | Copies |
|---|---|
| canonical → native kwargs translator with an unsupported-parameter policy | ocracy, scribed, denote (identical), arioso, illustration, foley (forks) |
| credential chain (explicit → … → env → …) with a helpful missing-key error | ocracy, scribed (identical), illustration, aix, falaw (three inline chains), voxy, foley (two inline chains) |
| per-OS install plans for optional backends | ocracy, scribed (identical mechanism) |

The copies drifted. A diff of every copy found real behavioural divergences, and six bugs that existed in some copies and not others (an explicitly unsupported parameter never raising under `raise`; a policy bypass; `.env` searched from the wrong directory; a store layer swallowing every exception; a health check ignoring the BYO key; three different ElevenLabs env-var orders). The full inventory is kept with the working notes for this change; its tables are summarised below.

## Decision

One stdlib-only subpackage, **`ocracy.kit`**, with three modules:

- `ocracy.kit.translation` — `make_translator(param_map, *, backend, on_unsupported, always_raise, vocabulary, passthrough, skip_none, out_of_range, stacklevel)` returns `translate(kwargs, *, on_unsupported=None) -> Translation(kwargs, notes, dropped)`. A `Translation` is read by attribute; it deliberately does not unpack, because the copies returned `(native, notes)` and `(native, dropped)` and a tuple would let either be silently wrong.
- `ocracy.kit.credentials` — `resolve_credential(provider, *, api_key, env_var, provider_env_vars, guidance, store, dotenv, prompt_if_missing, required, error, hint)`, `using_credentials(...)` (a `ContextVar` binding for bring-your-own-key), `credential_help`, `credential_lines`, `MissingCredentialError`.
- `ocracy.kit.install` — `Requirements`, `build_requirements(...)`, `run_install(...)`, `current_platform()`.

ocracy's own `translation.py`, `credentials.py` and `install.py` keep their public API and become thin bindings of ocracy's data (provider tables, recipes, registry lookups) to the kit. An old-versus-new comparison over every backend and ledger record (128 install plans, every dry-run result, 130 translation cases) found no difference.

### Every divergence, and what the kit does with it

A divergence that a consumer depends on became a seam: one keyword argument, defaulting to ocracy's behaviour. A divergence that was a bug or an accident got one canonical behaviour, recorded here.

| Divergence between copies | Kit | Kind |
|---|---|---|
| Spec forms: `None`, dict with `native_name` (ocracy, arioso) or `name` (illustration), bare `str` rename, bare callable | all accepted; `native_name` and `name` together must agree. A third-party spec that used `name` as a mere label would now rename. | canonical (superset) |
| `adapter_handled: True` (arioso): the value goes to the adapter under its canonical name, whatever `native_name` says | same | canonical |
| `native_name: None` in a dict silently dropped (arioso) | same as a bare `None`: unsupported, through the policy | bug fixed |
| `None` spec never raises under `raise` (ocracy, scribed, denote) | raises | bug fixed |
| Policy vocabulary: warn/raise/ignore vs raise/warn/note | `raise`, `warn`, `note`, `ignore` (`ignore` = `note`). An unknown policy now raises when the translator is built (it used to behave like `ignore`). | seam: `on_unsupported` |
| Message text | foley's wording: `name=value is not supported by <backend>; dropped` / `is not a parameter of` for unknown names. ocracy's old `Unsupported parameter: 'x'. Supported: [...]` (`raise`) and `... will be ignored.` (`warn`) are gone; the error is `UnsupportedParameter`, a `ValueError`. | canonical |
| Values in notes, warnings and errors | shortened (`reprlib`, 80 chars) and **secret-free, erring toward hiding**: a value is `<redacted>` when its parameter name or a mapping key (any depth) contains a secret segment — split on `_ - .`, spaces and camelCase: `key`, `token`, `auth`, `secret`, `password`, `pwd`, `credentials`, `signature`, `private`, `session`… (`is_secret_name`) — or when a string is shaped like a credential (`Bearer …`, `https://user:pw@host`, `?key=…`); anything that is not plain data (an object, bytes) shows only its type. Hiding an ordinary value (`key_frames`, a musical `key`) costs a drop note its value; a leak costs a key. Best-effort: a secret passed under an innocent name with no recognisable shape can still show. Notes land in results that get stored and logged. | canonical (review blocker) |
| Which frame a `warn` blames | `stacklevel=` (counted from the code calling `translate`); ocracy's wrappers keep the frame they always blamed | seam |
| Drops returned to the caller: never / names / notes | always both: `.notes` and `.dropped` | canonical (never silent) |
| Meaning-carrying params: arioso's `lyrics`, foley's `seed` / `negative_prompt` | `always_raise=`; an explicit per-call `on_unsupported=` wins (foley); a facade that never exposes the per-call override gets arioso's "always" | seam |
| A value left at its vocabulary default is "not asked for" (foley) | `vocabulary=` (also drives "not supported by" vs "not a parameter of") | seam |
| `None` means unset, even for supported params (illustration) | `skip_none=` | seam |
| Adapter-only params passed through (arioso `passthrough` / `adapter_handled`) | `passthrough=`; `adapter_handled` is just an identity spec | seam |
| Defaults injected for omitted params (ocracy) | spec `default` | canonical |
| Ranges: ocracy `validate_param` raises (but was never called), illustration drops on `choices`, foley clamps `duration` | spec `min`/`max`/`choices` + `out_of_range='raise'|'clamp'|'drop'` + `unit` for the clamp note; the translator's `out_of_range=` is the default for specs that do not say (illustration: `drop`). `None` is "unset" and always in range, so `validate_param(None, choices=…)` no longer raises. A clamped value is the bound itself (foley's bounds are floats, so foley still gets floats). | seam (per spec + per translator) |
| Exceptions: `ValueError` vs foley's `UnsupportedParameter(ValueError)` | `UnsupportedParameter(ValueError)`; a consumer re-exports it | canonical |
| Explicit `api_key=""`: absent (5 copies) vs given (foley) | absent | canonical (foley's behaviour changes; noted on its PR) |
| ContextVar binding: per-provider dict (illustration), single fal key (falaw), none (others) | one per-provider binding, nested overlay, falsy ignored, inert unless used. **Shared by provider id across every package** (bind `openai` once, every facade calling OpenAI sees it), so provider ids name the account, not the facade. It follows the context: `asyncio` tasks and `to_thread` see it; a bare thread or executor does not (submit `copy_context().run`). | canonical (superset) |
| Binding key in ocracy: adapters resolved `openai` / `anthropic`, `status.is_set_up` resolved the backend id | both read `BACKEND_CONFIG["credential_provider"]` (default: the backend id) | bug fixed |
| Env vars: explicit first then the provider table, ordered, de-duplicated | `env_var=` + `provider_env_vars=`, order preserved (so voxy keeps `ELEVEN_API_KEY` first) | seam (data) |
| `.env`: on every miss from the package directory (ocracy, scribed) vs once from the cwd (aix) | `dotenv=True` loads the `.env` found from the cwd on every environment miss, then looks again (so a key added mid-session, or a notebook that `chdir`s, is found), never overriding. Like any `.env` loader it writes to `os.environ`, which every later reader in the process sees. | seam; ocracy's search directory fixed |
| Store: config2py with `except Exception` (aix, illustration) | `store=` any mapping; only `KeyError` moves on | seam; bug fixed |
| Prompt result: set in `os.environ` (ocracy) vs persisted to the store (aix) | persisted to `store` when it is a `MutableMapping`, else `os.environ` | canonical rule |
| Missing-key exception: `MissingCredentialError`, `RuntimeError`, `SourceConfigurationError`, illustration's / aix's keyword-constructed errors | `error=` (called with the message only, so any exception class works); when it builds the kit's `MissingCredentialError` or a subclass, the kit fills its `provider`, `env_vars`, `get_key_url` attributes | seam |
| Explicit credentials in ocracy: remote adapters read `api_key` / `app_key` / `app_id` from their kwargs, but no `param_map` declared them, so `ocracy.ocr(..., api_key=...)` was always dropped with a warning | `BaseOcrAdapter.ADAPTER_KWARGS` pass them through untranslated on a remote backend; a local backend drops them with a redacted note (a local engine forwarding `**extra` to its library would choke on them) | bug fixed (found by the review) |
| Extra context in the message (falaw: "the pricing endpoint is free but authenticated") | `hint=` | seam |
| Install plans: package name, recipes, "Lighter" vs "Faster/lighter alternative", the Verify line | `package=`, `recipe=`, `alternative_label=`, `verify_command=`. A `Requirements` built by hand shows no `Verify:` line unless given one. | seams (data) |
| Credential lines with several env vars (scribed's `api_env_var` lists) | `export A / B` | canonical |
| `requirements(gpu=)` | had no effect in either copy (the recipe's GPU line was always shown); kept as a no-op in ocracy's signature, not in the kit | canonical |

### Why `ocracy.kit`, and what that costs a consumer

The alternatives were a new distribution, `i2` (signature transforms), and a second top-level package inside the ocracy wheel. A new distribution is the end state if more than facades start to need the kit; until then a subpackage costs nothing to create, and every kit module imports only the standard library and `ocracy.kit` (a test enforces it), so moving it later is a `git mv` plus a re-export. `i2` would carry the policy and the chain into a package with many dependents, where every observable behaviour gets depended on (Hyrum's law). A second top-level name in the wheel would claim a PyPI-like name nobody owns.

The cost is that `import ocracy.kit` runs `ocracy/__init__.py`. Two changes keep that small: `__version__` is computed on first access (PEP 562, and listed by `dir()`), so `import ocracy` no longer loads `importlib.metadata`, and `subprocess` is imported only by an actual install. Measured on the maintainer's Mac, `python -X importtime`, median of 7 runs, cumulative time of the last import:

| Imported first | `import ocracy` on main | `import ocracy.kit` on this branch |
|---|---|---|
| nothing (cold) | 43.5 ms | 16.9 ms |
| `foley` | 41.3 ms | 5.4 ms |
| `falaw` | 18.3 ms | 5.8 ms |
| `voxy` | 3.7 ms | 6.0 ms |
| `scribed` | 3.4 ms | 6.1 ms |

The right comparison for a consumer is the last column against zero: its own copy cost nothing extra, so depending on the kit adds about **5–6 ms** to its import when imported at module level (voxy and scribed already load `importlib.metadata`, so for them the lazy version saves nothing). About half of that is ocracy's root re-exports (`base`, `catalog`, `registry`, `services`, `make_backend`, `install`, `status`), which do no I/O at import (no `backends.json` read, no package scan). Making the root lazy would save roughly another 3 ms per consumer; it changes ocracy's import surface for everyone, so it is a separate, measured change: [#11](https://github.com/thorwhalen/ocracy/issues/11). A test pins that importing the kit loads no Pillow, numpy, pandas, requests, torch, `importlib.metadata`, `subprocess`, `dotenv` or any `ocracy.backends` module.

### Moving the kit to its own distribution later

Every kit module imports only the standard library and `ocracy.kit`, so the code moves with a `git mv`. Two things do not move for free, and whoever does it must handle both: ocracy then depends on the new distribution (the first entry in its `dependencies`, which is otherwise empty on purpose), and the binding `ContextVar` and the two exception classes must exist in exactly one module, with `ocracy.kit` re-exporting them, or a key bound through one import path is invisible through the other and `except UnsupportedParameter` stops matching.

Three small public pieces exist for a named consumer, not for generality: `check_range` backs `validate_param` (ocracy, scribed, denote; denote's tests call it), `build_requirements(platform=)` renders a plan for another OS (docs, tests), and `stacklevel=` lets each wrapper keep the frame its warnings always blamed.

## Not in v1

- **The cost gate** (foley's `cost.py`: stacked budgets, atomic reserve/settle, `scoped_iter`) and **metered LLM calls**. foley proposed both on #7. The budget exists in one package, and the two estimate conventions (falaw's per-model `count/seconds/megapixels/tokens`, foley's per-config `free/per_call/per_second`) have different shapes. By the rule of three and "duplication is cheaper than the wrong abstraction", it waits for a second budget: [#9](https://github.com/thorwhalen/ocracy/issues/9).
- **The ledger loader** (`catalog.py`, ocracy and scribed: 97 lines of diff). Optional in #7: [#10](https://github.com/thorwhalen/ocracy/issues/10).
- **`make_backend.py`** (adapter base class, scaffolding): domain-specific per facade.

## Consequences

- New facades import the kit instead of copying files; the facade-design skill's "copy ocracy's three files" advice becomes "import `ocracy.kit`".
- Draft swap PRs go to foley, falaw and voxy. scribed, denote, arioso, illustration and aix can swap the same way; each is listed on #7.
- `BaseOcrAdapter.read` now records every dropped parameter in `result.meta["notes"]` (it still warns): ocracy adopts foley's "drops reach the result" behaviour.
- Three independent adversarial reviews (API seam completeness, hidden behaviour differences, import-time cost) ran before landing; every confirmed finding is either fixed above or recorded here as a deliberate change.
- `testpaths` now includes `ocracy`, so CI's `--doctest-modules` runs the kit's examples, and `doctest_optionflags` matches what CI passes.
