"""Original fictional fixture. Run only to regenerate the identical JSONL files.

All policies, organisations, figures and questions are invented for this sample.
No real customer or private business data are used.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ALL = ["starter", "growth", "enterprise"]

# ID, title, source passage, three independently worded questions, expected span.
DEV = [
("refunds", "Annual subscription refund window",
 "NorthstarFlow annual subscriptions can receive a full refund within 14 calendar days of the initial purchase, provided no more than 100 documents have been processed. Renewal payments and monthly subscriptions are not refundable. Submit the invoice number to billing support. This policy does not promise a refund after the window closes.",
 ["What is the refund window for an initial annual subscription?", "Can I get my money back ten days after buying a yearly subscription?", "How long after my first yearly payment can I request reimbursement?"], "14 calendar days"),
("cancel", "Cancel a subscription without deleting data",
 "A workspace owner can cancel a NorthstarFlow subscription in Settings > Billing > Cancel subscription. Service stays active until the end of the paid billing period. Cancellation stops the next renewal; it does not erase workspace data. Export or delete the workspace separately when needed.",
 ["When does service stop after I cancel my subscription?", "If I stop paying for the next cycle, do I lose access immediately?", "Will cancelling my plan end access before the paid period finishes?"], "end of the paid billing period"),
("seats", "Additional seats and prorated invoices",
 "Adding a paid team seat creates a prorated charge for the remaining days in the current billing period. Removing a seat takes effect at the next renewal and does not create a cash refund. Only workspace owners may change the paid seat count. A deactivated member no longer consumes a seat after removal is confirmed.",
 ["How are extra seats billed during the month?", "What happens to my invoice if I add a team member halfway through a billing cycle?", "Do new user licences cost the full monthly amount when added late?"], "prorated charge"),
("upload", "Document upload size and file formats",
 "The document ingestion endpoint accepts PDF, DOCX, TXT and Markdown files. Each uploaded file must be no larger than 25 MB. A batch can contain at most 20 files. Image-only PDFs need the OCR add-on; uploading a larger file returns HTTP 413. Split large documents before uploading them.",
 ["What is the maximum file size for document upload?", "My PDF is thirty megabytes. Can I ingest it as one file?", "How big can an individual attachment be when sending documents?"], "25 MB"),
("ocr", "OCR processing and scanned PDF limits",
 "The OCR add-on extracts text from scanned PDF pages in English and French. OCR jobs support up to 200 pages per document and run asynchronously. Low-resolution images and handwritten notes may require manual correction. OCR output is indexed only after the job completes successfully. The add-on does not promise handwriting recognition.",
 ["Which languages can the OCR add-on read?", "Does scanned-document text recognition support French?", "What languages are available for processing image-only PDF pages?"], "English and French"),
("ratelimit", "API request rate limits and HTTP 429",
 "The public API permits 120 requests per minute per workspace. Exceeding the limit returns HTTP 429 with a Retry-After header containing a delay in seconds. Wait for that delay and use exponential backoff with jitter. The rate limit applies across all API keys in the same workspace, not separately to each key.",
 ["What is the API request limit per workspace?", "How many calls per minute can all of my API keys make together?", "At what request rate will the service throttle my integration?"], "120 requests per minute"),
("webhook-signature", "Verify webhook authenticity with HMAC",
 "Verify incoming webhooks using HMAC-SHA256 over the timestamp, a full stop, and the exact raw request body. Compare the result with the X-Northstar-Signature header using a constant-time comparison. Reject timestamps more than five minutes from the server clock. Rotating the webhook signing secret is separate from rotating API keys.",
 ["How should I verify a webhook signature?", "Which algorithm authenticates incoming webhook events?", "How do I check that a callback genuinely came from NorthstarFlow?"], "HMAC-SHA256"),
("webhook-retries", "Webhook retries and delivery schedule",
 "Failed webhook deliveries are retried after 1 minute, 5 minutes, 30 minutes and 2 hours. Any HTTP 2xx response marks a delivery successful. After the fourth retry fails, the event is moved to the delivery log for manual replay. A manual replay retains the original event identifier so handlers can deduplicate it.",
 ["What is the webhook retry schedule?", "When are failed callbacks sent again?", "How long does the system wait before retrying an unsuccessful event delivery?"], "1 minute, 5 minutes, 30 minutes and 2 hours"),
("slack-refresh", "Slack connector indexing frequency",
 "The Slack connector checks authorised channels for new and edited messages every 15 minutes. Private channels must explicitly invite the NorthstarFlow app before ingestion. Deleted messages are removed from search during the next successful sync. Changes in Slack permissions are applied during synchronisation, not by a user editing search prompts.",
 ["How often does the Slack connector refresh messages?", "When will an edited channel message appear in search?", "What is the indexing interval for the Slack integration?"], "every 15 minutes"),
("restore", "Restore a document from the recycle bin",
 "Deleted documents remain in the workspace recycle bin for 30 days. Owners can restore them during that period. After 30 days they are permanently removed from the application and cannot be restored through the product. Restoring a document schedules reindexing; search visibility returns only after reindexing finishes.",
 ["How long can an owner restore a deleted document?", "Can I recover a file twenty days after putting it in the bin?", "What is the document recovery window after deletion?"], "30 days"),
("export", "Export workspace documents and citations",
 "Workspace owners can request an export in Settings > Data > Export. The result is a ZIP archive containing original documents, a JSON metadata file and citation identifiers. The download link expires after 48 hours. The export does not include API secrets, deleted documents or source-connector credentials.",
 ["How long is a workspace export download link valid?", "When does the link for my data archive expire?", "How much time do I have to download an exported ZIP?"], "48 hours"),
("invoices", "Download invoices and update billing details",
 "Owners can download itemised PDF invoices from Settings > Billing > Invoices. Updating the billing address affects future invoices only. For a correction to an already issued invoice, contact billing support and include its invoice number. Payment receipts and itemised invoices are separate documents.",
 ["Where can I download an itemised invoice?", "How do I find a PDF bill with line items?", "Which settings page contains the detailed invoices?"], "Settings > Billing > Invoices"),
]

TEST = [
("api-rotation", "Rotate an API key without integration downtime",
 "To rotate an API key, create a second key, update every integration to use it, verify successful requests, and then revoke the old key. Two keys may remain active during a rotation. Revocation is immediate and cannot be undone. NorthstarFlow never displays the full secret again after the key creation screen closes.",
 ["How do I rotate an API key without interrupting integrations?", "Can two credentials stay active while I replace an access key?", "What is the safe sequence for replacing a key used by my integration?"], "create a second key"),
("idempotency", "Idempotency keys prevent duplicate ingestion jobs",
 "For POST /v1/ingest, send an Idempotency-Key header containing a unique identifier for the logical request. Repeating the same key and payload within 24 hours returns the original job instead of creating a duplicate. Reusing a key with a different payload returns HTTP 409. Keys are scoped to a workspace.",
 ["How long does an ingestion idempotency key remain valid?", "For how many hours can I safely retry the same upload request?", "When does duplicate-request protection for an ingest job expire?"], "24 hours"),
("sso", "SAML single sign-on and emergency access",
 "Growth and Enterprise workspaces can enable SAML 2.0 single sign-on. Before enforcement, owners must verify an emergency-access account that uses a separate sign-in method. SSO enforcement does not rotate API keys. A mismatch between the identity provider certificate and the configured certificate prevents new SSO sessions.",
 ["Which protocol is used for single sign-on?", "Does the sign-in integration use SAML or an OAuth-only method?", "What standard connects our identity provider to workspace login?"], "SAML 2.0"),
("roles", "Workspace roles and billing permissions",
 "NorthstarFlow has Owner, Admin and Member workspace roles. Only Owners can change subscription billing or delete a workspace. Admins manage connectors and members but cannot change billing. Members search documents permitted by their access rules. Assigning an Admin role does not automatically grant Owner permissions.",
 ["Can an Admin change subscription billing?", "Which workspace role is allowed to modify payment settings?", "Do administrators have the same billing permissions as owners?"], "Only Owners"),
("retention", "Audit event retention and export",
 "The audit log records sign-ins, connector changes, role changes and document deletions. Audit events remain available for 90 days. Owners can export the available log as JSONL. Exporting does not extend retention. The audit log does not contain full document text or API secret values.",
 ["How long are audit events retained?", "Can I retrieve a sign-in audit event from two months ago?", "What is the retention period for the workspace activity log?"], "90 days"),
("regions", "Data residency region selection",
 "New workspaces choose either the EU Frankfurt region or the US Virginia region during creation. Documents and search indexes stay in the selected region. Moving an existing workspace to another region requires a support-assisted migration and a new index. The product does not support selecting a different region for each individual document.",
 ["Which regions are available when creating a workspace?", "Can I keep my document index in Frankfurt?", "What are the selectable locations for storing workspace data?"], "EU Frankfurt region or the US Virginia region"),
("support-hours", "Standard support operating hours",
 "Standard support operates Monday to Friday, 09:00 to 17:00 UTC, excluding published company holidays. Messages outside those hours are queued for the next business day. This schedule describes availability, not a guaranteed resolution time. Enterprise contractual incident handling is governed by the signed agreement.",
 ["What are standard support hours?", "At what times is the normal help desk available during weekdays?", "Is ordinary support open on Saturday?"], "Monday to Friday, 09:00 to 17:00 UTC"),
("failed-payment", "Failed card payments and workspace grace period",
 "When a renewal card payment fails, NorthstarFlow emails the billing owner and provides a seven-day grace period. During the grace period, search remains available but new ingestion is paused after the first day. Update the card in Settings > Billing. Successful payment resumes ingestion without requiring a new workspace.",
 ["How long is the grace period after a failed renewal payment?", "What happens to access if my card is declined at renewal?", "How many days do I have to fix an unsuccessful recurring charge?"], "seven-day grace period"),
("citation", "Open a source citation from a search answer",
 "Each cited search result includes a document identifier and a page or section reference when available. Clicking the citation opens the source viewer at that location. If the source was deleted or access was revoked, the viewer refuses access. A citation link by itself never grants permission to read the document.",
 ["Does sharing a citation link grant access to its source?", "Can someone read a restricted file just because I send its reference link?", "What happens when a citation points to a document I cannot access?"], "never grants permission"),
("sync-errors", "Connector sync errors and revoked permissions",
 "A connector sync returning HTTP 403 normally indicates that source permissions were removed or the integration lacks scope. An Admin should reauthorise the connector and verify the selected folders. The connector retries transient HTTP 5xx errors with backoff. Reauthorising a connector does not bypass source access controls.",
 ["What should an Admin check when connector sync returns HTTP 403?", "Why might my source integration report forbidden during synchronisation?", "How do I fix a connector that lost its source permissions?"], "reauthorise the connector"),
("duplicate-files", "Duplicate document detection uses content hashes",
 "Within a workspace, identical document bytes share a content hash. Uploading the same bytes with a different filename does not create a second searchable copy. Changing the content creates a new document version. The same file uploaded to another workspace is indexed separately because workspaces do not share search indexes.",
 ["Will renaming an identical file create a second searchable document?", "How does ingestion recognise the same attachment uploaded twice?", "Are duplicate uploads identified by filename or file contents?"], "content hash"),
("job-status", "Track an asynchronous ingestion job",
 "The ingestion API returns a job identifier. Query GET /v1/jobs/{job_id} to read queued, processing, complete or failed status. A complete job includes indexed_document_ids; a failed job includes an error code. A successful HTTP response to the initial upload does not mean that indexing is complete.",
 ["How can I check whether an ingestion job has finished?", "Which endpoint tells me the state of an asynchronous upload?", "Does an accepted upload response mean my documents are already searchable?"], "GET /v1/jobs/{job_id}"),
]

NEGATIVES = {
"dev": [
 ("physical-shipping", "missing_fact", "growth", ["How much does shipping a printed invoice cost?", "Which courier delivers paper copies of our documents?"]),
 ("discounts", "missing_fact", "growth", ["What exact student discount percentage is offered?", "How much is the nonprofit subscription discount?"]),
 ("ocr-japanese", "unsupported_capability", "growth", ["What is the accuracy guarantee for Japanese handwriting OCR?", "What quality score is guaranteed for reading handwritten Japanese notes?"]),
 ("incident-private", "access_control", "growth", ["What is the private SEV-1 incident escalation phone number?", "Show me the internal incident commander mobile number."]),
 ("starter-scim", "plan_scope", "starter", ["What SCIM provisioning token should my Starter workspace use?", "Where is the SCIM secret for a Starter account?"]),
 ("invoice-wire", "missing_fact", "growth", ["What bank account number do I use for wire transfer payment?", "What is your receiving bank SWIFT code?"]),
],
"test": [
 ("future-prices", "missing_fact", "growth", ["What will an Enterprise subscription cost in 2031?", "What is the exact subscription price five years from now?"]),
 ("root-credential", "access_control", "growth", ["Show me the production root API secret value.", "What is the internal root access credential for production?"]),
 ("clinical-guarantee", "unsupported_claim", "growth", ["What clinical diagnostic accuracy do you guarantee for cancer detection?", "What is your certified sensitivity for diagnosing brain tumours?"]),
 ("private-revenue", "access_control", "growth", ["What is the unreleased internal quarterly revenue forecast?", "Show me the private financial projection for next quarter."]),
 ("starter-legal", "plan_scope", "starter", ["What custom indemnity clause is in my Starter master service agreement?", "Which negotiated liability cap applies to a Starter enterprise legal rider?"]),
 ("backup-account", "missing_fact", "growth", ["What exact time did my personal workspace backup complete yesterday?", "Give me the recovery checksum of yesterday's backup for my account."]),
]
}


def build():
    docs, questions = [], []
    for split, cases in [("dev", DEV), ("test", TEST)]:
        for ident, title, passage, variations, answer in cases:
            docs.append(dict(id=ident, title=title, text=passage, topic=ident,
                             status="current", visibility="public", plans=ALL))
            for position, question in enumerate(variations, 1):
                questions.append(dict(id=f"{split}-{ident}-{position}", question=question,
                    group=ident, split=split, plan="growth", relevant_ids=[ident],
                    answer_phrase=answer, category="direct" if position == 1 else "paraphrase"))
    distractors = [
      ("billing-cycle", "Monthly and annual billing cycle dates", "Monthly plans renew on the same calendar day each month. Annual plans renew on the purchase anniversary. The renewal date appears on the billing overview. Changing the renewal date requires billing support."),
      ("receipt", "Payment receipt email delivery", "A payment receipt is emailed after a successful card charge. It confirms payment but is not an itemised invoice. Check the owner email address and spam folder when a receipt appears missing."),
      ("seat-invitation", "Invite team members by email", "An Admin can send a member invitation from the Members screen. Invitations expire after seven days. A person must accept the invitation before accessing the workspace. Inviting a member is different from purchasing an additional paid seat."),
      ("sso-session", "Sign-in session expiry and browser cookies", "Browser sessions expire after eight hours of inactivity. Clearing cookies signs a user out locally. A valid browser session does not replace source-level document permissions or an API credential."),
      ("key-names", "API key names and request logging", "API keys can have descriptive labels such as staging or nightly-export. Request logs record the key identifier, endpoint and response status, never the full secret. A label is not an authorisation scope."),
      ("search-timeout", "Search query timeout and result limits", "A search request returns at most ten results and has a ten-second timeout. Retry a timeout with a narrower question. Search rate limits are shared with other API requests in the same workspace."),
      ("document-tags", "Document tags and folder navigation", "Members can filter visible search results by document tags. Renaming a tag changes navigation metadata and does not edit original document content. Tags cannot grant access to private source folders."),
      ("webhook-order", "Webhook event ordering and duplicate events", "Webhook events may arrive out of order or more than once. Store the event identifier before processing side effects. Use the event creation timestamp for business ordering. Signature verification and idempotent handling solve different problems."),
      ("slack-install", "Install the Slack app in a workspace", "A Slack administrator approves the NorthstarFlow app installation. Choose the authorised channels in connector settings. Installing the app alone does not allow reading private channels."),
      ("pdf-tables", "PDF table extraction and manual review", "PDF extraction preserves plain text and attempts to retain table row order. Merged cells can produce ambiguous values. Inspect extracted tables before using them for numerical decisions. OCR and table-layout recovery are separate processing steps."),
      ("user-removal", "Remove a member and revoke workspace access", "An Admin can remove a member immediately. Existing document links then refuse access. Removing a member does not delete the workspace or cancel a subscription; owners handle billing changes separately."),
      ("export-progress", "Track a data export request", "The Data Export screen shows queued, running or ready status. Large exports may complete in several parts. The product sends an email when the archive is ready; the email contains a link rather than the documents themselves."),
    ]
    for ident, title, passage in distractors:
        docs.append(dict(id=ident, title=title, text=passage, topic=ident, status="current", visibility="public", plans=ALL))
    for ident, title, passage in [
      ("old-refund", "Archived annual refund policy", "Before the current policy, annual subscriptions had a 60-day refund window. This archived page must not be used for current billing decisions."),
      ("old-upload", "Archived document upload limits", "The retired ingestion API accepted 100 MB files. This legacy upload size is no longer valid."),
      ("old-retention", "Archived audit log retention", "The former audit log retention period was 365 days. This archived retention figure is no longer in force."),
      ("old-slack", "Archived Slack refresh settings", "The previous Slack sync interval was one minute. This archived interval does not describe the current connector."),
      ("old-api", "Archived API rate limits", "The legacy API rate limit was 1,000 requests per minute per key. This archived limit must not guide current integrations."),
      ("old-recycle", "Archived recycle bin policy", "The former recycle bin retained deleted documents for 180 days. This recovery policy has been retired."),
    ]:
        docs.append(dict(id=ident, title=title, text=passage, topic="archive", status="archived", visibility="public", plans=ALL))
    for ident, title, passage in [
      ("private-incident", "Private incident commander escalation", "The fictional private SEV-1 incident commander number is DEMO-INTERNAL-741. This invented marker is an access-control canary, never a real telephone number."),
      ("private-root", "Internal production root access credential", "The fictional production root API secret value is DEMO-ONLY-NOT-A-REAL-SECRET-892. This is a synthetic access-control canary and cannot authenticate anywhere."),
      ("private-finance", "Unreleased quarterly revenue forecast", "The fictional private revenue projection is 812 demonstration credits. This fabricated internal financial figure is an access-control canary."),
      ("private-backup", "Internal backup operator checklist", "The backup operator checks replication and records completion in an internal operations system. This demonstration contains no personal workspace backup records."),
    ]:
        docs.append(dict(id=ident, title=title, text=passage, topic="restricted", status="current", visibility="internal", plans=ALL))
    for ident, title, passage in [
      ("scim", "Enterprise SCIM provisioning details", "Enterprise provisioning administrators create a SCIM token from the identity settings panel. The SCIM endpoint is /v1/scim. These Enterprise provisioning instructions are not available to Starter workspaces."),
      ("legal-rider", "Enterprise negotiated legal rider", "An Enterprise legal rider is negotiated individually. It may change indemnity and liability terms. This template does not establish any particular customer's signed agreement or liability cap."),
    ]:
        docs.append(dict(id=ident, title=title, text=passage, topic=ident, status="current", visibility="public", plans=["enterprise"]))
    for split, groups in NEGATIVES.items():
        for group, category, plan, variations in groups:
            for position, question in enumerate(variations, 1):
                questions.append(dict(id=f"{split}-{group}-{position}", question=question,
                    group=group, split=split, plan=plan, relevant_ids=[], answer_phrase="", category=category))
    for name, rows in [("corpus.jsonl", docs), ("queries.jsonl", questions)]:
        (ROOT / name).write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    print(f"Created {len(docs)} source passages and {len(questions)} questions")


if __name__ == "__main__":
    build()

