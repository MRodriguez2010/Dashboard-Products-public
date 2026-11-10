# Dashboard Products

Six local analytics demos cover employee sentiment, competitive pricing, market demand, subscription churn, brand reputation and a sales pipeline. The examples use synthetic data. The public portfolio preserves the standalone dashboard modules and replaces internal sales materials and workforce fixtures with fictional examples.

| Folder | Example |
| --- | --- |
| `employee-sentiment` | Compare fictional survey counts, inspect topic gaps and download a PowerPoint |
| `cpi-dashboard/backend` | Compare competitive price points by category |
| `market-heatmap` | Compare demand across regions and categories |
| `churn-dashboard/backend` | Review churn and revenue signals |
| `brand-dashboard/backend` | Inspect synthetic reputation metrics |
| `sales-workbench` | Group fictional opportunities by stage and reconcile weighted pipeline value |

## Run one dashboard

Create a virtual environment, activate it and install `requirements.txt`. For example:

```sh
python -m pip install -r requirements.txt
cd churn-dashboard/backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8003
```

For the pricing, market and brand dashboards, use the table’s folder and the same `app.main:app` entry point. For the sales workbench, use `app:app`. For employee sentiment, run `python server.py` from its folder. Each UI opens at the loopback address printed during startup. [Related employee sentiment projects](https://github.com/search?q=user%3AMRodriguez2010+topic%3Aemployee-sentiment-analysis&type=repositories)
