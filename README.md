
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

Docker Run Command to run Grafana 

```bash
docker run -d -p 3000:3000 --name=grafana \
  -e GF_PLUGIN_ALLOW_LOCAL_MODE=true \
  --user "$(id -u)" \
  --volume "$PWD/data:/var/lib/grafana" \
  grafana/grafana-oss
```

Setting up a Daily Cron job 

Add a new script under `/etc/cron.daily/` with the contents

```bash
cd /path/to/etreco;
/path/to/etreco/venv/bin /path/to/etreco/src/recommend.py;
```