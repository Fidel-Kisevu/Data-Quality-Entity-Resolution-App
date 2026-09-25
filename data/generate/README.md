# Dataset Generation

## Quick run

```bash
cd dataq
pip install faker pandas openpyxl
python data/generate/generate_datasets.py
```

Re-running with the same seed (`42`) produces identical files.

## Outputs

| Path | Description |
|------|-------------|
| `data/samples/crm_customers.csv` | ~189 CRM customers |
| `data/samples/erp_customers.csv` | ~156 ERP customers |
| `data/samples/erp_transactions.csv` | ~458 transactions |
| `data/samples/marketing_customers.xlsx` | ~176 marketing customers |
| `data/ground_truth/ground_truth.csv` | True entity mappings |
| `data/ground_truth/injected_issues.json` | Every deliberate issue + rule_id |
| `data/ground_truth/data_dictionary.md` | Column reference |

## Configuration

Edit `config.py` to change counts, rates, or seed.
