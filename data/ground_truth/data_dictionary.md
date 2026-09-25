# DataQ — Sample Data Dictionary

**Generated:** 2026-09-24T14:07:48.689068Z  
**Seed:** 42  
**Industry:** E-commerce  
**Locale:** Kenyan-mixed  

## Files

| File | Rows | Description |
|------|------|-------------|
| `crm_customers.csv` | 189 | CRM customer master |
| `erp_customers.csv` | 156 | ERP customer master |
| `erp_transactions.csv` | 458 | ERP orders / payments |
| `marketing_customers.xlsx` | 176 | Marketing list (Excel) |
| `ground_truth.csv` | 971 | True entity mappings |
| `injected_issues.json` | 179 | Every deliberate quality issue |

## Customer columns
- `source_customer_id` — ID in the source system
- `full_name`, `first_name`, `last_name`
- `email`, `phone` (various Kenyan + international formats)
- `date_of_birth` (ISO or null / invalid)
- `address_line1`, `city`, `country` (ISO-ish)
- `status` — active / inactive / unknown
- `source_system` — CRM / ERP / MKT
- `true_id` — ground-truth entity key (for evaluation only; not present in real systems)

## Transaction columns
- `source_transaction_id`, `source_customer_id`
- `transaction_date`, `amount`, `currency` (KES / USD / EUR + invalid)
- `description`, `status`
- `true_customer_id` — links back to canonical customer

## Injected issue categories
See `injected_issues.json` for the full list with rule_id, record_id, and evidence.
