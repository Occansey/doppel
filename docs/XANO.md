# Xano — the system of record

Xano holds the estate, the executor's identity, and the account of what was done. The dataclasses
in `src/pending_delete/model.py` are the contract; these tables are its deployment. `Store` and
`XanoStore` satisfy the same five methods, so the console runs identically against either.

## Why the backend is the interesting part here

An executor may have to justify, to a family or to a probate court, what was done to a dead
person's property. That makes this less a CRUD app than a ledger with a UI. Three consequences
shape the schema:

1. **`actions` is append-only.** No update or delete endpoint exists for it. What was done
   stays written, including the things that failed.
2. **Discovery is separated from belief.** `candidates` holds what a search returned;
   `status` records a human's decision and who made it. Nothing acts on `pending`.
3. **Every date carries provenance.** `domains.source` says where `expires_on` came from. A
   deadline without its source is a guess, and this product's whole value is the deadline.

## Tables

### `estates`
| field | type | notes |
|---|---|---|
| id | text (pk) | |
| subject_name | text | the person who died |
| died_on | date? | |
| executor_email | text | who is acting |
| anchors | json | city, employer, known handles — seeds for discovery |
| created_at | timestamp | |

### `candidates`
| field | type | notes |
|---|---|---|
| id | text (pk) | |
| estate_id | text (fk → estates) | |
| kind | enum | domain, profile, byline, listing, obituary |
| label, url, snippet | text | |
| source | text | the SerpApi engine + query that produced it |
| status | enum | pending, confirmed, rejected — default pending |
| decided_by, decided_at | text, timestamp | who decided, and when |

Unique index on `(estate_id, url)` — re-running discovery must not duplicate.

### `domains`
| field | type | notes |
|---|---|---|
| id | text (pk) | |
| estate_id | text (fk) | |
| name | text | |
| expires_on | date? | null until a real record is read |
| registrar | text? | |
| auto_renew_grace_days | int? | registrar-specific; overrides the 30-day default |
| source | text | provenance of `expires_on` |
| last_checked | timestamp? | |

Unique index on `(estate_id, name)`.

### `actions` — append-only
| field | type | notes |
|---|---|---|
| id | text (pk) | |
| estate_id | text (fk) | |
| verb | enum | discover, confirm, reject, renew, register, dns_update |
| target | text | the domain or candidate acted on |
| actor | text | executor email |
| detail | json | full request as sent |
| dry_run | bool | true unless a human confirmed a real write |
| result | text | including failures |
| at | timestamp | |

## Endpoints (Xano function stack)

| method | path | does |
|---|---|---|
| POST | `/estate` | create an estate; logs `discover` intent |
| GET | `/estate/{id}` | estate + candidates + domains + actions |
| POST | `/estate/{id}/discover` | calls SerpApi, writes candidates, logs the query |
| POST | `/candidate/{id}/decide` | confirm or reject; writes decided_by/at |
| POST | `/domain/{id}/refresh` | reads name.com; updates expiry + source |
| POST | `/domain/{id}/hold` | renew / register / DNS — **requires `confirm: true`** |
| GET | `/estate/{id}/ledger` | the audit trail, oldest first |

`/domain/{id}/hold` is the only endpoint that spends money or claims a name. It rejects any
request without an explicit `confirm` and writes the action either way — a refused attempt is
part of the account too.
