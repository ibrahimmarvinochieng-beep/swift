"""Demo collector — generates realistic signals with zero external API keys.

Used for local testing and demonstrations.  Produces a rotating set of
realistic event signals covering all event categories so every stage
of the pipeline (filter → classify → extract → dedup → structure) gets
exercised on every run.
"""

import random
from datetime import datetime, timezone
from typing import List
from collectors.base_collector import BaseCollector

DEMO_SIGNALS = [
    {
        "content": "BREAKING: A 6.4 magnitude earthquake struck central Turkey near Malatya early this morning, causing buildings to collapse and trapping residents. Rescue teams have been deployed to the affected region. At least 12 people confirmed dead.",
        "source_name": "Reuters",
        "url": "https://reuters.com/world/earthquake-turkey",
    },
    {
        "content": "Hurricane Maria has been upgraded to Category 4 as it approaches the Caribbean coast. Mandatory evacuations ordered for coastal areas in Puerto Rico and the Dominican Republic. Emergency shelters opening across the region.",
        "source_name": "AP News",
        "url": "https://apnews.com/hurricane-maria-caribbean",
    },
    {
        "content": "Dubai International Airport has suspended all flights due to severe flooding caused by unprecedented rainfall. Thousands of passengers stranded. Emirates and FlyDubai have cancelled over 200 flights.",
        "source_name": "BBC",
        "url": "https://bbc.com/news/dubai-airport-floods",
    },
    {
        "content": "Major ransomware cyberattack hits multiple hospitals across the UK National Health Service. Patient records encrypted, emergency services diverted. The NCSC has declared a critical incident.",
        "source_name": "The Guardian",
        "url": "https://theguardian.com/nhs-ransomware-attack",
    },
    {
        "content": "Massive wildfire spreading rapidly through northern California wine country. Over 50,000 acres burned, 15,000 residents evacuated. Air quality index reaches hazardous levels in San Francisco Bay Area.",
        "source_name": "AP News",
        "url": "https://apnews.com/california-wildfire",
    },
    {
        "content": "WHO declares new Ebola outbreak in the Democratic Republic of Congo a Public Health Emergency of International Concern. 47 confirmed cases with 23 deaths reported in North Kivu province.",
        "source_name": "WHO",
        "url": "https://who.int/ebola-drc-emergency",
    },
    {
        "content": "Nationwide power grid failure leaves 140 million people without electricity across Pakistan. Authorities blame cascading frequency fluctuation. Hospitals switch to emergency generators.",
        "source_name": "Al Jazeera",
        "url": "https://aljazeera.com/pakistan-power-outage",
    },
    {
        "content": "Train derailment in Ohio releases toxic vinyl chloride into the atmosphere. Mandatory evacuation zone expanded to 5-mile radius. EPA deploys hazmat response teams to East Palestine.",
        "source_name": "Reuters",
        "url": "https://reuters.com/ohio-train-derailment",
    },
    {
        "content": "Large-scale anti-government protests erupt in Nairobi, Kenya after proposed tax increases. Police deploy tear gas as thousands march toward parliament. Several injuries reported.",
        "source_name": "BBC",
        "url": "https://bbc.com/news/kenya-protests-nairobi",
    },
    {
        "content": "Global stock markets plunge as major US bank declares bankruptcy. Dow Jones drops 800 points in early trading. Federal Reserve calls emergency meeting to discuss financial stability measures.",
        "source_name": "Reuters",
        "url": "https://reuters.com/markets-crash-bank-failure",
    },
    {
        "content": "Volcanic eruption at Mount Etna forces closure of Catania airport in Sicily. Ash cloud reaches 30,000 feet. Italian Civil Protection issues highest alert level for surrounding communities.",
        "source_name": "GDACS",
        "url": "https://gdacs.org/volcano-etna-eruption",
    },
    {
        "content": "Severe drought in East Africa threatens 20 million people with famine. UN World Food Programme launches emergency appeal for $1.5 billion. Water sources in Somalia and Ethiopia critically depleted.",
        "source_name": "UN",
        "url": "https://news.un.org/east-africa-drought-famine",
    },
    {
        "content": "Critical zero-day vulnerability discovered in widely used open-source library affecting millions of servers worldwide. CVE score rated 10.0. Tech companies scramble to deploy emergency patches.",
        "source_name": "The Guardian",
        "url": "https://theguardian.com/tech/zero-day-vulnerability",
    },
    {
        "content": "Bridge collapse on major highway near Mumbai during monsoon rains kills at least 8 people. Search and rescue operations underway. Authorities suspend traffic on adjacent routes.",
        "source_name": "Reuters",
        "url": "https://reuters.com/india-bridge-collapse-mumbai",
    },
    {
        "content": "European Union imposes sweeping new sanctions on Russia targeting energy exports and financial institutions. Russian ruble drops 8% against the dollar. Retaliatory measures expected.",
        "source_name": "AFP",
        "url": "https://france24.com/eu-russia-sanctions",
    },
]


class DemoCollector(BaseCollector):
    name = "demo"

    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size

    async def collect(self) -> List[dict]:
        selected = random.sample(DEMO_SIGNALS, min(self.batch_size, len(DEMO_SIGNALS)))
        signals = []

        for item in selected:
            signal = self.normalize_signal(
                content=item["content"],
                source_type="demo",
                source_name=item["source_name"],
                url=item["url"],
                metadata={"demo": True},
                published_at=datetime.now(timezone.utc),
            )
            signals.append(signal)

        return signals
