
# ET Reco





## Run Locally

Clone the project

```bash
git clone https://github.com/ishan-agarwal/etreco.git
```

Go to the project directory

```bash
cd etreco
```

Install dependencies

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the Script

```bash
python src/recommend.py
```

Docker Command to run Grafana 

```bash
docker compose -f docker-compose-grafana.yaml up
```

Setting up a Daily Cron job 

Add a new script under `/etc/cron.daily/` with the contents

```bash
cd /path/to/etreco;
/path/to/etreco/venv/bin /path/to/etreco/src/recommend.py;
```