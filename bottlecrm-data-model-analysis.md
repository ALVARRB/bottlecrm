# BottleCRM Data Model Analysis

## Sources
- **schema.yml**: OpenAPI spec (~69KB, 3107 lines) — describes API endpoints, request/response shapes
- **Django Models**: 11 `models.py` files across `backend/` apps (accounts, leads, contacts, common, cases, opportunity, invoices, tasks, orders, macros, business_hours)
- **Base classes**: `common/base.py`, `common/mixins.py`
- **RLS Setup**: `RLS_SETUP.md`

---

## Entity Summary (67 Tables)

### Base Model Mixin Fields (inherited by all org-scoped entities)

Every entity inheriting from `BaseModel` (via `AuditModel`) gets:
| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID (PK) | `uuid.uuid4`, auto-generated, `db_index=True` |
| `created_at` | DateTime | `auto_now_add=True` |
| `updated_at` | DateTime | `auto_now=True` |
| `created_by` | FK → User | nullable, `SET_NULL` |
| `updated_by` | FK → User | nullable, `SET_NULL` |

---

### 1. Core Business Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M Relationships | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|------------------|-------------------|---------|
| 1 | **Account** (`accounts`) | accounts | name, email, phone, website, industry, num_employees, annual_revenue, currency, address_line, city, state, postcode, country, description, custom_fields (JSON), is_active | **org** → Org (CASCADE) | assigned_to → Profile, teams → Teams, contacts → Contact, tags → Tags | `Lower(name) + org` (case-insensitive unique name per org) | name, industry, org+created_at |
| 2 | **Lead** (`lead`) | leads | title, salutation, first_name, last_name, email, phone, job_title, website, linkedin_url, status, source, industry, rating, opportunity_amount, currency, probability, close_date, address_line, city, state, postcode, country, last_contacted, next_follow_up, description, company_name, is_active, custom_fields (JSON), kanban_order | **org** → Org (CASCADE), **stage** → LeadStage (SET_NULL) | assigned_to → Profile, teams → Teams, contacts → Contact, tags → Tags | `Lower(email) + org` (when email not null/empty) | status, source, org+created_at, stage+kanban_order, status+kanban_order |
| 3 | **Contact** (`contacts`) | contacts | first_name, last_name, email, phone, organization, title, department, do_not_call, linkedin_url, address_line, city, state, postcode, country, description, is_active, auto_created, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (SET_NULL) | assigned_to → Profile, teams → Teams, tags → Tags | `Lower(email) + org` (when email not null/empty) | org+created_at |
| 4 | **Opportunity** (`opportunity`) | opportunity | name, stage, opportunity_type, currency, amount, amount_source, probability, closed_on, lead_source, description, stage_changed_at, kanban_order, is_active, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (CASCADE) | contacts → Contact, assigned_to → Profile, teams → Teams, tags → Tags | probability 0-100, amount ≥ 0 | stage, org+created_at, stage+kanban_order |
| 5 | **Case** (`case`) | cases | name, status, priority, case_type, closed_on, description, is_active, sla_first_response_hours, sla_resolution_hours, first_response_at, resolved_at, sla_paused_at, sla_paused_seconds, last_escalation_fired_at, escalation_count, external_thread_id, merged_into (self-FK), merged_at, alt_thread_ids (JSON), merge_record (JSON), parent (self-FK), is_problem, kanban_order, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (CASCADE), **stage** → CaseStage (SET_NULL), **merged_into** → Case (SET_NULL), **parent** → Case (SET_NULL), **merged_by** → Profile (SET_NULL) | contacts → Contact, assigned_to → Profile, teams → Teams, tags → Tags, watchers → Profile (through CaseWatcher) | — | status, priority, org+created_at, stage+kanban_order, status+kanban_order, org+resolved_at, parent |
| 6 | **Task** (`task`) | tasks | title, status, priority, due_date, description, kanban_order, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (SET_NULL), **opportunity** → Opportunity (SET_NULL), **case** → Case (SET_NULL), **lead** → Lead (SET_NULL), **stage** → TaskStage (SET_NULL) | contacts → Contact, assigned_to → Profile, teams → Teams, tags → Tags | — | status, due_date, org+created_at, status+kanban_order, stage+kanban_order |
| 7 | **Invoice** (`invoice`) | invoices | invoice_title, invoice_number (unique), status, client_name, client_email, client_phone, billing_address fields, client_address fields, subtotal, discount_type, discount_value, discount_amount, tax_rate, tax_amount, shipping_amount, total_amount, currency, amount_paid, amount_due, issue_date, due_date, payment_terms, sent_at, viewed_at, paid_at, cancelled_at, reminder fields, public_token (unique), public_link_enabled, notes, terms, details, billing_period, po_number, is_email_sent, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (PROTECT), **contact** → Contact (SET_NULL), **opportunity** → Opportunity (SET_NULL), **template** → InvoiceTemplate (SET_NULL) | assigned_to → Profile, teams → Teams | invoice_number (unique), public_token (unique) | org+created_at, org+status, account, due_date, public_token |

---

### 2. Pipeline/Stage Entities (Kanban)

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 8 | **LeadPipeline** (`lead_pipeline`) | leads | name, description, is_default, is_active | **org** → Org (CASCADE) | — | One default pipeline per org | org+created_at |
| 9 | **LeadStage** (`lead_stage`) | leads | name, order, color, stage_type, maps_to_status, win_probability, wip_limit | **pipeline** → LeadPipeline (CASCADE), **org** → Org (CASCADE) | — | pipeline + name (unique_together) | org+order, pipeline+order |
| 10 | **CasePipeline** (`case_pipeline`) | cases | name, description, is_default, is_active | **org** → Org (CASCADE) | — | One default pipeline per org | org+created_at |
| 11 | **CaseStage** (`case_stage`) | cases | name, order, color, stage_type, maps_to_status, wip_limit | **pipeline** → CasePipeline (CASCADE), **org** → Org (CASCADE) | — | pipeline + name (unique_together) | org+order, pipeline+order |
| 12 | **TaskPipeline** (`task_pipeline`) | tasks | name, description, is_default, is_active | **org** → Org (CASCADE) | — | One default pipeline per org | org+created_at |
| 13 | **TaskStage** (`task_stage`) | tasks | name, order, color, stage_type, maps_to_status, wip_limit | **pipeline** → TaskPipeline (CASCADE), **org** → Org (CASCADE) | — | pipeline + name (unique_together) | org+order, pipeline+order |

---

### 3. Board (Kanban) Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 14 | **Board** (`board`) | tasks | name, description, is_archived | **org** → Org (CASCADE), **owner** → Profile (CASCADE) | members → Profile (through BoardMember) | — | org+created_at |
| 15 | **BoardColumn** (`board_column`) | tasks | name, order, color, limit (WIP) | **board** → Board (CASCADE), **org** → Org (CASCADE) | — | board + name (unique_together) | org+order |
| 16 | **BoardTask** (`board_task`) | tasks | title, description, order, priority, due_date, completed_at | **column** → BoardColumn (CASCADE), **org** → Org (CASCADE), **account** → Account (SET_NULL), **contact** → Contact (SET_NULL), **opportunity** → Opportunity (SET_NULL) | assigned_to → Profile | — | org+order |
| 17 | **BoardMember** (`board_member`) | tasks | role | **board** → Board (CASCADE), **profile** → Profile (CASCADE), **org** → Org (CASCADE) | — | board + profile (unique_together) | org+created_at |

---

### 4. Case-Specific Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 18 | **CaseWatcher** (`case_watcher`) | cases | subscribed_via | **case** → Case (CASCADE), **profile** → Profile (CASCADE), **org** → Org (CASCADE) | — | case + profile | profile+created_at, case |
| 19 | **CsatSurvey** (`csat_survey`) | cases | token_hash, sent_at, rating, comment, responded_at, expires_at | **case** → Case (OneToOne, CASCADE), **contact** → Contact (SET_NULL), **org** → Org (CASCADE) | — | token_hash (unique) | org+responded_at, case, token_hash |
| 20 | **Solution** (`solution`) | cases | title, description, status, is_published | **org** → Org (CASCADE) | cases → Case | — | status, is_published, org |
| 21 | **ReopenPolicy** (`reopen_policy`) | cases | is_enabled, reopen_window_days, reopen_to_status, notify_assigned | **org** → Org (OneToOne, CASCADE) | — | — | — |
| 22 | **EscalationPolicy** (`escalation_policy`) | cases | priority, first_response_action, resolution_action, is_active | **org** → Org (CASCADE), **first_response_target** → Profile (SET_NULL), **resolution_target** → Profile (SET_NULL), **notify_team** → Teams (SET_NULL) | — | org + priority | org+is_active |
| 23 | **InboundMailbox** (`inbound_mailbox`) | cases | address, provider, webhook_secret, imap_host, imap_port, imap_username, imap_password_enc, default_priority, default_case_type, is_active | **org** → Org (CASCADE), **default_assignee** → Profile (SET_NULL) | — | org + address | org+is_active |
| 24 | **EmailMessage** (`email_message`) | cases | direction, message_id, in_reply_to, references, from_address, to_addresses, cc_addresses, subject, body_text, body_html, received_at, drop_reason | **org** → Org (CASCADE), **case** → Case (CASCADE) | — | org + message_id | org+received_at, case+received_at, in_reply_to |
| 25 | **RoutingRule** (`routing_rule`) | cases | name, priority_order, is_active, conditions (JSON), strategy, stop_processing | **org** → Org (CASCADE), **target_team** → Teams (SET_NULL) | target_assignees → Profile | — | org+is_active+priority_order |
| 26 | **RoutingRuleState** (`routing_rule_state`) | cases | last_assigned_index | **org** → Org (CASCADE), **rule** → RoutingRule (OneToOne, CASCADE) | — | — | — |
| 27 | **TimeEntry** (`time_entry`) | cases | started_at, ended_at, duration_minutes, description, billable, hourly_rate, currency, auto_stopped | **org** → Org (CASCADE), **case** → Case (CASCADE), **profile** → Profile (PROTECT), **invoice** → Invoice (SET_NULL) | — | One active timer per profile (partial: ended_at IS NULL) | org+profile+started_at, case+started_at, billable+invoice |
| 28 | **ApprovalRule** (`approval_rule`) | cases/approvals | name, trigger_event, priority, case_type, team, is_active, conditions (JSON) | **org** → Org (CASCADE) | — | — | — |
| 29 | **Approval** (`approval`) | cases/approvals | state (pending/approved/rejected/cancelled), comment | **org** → Org (CASCADE), **case** → Case (CASCADE), **rule** → ApprovalRule (SET_NULL), **requested_by** → Profile (SET_NULL), **reviewed_by** → Profile (SET_NULL) | — | — | — |

---

### 5. Supporting Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 30 | **AccountEmail** (`account_email`) | accounts | message_subject, message_body, timezone, scheduled_date_time, scheduled_later, from_email, rendered_message_body | **org** → Org (CASCADE), **from_account** → Account (SET_NULL) | recipients → Contact | — | org+created_at |
| 31 | **AccountEmailLog** (`emailLogs`) | accounts | is_sent | **org** → Org (CASCADE), **email** → AccountEmail (SET_NULL), **contact** → Contact (SET_NULL) | — | — | org+created_at |
| 32 | **Comment** (`comment`) | common | comment (255 chars), commented_on, is_internal | **org** → Org (CASCADE), **commented_by** → Profile (CASCADE), **content_type** → ContentType (CASCADE) — GenericForeignKey to any model | — | — | content_type+object_id, org+created_at, content_type+object_id+is_internal |
| 33 | **CommentFiles** (`commentFiles`) | common | comment_file | **comment** → Comment (CASCADE), **org** → Org (CASCADE) | — | — | — |
| 34 | **Attachments** (`attachments`) | common | file_name, attachment | **org** → Org (CASCADE), **content_type** → ContentType (CASCADE) — GenericForeignKey | — | — | content_type+object_id, org+created_at |
| 35 | **Document** (`document`) | common | title, document_file, status | **org** → Org (CASCADE) | shared_to → Profile, teams → Teams | — | — |
| 36 | **Activity** (`activity`) | common | action, entity_type, entity_id, entity_name, description, metadata (JSON) | **org** → Org (CASCADE), **user** → Profile (SET_NULL) | — | — | org+created_at, entity_type+entity_id, org+entity_type+action+created_at |
| 37 | **Notification** (`notification`) | common | verb, entity_type, entity_id, entity_name, data (JSON), link, read_at | **org** → Org (CASCADE), **recipient** → Profile (CASCADE), **actor** → Profile (SET_NULL) | — | — | org+recipient+created_at, recipient+read_at |
| 38 | **Teams** (`teams`) | common | name, description | **org** → Org (CASCADE) | users → Profile | — | — |
| 39 | **Tags** (`tags`) | common | name, slug, color, description, is_active | **org** → Org (CASCADE) | — | slug + org | — |
| 40 | **Address** (`address`) | common | address_line, street, city, state, postcode, country | **org** → Org (CASCADE) | — | — | — |
| 41 | **Macro** (`macro`) | macros | title, body, scope, is_active, usage_count | **org** → Org (CASCADE), **owner** → Profile (CASCADE) | — | scope+owner consistency check | org+scope+is_active, owner+created_at |

---

### 6. Settings/Email/Product Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 42 | **APISettings** (`apiSettings`) | common | title, apikey, website | **org** → Org (CASCADE) | lead_assigned_to → Profile, tags → Tags | — | — |
| 43 | **InvoiceTemplate** (`invoice_template`) | invoices | name, logo, primary_color, secondary_color, template_html, template_css, default_notes, default_terms, footer_text, is_default | **org** → Org (CASCADE) | — | — | org+created_at |
| 44 | **Product** (`product`) | invoices | name, description, sku, price, currency, category, is_active | **org** → Org (CASCADE) | — | sku + org | org+is_active |
| 45 | **OpportunityLineItem** (`opportunity_line_item`) | opportunity | name, description, quantity, unit_price, discount_type, discount_value, discount_amount, subtotal, total, order | **opportunity** → Opportunity (CASCADE), **product** → Product (SET_NULL), **org** → Org (CASCADE) | — | — | opportunity, org |

---

### 7. Invoice Financial Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 46 | **InvoiceLineItem** (`invoice_line_item`) | invoices | name, description, quantity, unit_price, discount_type, discount_value, discount_amount, tax_rate, tax_amount, subtotal, total, order | **invoice** → Invoice (CASCADE), **product** → Product (SET_NULL), **org** → Org (CASCADE) | — | — | org+order |
| 47 | **Payment** (`payment`) | invoices | amount, payment_date, payment_method, reference_number, notes | **invoice** → Invoice (CASCADE), **org** → Org (CASCADE) | — | — | org+payment_date, invoice |
| 48 | **Estimate** (`estimate`) | invoices | estimate_number (unique), title, status, client_name, client_email, client_phone, client_address fields, subtotal, discount fields, tax fields, total_amount, currency, issue_date, expiry_date, sent_at, viewed_at, accepted_at, declined_at, notes, terms, public_token (unique), public_link_enabled, custom_fields (JSON) | **org** → Org (CASCADE), **account** → Account (PROTECT), **contact** → Contact (SET_NULL), **opportunity** → Opportunity (SET_NULL), **converted_to_invoice** → Invoice (SET_NULL) | assigned_to → Profile, teams → Teams | estimate_number (unique), public_token (unique) | org+created_at, org+status, account, expiry_date, public_token |
| 49 | **EstimateLineItem** (`estimate_line_item`) | invoices | name, description, quantity, unit_price, discount fields, tax fields, subtotal, total, order | **estimate** → Estimate (CASCADE), **product** → Product (SET_NULL), **org** → Org (CASCADE) | — | — | org+order |
| 50 | **RecurringInvoice** (`recurring_invoice`) | invoices | title, is_active, frequency, custom_days, start_date, end_date, next_generation_date, payment_terms, auto_send, currency, subtotal, discount fields, tax_rate, total_amount, notes, terms, custom_fields (JSON), invoices_generated | **org** → Org (CASCADE), **account** → Account (PROTECT), **contact** → Contact (SET_NULL), **opportunity** → Opportunity (SET_NULL) | assigned_to → Profile, teams → Teams | — | org+created_at, org+is_active, next_generation_date |
| 51 | **RecurringInvoiceLineItem** (`recurring_invoice_line_item`) | invoices | name, description, quantity, unit_price, discount fields, tax_rate, order | **recurring_invoice** → RecurringInvoice (CASCADE), **product** → Product (SET_NULL), **org** → Org (CASCADE) | — | — | — |
| 52 | **InvoiceHistory** (`invoice_history`) | invoices | invoice_title, invoice_number, status, client_name, client_email, total_amount, amount_due, currency, due_date, details | **invoice** → Invoice (CASCADE), **updated_by** → Profile (SET_NULL), **org** → Org (CASCADE) | — | — | org+created_at, invoice |

---

### 8. Opportunity/Financial Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 53 | **StageAgingConfig** (`stage_aging_config`) | opportunity | stage, expected_days, warning_days | **org** → Org (CASCADE) | — | org + stage (unique_together) | — |
| 54 | **SalesGoal** (`sales_goal`) | opportunity | name, goal_type, target_value, period_type, period_start, period_end, is_active, milestone tracking | **org** → Org (CASCADE), **assigned_to** → Profile (SET_NULL), **team** → Teams (SET_NULL) | — | — | org+created_at, org+period_start+period_end |

---

### 9. Order Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 55 | **Order** (`orders`) | orders | name, order_number, status, currency, subtotal, discount_amount, tax_amount, total_amount, order_date, activated_date, shipped_date, billing_address fields, shipping_address fields, description | **org** → Org (FK via BaseOrgModel), **account** → Account (CASCADE), **contact** → Contact (SET_NULL), **opportunity** → Opportunity (SET_NULL) | — | — | inherited org+created_at |
| 56 | **OrderLineItem** (`order_line_item`) | orders | name, description, quantity, unit_price, discount_amount, total, sort_order | **org** → Org (via BaseOrgModel), **order** → Order (CASCADE), **product** → Product (SET_NULL) | — | — | — |

---

### 10. Business Hours Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 57 | **BusinessCalendar** (`business_calendar`) | business_hours | name, timezone, is_default, monday_open/close through sunday_open/close | **org** → Org (CASCADE) | — | One default calendar per org | org+is_default |
| 58 | **BusinessHoliday** (`business_holiday`) | business_hours | date, name | **calendar** → BusinessCalendar (CASCADE), **org** → Org (CASCADE) | — | calendar + date | calendar+date |

---

### 11. Auth/Identity Entities

| # | Entity (Table) | App | Key Fields | FK Relationships | M2M | Unique Constraints | Indexes |
|---|---------------|-----|-----------|-----------------|-----|-------------------|---------|
| 59 | **User** (`users`) | common | email (unique), name, profile_pic, activation_key, key_expires, is_active, is_staff | — | — | email (unique) | — |
| 60 | **Profile** (`profile`) | common | phone, alternate_phone, role, has_sales_access, has_marketing_access, is_active, is_organization_admin, date_of_joining | **user** → User (CASCADE), **org** → Org (CASCADE), **address** → Address (CASCADE) | — | user+org, phone+org | — |
| 61 | **Org** (`organization`) | common | name, api_key (unique), is_active, company_name, logo, address_line, city, state, postcode, country, phone, email, website, tax_id, default_currency, default_country, csat_enabled, auto_close_children_on_parent_close | — | — | api_key (unique) | — |
| 62 | **SessionToken** (`session_token`) | common | token_jti (unique), refresh_token_jti (unique), ip_address, user_agent, expires_at, is_active, revoked_at, last_used_at | **user** → User (CASCADE) | — | token_jti (unique), refresh_token_jti (unique) | user+is_active, token_jti, expires_at |
| 63 | **MagicLinkToken** (`magic_link_token`) | common | email, token (unique), delivery, code_hash, attempts, expires_at, is_used, used_at, ip_address | — | — | token (unique) | email+created_at |
| 64 | **PersonalAccessToken** (`personal_access_token`) | common | name, token_hash (unique), token_prefix, scopes (JSON), expires_at, last_used_at, revoked_at | **org** → Org (via BaseOrgModel), **profile** → Profile (CASCADE) | — | token_hash (unique) | org+created_at |
| 65 | **ContactFormSubmission** (`contact_form_submission`) | common | name, email, message, reason, status, ip_address, user_agent, referrer, replied_at | **replied_by** → User (SET_NULL) | — | — | email, status, created_at |
| 66 | **CustomFieldDefinition** (`custom_field_definition`) | common | target_model, key, label, field_type, options (JSON), is_required, is_filterable, display_order, is_active | **org** → Org (CASCADE) | — | org + target_model + key | org+target_model+is_active |
| 67 | **SecurityAuditLog** (`security_audit_log`) | common/audit_log | event_type, description, metadata (JSON), ip_address, user_agent, request_path, request_method, success | **user** → User (SET_NULL), **org** → Org (SET_NULL) | — | — | event_type+created_at, user+created_at, org+created_at, ip_address, success+created_at |

---

## Database Tables by Category (from RLS_SETUP.md)

| Category | Tables |
|----------|--------|
| **Core Business** | `lead`, `accounts`, `contacts`, `opportunity`, `case`, `task`, `invoice` |
| **Supporting** | `comment`, `commentFiles`, `attachments`, `document`, `teams`, `activity`, `tags`, `address`, `solution` |
| **Boards (Kanban)** | `board`, `board_column`, `board_task`, `board_member` |
| **Settings/Email** | `apiSettings`, `account_email`, `emailLogs`, `invoice_history` |
| **Security** | `security_audit_log` |

**Total: 24 RLS-protected tables**

---

## Row-Level Security (RLS) Strategy Summary

From `RLS_SETUP.md`:

### Mechanism
- PostgreSQL Row-Level Security using session variable `app.current_org`
- Each request sets the org context via middleware: `SELECT set_config('app.current_org', '<org_uuid>', true)`
- Application user must be **non-superuser** (superusers bypass RLS)

### Per-Table Policies (2 per table)
1. **Isolation Policy** (SELECT/UPDATE/DELETE):
   ```sql
   CREATE POLICY org_isolation ON "lead"
       FOR ALL
       USING (org_id::text = NULLIF(current_setting('app.current_org', true), ''));
   ```
2. **Insert Check Policy** (FOR INSERT):
   ```sql
   CREATE POLICY org_insert_check ON "lead"
       FOR INSERT
       WITH CHECK (org_id::text = NULLIF(current_setting('app.current_org', true), ''));
   ```

### Key Design Decisions
- **Force RLS**: `ALTER TABLE "lead" FORCE ROW LEVEL SECURITY` — applies to table owner too
- **Fail-safe**: `NULLIF(..., '')` ensures **no rows returned** when context is unset
- **24 tables** protected (see table above)
- **BaseOrgModel** vs **BaseModel**: Most entities declare their own `org` FK (following `BaseModel` pattern) rather than using `BaseOrgModel`, but RLS is still enforced via migration policies
- **Celery tasks** must manually set RLS context via `set_rls_context(org_id)` before any query

### Verification Commands
```bash
python manage.py manage_rls --status
python manage.py manage_rls --verify-user
python manage.py manage_rls --test
```

### Entities NOT RLS-Protected (by design)
- `User` (platform-level, cross-org)
- `Org` (root tenant entity)
- `ContactFormSubmission` (platform-level submissions)
- `MagicLinkToken` (auth tokens)
- `SessionToken` (auth tokens)
- `PersonalAccessToken` (auth tokens — but uses BaseOrgModel so has org field)
- `CustomFieldDefinition` (has org but schema-level)
- `BusinessCalendar`/`BusinessHoliday` (not in the RLS list)
- `Macro` (not in the RLS list but has org field)
- `Order`/`OrderLineItem` (not in the RLS list but uses BaseOrgModel)
- `Approval`/`ApprovalRule` (not in the RLS list but policies added via migration)
- `TimeEntry` (not in the RLS list but policies added via migration)
- `EmailMessage`/`RoutingRule`/`RoutingRuleState`/`InboundMailbox`/`EscalationPolicy`/`ReopenPolicy` (case-specific, added via migration)
- `StageAgingConfig`/`SalesGoal` (opportunity-specific, not in RLS list)
- `OpportunityLineItem` (not in RLS list)
- `InvoiceTemplate`/`Product`/`InvoiceLineItem`/`Payment`/`Estimate`/`EstimateLineItem`/`RecurringInvoice`/`RecurringInvoiceLineItem` (not in RLS list)

---

## Relationship Patterns

### Common FK patterns
- **`org` → Org (CASCADE)**: Every multi-tenant entity has this FK. The `org` field is the foundation of RLS isolation.
- **`assigned_to` → Profile (M2M)**: Assignment to multiple users. Present on Account, Lead, Contact, Opportunity, Case, Task, Invoice, Estimate, RecurringInvoice.
- **`teams` → Teams (M2M)**: Team-based assignment. Present on Account, Lead, Contact, Opportunity, Case, Task, Invoice, Estimate, RecurringInvoice.
- **`tags` → Tags (M2M)**: Tagging/categorization. Present on Account, Lead, Contact, Opportunity, Case, Task.

### Generic Foreign Keys
- **Comment** and **Attachments** use Django's ContentType framework for generic relations to any model (`content_type` + `object_id` → `content_object`)

### Self-Referential
- **Case.merged_into** → Case (SET_NULL) — merge tracking
- **Case.parent** → Case (SET_NULL) — parent/child hierarchy (Tier 3, max depth 3)

### Key Unique Constraints
| Constraint | Purpose |
|-----------|---------|
| `Lower("name") + "org"` on Account | Case-insensitive unique account name per org |
| `Lower("email") + "org"` on Lead/Contact | Unique email per org (when non-null) |
| `"org" + "is_default"` on LeadPipeline/CasePipeline/TaskPipeline | One default pipeline per org |
| `"org" + "priority"` on EscalationPolicy | One escalation policy per priority per org |
| `"org" + "address"` on InboundMailbox | Unique inbound email address per org |
| `"org" + "message_id"` on EmailMessage | Unique Message-ID per org |
| `"profile" + ended_at__isnull=True` on TimeEntry | One active timer per profile |
| `"invoice_number"` on Invoice | Globally unique |
| `"estimate_number"` on Estimate | Globally unique |
| `"public_token"` on Invoice/Estimate | Globally unique for client portal |
| `"token_hash"` on PersonalAccessToken | Globally unique |
| `"sku" + "org"` on Product | Unique SKU per org |
| `"slug" + "org"` on Tags | Unique tag slug per org |
| `"user" + "org"` on Profile | One profile per user per org |
| `"phone" + "org"` on Profile | Unique phone per org |
| `"board" + "name"` on BoardColumn | Unique column name per board |
| `"board" + "profile"` on BoardMember | Unique membership per board |
| `"pipeline" + "name"` on LeadStage/CaseStage/TaskStage | Unique stage name per pipeline |
| `"org" + "target_model" + "key"` on CustomFieldDefinition | Unique custom field key per org+model |
| `"calendar" + "date"` on BusinessHoliday | Unique holiday per calendar date |
| `"org" + "is_default"` on BusinessCalendar | One default calendar per org |
| `"case" + "profile"` on CaseWatcher | Unique watcher per case |

### Check Constraints
| Constraint | Entity | Rule |
|-----------|--------|------|
| `account_revenue_non_negative` | Account | annual_revenue ≥ 0 or null |
| `lead_probability_range` | Lead | probability 0-100 |
| `lead_amount_non_negative` | Lead | opportunity_amount ≥ 0 or null |
| `opportunity_probability_range` | Opportunity | probability 0-100 |
| `opportunity_amount_non_negative` | Opportunity | amount ≥ 0 or null |
| `time_entry_end_after_start` | TimeEntry | ended_at ≥ started_at or null |
| `macro_scope_owner_consistent` | Macro | org scope → no owner; personal scope → has owner |

---

## Notes
- **schema.yml** is an OpenAPI 3.0 spec describing the REST API surface — it defines request/response schemas (e.g., `LeadCreateSwaggerRequest`, `CreateContactRequest`, `TeamswaggerCreateRequest`) but does NOT define the database schema. The actual data model lives in the Django `models.py` files.
- All entities use UUID primary keys (except `User` which uses UUID too, and `MagicLinkToken` which uses UUID).
- The `BaseModel` → `AuditModel` → `TimeAuditModel` + `UserAuditModel` inheritance chain provides `created_at`, `updated_at`, `created_by`, `updated_by` on every entity.
- `AssignableMixin` is an abstract mixin providing `get_team_users`, `get_team_and_assigned_users` helpers for entities with `assigned_to` + `teams` M2M fields.