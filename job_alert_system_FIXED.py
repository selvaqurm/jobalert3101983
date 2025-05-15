import requests
import smtplib
import time
import json
import schedule
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("job_alert.log"), logging.StreamHandler()]
)
logger = logging.getLogger("gold_job_alerts")

# Configuration - update these variables
EMAIL_ADDRESS = os.getenv("JOB_ALERT_EMAIL")  # Your email to receive alerts
EMAIL_PASSWORD = os.getenv("JOB_ALERT_PASS")  # App password for Gmail
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")

# Search settings
SEARCH_FREQUENCY = "every_30_minutes"  # "every_30_minutes", "hourly", "daily", or "weekly"
ALERT_TIME = "08:00"  # Time of day to send alerts (24-hour format)
SEARCH_LIMIT_PER_COUNTRY = 10  # Limit results per country to avoid excessive emails
MAX_JOB_AGE_DAYS = 30  # Only include jobs posted within this many days

# Search terms related to gold and precious metals jobs
SEARCH_TERMS = [
    "Gold",
    "Gold bullion",
    "Gold trader",
    "Gold Bullion Manager",
    "Gold dealer",
    "Gold dealing manager",
    "precious metal",
    "precious metal specialist",
    "bullion dealer",
    "gold consultant",
    "precious metals broker",
    "gold trading analyst",
    "gold refiner",
    "gold assayer",
    "gold vault manager",
    "metal trading specialist"
]

# Additional search terms to refine results
SECONDARY_TERMS = [
    "trading",
    "investment",
    "banking",
    "finance",
    "refinery",
    "vault",
    "dealer",
    "broker",
    "wealth management",
    "commodity",
    "treasury"
]

# Regional job boards
REGIONAL_JOB_BOARDS = {
    "asia": [
        "naukri.com", "timesjobs.com", "shine.com", "jobstreet.com", "jobsdb.com",
        "bayt.com", "gulftalent.com", "karir.com", "jobkorea.co.kr", "jobstreet.co.id"
    ],
    "europe": ["eurojobs.com", "euractiv.com", "europelanguagejobs.com", "eures.europa.eu"],
    "north_america": ["usajobs.gov", "workopolis.com", "jobbank.gc.ca", "empleos.gob.mx"],
    "south_america": ["laborum.com", "bumeran.com", "computrabajo.com", "vagas.com.br"],
    "oceania": ["seek.com.au", "trademe.co.nz", "adzuna.com.au", "workingholidays.co.nz"],
    "africa": ["careerjunction.co.za", "pnet.co.za", "jobwebkenya.com", "brightermonday.com"]
}

# Global job boards that cover multiple regions
GLOBAL_JOB_BOARDS = ["linkedin.com", "glassdoor.com", "indeed.com", "monster.com", "careerbuilder.com"]

# Gold and precious metals specific job boards
GOLD_SPECIFIC_JOB_BOARDS = [
    "miningjobsearch.com",
    "infomine.com/careers",
    "miningconnection.com",
    "careermine.com",
    "mineralsjobs.com",
    "bullionstar.com/careers",
    "jobs.goldhub.com",
    "preciousmetalscareers.com",
    "kitco.com/jobs",
    "mineralprocessing.com/jobs"
]
from typing import Dict, Any

# Countries organized by region
COUNTRIES: Dict[str, Dict[str, Any]] = {
    # Global entry for global job boards
    "global": {"name": "Global", "domains": GLOBAL_JOB_BOARDS, "region": "global"},
    
    # Asia
    "afghanistan": {"name": "Afghanistan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "armenia": {"name": "Armenia", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "azerbaijan": {"name": "Azerbaijan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "bahrain": {"name": "Bahrain", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "bangladesh": {"name": "Bangladesh", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "bhutan": {"name": "Bhutan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "brunei": {"name": "Brunei", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "cambodia": {"name": "Cambodia", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "china": {"name": "China", "domains": ["51job.com", "zhaopin.com", "liepin.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "cyprus": {"name": "Cyprus", "domains": REGIONAL_JOB_BOARDS["asia"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "georgia": {"name": "Georgia", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "india": {"name": "India", "domains": ["naukri.com", "timesjobs.com", "shine.com", "iimjobs.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "indonesia": {"name": "Indonesia", "domains": ["jobstreet.co.id", "karir.com", "jobs.id"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "iran": {"name": "Iran", "domains": ["irantalent.com", "karboom.io"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "iraq": {"name": "Iraq", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "israel": {"name": "Israel", "domains": ["alljobs.co.il", "drushim.co.il"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "japan": {"name": "Japan", "domains": ["daijob.com", "careercross.com", "japan-dev.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "jordan": {"name": "Jordan", "domains": ["akhtaboot.com", "bayt.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "kazakhstan": {"name": "Kazakhstan", "domains": ["hh.kz", "rabota.kz"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "kuwait": {"name": "Kuwait", "domains": ["bayt.com", "gulftalent.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "kyrgyzstan": {"name": "Kyrgyzstan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "laos": {"name": "Laos", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "lebanon": {"name": "Lebanon", "domains": ["bayt.com", "olx.com.lb"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "malaysia": {"name": "Malaysia", "domains": ["jobstreet.com.my", "jobstore.com", "wobb.co"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "maldives": {"name": "Maldives", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "mongolia": {"name": "Mongolia", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "myanmar": {"name": "Myanmar", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "nepal": {"name": "Nepal", "domains": ["merojob.com", "kumarijob.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "north_korea": {"name": "North Korea", "domains": GLOBAL_JOB_BOARDS, "region": "asia"},
    "oman": {"name": "Oman", "domains": ["bayt.com", "gulftalent.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "pakistan": {"name": "Pakistan", "domains": ["rozee.pk", "mustakbil.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "palestine": {"name": "Palestine", "domains": ["jobs.ps", "bayt.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "philippines": {"name": "Philippines", "domains": ["jobstreet.com.ph", "kalibrr.com", "mynimo.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "qatar": {"name": "Qatar", "domains": ["bayt.com", "gulftalent.com", "qatarliving.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "saudi_arabia": {"name": "Saudi Arabia", "domains": ["bayt.com", "gulftalent.com", "mihnati.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "singapore": {"name": "Singapore", "domains": ["jobstreet.com.sg", "jobscentral.com.sg", "careers.gov.sg"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "south_korea": {"name": "South Korea", "domains": ["saramin.co.kr", "jobkorea.co.kr"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "sri_lanka": {"name": "Sri Lanka", "domains": ["topjobs.lk", "xpressjobs.lk"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "syria": {"name": "Syria", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "taiwan": {"name": "Taiwan", "domains": ["104.com.tw", "1111.com.tw"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "tajikistan": {"name": "Tajikistan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "thailand": {"name": "Thailand", "domains": ["jobsdb.co.th", "jobthai.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "timor_leste": {"name": "Timor-Leste", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "turkey": {"name": "Turkey", "domains": ["kariyer.net", "yenibiris.com", "secretcv.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "turkmenistan": {"name": "Turkmenistan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "uae": {"name": "United Arab Emirates", "domains": ["bayt.com", "gulftalent.com", "dubizzle.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "uzbekistan": {"name": "Uzbekistan", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "vietnam": {"name": "Vietnam", "domains": ["vietnamworks.com", "careerbuilder.vn", "itviec.com"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    "yemen": {"name": "Yemen", "domains": REGIONAL_JOB_BOARDS["asia"] + GLOBAL_JOB_BOARDS, "region": "asia"},
    
    # Europe
    "albania": {"name": "Albania", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "andorra": {"name": "Andorra", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "austria": {"name": "Austria", "domains": ["karriere.at", "stepstone.at"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "belarus": {"name": "Belarus", "domains": ["jobs.tut.by", "praca.by"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "belgium": {"name": "Belgium", "domains": ["references.be", "stepstone.be"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "bosnia": {"name": "Bosnia and Herzegovina", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "bulgaria": {"name": "Bulgaria", "domains": ["jobs.bg", "jobtiger.bg"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "croatia": {"name": "Croatia", "domains": ["moj-posao.net", "posao.hr"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "czech_republic": {"name": "Czech Republic", "domains": ["jobs.cz", "prace.cz"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "denmark": {"name": "Denmark", "domains": ["jobindex.dk", "jobnet.dk"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "estonia": {"name": "Estonia", "domains": ["cv.ee", "cvkeskus.ee"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "finland": {"name": "Finland", "domains": ["mol.fi", "oikotie.fi"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "france": {"name": "France", "domains": ["pole-emploi.fr", "apec.fr", "monster.fr"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "germany": {"name": "Germany", "domains": ["stepstone.de", "monster.de", "xing.com"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "greece": {"name": "Greece", "domains": ["kariera.gr", "skywalker.gr"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "hungary": {"name": "Hungary", "domains": ["profession.hu", "jobline.hu"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "iceland": {"name": "Iceland", "domains": ["vinnumalastofnun.is", "alfred.is"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "ireland": {"name": "Ireland", "domains": ["irishjobs.ie", "indeed.ie"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "italy": {"name": "Italy", "domains": ["monster.it", "infojobs.it"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "kosovo": {"name": "Kosovo", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "latvia": {"name": "Latvia", "domains": ["cv.lv", "workingday.lv"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "liechtenstein": {"name": "Liechtenstein", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "lithuania": {"name": "Lithuania", "domains": ["cvbankas.lt", "cvonline.lt"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "luxembourg": {"name": "Luxembourg", "domains": ["jobfinder.lu", "monster.lu"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "malta": {"name": "Malta", "domains": ["timesofmalta.com/classifieds/jobs", "keepmeposted.com"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "moldova": {"name": "Moldova", "domains": ["rabota.md", "cariera.md"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "monaco": {"name": "Monaco", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "montenegro": {"name": "Montenegro", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "netherlands": {"name": "Netherlands", "domains": ["nationalevacaturebank.nl", "monsterboard.nl"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "north_macedonia": {"name": "North Macedonia", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "norway": {"name": "Norway", "domains": ["finn.no/jobb", "nav.no"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "poland": {"name": "Poland", "domains": ["pracuj.pl", "infopraca.pl"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "portugal": {"name": "Portugal", "domains": ["net-empregos.com", "expressoemprego.pt"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "romania": {"name": "Romania", "domains": ["ejobs.ro", "bestjobs.ro"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "russia": {"name": "Russia", "domains": ["hh.ru", "superjob.ru"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "san_marino": {"name": "San Marino", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "serbia": {"name": "Serbia", "domains": ["infostud.com", "poslovi.infostud.com"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "slovakia": {"name": "Slovakia", "domains": ["profesia.sk", "kariera.sk"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "slovenia": {"name": "Slovenia", "domains": ["mojedelo.com", "zaloske.si"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "spain": {"name": "Spain", "domains": ["infojobs.net", "monster.es"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "sweden": {"name": "Sweden", "domains": ["arbetsformedlingen.se", "monster.se"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "switzerland": {"name": "Switzerland", "domains": ["jobup.ch", "indeed.ch"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "ukraine": {"name": "Ukraine", "domains": ["rabota.ua", "work.ua"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "united_kingdom": {"name": "United Kingdom", "domains": ["gov.uk/find-a-job", "reed.co.uk", "indeed.co.uk", "monster.co.uk", "totaljobs.com"] + REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},
    "vatican_city": {"name": "Vatican City", "domains": REGIONAL_JOB_BOARDS["europe"] + GLOBAL_JOB_BOARDS, "region": "europe"},

    # North America
    "antigua_and_barbuda": {"name": "Antigua and Barbuda", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "bahamas": {"name": "Bahamas", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "barbados": {"name": "Barbados", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "belize": {"name": "Belize", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "canada": {"name": "Canada", "domains": ["jobbank.gc.ca", "indeed.ca", "linkedin.com"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "costa_rica": {"name": "Costa Rica", "domains": ["computrabajo.cr", "elempleo.com"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "cuba": {"name": "Cuba", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "dominica": {"name": "Dominica", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "dominican_republic": {"name": "Dominican Republic", "domains": ["empleos.do", "computrabajo.do"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "el_salvador": {"name": "El Salvador", "domains": ["computrabajo.sv", "sv.trabajos.com"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "grenada": {"name": "Grenada", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "guatemala": {"name": "Guatemala", "domains": ["computrabajo.gt", "getonbrd.com/guatemala"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "haiti": {"name": "Haiti", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "honduras": {"name": "Honduras", "domains": ["computrabajo.hn", "getonbrd.com/honduras"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "jamaica": {"name": "Jamaica", "domains": ["caribbeanjobs.com", "go-jamaica.com/classifieds/job"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "mexico": {"name": "Mexico", "domains": ["occ.com.mx", "computrabajo.mx"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "nicaragua": {"name": "Nicaragua", "domains": ["computrabajo.ni", "getonbrd.com/nicaragua"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "panama": {"name": "Panama", "domains": ["computrabajo.pa", "enlaze.com"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "saint_kitts_and_nevis": {"name": "Saint Kitts and Nevis", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "saint_lucia": {"name": "Saint Lucia", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "saint_vincent_and_the_grenadines": {"name": "Saint Vincent and the Grenadines", "domains": REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "trinidad_and_tobago": {"name": "Trinidad and Tobago", "domains": ["caribbeanjobs.com", "guardian.co.tt/classifieds/jobs"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},
    "united_states": {"name": "United States", "domains": ["indeed.com", "linkedin.com", "monster.com", "careerbuilder.com", "usajobs.gov"] + REGIONAL_JOB_BOARDS["north_america"] + GLOBAL_JOB_BOARDS, "region": "north_america"},

    # South America
    "argentina": {"name": "Argentina", "domains": ["zonajobs.com.ar", "computrabajo.ar"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "bolivia": {"name": "Bolivia", "domains": ["clasificados.eldeber.com.bo", "opcionempleo.com.bo"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "brazil": {"name": "Brazil", "domains": ["infojobs.com.br", "vagas.com.br"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "chile": {"name": "Chile", "domains": ["laborum.cl", "computrabajo.cl"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "colombia": {"name": "Colombia", "domains": ["elempleo.com", "computrabajo.co"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "ecuador": {"name": "Ecuador", "domains": ["multitrabajos.com", "computrabajo.ec"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "guyana": {"name": "Guyana", "domains": REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "paraguay": {"name": "Paraguay", "domains": ["clasipar.com/empleos", "opcionempleo.com.py"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "peru": {"name": "Peru", "domains": ["bumeran.com.pe", "computrabajo.pe"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "suriname": {"name": "Suriname", "domains": REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "uruguay": {"name": "Uruguay", "domains": ["gallito.com.uy/empleos", "computrabajo.uy"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},
    "venezuela": {"name": "Venezuela", "domains": ["computrabajo.ve", "opcionempleo.com.ve"] + REGIONAL_JOB_BOARDS["south_america"] + GLOBAL_JOB_BOARDS, "region": "south_america"},

    # Oceania
    "australia": {"name": "Australia", "domains": ["seek.com.au", "indeed.com.au", "linkedin.com"] + REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "fiji": {"name": "Fiji", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "kiribati": {"name": "Kiribati", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "marshall_islands": {"name": "Marshall Islands", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "micronesia": {"name": "Micronesia", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "nauru": {"name": "Nauru", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "new_zealand": {"name": "New Zealand", "domains": ["seek.co.nz", "trademe.co.nz", "indeed.co.nz"] + REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "palau": {"name": "Palau", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "papua_new_guinea": {"name": "Papua New Guinea", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "samoa": {"name": "Samoa", "domains": ["job54.com", "jobberman.com"] + REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "solomon_islands": {"name": "Solomon Islands", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "tonga": {"name": "Tonga", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "tuvalu": {"name": "Tuvalu", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    "vanuatu": {"name": "Vanuatu", "domains": REGIONAL_JOB_BOARDS["oceania"] + GLOBAL_JOB_BOARDS, "region": "oceania"},
    
    # Africa (not in your original list but added for completeness)
    "algeria": {"name": "Algeria", "domains": ["emploi.dz", "algerie-emploi.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "angola": {"name": "Angola", "domains": ["net-empregos.co.ao"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "benin": {"name": "Benin", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "botswana": {"name": "Botswana", "domains": ["careers24.co.bw"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "burkina_faso": {"name": "Burkina Faso", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "burundi": {"name": "Burundi", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "cabo_verde": {"name": "Cabo Verde", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "cameroon": {"name": "Cameroon", "domains": ["cvmobile.net"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "central_african_republic": {"name": "Central African Republic", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "chad": {"name": "Chad", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "comoros": {"name": "Comoros", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "congo_democratic": {"name": "Congo, Democratic Republic of the", "domains": ["emploirdc.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "congo_republic": {"name": "Congo, Republic of the", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "cote_d_ivoire": {"name": "Cote d'Ivoire", "domains": ["emploici.net"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "djibouti": {"name": "Djibouti", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "egypt": {"name": "Egypt", "domains": ["wuzzuf.net", "akhtaboot.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "equatorial_guinea": {"name": "Equatorial Guinea", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "eritrea": {"name": "Eritrea", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "eswatini": {"name": "Eswatini", "domains": ["careerjunction.co.za"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "ethiopia": {"name": "Ethiopia", "domains": ["ethiojobs.net"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "gabon": {"name": "Gabon", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "gambia": {"name": "Gambia", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "ghana": {"name": "Ghana", "domains": ["jobberman.com.gh", "jobhouse.com.gh"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "guinea": {"name": "Guinea", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "guinea_bissau": {"name": "Guinea-Bissau", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "kenya": {"name": "Kenya", "domains": ["brightermonday.co.ke", "fuzu.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "lesotho": {"name": "Lesotho", "domains": ["careerjunction.co.za"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "liberia": {"name": "Liberia", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "libya": {"name": "Libya", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "madagascar": {"name": "Madagascar", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "malawi": {"name": "Malawi", "domains": ["careerplus.mw"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "mali": {"name": "Mali", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "mauritania": {"name": "Mauritania", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "mauritius": {"name": "Mauritius", "domains": ["myjob.mu"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "morocco": {"name": "Morocco", "domains": ["emploi.ma", "rekrute.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "mozambique": {"name": "Mozambique", "domains": ["jobweb.co.mz"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "namibia": {"name": "Namibia", "domains": ["myjob.com.na"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "niger": {"name": "Niger", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "nigeria": {"name": "Nigeria", "domains": ["jobberman.com", "ng.jiji.ng"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "rwanda": {"name": "Rwanda", "domains": ["jobinrwanda.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "sao_tome_and_principe": {"name": "Sao Tome and Principe", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "senegal": {"name": "Senegal", "domains": ["emploi.sn"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "seychelles": {"name": "Seychelles", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "sierra_leone": {"name": "Sierra Leone", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "somalia": {"name": "Somalia", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "south_sudan": {"name": "South Sudan", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "sudan": {"name": "Sudan", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "tanzania": {"name": "Tanzania", "domains": ["brightermonday.co.tz"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "togo": {"name": "Togo", "domains": REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "tunisia": {"name": "Tunisia", "domains": ["emploi.nat.tn", "tanitjobs.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "uganda": {"name": "Uganda", "domains": ["brightermonday.co.ug"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "zambia": {"name": "Zambia", "domains": ["gozambiajobs.com"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"},
    "zimbabwe": {"name": "Zimbabwe", "domains": ["classifieds.co.zw"] + REGIONAL_JOB_BOARDS["africa"] + GLOBAL_JOB_BOARDS, "region": "africa"}
}

# Job board APIs - replace with actual API keys and endpoints
JOB_APIS = {
    "indeed": {
        "url": "https://api.indeed.com/v2/jobs",
        "api_key": "YOUR_INDEED_API_KEY"
    },
    "linkedin": {
        "url": "https://api.linkedin.com/v2/jobSearch",
        "api_key": "YOUR_LINKEDIN_API_KEY"
    },
    "glassdoor": {
        "url": "https://api.glassdoor.com/api/api.htm",
        "api_key": "YOUR_GLASSDOOR_API_KEY"
    }
}

# Storage for already sent job listings to avoid duplicates
job_cache_file = "job_cache.json"

def load_job_cache() -> dict[str, Any]:
    """Load previously found jobs from cache file"""
    try:
        with open(job_cache_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_job_cache(cache: dict[str, Any]):
    """Save job cache to file"""
    with open(job_cache_file, "w") as f:
        json.dump(cache, f)

from typing import List, Dict, Any

def search_indeed(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Search for jobs on Indeed"""
    jobs: List[Dict[str, Any]] = []
    try:
        url = JOB_APIS["indeed"]["url"]
        params: Dict[str, str] = {
            "q": str(keyword),
            "l": str(location),
            "limit": str(SEARCH_LIMIT_PER_COUNTRY),
            "v": str(2),  # API version
            "format": "json",
            "publisher": str(JOB_APIS["indeed"]["api_key"])  # Replace with your Indeed API key
        }
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data and "results" in data:
            for result in data["results"]:
                job: Dict[str, Any] = {
                    "title": str(result.get("jobtitle", "")),
                    "company": str(result.get("company", "")),
                    "location": str(result.get("formattedLocation", "")),
                    "url": str(result.get("url", "")),
                    "date_posted": datetime.fromtimestamp(result.get("date", time.time())).strftime('%Y-%m-%d'),
                    "description": str(result.get("snippet", "")),
                    "source": "Indeed",
                    "country": str(country_code),
                    "search_term": str(keyword)  # Include the search term
                }
                jobs.append(job)
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching from Indeed for {keyword} in {location}: {e}")
    except KeyError:
        logger.error("Indeed API key not found.")
    return jobs

def search_linkedin(keyword: str, location: str, country_code: str) -> list[dict[str, Any]]:
    """Search for jobs on LinkedIn (Requires API - Placeholder)"""
    #   Replace with actual LinkedIn API calls
    logger.warning("LinkedIn search is a placeholder. Implement with LinkedIn API.")
    return []

def search_glassdoor(keyword: str, location: str, country_code: str) -> list[dict[str, Any]]:
    """Search for jobs on Glassdoor (Requires API - Placeholder)"""
    #   Replace with actual Glassdoor API calls
    logger.warning("Glassdoor search is a placeholder. Implement with Glassdoor API.")
    return []

from typing import List, Dict, Any

def search_other_boards(
    keyword: str,
    location: str,
    country_code: str,
    domains: List[str]
) -> List[Dict[str, Any]]:
    """Search on other job boards using web scraping"""

    jobs: List[Dict[str, Any]] = []
    for domain in domains:
        try:
            if domain == "naukri.com":
                jobs.extend(scrape_naukri(keyword, location, country_code))
            elif domain == "timesjobs.com":
                jobs.extend(scrape_timesjobs(keyword, location, country_code))
            elif domain == "shine.com":
                jobs.extend(scrape_shine(keyword, location, country_code))
            elif domain == "jobstreet.com":
                jobs.extend(scrape_jobstreet(keyword, location, country_code))
            elif domain == "indeed.com":
                # Handle indeed.com separately if needed, since we have a dedicated function
                pass
            elif domain == "linkedin.com":
                # Handle linkedin.com separately if needed, since we have a dedicated function
                pass
            elif domain == "glassdoor.com":
                # Handle glassdoor.com separately if needed, since we have a dedicated function
                pass
            else:
                jobs.extend(scrape_general(keyword, location, country_code, domain))
        except Exception as e:
            logger.error(f"Error scraping {domain} for {keyword} in {location}: {e}")
    return jobs

def scrape_general(keyword: str, location: str, country_code: str, domain: str) -> List[Dict[str, Any]]:
    """General web scraping function (Needs customization per site)"""
    logger.warning(f"General scraping on {domain} needs customization.")
    return []  # Placeholder - Implement scraping logic

from typing import List, Dict, Any

def scrape_naukri(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Web scrape jobs from Naukri.com"""
    jobs: List[Dict[str, Any]] = []
    try:
        base_url = "https://www.naukri.com"
        search_url = f"{base_url}/{keyword}-jobs-{location}"
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        job_listings = soup.find_all("article", attrs={"class": "jobTuple"})

        for job_listing in job_listings:
            title_elem = job_listing.find("a", attrs={"class": "title"})
            company_elem = job_listing.find("a", attrs={"class": "subTitle"})
            location_elem = job_listing.find("li", attrs={"class": "fleft br2 placeHolderCls"})
            date_elem = job_listing.find("div", attrs={"class": "mt-8"})  # Adjust this selector
            desc_elem = job_listing.find("li", attrs={"class": "desc"})

            if (
                title_elem is not None
                and company_elem is not None
                and location_elem is not None
                and date_elem is not None
                and desc_elem is not None
            ):
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True)
                location = location_elem.get_text(strip=True)
                url = title_elem.get("href", "")
                date_posted = date_elem.get_text(strip=True)
                description = desc_elem.get_text(strip=True)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "date_posted": date_posted,
                    "description": description,
                    "source": "Naukri",
                    "country": country_code,
                    "search_term": keyword
                })
        logger.info(f"Successfully scraped {len(jobs)} jobs from Naukri.com")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping Naukri.com for {keyword} in {location}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping Naukri.com: {e}")
    return jobs

def scrape_timesjobs(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Web scrape jobs from TimesJobs.com"""
    jobs: List[Dict[str, Any]] = []
    try:
        base_url = "https://www.timesjobs.com"
        search_url = f"{base_url}/candidate/job-search.html?searchType=home_page&from=submit&txtKeywords={keyword}&txtLocation={location}"
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        job_listings = soup.find_all("li", attrs={"class": "clearfix job-bx wht-shd-bx"})

        for job_listing in job_listings:
            title_elem = job_listing.find("h3")
            company_elem = job_listing.find("h4", attrs={"class": "company-name"})
            ul_elem = job_listing.find("ul", attrs={"class": "top-in-srp"})
            location_elem = ul_elem.find("li") if ul_elem else None
            date_elem = job_listing.find("span", attrs={"class": "sim-posted"})
            desc_elem = job_listing.find("ul", attrs={"class": "list-job-dtl clearfix"})

            if title_elem is not None and company_elem is not None and location_elem is not None and date_elem is not None and desc_elem is not None:
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True)
                location = location_elem.get_text(strip=True)
                parent_a = title_elem.find_parent("a")
                url = parent_a.get("href", "") if parent_a else ""
                date_posted = date_elem.get_text(strip=True).replace("Card Poste", "").strip()
                description = desc_elem.get_text(strip=True)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "date_posted": date_posted,
                    "description": description,
                    "source": "TimesJobs",
                    "country": country_code,
                    "search_term": keyword
                })
        logger.info(f"Successfully scraped {len(jobs)} jobs from TimesJobs.com")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping TimesJobs.com for {keyword} in {location}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping TimesJobs.com: {e}")
    return jobs

def scrape_shine(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Web scrape jobs from Shine.com"""

    jobs: List[Dict[str, Any]] = []
    try:
        base_url = "https://www.shine.com"
        search_url = f"{base_url}/job-search/{keyword}-jobs-{location}"
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        job_listings = soup.find_all("div", class_="job_card_list")

        for job_listing in job_listings:
            title_elem = job_listing.find("h2")
            company_elem = job_listing.find("div", class_="jobCard_jobCard_cName")
            location_elem = job_listing.find("li", class_="jobCard_jobCard_location")
            date_elem = job_listing.find("div", class_="jobCard_jobCard_posted")
            desc_elem = job_listing.find("div", class_="jobCard_jobCard_desc")

            if title_elem is not None and company_elem is not None and location_elem is not None and date_elem is not None and desc_elem is not None:
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True)
                location = location_elem.get_text(strip=True)
                parent_a = title_elem.find_parent("a")
                url = parent_a.get("href", "") if parent_a else ""
                date_posted = date_elem.get_text(strip=True).replace("Posted ", "").strip()
                description = desc_elem.get_text(strip=True)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "date_posted": date_posted,
                    "description": description,
                    "source": "Shine",
                    "country": country_code,
                    "search_term": keyword
                })
        logger.info(f"Successfully scraped {len(jobs)} jobs from Shine.com")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping Shine.com for {keyword} in {location}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping Shine.com: {e}")
    return jobs
def scrape_jobstreet(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Web scrape jobs from JobStreet.com"""

    jobs: List[Dict[str, Any]] = []
    try:
        base_url = "https://www.jobstreet.com.my" # You might need to adjust the base URL based on the specific JobStreet region
        search_url = f"{base_url}/job/{keyword}-in-{location}"
        response = requests.get(search_url)
def scrape_jobstreet(keyword: str, location: str, country_code: str) -> List[Dict[str, Any]]:
    """Web scrape jobs from JobStreet.com"""

    jobs: List[Dict[str, Any]] = []
    try:
        base_url = "https://www.jobstreet.com.my" # You might need to adjust the base URL based on the specific JobStreet region
        search_url = f"{base_url}/job/{keyword}-in-{location}"
        response = requests.get(search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml")
        job_listings = soup.find_all("div", attrs={"class": "FYwKg _1GAu4 _2Svoz"})

        for job_listing in job_listings:
            title_elem = job_listing.find("div", attrs={"class": "_1hr6a _2UwQw"})
            company_elem = job_listing.find("span", attrs={"class": "_2nWYu"})
            location_elem = job_listing.find("span", attrs={"class": "_2nWYu"})
            date_elem = job_listing.find("time", attrs={"class": "_3h0JT _1lTZw"})
            desc_elem = job_listing.find("div", attrs={"class": "_2B3hr"})

            if title_elem is not None and company_elem is not None and location_elem is not None and date_elem is not None and desc_elem is not None:
                title = title_elem.get_text(strip=True)
                company = company_elem.get_text(strip=True)
                location = location_elem.get_text(strip=True)
                parent_a = title_elem.find_parent("a")
                url = parent_a.get("href", "") if parent_a else ""
                date_posted = date_elem.get("datetime", "") if date_elem else ""
                description = desc_elem.get_text(strip=True)

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "date_posted": date_posted,
                    "description": description,
                    "source": "JobStreet",
                    "country": country_code,
                    "search_term": keyword
                })
        logger.info(f"Successfully scraped {len(jobs)} jobs from JobStreet.com")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error scraping JobStreet.com for {keyword} in {location}: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while scraping JobStreet.com: {e}")
    return jobs

    all_jobs: List[Dict[str, Any]] = []

def search_jobs(
    keyword: str,
    location: str,
    country_code: str,
    domains: List[str]
) -> List[Dict[str, Any]]:
    """Search for jobs across different platforms"""

    all_jobs: List[Dict[str, Any]] = []

    # Search using APIs (if keys are available)
    if "indeed.com" in domains and "indeed" in JOB_APIS and JOB_APIS["indeed"]["api_key"]:
        all_jobs.extend(search_indeed(keyword, location, country_code))
    if "linkedin.com" in domains and "linkedin" in JOB_APIS and JOB_APIS["linkedin"]["api_key"]:
        all_jobs.extend(search_linkedin(keyword, location, country_code))
    if "glassdoor.com" in domains and "glassdoor" in JOB_APIS and JOB_APIS["glassdoor"]["api_key"]:
        all_jobs.extend(search_glassdoor(keyword, location, country_code))

    # Search other boards (scraping)
    all_jobs.extend(search_other_boards(keyword, location, country_code, domains))

    return all_jobs
            if datetime.now() - post_date <= timedelta(days=max_age_days):
                recent_jobs.append(job)
        except ValueError:
            # Handle cases where the date format is different or invalid
            logger.warning(f"Could not parse date '{job['date_posted']}' for job: {job['title']}. Skipping age filter.")
            recent_jobs.append(job)  # Include the job for review
        except Exception as e:
            logger.error(f"Error filtering job date: {e}. Including job for review.")
            recent_jobs.append(job)  # Include the job for review
    return recent_jobs

def send_email_alert(jobs: List[Dict[str, Any]]) -> None:
    """Send email alert with job listings"""

    if not jobs:
        logger.info("No new jobs to send")
        return

    try:
        logger.info("Preparing to send email...")
        msg = MIMEMultipart("alternative")
        msg["From"] = EMAIL_ADDRESS or ""
        msg["To"] = RECIPIENT_EMAIL or ""
        msg["Subject"] = f"Gold & Precious Metals Job Alert - {len(jobs)} New Positions"

        body = "<html><body>"
        body += "<h2>New Gold & Precious Metals Jobs</h2><ul>"
        for job in jobs:
            body += f"<li><b>{job['title']}</b> at {job['company']} - {job['location']} ({job['country']})<br>"
            body += f"<a href='{job['url']}'>View Job</a><br>"
            body += f"Posted: {job['date_posted']}<br>"
            body += f"Source: {job['source']}<br>"
            body += f"Search Term: {job['search_term']}<br>"
            body += f"<p>{job['description']}</p></li><br>"
        body += "</ul></body></html>"

        msg.attach(MIMEText(body, "html", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS or "", EMAIL_PASSWORD or "")
            server.send_message(msg)

        logger.info("Email sent successfully!")
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")

def run_job_search():
    """Run the full job search across all terms and countries"""
    logger.info("Starting global job search")

    # Load cache of already processed jobs
    job_cache = load_job_cache()
    new_jobs = []

    # Count stats for logging
    total_countries_searched = 0
    total_domains_searched = 0
    jobs_found_by_region = {}

    # Search for each term in each country
    for search_term in SEARCH_TERMS:
        logger.info(f"Searching for '{search_term}' jobs globally")

        # First search global job boards
        global_board_results = search_jobs(search_term, COUNTRIES["global"]["name"], COUNTRIES["global"]["domains"])

        # Add global results to new jobs list (if not already seen)
        for job in global_board_results:
            job_id = f"{job['url']}_{job['title']}"
            if job_id not in job_cache:
                new_jobs.append(job)
                job_cache[job_id] = {
                    "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "title": job["title"],
                    "search_term": search_term
                }

                # Update stats
                region = "global"
                if region not in jobs_found_by_region:
                    jobs_found_by_region[region] = 0
                jobs_found_by_region[region] += 1

        # Now search country-specific job boards
        for country_code, country in COUNTRIES.items():
            if country_code == "global":
                continue  # Skip global, already searched

            total_countries_searched += 1
            total_domains_searched += len(country["domains"])

            # Search job boards for this country
            country_results = search_jobs(search_term, country["name"], country["domains"])
            all_results = country_results

            # Filter out jobs we've already seen
            for job in all_results:
                job_id = f"{job['url']}_{job['title']}"
                if job_id not in job_cache:
                    new_jobs.append(job)
                    job_cache[job_id] = {
                        "first_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "title": job["title"],
                        "search_term": search_term,
                        "country": country["name"]
                    }

                    # Update stats
                    region = country["region"]
                    if region not in jobs_found_by_region:
                        jobs_found_by_region[region] = 0
                    jobs_found_by_region[region] += 1

    # Log statistics
    logger.info(f"Job search complete: Searched {total_countries_searched} countries across {len(SEARCH_TERMS)} search terms")
    logger.info(f"Total job sites checked: {total_domains_searched}")
    logger.info(f"New jobs found: {len(new_jobs)}")
    for region, count in jobs_found_by_region.items():
        logger.info(f"- {region.title()}: {count} new jobs")

    # Filter for recent jobs
    recent_jobs = filter_recent_jobs(new_jobs, MAX_JOB_AGE_DAYS)
    logger.info(f"Found {len(recent_jobs)} jobs posted in the last {MAX_JOB_AGE_DAYS} days")

    # Send email alert if we found new jobs
    if recent_jobs:
        send_email_alert(recent_jobs)

    # Save updated job cache
    save_job_cache(job_cache)

    logger.info(f"Job search complete. Found {len(recent_jobs)} new recent jobs.")
def main():
    """Main function to run the job alert system"""

    logger.info("Starting Gold & Precious Metals Job Alert System")
    logger.info(f"Configured to search across {len(COUNTRIES)} countries and regions")
    logger.info(f"Searching for {len(SEARCH_TERMS)} primary job terms")

    # Run job search immediately
    run_job_search()

    # Schedule job search based on frequency setting
    if SEARCH_FREQUENCY == "hourly":
    # Run job search immediately
    run_job_search()

    # Schedule job search based on frequency setting
    if SEARCH_FREQUENCY == "every_30_minutes":
        logger.info("Setting up job search schedule every 30 minutes")
        schedule.every(30).minutes.do(run_job_search)
    elif SEARCH_FREQUENCY == "hourly":
        logger.info("Setting up hourly job search schedule")
        schedule.every().hour.do(run_job_search)
    elif SEARCH_FREQUENCY == "weekly":
        logger.info("Setting up weekly job search schedule")
        schedule.every().monday.at(ALERT_TIME).do(run_job_search)
    else:  # Default to daily
        logger.info(f"Setting up daily job search schedule at {ALERT_TIME}")
        schedule.every().day.at(ALERT_TIME).do(run_job_search)

    # Keep the script running
    try:
        logger.info("Job alert system is now running...")
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Job alert system stopped by user")
    except Exception as e:
        logger.error(f"An error occurred in the main loop: {str(e)}")
        raise  # Re-raise the exception after logging it

if __name__ == "__main__":
    main()