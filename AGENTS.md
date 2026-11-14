<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.

## What Lovable manages

Rules outside this block are the project's own. Change the pieces below in
Lovable, not by hand. With the [Lovable MCP](https://mcp.lovable.dev)
connected, `send_message` asks Lovable to do it; otherwise ask the user to
use the editor.

- **Database.** Do not add or edit `supabase/migrations/` or `drizzle/`.
  Ask Lovable to change the schema.
- **Generated files.** Do not edit a file whose header says it is automatically
  generated.
- **AI gateway.** Keep model calls on Lovable's gateway, and keep
  `LOVABLE_API_KEY` out of browser code.
- **Connectors.** Lovable provides native connectors. `list_connectors` shows
  which are enabled; `add_connector` only returns the dashboard link. When a
  connector is enabled, calls go through the connector gateway and need
  `LOVABLE_API_KEY`. When Lovable does not provide one, users can bring their
  own key and store it in Secrets.
- **Secrets.** Lovable manages them. Do not put secret values in the repo.
<!-- LOVABLE:END -->

## Application rules
- Keep the two health journeys in a shared client-side workspace with React state; this prototype must work without external APIs and reset on refresh.
- Keep clinical fixtures and deterministic educational explanations in a browser-safe data module; both journeys must read the same values.
- Label simulated imports and clinical model outputs as demonstration data; never present the prototype as a diagnostic or certified clinical system.

## Live API integration
- Keep public status reads in the browser; proxy authorizer, metrics and causal calls with authenticated server functions and a server-only token to prevent credential exposure.
- Scope live alert queries by the explicitly selected API patient ID, invalidate alerts and operational metrics after mutations, and keep live responses distinct from educational fixtures to avoid presenting synthetic measurements as imported data.
- Derive protected API patient IDs from the verified session; reject mismatched callback IDs to prevent cross-account access.
- Reject synthetic or unclassified sync before reading metrics/evaluating labs; show a direct owner-scoped ROOK portal link on entry.
- Sync before 30-day reads; preserve mode/counters in caches. Reject known placeholder PDF results to avoid false patient records.
- Send owner-scoped labs with exact names/units after consent, absent ferritin as null and absent confounders as zero under the provider contract.
- Handle ROOK returns in a public TanStack route after session restoration and return to the dashboard; URL parameters never prove authorization.

## PDF extraction
- Share conservative component-name and reference feedback across PDF review, displays and exports; preserve tri-state API status and never infer fasting, codes, conversions or five-level severity from numbers alone.
- Send consented files to Render /api/extrair with browser FormData (arquivo, motor=nuvem); show failures and returned motor without silent local substitution.
- Audit v3 metadata/references against full PDF text when available, not just the provider preview; absent fields and edited statuses stay unknown.
- Keep imported reports in separate session state with document patient identity and raw results/references; never merge them into demo charts or assign unvalidated LOINC/UCUM codes.
- Export imported observations as preliminary with per-document patient references and provenance; this prevents attributing another patient's document to the demo identity.

## Accounts and access
- Keep Cloud accounts separate from the session-only clinical demo; never label demo fixtures or local PDFs as a signed-in patient's shared medical record.
- Store privileges only in protected user_roles, grant admin access through single-use email-bound invitations, and enforce connection approval and revocation in database functions and RLS.
- Use the authenticated dashboard for account connections and keep the presentation, auth, and educational demo public; private server functions always require the generated auth middleware.

## Patient health records
- Keep persistent patient records in a dedicated dashboard component and authenticated functions, separate from the session-only demo, so fixtures never enter medical history.
- Store reviewed documents after ownership/storage consent in the private PDF bucket; convert images to PDF in-browser to retain the existing storage contract.
- Build history series from actual reports grouped by exact biomarker name and unit; never infer unit conversions or missing collection dates.
- Keep clinical records owner-only in RLS until an explicit medical-sharing feature is implemented; account connection approval alone must not grant new clinical access.
- Grant doctors structured report access only through patient-selected report shares plus an active approved connection; never extend this to PDF storage or wearable records.
- Keep exam safety questionnaires deterministic and explicitly non-predictive until a validated model is integrated; persist answers and send minimal in-app notices only with patient consent through an authenticated database function.
- Parse CSV wearables locally with strict columns, dates, units and per-day uniqueness before authenticated persistence; do not synthesize absent measurements.
- Read remote wearables through authenticated owner-scoped functions; show provider failures and keep remote readings separate from persisted CSV data.

- Build the patient overview from saved reports and latest wearable values per metric and source, preserving measurement dates and file provenance; do not apply laboratory reference labels to device metrics.

## Consultation scheduling
- Store doctor-published slots in Cloud and reserve/cancel through authenticated database functions with atomic locking and approved-connection checks; never generate placeholder availability.
- Keep patient scheduling in a dedicated dashboard section and display appointment dates in America/Sao_Paulo to prevent browser timezone ambiguity; the doctor agenda editor is a separate future surface.
