semantic_model = """
## Database: json_insurancedb (MySQL)
An insurance management system containing providers (agencies), customers, policies, vehicles, coverages, claims, and billing data.

---

### Table: providers
Insurance agencies and brokers.
| Column | Type | Description |
|--------|------|-------------|
| system_id (PK) | VARCHAR | Unique provider ID |
| index_name | VARCHAR | Short search name (often a username, not the commercial name) |
| commercial_name | VARCHAR | **The human-readable business name** (e.g. "Smart Insurance Company") |
| provider_type | VARCHAR | E.g. "Producer" |
| provider_number | VARCHAR | Official agency number like "80031-000-000" |
| email | VARCHAR | Business email |
| phone | VARCHAR | Business phone |
| status | VARCHAR | Active, Deleted, etc. |

### Table: agent_logins
Individual user accounts for agent portal access.
| Column | Type | Description |
|--------|------|-------------|
| login_id (PK) | VARCHAR | Unique login username (e.g. acmea1, acmegroup) |
| system_id | VARCHAR | Shared system user ID (multiple logins may share one) |
| first_name | VARCHAR | Agent first name (e.g. "Acme Agent1", "Acme Group") |
| last_name | VARCHAR | Agent surname |
| email | VARCHAR | Contact email |
| status | VARCHAR | Active or not |
| provider_ref (FK→providers.system_id) | VARCHAR | Links to the agency they work for |

### Table: customers
The insured policyholders (individuals or companies).
| Column | Type | Description |
|--------|------|-------------|
| system_id (PK) | VARCHAR | Unique customer ID |
| customer_number | VARCHAR | Customer reference number |
| index_name | VARCHAR | Human-readable name (e.g. "Patrick Myers", "Summit Shield Risk Solutions") |
| status | VARCHAR | Active, etc. |
| entity_type | VARCHAR | Individual or Company |
| email | VARCHAR | Contact email |
| phone | VARCHAR | Phone number |
| birth_date | DATE | Date of birth (individuals only) |
| add_date | DATE | Date customer was created |

### Table: policies
Insurance policies linking customers to providers.
| Column | Type | Description |
|--------|------|-------------|
| system_id (PK) | VARCHAR | Unique policy ID |
| policy_number | VARCHAR | Policy number like "PA0015567" |
| status | VARCHAR | Active, Cancelled, etc. |
| effective_date | DATE | Policy start |
| expiration_date | DATE | Policy end |
| carrier_group | VARCHAR | Carrier code like "ACME" |
| full_term_amt | FLOAT | Total premium for the term |
| description | VARCHAR | Product name, e.g. "Texas Ranger" |
| insured_name | VARCHAR | Name of the insured on this policy |
| provider_ref (FK→providers.system_id) | VARCHAR | The agency servicing this policy |
| customer_ref (FK→customers.system_id) | VARCHAR | The customer who owns this policy |

### Table: vehicles
Insured vehicles on a policy.
| Column | Type | Description |
|--------|------|-------------|
| id (PK) | VARCHAR | Vehicle ID |
| policy_id (FK→policies.system_id) | VARCHAR | Which policy this vehicle is on |
| vehicle_number | INT | Vehicle sequence number |
| vin | VARCHAR | VIN |
| year | INT | Model year |
| make | VARCHAR | Manufacturer (e.g. NISSAN) |
| model | VARCHAR | Model name |
| body_type | VARCHAR | Body style |
| status | VARCHAR | Active, etc. |

### Table: coverages
Individual coverage lines on a vehicle.
| Column | Type | Description |
|--------|------|-------------|
| id (PK) | VARCHAR | Coverage ID |
| vehicle_id (FK→vehicles.id) | VARCHAR | Which vehicle this covers |
| coverage_code | VARCHAR | Code like BODI, PROP, COLL, COMP |
| description | VARCHAR | Full name, e.g. "Bodily Injury" |
| status | VARCHAR | Active, etc. |
| limit1 | VARCHAR | Primary limit |
| limit2 | VARCHAR | Secondary limit |
| deductible | VARCHAR | Deductible amount |
| premium_amt | FLOAT | Premium for this coverage |

### Table: claims
Insurance claims filed against a policy.
| Column | Type | Description |
|--------|------|-------------|
| system_id (PK) | VARCHAR | Claim ID |
| claim_number | VARCHAR | Tracking number like "24PAZ-00000001" |
| status | VARCHAR | Open, Closed |
| loss_date | DATE | Date the loss occurred |
| reported_date | DATE | Date it was reported |
| description | TEXT | Short description of the loss |
| loss_cause | VARCHAR | Categorized cause |
| product_line | VARCHAR | PersonalAuto, etc. |
| at_fault | VARCHAR | At Fault, Not At Fault |
| customer_ref (FK→customers.system_id) | VARCHAR | The customer who filed |
| policy_ref (FK→policies.system_id) | VARCHAR | The policy it's against |

### Table: billing_accounts
Payment accounts for customers.
| Column | Type | Description |
|--------|------|-------------|
| system_id (PK) | VARCHAR | Account ID |
| account_number | VARCHAR | Account number (often same as policy number) |
| account_status | VARCHAR | Status description |
| pay_plan | VARCHAR | Payment plan type |
| total_amt | FLOAT | Total amount |
| open_amt | FLOAT | Outstanding balance |
| paid_amt | FLOAT | Amount paid |
| customer_ref (FK→customers.system_id) | VARCHAR | Customer who pays |
| policy_ref (FK→policies.system_id) | VARCHAR | Associated policy |

### Table: billing_history
Individual financial transactions on accounts.
| Column | Type | Description |
|--------|------|-------------|
| id (PK) | VARCHAR | Transaction ID |
| billing_account_id (FK→billing_accounts.system_id) | VARCHAR | Parent account |
| type_cd | VARCHAR | Transaction type (CreateAccount, Receipt, etc.) |
| description | VARCHAR | Description |
| transaction_date | DATE | Transaction date |
| transaction_amount | FLOAT | Dollar amount |
| due_amount | FLOAT | Amount due |

### Table: provider_policy_access
Junction table mapping sub-providers (agent-level) to the policies they can access. Providers have a hierarchy: parent providers (e.g. system_id=1) own policies, sub-providers (e.g. 101-104) are agent-level access scopes.
| Column | Type | Description |
|--------|------|-------------|
| provider_ref | VARCHAR | Sub-provider ID (matches agent_logins.provider_ref) |
| policy_system_id | VARCHAR | Policy ID the sub-provider can access |
| policy_number | VARCHAR | Policy number for convenience |
| customer_ref | VARCHAR | Customer on the policy for convenience |

---

## Key Relationships
- **providers** → **policies** via `policies.provider_ref = providers.system_id`
- **customers** → **policies** via `policies.customer_ref = customers.system_id`
- **policies** → **vehicles** via `vehicles.policy_id = policies.system_id`
- **vehicles** → **coverages** via `coverages.vehicle_id = vehicles.id`
- **customers** → **claims** via `claims.customer_ref = customers.system_id`
- **policies** → **claims** via `claims.policy_ref = policies.system_id`
- **customers** → **billing_accounts** via `billing_accounts.customer_ref = customers.system_id`
- **policies** → **billing_accounts** via `billing_accounts.policy_ref = policies.system_id`
- **billing_accounts** → **billing_history** via `billing_history.billing_account_id = billing_accounts.system_id`
- **providers** → **agent_logins** via `agent_logins.provider_ref = providers.system_id`
- **agent_logins** → **policies** via `provider_policy_access` (agent_logins.provider_ref = provider_policy_access.provider_ref)

## Important Notes
- Use `providers.commercial_name` for human-readable provider names.
- Use `customers.index_name` for human-readable customer names.
- Use `policies.insured_name` when you need the insured name on a specific policy.

## Agent→Policy/Customer Linkage (CRITICAL)
ALL queries involving an agent login MUST go through the `provider_policy_access` junction table.
NEVER join `agent_logins` directly to `policies` or `customers` — the provider_ref values differ.

**Agent → Customers:**
```sql
SELECT DISTINCT ppa.customer_ref, c.index_name
FROM agent_logins al
JOIN provider_policy_access ppa ON al.provider_ref = ppa.provider_ref
LEFT JOIN customers c ON ppa.customer_ref = c.system_id
WHERE al.login_id = 'acmea1'
```

**Agent → Policies (e.g. count active policies):**
```sql
SELECT COUNT(*) AS active_policy_count
FROM agent_logins al
JOIN provider_policy_access ppa ON al.provider_ref = ppa.provider_ref
JOIN policies p ON ppa.policy_system_id = p.system_id
WHERE al.login_id = 'acmegroup' AND p.status = 'Active'
```

**Agent → Claims:**
```sql
SELECT cl.*
FROM agent_logins al
JOIN provider_policy_access ppa ON al.provider_ref = ppa.provider_ref
JOIN claims cl ON cl.policy_ref = ppa.policy_system_id
WHERE al.login_id = 'acmea1'
```

WRONG (will return 0): `policies.provider_ref = agent_logins.provider_ref`
RIGHT: `agent_logins → provider_policy_access → policies` (via junction table)
"""
