
# ET Reco

Aggregate recommendations from Economic Times



## Screenshots

![ET Reco Dashboard](screenshots/et_reco_dashboard.png?raw=true "ET Reco Dashboard")



## Run Locally

Clone the project

```bash
git clone https://github.com/ishan-agarwal/etreco.git
```

Go to the project directory

```bash
cd etreco
```

Docker Command to run Grafana 

```bash
mkdir mysql_data
docker compose up -d
```

## Helpful Commands

open mysql shell
```bash
docker exec -it mysql_container mysql -u admin -p ETRECODB
```