# ocracy.kit.ledger

The ledger loader: a filterable catalog over a facade’s `backends.json`.

Each fleet facade ships a *ledger*: a JSON catalog that describes every engine or
service in its domain, whether or not the facade can run it yet. The research
changes far more often than the code, so it is data, not code. This module reads
any such file and exposes it as a dict-like [`Catalog`](#ocracy.kit.ledger.Catalog) of
[`BackendInfo`](#ocracy.kit.ledger.BackendInfo) records. A facade binds its own data:

```default
from ocracy.kit.ledger import Catalog

catalog = Catalog(
    default_path=Path(__file__).parent / "data" / "backends.json",
    env_var="ACME_LEDGER",                      # override the path from the env
    implemented=lambda: registry.list_backends(),
    text_fields=DEFAULT_TEXT_FIELDS | {"pros", "cons"},
)
catalog["some-engine"]                           # one record
catalog.filter(is_local=True, open_source=True)  # a new Catalog; filters compose
catalog.filter(implemented=True)                 # what the facade runs today
catalog.supports_language("French")
catalog.can("diarization")
```

`implemented` is the one computed field. It comes from the facade’s registry
through the `implemented=` callable, so it cannot drift from the code. A record
that stores its own `implemented` keeps it.

The seams, all keyword-only: `default_path` and `env_var` (where the JSON
lives), `implemented` (ids with a working adapter), `text_fields` (fields
filtered by case-insensitive membership rather than equality),
`capability_suffixes` (extra field names [`Catalog.can()`](#ocracy.kit.ledger.Catalog.can) looks at, such as
ocracy’s `math` -> `math_formula`) and `compare_fields` (the default columns
of [`Catalog.compare()`](#ocracy.kit.ledger.Catalog.compare)).

Stdlib only; imports nothing else from ocracy. pandas is imported by
[`Catalog.to_dataframe()`](#ocracy.kit.ledger.Catalog.to_dataframe) only.

### Module Attributes

| [`DEFAULT_TEXT_FIELDS`](#ocracy.kit.ledger.DEFAULT_TEXT_FIELDS)    | filtered by a case-insensitive substring test rather than by equality.                                                        |
|-------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| [`DEFAULT_COMPARE_FIELDS`](#ocracy.kit.ledger.DEFAULT_COMPARE_FIELDS) | The columns [`Catalog.compare()`](#ocracy.kit.ledger.Catalog.compare) shows when a facade does not name its own.     |
| [`CAPABILITY_VALUES`](#ocracy.kit.ledger.CAPABILITY_VALUES)      | Field values that mean "this backend has the capability", for [`Catalog.can()`](#ocracy.kit.ledger.Catalog.can). |

### Classes

| [`BackendInfo`](#ocracy.kit.ledger.BackendInfo)(record, \*[, implemented])      | One backend's ledger entry: a read-only record, by key or by attribute.                                          |
|----------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| [`Catalog`](#ocracy.kit.ledger.Catalog)([path, records, default_path, ...]) | A filterable, dict-like collection of [`BackendInfo`](#ocracy.kit.ledger.BackendInfo), keyed by id. |

### *class* ocracy.kit.ledger.BackendInfo(record, , implemented=False)

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

One backend’s ledger entry: a read-only record, by key or by attribute.

New fields added to the JSON are available at once (`info.price_note`,
`info["price_note"]`) with no code change; a few common fields get typed
properties.

### ocracy.kit.ledger.CAPABILITY_VALUES *= ('yes', True)*

Field values that mean “this backend has the capability”, for [`Catalog.can()`](#ocracy.kit.ledger.Catalog.can).
Compared by identity for `True`, so a count of `1` is not a capability –
and neither is a numpy `True` or the string `"True"`: JSON gives real bools.

### *class* ocracy.kit.ledger.Catalog(path=None, \*, records=None, default_path=None, env_var=None, implemented=<function \_nothing_implemented>, text_fields=frozenset({'beyond_text', 'languages_note', 'output_formats'}), capability_suffixes=(), compare_fields=('name', 'is_local', 'is_remote', 'open_source', 'pricing_model', 'price_note', 'accuracy_tier', 'languages_count', 'best_for'))

Bases: [`Mapping`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Mapping)

A filterable, dict-like collection of [`BackendInfo`](#ocracy.kit.ledger.BackendInfo), keyed by id.

Loaded lazily from `path`, else from the `env_var` environment variable,
else from `default_path`; a missing file is an empty catalog. `records`
gives the records directly instead. [`filter()`](#ocracy.kit.ledger.Catalog.filter) returns a new `Catalog`
with the same settings over the matching subset, so filters compose:

```default
catalog.filter(is_remote=True).filter(pricing_model="free_tier_then_paid")
```

* **Parameters:**
  * **path** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – The ledger JSON (a `{"backends": [...]}` object or a bare list).
  * **records** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]]) – The records themselves, instead of a file.
  * **default_path** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Where the ledger lives when neither `path` nor the
    environment says otherwise.
  * **env_var** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – An environment variable that overrides `default_path`.
  * **implemented** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[], [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – Returns the ids that have a working adapter; called once,
    on first load (a filtered subset reuses the flags already computed).
    An exception it raises propagates: catch it in the binding if a
    broken registry should read as “nothing implemented”.
  * **text_fields** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Fields filtered by case-insensitive membership.
  * **capability_suffixes** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Extra field-name suffixes [`can()`](#ocracy.kit.ledger.Catalog.can) checks besides
    the capability’s own field: `("_formula",)` makes `can("math")`
    also read `math_formula`.
  * **compare_fields** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Default columns of [`compare()`](#ocracy.kit.ledger.Catalog.compare).

`text_fields`, `capability_suffixes` and `compare_fields` take
collections of names; a bare string is refused rather than split into letters.
A subclass binding a facade’s data should keep no derived state of its own:
[`filter()`](#ocracy.kit.ledger.Catalog.filter) builds a subset from these settings alone.

#### can(capability)

Backends with `capability`: listed in `beyond_text`, or a field set.

A field counts when it is named `capability`, or that plus one of the
catalog’s `capability_suffixes`, and its value is one of
[`CAPABILITY_VALUES`](#ocracy.kit.ledger.CAPABILITY_VALUES).

* **Return type:**
  [`Catalog`](#ocracy.kit.ledger.Catalog)

#### compare(ids=None, , fields=None)

A trimmed, side-by-side view of selected backends and fields.

* **Return type:**
  [`List`](https://docs.python.org/3/library/typing.html#typing.List)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

#### filter(, predicate=None, implemented=None, \*\*criteria)

Return a new `Catalog` of backends matching every criterion.

* **Parameters:**
  * **predicate** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`BackendInfo`](#ocracy.kit.ledger.BackendInfo)], [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]]) – An arbitrary `BackendInfo -> bool` callable.
  * **implemented** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]) – If set, keep only (un)implemented backends.
  * **\*\*criteria** ([`Any`](https://docs.python.org/3/library/typing.html#typing.Any)) – `field=value` constraints. `value` may be a
    set/list/tuple meaning “one of”. The catalog’s text fields (by
    default `languages_note`, `beyond_text`, `output_formats`)
    use a case-insensitive substring match.
* **Return type:**
  [`Catalog`](#ocracy.kit.ledger.Catalog)

Example:

```default
catalog.filter(is_local=True, open_source=True)
```

#### supports_language(language)

Backends whose `languages_note` mentions `language` (name or code).

* **Return type:**
  [`Catalog`](#ocracy.kit.ledger.Catalog)

#### to_dataframe(, columns=None)

Return a pandas DataFrame of the catalog (pandas imported lazily).

### ocracy.kit.ledger.DEFAULT_COMPARE_FIELDS *= ('name', 'is_local', 'is_remote', 'open_source', 'pricing_model', 'price_note', 'accuracy_tier', 'languages_count', 'best_for')*

The columns [`Catalog.compare()`](#ocracy.kit.ledger.Catalog.compare) shows when a facade does not name its own.

### ocracy.kit.ledger.DEFAULT_TEXT_FIELDS *= frozenset({'beyond_text', 'languages_note', 'output_formats'})*

filtered by a
case-insensitive substring test rather than by equality.

* **Type:**
  Fields whose meaning is “membership in a free-text description”
