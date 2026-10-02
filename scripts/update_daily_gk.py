#!/usr/bin/env python3
import json, random
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST=timezone(timedelta(hours=5, minutes=30))
now=datetime.now(IST)
date_str=now.strftime("%Y-%m-%d")

facts=[
("Capital of France","Paris"),("Capital of Germany","Berlin"),("Capital of Italy","Rome"),("Capital of Spain","Madrid"),
("Capital of Portugal","Lisbon"),("Capital of Japan","Tokyo"),("Capital of China","Beijing"),("Capital of South Korea","Seoul"),
("Capital of Thailand","Bangkok"),("Capital of Nepal","Kathmandu"),("Capital of Bhutan","Thimphu"),("Capital of Bangladesh","Dhaka"),
("Capital of Sri Lanka","Sri Jayawardenepura Kotte"),("Capital of Australia","Canberra"),("Capital of New Zealand","Wellington"),
("Capital of Canada","Ottawa"),("Capital of the United States","Washington, D.C."),("Capital of Brazil","Brasilia"),
("Capital of Argentina","Buenos Aires"),("Capital of Egypt","Cairo"),("Capital of Kenya","Nairobi"),("Capital of Nigeria","Abuja"),
("Capital of Ghana","Accra"),("Capital of South Africa","Pretoria"),("Capital of Russia","Moscow"),
("Capital of the United Kingdom","London"),("Capital of Norway","Oslo"),("Capital of Sweden","Stockholm"),
("Capital of Finland","Helsinki"),("Capital of Denmark","Copenhagen"),
("Capital of Telangana","Hyderabad"),("Capital of Andhra Pradesh","Amaravati"),("Capital of Karnataka","Bengaluru"),
("Capital of Tamil Nadu","Chennai"),("Capital of Kerala","Thiruvananthapuram"),("Capital of Maharashtra","Mumbai"),
("Capital of Gujarat","Gandhinagar"),("Capital of Rajasthan","Jaipur"),("Capital of Odisha","Bhubaneswar"),
("Capital of West Bengal","Kolkata"),("Capital of Bihar","Patna"),("Capital of Uttar Pradesh","Lucknow"),
("Capital of Madhya Pradesh","Bhopal"),("Capital of Punjab","Chandigarh"),("Capital of Haryana","Chandigarh"),
("Capital of Assam","Dispur"),("Capital of Meghalaya","Shillong"),("Capital of Sikkim","Gangtok"),
("Capital of Goa","Panaji"),("Capital of Uttarakhand","Dehradun"),
("Largest planet in the Solar System","Jupiter"),("Smallest planet in the Solar System","Mercury"),
("Planet known as the Red Planet","Mars"),("Planet famous for its rings","Saturn"),
("Nearest star to Earth","the Sun"),("Natural satellite of Earth","the Moon"),
("Gas absorbed by plants during photosynthesis","carbon dioxide"),("Gas released by plants during photosynthesis","oxygen"),
("Chemical formula of water","H2O"),("Chemical symbol for gold","Au"),("Chemical symbol for silver","Ag"),
("Chemical symbol for sodium","Na"),("Chemical symbol for iron","Fe"),("Number of chambers in the human heart","4"),
("Organ that pumps blood","the heart"),("Largest organ of the human body","the skin"),("Largest internal organ of the human body","the liver"),
("Basic unit of life","the cell"),("Vitamin produced in skin in sunlight","Vitamin D"),
("Fastest land animal","the cheetah"),("Largest mammal","the blue whale"),("Bird known for the fastest dive","the peregrine falcon"),
("Number of continents","7"),("Largest continent","Asia"),("Largest ocean","Pacific Ocean"),
("Smallest ocean","Arctic Ocean"),("Highest mountain above sea level","Mount Everest"),
("Longest river traditionally recognized in Africa","the Nile"),("Largest hot desert","the Sahara Desert"),
("Instrument used to measure temperature","thermometer"),("Instrument used to measure atmospheric pressure","barometer"),
("Instrument used to measure earthquakes","seismograph"),("SI unit of force","newton"),
("SI unit of energy","joule"),("SI unit of power","watt"),("Speed of light in vacuum","approximately 3 × 10^8 m/s"),
("Smallest prime number","2"),("Only even prime number","2"),("Number of sides in a hexagon","6"),
("Number of sides in an octagon","8"),("Number of degrees in a right angle","90°"),
("National animal of India","Bengal tiger"),("National bird of India","Indian peacock"),
("National flower of India","lotus"),("National aquatic animal of India","Ganges river dolphin"),
("National tree of India","banyan tree"),("National fruit of India","mango"),
("Currency of India","Indian rupee"),("Currency of Japan","yen"),("Currency of the United Kingdom","pound sterling"),
("Currency of the United States","US dollar"),("Currency of China","renminbi (yuan)"),
("Author of the Indian national anthem","Rabindranath Tagore"),("Father of the Indian Constitution","B. R. Ambedkar"),
("First President of India","Dr. Rajendra Prasad"),("First Prime Minister of India","Jawaharlal Nehru"),
("Number of players in a cricket team on the field","11"),("Number of rings in the Olympic symbol","5"),
("Sport associated with Wimbledon","tennis"),("Sport associated with the Ryder Cup","golf"),
("Festival known as the Festival of Lights","Diwali"),("Festival associated with colours in India","Holi"),
("National space agency of India","ISRO"),("Headquarters of ISRO","Bengaluru"),
("Study of plants","botany"),("Study of animals","zoology"),("Study of earthquakes","seismology"),
("Study of weather and atmosphere","meteorology"),("Study of stars and planets","astronomy")
]

# Create two differently worded questions for each fact, giving a large unique pool.
pool=[]
for topic,answer in facts:
    pool.append({"q":f"What is the {topic.lower()}?","a":answer})
    pool.append({"q":f"Which answer is correct for: {topic}?","a":answer})

# Stable daily selection: 5 unique questions per day, sequentially consuming the pool.
day_number=(now.date()-datetime(2026,1,1).date()).days
start=(day_number*5)%len(pool)
items=[pool[(start+i)%len(pool)] for i in range(5)]
data={"date":date_str,"title":"Daily General Knowledge","questions":items}

Path("daily-gk.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
archive=Path("daily-gk-history"); archive.mkdir(exist_ok=True)
(Path(archive)/f"{date_str}.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Updated {date_str}: 5 GK questions from {len(pool)} unique questions")
