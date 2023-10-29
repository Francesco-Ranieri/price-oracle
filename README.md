# big-data
Big Data exam


## Instructions

helm repo add apache-airflow https://airflow.apache.org
helm repo add apache-cassandra oci://registry-1.docker.io/bitnamicharts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add community-charts https://community-charts.github.io/helm-charts

## RUN
skaffold dev
skaffold dev --status-check=false
mlflow server --backend-store-uri sqlite:///:memory -p 5001

## TO DEBUG DAGS:
1) Install airflow on your host machine
2) Edit the `airflow.cfg` file (~/airflow/airflow.cfg) and set `allowed_deserialization_classes` to `common\..*`. 
3) Run `airflow connections add cassandra_default --conn-uri cassandra://cassandra:l1Lc%C2%A3C9eKFR5@localhost:9042/price_oracle`
4) Run `airflow db migrate`
5) Debug the dag file as usual


## DATA

https://www.cryptodatadownload.com/data/cexio/


# Download data:

1) Go to https://www.cryptodatadownload.com/data/binance/
2) Filter by "USDT"
3) Change the HTML of the select to show 1000 items
4) Run the following code in the console

```javascript
// Get all links with href attributes that start with the specified URL
var links = document.querySelectorAll('a[href^="https://www.cryptodatadownload.com/cdd/Binance"]');

// Function to download the links with a delay
function downloadWithDelay(linkIndex) {
    if (linkIndex < links.length) {
        var link = links[linkIndex];
        var url = link.href;
        var fileName = url.split('/').pop().replace('.csv', ''); // Extract and format the filename

        fetch(url)
            .then(response => response.blob())
            .then(blob => {
                var a = document.createElement('a');
                a.href = window.URL.createObjectURL(blob);
                a.download = fileName + '.csv'; // Add the ".csv" extension
                a.style.display = 'none';
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                // Continue with the next link after a delay (e.g., 2 seconds)
                setTimeout(function () {
                    downloadWithDelay(linkIndex + 1);
                }, 2000); // 2000 milliseconds = 2 seconds
            })
            .catch(error => {
                console.error('Error:', error);
                // Continue with the next link after a delay (e.g., 2 seconds)
                setTimeout(function () {
                    downloadWithDelay(linkIndex + 1);
                }, 2000); // 2000 milliseconds = 2 seconds
            });
    }
}

// Start downloading with a delay from the first link
downloadWithDelay(0);
```