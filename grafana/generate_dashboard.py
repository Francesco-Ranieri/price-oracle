import json
import os

# Read the json in price-oracle-dashboard.json
with open('grafana/price-oracle-dashboard.json') as f:
    data = json.load(f)

# Read all of the cripto names by listing files in ../airflow/assets/binance_1d and removing the .csv extension
criptos = [f.split('.')[0] for f in os.listdir('airflow/assets/binance_1d')]

# For each cripto, duplicate the first two panels in the dashboard, and change all occurernces of "BTCUSDT" to the cripto name
for cripto in criptos:
    data['panels'].append(json.loads(json.dumps(data['panels'][0]).replace('BTCUSDT', cripto)))
    data['panels'].append(json.loads(json.dumps(data['panels'][1]).replace('BTCUSDT', cripto)))

# Write the new dashboard to price-oracle-dashboard.json
with open('grafana/price-oracle-dashboard.json', 'w') as f:
    json.dump(data, f, indent=4)