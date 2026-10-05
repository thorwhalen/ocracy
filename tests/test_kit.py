"""Tests for the facade kit (``ocracy.kit``): the translator, the credential chain,
install plans, and the import hygiene that lets other facades depend on it.

Each ``Consumer:`` section encodes how one fleet facade uses (or will use) the kit,
with the exact behaviour that facade's own tests pin, so a kit change that would
break a consumer fails here first.
"""

import ast
import os
import subprocess
import sys
import threading
import warnings
from pathlib import Path

import pytest

import ocracy.kit.credentials as kit_credentials
from ocracy.kit import (
    MissingCredentialError,
    Requirements,
    Translation,
    UnsupportedParameter,
    build_requirements,
    check_range,
    credential_help,
    credential_lines,
    current_credentials,
    env_var_names,
    make_translator,
    resolve_credential,
    run_install,
    using_credentials,
)

KIT_DIR = Path(__file__).resolve().parent.parent / "ocracy" / "kit"


# ---------------------------------------------------------------------------
# Translator: spec forms and the result
# ---------------------------------------------------------------------------


def test_spec_forms_rename_coerce_default():
    translate = make_translator(
        {
            "languages": {"native_name": "lang", "coerce": "+".join},
            "size": "img_size",  # a str is a rename
            "scale": lambda v: v * 100,  # a callable coerces, keeps the name
            "mode": {"default": "fast"},  # injected when omitted
        }
    )
    t = translate({"languages": ["eng", "fra"], "size": 3, "scale": 0.5})
    assert t.kwargs == {"lang": "eng+fra", "img_size": 3, "scale": 50.0, "mode": "fast"}
    assert t.notes == [] and t.dropped == []


def test_translation_is_explicit_and_not_a_tuple():
    t = make_translator({"a": {}}, on_unsupported="note")({"a": 1, "b": 2})
    assert isinstance(t, Translation)
    assert t.kwargs == {"a": 1}
    assert t.notes == ["b=2 is not a parameter of this backend; dropped"]
    assert t.dropped == ["b"]
    with pytest.raises(TypeError):  # (kwargs, notes) vs (kwargs, dropped): no guessing
        native, notes = t


def test_secret_values_never_reach_notes_warnings_or_errors():
    translate = make_translator({}, backend="b", on_unsupported="warn")
    with pytest.warns(UserWarning) as rec:
        t = translate({"api_key": "sk-SECRET", "auth_token": "tk-SECRET", "x": "y"})
    shown = " ".join([*t.notes, *(str(w.message) for w in rec)])
    assert "SECRET" not in shown and "api_key=<redacted>" in shown
    with pytest.raises(UnsupportedParameter) as ei:
        translate({"password": "pw-SECRET"}, on_unsupported="raise")
    assert "SECRET" not in str(ei.value)


def test_secrets_nested_shaped_or_in_range_errors_are_redacted():
    translate = make_translator({}, on_unsupported="note")
    t = translate(
        {
            "headers": {"Authorization": "Bearer sk-SECRET", "Accept": "json"},
            "authorization": "Basic SECRET",
            "options": {"retries": 2, "auth": {"token": "SECRET"}},
            "bearer_like": "Bearer SECRET",
        }
    )
    joined = " ".join(t.notes)
    assert "SECRET" not in joined
    assert "'Accept': 'json'" in joined and "'retries': 2" in joined
    with pytest.raises(ValueError) as ei:
        make_translator({"token": {"choices": ["a"]}})({"token": "sk-SECRET"})
    assert "SECRET" not in str(ei.value)
    with pytest.raises(ValueError) as ei:
        check_range("db_password", "pw-SECRET", {"max": "a"})
    assert "SECRET" not in str(ei.value)


def test_only_names_ending_in_a_secret_word_are_redacted():
    t = make_translator({}, on_unsupported="note")(
        {"key_frames": 12, "token_budget": 5, "access_token": "tk", "key": "k"}
    )
    assert [n.split(" ")[0] for n in t.notes] == [
        "key_frames=12",
        "token_budget=5",
        "access_token=<redacted>",
        "key=<redacted>",
    ]


def test_long_and_unrepresentable_values_are_shortened():
    class NoRepr:
        def __repr__(self):
            raise RuntimeError("no repr")

    t = make_translator({}, on_unsupported="note")(
        {"blob": b"x" * 10_000, "o": NoRepr()}
    )
    assert len(t.notes[0]) < 200
    assert t.notes[1].startswith("o=<NoRepr")  # a failing repr still yields a note


def test_warning_points_at_the_requested_frame():
    translate = make_translator({}, stacklevel=1)

    def caller():
        return translate({"x": 1})  # stacklevel=1 blames this line

    with pytest.warns(UserWarning) as rec:
        caller()
    assert rec[0].lineno == caller.__code__.co_firstlineno + 1


def test_caller_value_beats_default():
    translate = make_translator({"mode": {"default": "fast"}})
    assert translate({"mode": "slow"}).kwargs == {"mode": "slow"}


def test_malformed_spec_fails_when_the_translator_is_built():
    with pytest.raises(TypeError, match="Invalid param_map spec"):
        make_translator({"x": 42})
    with pytest.raises(TypeError, match="native_name only"):
        make_translator({"x": {"native_name": "a", "name": "b"}})
    with pytest.raises(ValueError, match="out_of_range"):
        make_translator({"x": {"out_of_range": "wrap"}})
    with pytest.raises(ValueError, match="needs min/max"):
        make_translator({"x": {"choices": {1}, "out_of_range": "clamp"}})


def test_unknown_policy_rejected_at_build_and_call():
    with pytest.raises(ValueError, match="on_unsupported"):
        make_translator({}, on_unsupported="silently")
    translate = make_translator({})
    with pytest.raises(ValueError, match="on_unsupported"):
        translate({"x": 1}, on_unsupported="silently")


# ---------------------------------------------------------------------------
# Translator: the unsupported-parameter policy
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("spec", [None, {"native_name": None}])
def test_explicitly_unsupported_raises_under_raise(spec):
    # The ocracy/scribed/denote copies silently dropped a None spec under 'raise',
    # and arioso's native_name=None bypassed the policy entirely.
    translate = make_translator({"dpi": spec}, backend="tess", on_unsupported="raise")
    with pytest.raises(UnsupportedParameter, match="dpi=300 is not supported by tess"):
        translate({"dpi": 300})


def test_warn_drops_notes_and_warns():
    translate = make_translator({"dpi": None}, backend="tess")  # default policy: warn
    with pytest.warns(UserWarning, match="dpi=300 is not supported by tess; dropped"):
        t = translate({"dpi": 300})
    assert t.kwargs == {} and t.notes == ["dpi=300 is not supported by tess; dropped"]


@pytest.mark.parametrize("policy", ["note", "ignore"])
def test_note_and_ignore_drop_without_warning_but_never_silently(policy):
    translate = make_translator({"dpi": None}, on_unsupported=policy)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        t = translate({"dpi": 300})
    assert t.dropped == ["dpi"] and t.notes


def test_unsupported_parameter_is_a_value_error():
    assert issubclass(UnsupportedParameter, ValueError)


def test_always_raise_beats_the_backend_policy_but_not_the_callers():
    translate = make_translator(
        {"prompt": {}}, backend="b", on_unsupported="note", always_raise=("seed",)
    )
    with pytest.raises(UnsupportedParameter, match="would change what you get"):
        translate({"seed": 7})
    t = translate({"seed": 7}, on_unsupported="note")  # the caller chose explicitly
    assert t.dropped == ["seed"]


def test_caller_policy_overrides_backend_policy():
    translate = make_translator({}, on_unsupported="note")
    with pytest.raises(UnsupportedParameter):
        translate({"x": 1}, on_unsupported="raise")


def test_vocabulary_not_asked_for_and_wording():
    vocab = {"loop": False, "steps": None, "seed": None}
    translate = make_translator({"prompt": {}}, on_unsupported="note", vocabulary=vocab)
    t = translate({"loop": False, "steps": None, "seed": 3, "colour": "red"})
    assert t.dropped == ["seed", "colour"]  # loop/steps were left at their defaults
    assert t.notes == [
        "seed=3 is not supported by this backend; dropped",
        "colour='red' is not a parameter of this backend; dropped",
    ]


def test_without_vocabulary_none_is_still_reported():
    t = make_translator({}, on_unsupported="note")({"steps": None})
    assert t.dropped == ["steps"]


def test_uncomparable_value_counts_as_asked_for():
    class Weird:
        def __eq__(self, other):
            raise RuntimeError("no")

    t = make_translator({}, on_unsupported="note", vocabulary={"w": 1})({"w": Weird()})
    assert t.dropped == ["w"]


def test_passthrough_and_skip_none():
    translate = make_translator(
        {"size": "img_size"},
        on_unsupported="raise",
        passthrough=("client",),
        skip_none=True,
    )
    t = translate({"client": "c", "size": None, "license": None})
    assert t.kwargs == {"client": "c"} and t.notes == []


# ---------------------------------------------------------------------------
# Translator: ranges
# ---------------------------------------------------------------------------


def test_out_of_range_raise_is_the_default_and_matches_validate_param():
    translate = make_translator({"t": {"min": 0.0, "max": 1.0}})
    with pytest.raises(ValueError, match="below minimum"):
        translate({"t": -0.1})
    with pytest.raises(ValueError, match="above maximum"):
        translate({"t": 1.5})
    with pytest.raises(ValueError, match=r"not in \['a'\]"):
        make_translator({"c": {"choices": ["a"]}})({"c": "b"})


def test_clamp_notes_with_unit_and_none_is_unset():
    translate = make_translator(
        {"duration": {"min": 0.5, "max": 30.0, "out_of_range": "clamp", "unit": "s"}},
        backend="elevenlabs",
    )
    t = translate({"duration": 45})
    assert t.kwargs == {"duration": 30.0}
    assert t.notes == [
        "duration=45 s is outside elevenlabs's [0.5, 30.0] s window; clamped to 30 s"
    ]
    assert translate({"duration": None}).kwargs == {"duration": None}
    assert translate({"duration": 2}).notes == []


def test_out_of_range_drop_follows_the_policy():
    translate = make_translator(
        {"orientation": {"choices": {"landscape"}, "out_of_range": "drop"}},
        on_unsupported="note",
    )
    t = translate({"orientation": "square"})
    assert t.kwargs == {} and t.dropped == ["orientation"]
    assert "outside" in t.notes[0]


def test_translator_level_out_of_range_default():
    translate = make_translator(
        {"o": {"choices": {"a"}}, "n": {"max": 1, "out_of_range": "clamp"}},
        on_unsupported="note",
        out_of_range="drop",
    )
    t = translate({"o": "b", "n": 5})
    assert t.dropped == ["o"] and t.kwargs == {"n": 1}  # a spec's own setting wins
    with pytest.raises(ValueError, match="out_of_range"):
        make_translator({}, out_of_range="wrap")


def test_check_range_standalone():
    assert check_range("t", 0.5, {"min": 0, "max": 1}) == 0.5
    with pytest.raises(ValueError, match="below minimum"):
        check_range("t", -1, {"min": 0})


# ---------------------------------------------------------------------------
# Consumer: ocracy / scribed / denote (the dict-returning shape, kept)
# ---------------------------------------------------------------------------


def test_consumer_ocracy_dict_shape_kept():
    from ocracy.translation import make_kwargs_translator, validate_param

    translate = make_kwargs_translator(
        {"languages": {"native_name": "lang"}, "gpu": {"default": False}, "dpi": None}
    )
    with pytest.warns(UserWarning):
        assert translate(languages="en", dpi=1) == {"lang": "en", "gpu": False}
    with pytest.raises(ValueError, match="above maximum"):
        validate_param("t", 2, {"max": 1})


def test_consumer_ocracy_adapter_puts_drop_notes_on_the_result():
    from ocracy.base import OcrResult
    from ocracy.make_backend import BaseOcrAdapter

    class Adapter(BaseOcrAdapter):
        def _read(self, image, **native):
            return OcrResult.from_text(repr(native), backend="fake")

    a = Adapter({"id": "fake", "param_map": {"languages": {"native_name": "lang"}}})
    with pytest.warns(UserWarning, match="dpi=300 is not a parameter of fake"):
        result = a.read(b"img", languages="en", dpi=300)
    assert result.text == "{'lang': 'en'}"
    assert result.meta["notes"] == ["dpi=300 is not a parameter of fake; dropped"]
    assert a._translate(languages="fr") == {"lang": "fr"}  # the old dict hook


def test_consumer_ocracy_credentials_reach_the_adapter_and_never_a_note():
    # Remote adapters pop api_key / app_key / app_id from their kwargs; no
    # param_map declares them, so before the kit they were dropped (and warned).
    from ocracy.base import OcrResult
    from ocracy.make_backend import BaseOcrAdapter

    class Adapter(BaseOcrAdapter):
        def _read(self, image, **native):
            return OcrResult.from_text(native.pop("api_key"), backend="fake")

    pm = {"languages": {"native_name": "lang"}}
    remote = Adapter({"id": "fake", "is_remote": True, "param_map": pm})
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        result = remote.read(b"img", api_key="sk-SECRET")
    assert result.text == "sk-SECRET" and "notes" not in result.meta

    class Local(BaseOcrAdapter):  # forwards **extra to its engine, like easyocr
        def _read(self, image, **native):
            assert "api_key" not in native
            return OcrResult.from_text("ok", backend="fake")

    local = Local({"id": "fake", "is_local": True, "param_map": pm})
    with pytest.warns(UserWarning, match="api_key=<redacted>"):
        result = local.read(b"img", api_key="sk-SECRET")
    assert "SECRET" not in " ".join(result.meta["notes"])


# ---------------------------------------------------------------------------
# Consumer: foley (supported-list sources, meaning-carrying params, clamps)
# ---------------------------------------------------------------------------


def _foley_style_translator(config, vocabulary, *, meaning=("seed", "negative_prompt")):
    """How foley's ``translate_affordances`` maps onto the kit."""
    nd = config.get("native_defaults") or {}
    param_map = {name: {} for name in config["supported_affordances"]}
    if "duration" in param_map:
        param_map["duration"] = {
            "min": nd.get("duration_min_s"),
            "max": nd.get("duration_max_s"),
            "out_of_range": "clamp",
            "unit": "s",
        }
    policy = "warn" if config.get("on_unsupported_param") == "warn" else "note"
    return make_translator(
        param_map,
        backend=config["name"],
        on_unsupported=policy,
        always_raise=(*meaning, *config.get("meaning_carrying", ())),
        vocabulary=vocabulary,
    )


_FOLEY_VOCAB = {
    "prompt": None,
    "duration": None,
    "prompt_influence": 0.3,
    "negative_prompt": None,
    "seed": None,
    "loop": False,
    "output_format": "wav",
}
_ELEVENLABS = {
    "name": "elevenlabs",
    "supported_affordances": ["prompt", "duration", "prompt_influence", "loop"],
    "native_defaults": {"duration_min_s": 0.5, "duration_max_s": 30.0},
    "on_unsupported_param": "warn",
}


def test_consumer_foley_meaning_carrying_raises_by_default():
    translate = _foley_style_translator(_ELEVENLABS, _FOLEY_VOCAB)
    with pytest.raises(UnsupportedParameter, match="seed"):
        translate({"prompt": "door", "seed": 7})
    t = translate({"prompt": "door", "seed": 7}, on_unsupported="note")
    assert t.dropped == ["seed"]


def test_consumer_foley_clamp_note_text_is_pinned():
    translate = _foley_style_translator(_ELEVENLABS, _FOLEY_VOCAB)
    t = translate({"prompt": "rain", "duration": 45.0})
    assert t.kwargs["duration"] == 30.0
    assert "clamped to 30 s" in " ".join(t.notes)


def test_consumer_foley_defaults_are_not_drops_and_warn_policy_warns():
    translate = _foley_style_translator(_ELEVENLABS, _FOLEY_VOCAB)
    with pytest.warns(UserWarning, match="output_format='mp3'"):
        t = translate({"prompt": "x", "output_format": "mp3", "steps": None})
    assert t.dropped == ["output_format"]
    assert t.notes == ["output_format='mp3' is not supported by elevenlabs; dropped"]
    quiet = translate({"prompt": "x", "output_format": "wav"})
    assert quiet.notes == []


def test_consumer_foley_per_source_meaning_carrying():
    cfg = dict(_ELEVENLABS, meaning_carrying=["output_format"])
    with pytest.raises(UnsupportedParameter):
        _foley_style_translator(cfg, _FOLEY_VOCAB)({"output_format": "mp3"})


def test_consumer_foley_credentials_raise_its_own_error_with_env_var_and_url(
    monkeypatch,
):
    class SourceConfigurationError(RuntimeError):
        pass

    monkeypatch.delenv("FREESOUND_API_KEY", raising=False)
    with pytest.raises(SourceConfigurationError) as ei:
        resolve_credential(
            "freesound",
            env_var="FREESOUND_API_KEY",
            guidance={
                "freesound": {"get_key_url": "https://freesound.org/apiv2/apply/"}
            },
            error=SourceConfigurationError,
        )
    assert "FREESOUND_API_KEY" in str(ei.value) and "http" in str(ei.value)


# ---------------------------------------------------------------------------
# Consumer: arioso (meaning-carrying ``lyrics``, adapter passthrough)
# ---------------------------------------------------------------------------


def test_consumer_arioso_adapter_handled_passes_the_canonical_name():
    # arioso: adapter_handled wins over native_name (even native_name=None).
    translate = make_translator(
        {
            "prompt": {"native_name": "tags", "adapter_handled": True},
            "lyrics": {"native_name": None, "adapter_handled": True},
            "genre": {"native_name": "tags"},
        },
        on_unsupported="warn",
        always_raise=("lyrics",),
    )
    t = translate({"prompt": "x", "lyrics": "la", "genre": "jazz"})
    assert t.kwargs == {"prompt": "x", "lyrics": "la", "tags": "jazz"} and not t.notes


def test_consumer_arioso_lyrics_always_raise_and_adapter_params_pass():
    translate = make_translator(
        {"prompt": {}, "duration": {"native_name": "length"}},
        backend="musicgen",
        on_unsupported="warn",
        always_raise=("lyrics",),
        passthrough=("guidance",),
    )
    with pytest.raises(UnsupportedParameter, match="lyrics"):
        translate({"prompt": "p", "lyrics": "la la"})
    t = translate({"prompt": "p", "duration": 10, "guidance": 3})
    assert t.kwargs == {"prompt": "p", "length": 10, "guidance": 3}


# ---------------------------------------------------------------------------
# Consumer: illustration (``name`` alias, str/callable specs, choices, None = unset)
# ---------------------------------------------------------------------------


def test_consumer_illustration_shapes():
    translate = make_translator(
        {
            "orientation": {
                "name": "aspect_ratio",
                "coerce": lambda o: {"landscape": "wide"}.get(o, o),
                "choices": {"landscape", "portrait"},
                "out_of_range": "drop",
            },
            "size": "size",
            "license_type": None,
        },
        on_unsupported="ignore",
        skip_none=True,
    )
    t = translate(
        {
            "orientation": "landscape",
            "size": "large",
            "license_type": "commercial",
            "q": None,
        }
    )
    assert t.kwargs == {"aspect_ratio": "wide", "size": "large"}
    native, dropped = t.kwargs, t.dropped  # illustration's (native, dropped) shape
    assert dropped == ["license_type"]
    assert translate({"license_type": "x"}).dropped == ["license_type"]
    assert translate({"orientation": "square"}).dropped == ["orientation"]


# ---------------------------------------------------------------------------
# Credentials: the chain
# ---------------------------------------------------------------------------


@pytest.fixture
def no_acme_env(monkeypatch):
    for var in ("ACME_KEY", "ACME_KEY_2"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(kit_credentials, "_load_dotenv", lambda: False)  # no .env


def test_chain_order_explicit_bound_env_store(monkeypatch, no_acme_env):
    store = {"ACME_KEY": "from-store\n"}
    kw = dict(env_var="ACME_KEY", store=store)
    assert resolve_credential("acme", **kw) == "from-store"  # stripped
    monkeypatch.setenv("ACME_KEY", "from-env")
    assert resolve_credential("acme", **kw) == "from-env"
    with using_credentials(acme="bound"):
        assert resolve_credential("acme", **kw) == "bound"
        assert resolve_credential("acme", api_key="explicit", **kw) == "explicit"


def test_empty_explicit_key_counts_as_not_given(monkeypatch, no_acme_env):
    monkeypatch.setenv("ACME_KEY", "from-env")
    assert resolve_credential("acme", api_key="", env_var="ACME_KEY") == "from-env"


def test_env_var_names_order_and_dedup():
    table = {"acme": ["ACME_KEY", "ACME_KEY_2"]}
    assert env_var_names("acme", env_var="ACME_KEY_2", provider_env_vars=table) == [
        "ACME_KEY_2",
        "ACME_KEY",
    ]
    assert env_var_names("other", provider_env_vars=table) == []


def test_store_only_skips_a_missing_key():
    class Broken(dict):
        def __getitem__(self, k):
            raise PermissionError("store unreadable")

    with pytest.raises(PermissionError):
        resolve_credential("acme", env_var="ACME_SURELY_UNSET", store=Broken())


def test_missing_message_names_vars_hint_and_link(no_acme_env):
    with pytest.raises(MissingCredentialError) as ei:
        resolve_credential(
            "acme",
            env_var=["ACME_KEY", "ACME_KEY_2"],
            guidance={
                "acme": {"note": "Sign up.", "get_key_url": "https://acme.test/k"}
            },
            hint="The pricing endpoint is free but authenticated.",
        )
    msg = str(ei.value)
    assert "set one of: ACME_KEY, ACME_KEY_2" in msg
    assert "free but authenticated" in msg
    assert "https://acme.test/k" in msg
    assert isinstance(ei.value, RuntimeError)


def test_not_required_returns_none(no_acme_env):
    assert resolve_credential("acme", env_var="ACME_KEY", required=False) is None


def test_prompt_persists_to_a_mutable_store_else_environ(monkeypatch, no_acme_env):
    import getpass

    monkeypatch.setattr(sys.stdin, "isatty", lambda: True, raising=False)
    monkeypatch.setattr(getpass, "getpass", lambda prompt="": " typed ")
    store: dict = {}
    assert (
        resolve_credential(
            "acme", env_var="ACME_KEY", store=store, prompt_if_missing=True
        )
        == "typed"
    )
    assert store == {"ACME_KEY": "typed"} and "ACME_KEY" not in os.environ
    frozen = type(
        "Frozen", (), {"__getitem__": lambda s, k: (_ for _ in ()).throw(KeyError(k))}
    )()
    assert (
        resolve_credential(
            "acme", env_var="ACME_KEY", store=frozen, prompt_if_missing=True
        )
        == "typed"
    )
    assert os.environ["ACME_KEY"] == "typed"


def test_dotenv_is_searched_from_the_cwd_on_every_miss(monkeypatch, tmp_path):
    pytest.importorskip("dotenv")
    monkeypatch.delenv("ACME_KEY", raising=False)
    project = tmp_path / "project"
    project.mkdir()
    monkeypatch.chdir(project)
    kw = dict(env_var="ACME_KEY", dotenv=True)
    assert resolve_credential("acme", required=False, **kw) is None
    (project / ".env").write_text("ACME_KEY=from-dotenv\n")  # added mid-session
    try:
        assert resolve_credential("acme", **kw) == "from-dotenv"
    finally:
        os.environ.pop("ACME_KEY", None)


def test_credential_help_and_lines():
    g = {"acme": {"note": "Sign up.", "get_key_url": "https://acme.test/k"}}
    assert credential_help("acme", guidance=g) == (
        "How to get a credential for acme: Sign up. Get a key: https://acme.test/k"
    )
    assert credential_help("other", guidance=g) == ""
    assert credential_lines("ACME_KEY", "acme", guidance=g) == [
        "export ACME_KEY  (get a key: https://acme.test/k)"
    ]
    assert credential_lines("", "acme", guidance=g) == []
    assert credential_lines(["A_KEY", "B_KEY"], "acme") == ["export A_KEY / B_KEY"]


def test_a_narrow_error_subclass_still_works(no_acme_env):
    class Narrow(MissingCredentialError):
        def __init__(self, msg):
            super().__init__(msg)

    with pytest.raises(Narrow) as ei:
        resolve_credential("acme", env_var="ACME_KEY", error=Narrow)
    assert ei.value.env_vars == ("ACME_KEY",)


def test_missing_credential_error_carries_structure(no_acme_env):
    g = {"acme": {"get_key_url": "https://acme.test/k"}}
    with pytest.raises(MissingCredentialError) as ei:
        resolve_credential("acme", env_var=("ACME_KEY", "ACME_KEY_2"), guidance=g)
    err = ei.value
    assert (err.provider, err.env_vars, err.get_key_url) == (
        "acme",
        ("ACME_KEY", "ACME_KEY_2"),
        "https://acme.test/k",
    )


# ---------------------------------------------------------------------------
# Credentials: context bindings
# ---------------------------------------------------------------------------


def test_bindings_nest_overlay_and_ignore_falsy():
    assert current_credentials() == {}
    with using_credentials({"google-vision": "g"}, acme="outer"):
        with using_credentials(acme="inner", other=None):
            assert current_credentials() == {"google-vision": "g", "acme": "inner"}
        assert current_credentials() == {"google-vision": "g", "acme": "outer"}
    assert current_credentials() == {}


def test_binding_is_invisible_to_other_threads():
    seen = {}
    with using_credentials(acme="mine"):
        t = threading.Thread(target=lambda: seen.update(other=current_credentials()))
        t.start()
        t.join()
    assert seen["other"] == {}


# ---------------------------------------------------------------------------
# Consumer: falaw (one BYO fal key; call_fal reads no env var, pricing does)
# ---------------------------------------------------------------------------


def test_consumer_falaw_byo_key(monkeypatch, no_acme_env):
    monkeypatch.delenv("FAL_KEY", raising=False)
    monkeypatch.setenv("FAL_API_KEY", "server-key")

    def call_fal_key(api_key=None):  # leaves env lookup to the fal SDK
        return resolve_credential("fal", api_key=api_key, required=False)

    def pricing_key(api_key=None):
        return resolve_credential(
            "fal",
            api_key=api_key,
            env_var=("FAL_KEY", "FAL_API_KEY"),
            error=RuntimeError,
        )

    assert call_fal_key() is None
    assert pricing_key() == "server-key"
    with using_credentials(fal="byo-key-123"):
        assert call_fal_key() == pricing_key() == "byo-key-123"
        assert current_credentials().get("fal") == "byo-key-123"
    with using_credentials(fal=None):  # a falsy key is a no-op
        assert current_credentials().get("fal") is None


# ---------------------------------------------------------------------------
# Consumer: voxy (ElevenLabs, ELEVEN_API_KEY before ELEVENLABS_API_KEY, no raise)
# ---------------------------------------------------------------------------


def test_consumer_voxy_env_order_and_optional(monkeypatch, no_acme_env):
    order = ("ELEVEN_API_KEY", "ELEVENLABS_API_KEY")
    for var in order:
        monkeypatch.delenv(var, raising=False)
    assert resolve_credential("elevenlabs", env_var=order, required=False) is None
    monkeypatch.setenv("ELEVENLABS_API_KEY", "second")
    monkeypatch.setenv("ELEVEN_API_KEY", "first")
    assert resolve_credential("elevenlabs", env_var=order, required=False) == "first"
    assert (
        resolve_credential("elevenlabs", api_key="explicit", env_var=order)
        == "explicit"
    )


# ---------------------------------------------------------------------------
# Install plans
# ---------------------------------------------------------------------------


def test_build_requirements_implemented_with_recipe():
    req = build_requirements(
        "tess",
        package="pkg",
        implemented=True,
        available=False,
        recipe={
            "extra": "tesseract",
            "system": {
                "linux": ["apt-get install tesseract-ocr"],
                "darwin": ["brew x"],
            },
            "gpu": "cuda wheel",
            "alt": "rapid",
            "heavy": True,
        },
        platform="linux",
        credentials=["export K"],
        verify_command="python -c ok",
        alternative_label="Faster/lighter alternative",
    )
    assert req.pip_command == 'pip install "pkg[tesseract]"'
    assert req.system == ["apt-get install tesseract-ocr"] and req.gpu == "cuda wheel"
    text = req.instructions()
    for piece in (
        "System dependency",
        "GPU: cuda wheel",
        "export K",
        "large download",
        "Faster/lighter alternative: rapid.",
        "Verify:   python -c ok",
    ):
        assert piece in text


def test_build_requirements_ledger_only():
    req = build_requirements(
        "surya",
        package="pkg",
        implemented=False,
        available=False,
        ledger_pip="pip install surya-ocr",
        unimplemented_note="ledger only",
    )
    assert req.pip_command == "pip install surya-ocr" and req.extra is None
    assert req.notes == ["ledger only"]
    bare = build_requirements("x", package="pkg", implemented=False, available=False)
    assert bare.pip_command == 'pip install "pkg[x]"'


def test_available_plan_is_one_line():
    req = Requirements("x", True, True, True, False, "pip install x")
    assert req.instructions() == "'x' is already installed and usable. ✓"


def test_run_install_dry_run_and_short_circuits():
    req = build_requirements("x", package="pkg", implemented=True, available=False)
    dry = run_install(req, package="pkg")
    assert dry["ran"] is False and "Dry run" in dry["message"]
    ledger = build_requirements("y", package="pkg", implemented=False, available=False)
    assert run_install(ledger, package="pkg", yes=True)["ran"] is False
    done = build_requirements("z", package="pkg", implemented=True, available=True)
    assert "nothing to do" in run_install(done, package="pkg", yes=True)["message"]


def test_run_install_runs_pip_then_verifies(monkeypatch):
    calls = []

    def fake_run(argv, **kw):
        calls.append(argv)
        out = "True\n" if argv[1] == "-c" else "x" * 5000
        return subprocess.CompletedProcess(argv, 0, stdout=out, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    req = build_requirements(
        "x",
        package="pkg",
        implemented=True,
        available=False,
        recipe={"extra": "xx", "system": {"linux": ["apt x"]}},
        platform="linux",
    )
    res = run_install(
        req, package="pkg", yes=True, upgrade=True, verify_code="print(True)"
    )
    assert calls[0][-3:] == ["install", "--upgrade", "pkg[xx]"]
    assert res["available_after"] is True and res["system_todo"] == ["apt x"]
    assert len(res["stdout_tail"]) == 2000


# ---------------------------------------------------------------------------
# Import hygiene: what depending on the kit costs a consumer
# ---------------------------------------------------------------------------


def _imports(path: Path) -> list:
    """``(module name, imported at module level?)`` for every import in ``path``."""
    found = []
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            found.extend((a.name, node.col_offset == 0) for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            found.append((node.module, node.col_offset == 0))
    return found


@pytest.mark.parametrize("module", sorted(p.name for p in KIT_DIR.glob("*.py")))
def test_kit_modules_import_only_stdlib_and_the_kit(module):
    stdlib = set(sys.stdlib_module_names)
    for name, module_level in _imports(KIT_DIR / module):
        top = name.split(".")[0]
        if top == "ocracy":
            assert name.startswith("ocracy.kit"), f"{module} imports {name}"
        elif top == "dotenv":  # optional: only ever inside a function, guarded
            assert not module_level, f"{module} imports dotenv at module level"
        else:
            assert top in stdlib or top == "__future__", f"{module} imports {name}"


def test_importing_the_kit_loads_no_engine_and_no_metadata():
    code = (
        "import sys, ocracy.kit; "
        "heavy = {'PIL', 'numpy', 'pandas', 'requests', 'torch', 'importlib.metadata', "
        "'subprocess', 'dotenv'}; "
        "loaded = heavy & set(sys.modules); "
        "loaded |= {m for m in sys.modules if m.startswith('ocracy.backends')}; "
        "print(sorted(loaded))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "[]"


def test_version_is_lazy_but_available():
    import ocracy

    assert "__version__" in dir(ocracy)  # listed before its first access
    assert isinstance(ocracy.__version__, str) and ocracy.__version__
    with pytest.raises(AttributeError):
        ocracy.no_such_attribute  # noqa: B018
