# Transform rules & batch semantics

**Status:** 0.45.7 contract  
**See also:** [VISION-0.45](VISION-0.45.md) Phase A / 0.45.7 hygiene

## TransformLeaf auto-batch (default `batch: null`)

When `batch` is omitted on a pipeline step, `TransformLeaf` inspects the source value and rule mode:

| Source | Rule `mode` | Default behavior |
|--------|-------------|------------------|
| Scalar | any | Single apply |
| List | `batch` (e.g. `filter_items`, `put_resource`) | **Whole list** — one `apply()` with the full list |
| List | `single` (e.g. `rename_field`, `map_fields`) | **Per-item** — map rule over each element |
| List | `chain` | Per-item chain |

Override explicitly:

- `"batch": true` — force per-item (or whole-list for batch-mode rules when `per_item: false`)
- `"batch": false` — force single apply even when source is a list

## `put_resource` + lists (0.45.7)

`put_resource` declares `TransformMode.BATCH`. A list at `source_key` is passed to one `put` invoke as `params.value` — the safe default for ring-buffer tails (`append_item` → `put_resource`).

Before 0.45.7, `put_resource` was `single` mode, so list sources silently entered per-item batch (last element won; kv tail became a dict). Definitions should **not** need `"batch": false` on persist steps anymore.

## Per-rule modes

| Mode | Meaning | Examples |
|------|---------|----------|
| `single` | One scalar or mapping | `rename_field`, `jsonpath_extract`, `append_item` |
| `batch` | Whole list in one apply | `filter_items`, `put_resource`, `count_by` |
| `auto` | Engine picks from value shape | `callable`, `lookup`, `string_format` |

Doctor and `TRANSFORM_CATALOG` in code list short descriptions; this doc is the batch footgun reference.

## Pipeline pattern

```yaml
- name: append_event
  rule: append_item
  source_key: row
  target_key: events
  options: {max_items: 50, prepend: true}
- name: persist_log
  rule: put_resource
  source_key: events
  options: {resource: my-log, action: put}
```

`append_item` mutates the list in state; `put_resource` persists the **entire** list in one kv `put`.