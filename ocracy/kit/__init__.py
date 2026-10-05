"""The facade kit: the three helpers every fleet facade used to copy by hand.

One interface over many backends needs the same three mechanisms whatever the
backends do, and until this kit each facade (ocracy, scribed, denote, arioso,
illustration, aix, foley, falaw, voxy) carried its own drifting copy:

- :mod:`~ocracy.kit.translation` -- canonical kwargs -> native kwargs from a
  declared ``param_map``, with an unsupported-parameter policy that never drops
  silently (every drop and clamp comes back as a note);
- :mod:`~ocracy.kit.credentials` -- the key chain (explicit -> bound in context ->
  env -> store -> prompt), whose error names the env vars and where to get a key;
- :mod:`~ocracy.kit.install` -- per-OS install plans an agent can act on.

Usage::

    from ocracy.kit import make_translator, resolve_credential, using_credentials

    translate = make_translator(BACKEND_CONFIG["param_map"], backend="acme",
                                on_unsupported="note", always_raise=("seed",))
    native, notes = translate(canonical_kwargs)
    key = resolve_credential("acme", env_var="ACME_API_KEY", api_key=api_key)

Every module here is stdlib-only and imports nothing from ocracy outside
``ocracy.kit``, so the kit can move to its own distribution without a rewrite.
The decisions behind its shape are in ``docs/adr/0001-facade-kit.md``.
"""

from ocracy.kit.credentials import (
    MissingCredentialError,
    credential_help,
    credential_lines,
    current_credentials,
    env_var_names,
    resolve_credential,
    using_credentials,
)
from ocracy.kit.install import (
    Requirements,
    build_requirements,
    current_platform,
    run_install,
)
from ocracy.kit.translation import (
    OUT_OF_RANGE,
    POLICIES,
    Translation,
    UnsupportedParameter,
    check_range,
    make_translator,
)

__all__ = [
    # translation
    "make_translator",
    "Translation",
    "UnsupportedParameter",
    "POLICIES",
    "OUT_OF_RANGE",
    "check_range",
    # credentials
    "resolve_credential",
    "using_credentials",
    "current_credentials",
    "env_var_names",
    "credential_help",
    "credential_lines",
    "MissingCredentialError",
    # install plans
    "Requirements",
    "build_requirements",
    "run_install",
    "current_platform",
]
