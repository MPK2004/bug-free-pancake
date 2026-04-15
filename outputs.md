(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: What are all the topics in the dataset?

Generated SQL: SELECT topic
FROM news;
Executing SQL: SELECT topic
FROM news LIMIT 50;

Results:
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('SCIENCE',)
('TECHNOLOGY',)
('TECHNOLOGY',)
('TECHNOLOGY',)
('TECHNOLOGY',)
('TECHNOLOGY',)
('SCIENCE',)
('TECHNOLOGY',)
('TECHNOLOGY',)

ANALYSIS:
- The dataset includes two topics: SCIENCE and TECHNOLOGY
- SCIENCE is the most common topic, appearing multiple times in the dataset
- TECHNOLOGY is also present in the dataset, but less frequently compared to SCIENCE
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Show 5 science news articles

Generated SQL: SELECT *
FROM news
WHERE topic = 'SCIENCE'
LIMIT 5;
Executing SQL: SELECT *
FROM news
WHERE topic = 'SCIENCE'
LIMIT 5;

Results:
(1, 'SCIENCE', 'https://www.eurekalert.org/pub_releases/2020-08/dbnl-acl080620.php', 'eurekalert.org', datetime.datetime(2020, 8, 6, 13, 59, 45), "A closer look at water-splitting's solar fuel potential", 'en')
(2, 'SCIENCE', 'https://www.pulse.ng/news/world/an-irresistible-scent-makes-locusts-swarm-study-finds/jy784jw', 'pulse.ng', datetime.datetime(2020, 8, 12, 15, 14, 19), 'An irresistible scent makes locusts swarm, study finds', 'en')
(3, 'SCIENCE', 'https://www.express.co.uk/news/science/1322607/artificial-intelligence-warning-machine-learning-algorithm-social-media-data', 'express.co.uk', datetime.datetime(2020, 8, 13, 21, 1), 'Artificial intelligence warning: AI will know us better than we know ourselves', 'en')
(4, 'SCIENCE', 'https://www.ndtv.com/world-news/glaciers-could-have-sculpted-mars-valleys-study-2273648', 'ndtv.com', datetime.datetime(2020, 8, 3, 22, 18, 26), 'Glaciers Could Have Sculpted Mars Valleys: Study', 'en')
(5, 'SCIENCE', 'https://www.thesun.ie/tech/5742187/perseid-meteor-shower-tonight-time-uk-see/', 'thesun.ie', datetime.datetime(2020, 8, 12, 19, 54, 36), 'Perseid meteor shower 2020: What time and how to see the huge bright FIREBALLS over UK again tonight', 'en')

ANALYSIS:
- A closer look at water-splitting's solar fuel potential
- An irresistible scent makes locusts swarm, study finds
- Artificial intelligence warning: AI will know us better than we know ourselves
- Glaciers Could Have Sculpted Mars Valleys: Study
- Perseid meteor shower 2020: What time and how to see the huge bright FIREBALLS over UK again tonight
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ List domains available in the dataset
Command 'List' not found, did you mean:
  command 'mist' from snap mist (master)
  command 'hist' from deb loki (2.4.7.4-10)
  command 'dist' from deb mmh (0.4-6)
  command 'dist' from deb nmh (1.8-1)
  command 'gist' from deb yorick (2.2.04+dfsg1-12)
See 'snap info <snapname>' for additional versions.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ List domains available in the dataset
Command 'List' not found, did you mean:
  command 'mist' from snap mist (master)
  command 'hist' from deb loki (2.4.7.4-10)
  command 'dist' from deb mmh (0.4-6)
  command 'dist' from deb nmh (1.8-1)
  command 'gist' from deb yorick (2.2.04+dfsg1-12)
See 'snap info <snapname>' for additional versions.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: List domains available in the dataset

Generated SQL: SELECT DISTINCT domain
FROM news;
Executing SQL: SELECT DISTINCT domain
FROM news LIMIT 50;

Results:
('chopchat.com',)
('oshawaexpress.ca',)
('soaps.sheknows.com',)
('pitpass.com',)
('sloughobserver.co.uk',)
('news.bloombergenvironment.com',)
('africanews.com',)
('mercatornet.com',)
('radio.foxnews.com',)
('nokiamob.net',)
('techexec.com.au',)
('manisteenews.com',)
('thephinsider.com',)
('upi.com',)
('ndinsider.com',)
('krgv.com',)
('recorder.com',)
('otakustudy.com',)
('arnnet.com.au',)
('ross-shirejournal.co.uk',)
('thewomenjournal.com',)
('westport-news.com',)
('storagereview.com',)
('fijitimes.com',)
('27east.com',)
('whyy.org',)
('torontosun.com',)
('southernstar.ie',)
('finnewsnetwork.com.au',)
('telegram.com',)
('playingfor90.com',)
('koreabiomed.com',)
('thehockeywriters.com',)
('thepharmaletter.com',)
('plymouthherald.co.uk',)
('thurrockgazette.co.uk',)
('uab.edu',)
('wis-wander.weizmann.ac.il',)
('datacenterdynamics.com',)
('sciencemag.org',)
('soapdirt.com',)
('gadgets.ndtv.com',)
('borkena.com',)
('houstonchronicle.com',)
('goodmenproject.com',)
('speedcafe.com',)
('tempo.com.ph',)
('soccer.nbcsports.com',)
('welivesecurity.com',)
('salaamgateway.com',)

ANALYSIS:
- The available domains in the dataset include a variety of news, tech, sports, and entertainment websites such as foxnews.com, thehockeywriters.com, and gadgets.ndtv.com.
- The dataset also contains domains from different countries like australia (arnnet.com.au), ireland (southernstar.ie), and the United States (houstonchronicle.com).
- Some domains in the dataset are specific to certain topics or industries, such as sciencemag.org for science news and speedcafe.com for motorsports updates.
- The dataset does not have a specific pattern or theme, as it includes a diverse range of domains covering different subjects and regions.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Show latest 10 articles

Generated SQL: SELECT *
FROM news
ORDER BY published_date DESC
LIMIT 10;
Executing SQL: SELECT *
FROM news
ORDER BY published_date DESC
LIMIT 10;

Results:
(88270, 'WORLD', 'https://www.ippmedia.com/en/news/jpm-hands-over-role%C2%A0-sadc-chair', 'ippmedia.com', datetime.datetime(2020, 8, 18, 5, 49), 'JPM hands over role as SADC chair', 'en')
(6667, 'HEALTH', 'https://www.standardmedia.co.ke/health/article/2001382950/more-infectious-coronavirus-mutation-may-be-a-good-thing-says-disease-expert', 'standardmedia.co.ke', datetime.datetime(2020, 8, 18, 5, 47, 50), "More infectious coronavirus mutation may be 'a good thing', says disease expert", 'en')
(38188, 'ENTERTAINMENT', 'https://indianexpress.com/article/entertainment/hollywood/angelina-jolie-the-one-and-only-ivan-disney-plus-6559391/', 'indianexpress.com', datetime.datetime(2020, 8, 18, 5, 47, 45), 'Angelina Jolie says The One and Only Ivan deals with heavy issues in a charming way', 'en')
(36372, 'BUSINESS', 'https://www.business-standard.com/article/markets/market-live-sensex-nifty-bse-nse-sgx-nifty-covid-19-hdfc-bank-ril-120081800148_1.html', 'business-standard.com', datetime.datetime(2020, 8, 18, 5, 45, 1), 'MARKET LIVE: Indices hold gains, Sensex up 200 pts; India VIX dips 2%', 'en')
(4041, 'TECHNOLOGY', 'https://www.gamasutra.com/view/pressreleases/368370/Genshin_Impact_Will_Launch_on_September_28th_on_PC_Android_and_iOS.php', 'gamasutra.com', datetime.datetime(2020, 8, 18, 5, 44, 33), 'Genshin Impact Will Launch on September 28th on PC, Android and iOS', 'en')
(14906, 'HEALTH', 'https://www.livemint.com/news/world/oxford-covid-vaccine-gives-britain-to-prove-its-science-prowess-11597727666330.html', 'livemint.com', datetime.datetime(2020, 8, 18, 5, 41, 17), 'Oxford covid vaccine gives Britain to prove its science prowess', 'en')
(57273, 'NATION', 'https://news.thevoicebw.com/fight-for-the-heart-of-bomu/', 'news.thevoicebw.com', datetime.datetime(2020, 8, 18, 5, 39, 9), 'Fight for the heart of BOMU', 'en')
(5369, 'HEALTH', 'https://www.news-medical.net/news/20200818/Researchers-identify-new-therapeutic-target-for-Alzheimers-disease.aspx', 'news-medical.net', datetime.datetime(2020, 8, 18, 5, 38), "Researchers identify new therapeutic target for Alzheimer's disease", 'en')
(54107, 'TECHNOLOGY', 'https://www.nme.com/news/gaming-news/new-batman-game-teaser-hints-at-court-of-owls-as-main-villain-2730914', 'nme.com', datetime.datetime(2020, 8, 18, 5, 36), 'New ‘Batman’ game teaser hints at Court Of Owls as main villain', 'en')
(53261, 'TECHNOLOGY', 'https://gadgets.ndtv.com/games/news/fortnite-app-store-apple-removal-epic-games-asks-judge-to-block-2281134', 'gadgets.ndtv.com', datetime.datetime(2020, 8, 18, 5, 34, 24), "Epic Games Asks Judge to Block Apple's Removal of Fortnite From App Store", 'en')

ANALYSIS:
- The latest 10 articles are:
    1. JPM hands over role as SADC chair - published on 2020-08-18 05:49:00
    2. More infectious coronavirus mutation may be 'a good thing', says disease expert - published on 2020-08-18 05:47:50
    3. Angelina Jolie says The One and Only Ivan deals with heavy issues in a charming way - published on 2020-08-18 05:47:45
    4. MARKET LIVE: Indices hold gains, Sensex up 200 pts; India VIX dips 2% - published on 2020-08-18 05:45:01
    5. Genshin Impact Will Launch on September 28th on PC, Android and iOS - published on 2020-08-18 05:44:33
    6. Oxford covid vaccine gives Britain to prove its science prowess - published on 2020-08-18 05:41:17
    7. Fight for the heart of BOMU - published on 2020-08-18 05:39:09
    8. Researchers identify new therapeutic target for Alzheimer's disease - published on 2020-08-18 05:38:00
    9. New ‘Batman’ game teaser hints at Court Of Owls as main villain - published on 2020-08-18 05:36:00
    10. Epic Games Asks Judge to Block Apple's Removal of Fortnite From App Store - published on 2020-08-18 05:34:24
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: How many articles are there in each topic?

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic LIMIT 50;

Results:
('BUSINESS', 15000)
('HEALTH', 15000)
('WORLD', 15000)
('SPORTS', 15000)
('TECHNOLOGY', 15000)
('ENTERTAINMENT', 15000)
('NATION', 15000)
('SCIENCE', 3774)

ANALYSIS:
- There are 15,000 articles in each of the topics: BUSINESS, HEALTH, WORLD, SPORTS, TECHNOLOGY, ENTERTAINMENT, and NATION.
- There are 3,774 articles in the topic: SCIENCE.
- The data indicates an equal distribution of 15,000 articles in most topics but a lower count in the SCIENCE category.
- The reason for the lower count in the SCIENCE topic compared to others is not specified in the available data.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Which topic has the most articles?

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC LIMIT 50;

Results:
('BUSINESS', 15000)
('HEALTH', 15000)
('WORLD', 15000)
('SPORTS', 15000)
('TECHNOLOGY', 15000)
('ENTERTAINMENT', 15000)
('NATION', 15000)
('SCIENCE', 3774)

ANALYSIS:
- The topics with BUSINESS, HEALTH, WORLD, SPORTS, TECHNOLOGY, ENTERTAINMENT, and NATION all have 15,000 articles each, making them tied for the most articles.
- SCIENCE has the least number of articles with only 3,774, indicating it is not the topic with the most articles.
- Based on the data provided, there is no single topic that clearly has the most articles as several topics have the same number of articles.
- It is not possible to determine which topic has the most articles without further information or data.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Compare science with business and sports

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
WHERE topic = 'SCIENCE' OR topic = 'BUSINESS' OR topic = 'SPORTS'
GROUP BY topic
ORDER BY count;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
WHERE topic = 'SCIENCE' OR topic = 'BUSINESS' OR topic = 'SPORTS'
GROUP BY topic
ORDER BY count LIMIT 50;

Results:
('SCIENCE', 3774)
('BUSINESS', 15000)
('SPORTS', 15000)

ANALYSIS:
- There are more articles related to Business and Sports compared to Science, with Business and Sports both having a count of 15,000 each, while Science has a count of only 3,774.
- This could indicate that Business and Sports are more popular or have a wider audience compared to Science, as evidenced by the higher number of articles related to those topics.
- It is not clear from the data alone why there is a difference in the number of articles between Science, Business, and Sports. Additional information or analysis would be needed to determine the underlying reasons for these counts.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Show articles for topic = SciEnCe

Generated SQL: SELECT *
FROM news
WHERE topic = 'SCIENCE';
Executing SQL: SELECT *
FROM news
WHERE topic = 'SCIENCE' LIMIT 50;

Results:
(1, 'SCIENCE', 'https://www.eurekalert.org/pub_releases/2020-08/dbnl-acl080620.php', 'eurekalert.org', datetime.datetime(2020, 8, 6, 13, 59, 45), "A closer look at water-splitting's solar fuel potential", 'en')
(2, 'SCIENCE', 'https://www.pulse.ng/news/world/an-irresistible-scent-makes-locusts-swarm-study-finds/jy784jw', 'pulse.ng', datetime.datetime(2020, 8, 12, 15, 14, 19), 'An irresistible scent makes locusts swarm, study finds', 'en')
(3, 'SCIENCE', 'https://www.express.co.uk/news/science/1322607/artificial-intelligence-warning-machine-learning-algorithm-social-media-data', 'express.co.uk', datetime.datetime(2020, 8, 13, 21, 1), 'Artificial intelligence warning: AI will know us better than we know ourselves', 'en')
(4, 'SCIENCE', 'https://www.ndtv.com/world-news/glaciers-could-have-sculpted-mars-valleys-study-2273648', 'ndtv.com', datetime.datetime(2020, 8, 3, 22, 18, 26), 'Glaciers Could Have Sculpted Mars Valleys: Study', 'en')
(5, 'SCIENCE', 'https://www.thesun.ie/tech/5742187/perseid-meteor-shower-tonight-time-uk-see/', 'thesun.ie', datetime.datetime(2020, 8, 12, 19, 54, 36), 'Perseid meteor shower 2020: What time and how to see the huge bright FIREBALLS over UK again tonight', 'en')
(6, 'SCIENCE', 'https://interestingengineering.com/nasa-releases-in-depth-map-of-beirut-explosion-damage', 'interestingengineering.com', datetime.datetime(2020, 8, 8, 11, 5, 45), 'NASA Releases In-Depth Map of Beirut Explosion Damage', 'en')
(7, 'SCIENCE', 'https://www.thequint.com/tech-and-auto/spacex-nasa-demo-2-rocket-launch-set-for-saturday-how-to-watch', 'thequint.com', datetime.datetime(2020, 5, 28, 9, 9, 46), 'SpaceX, NASA Demo-2 Rocket Launch Set for Saturday: How to Watch', 'en')
(8, 'SCIENCE', 'https://www.thespacereview.com/article/4003/1', 'thespacereview.com', datetime.datetime(2020, 8, 10, 22, 48, 23), 'Orbital space tourism set for rebirth in 2021', 'en')
(9, 'SCIENCE', 'https://www.businessinsider.com/greenland-melting-ice-sheet-past-tipping-point-2020-8', 'businessinsider.com', datetime.datetime(2020, 8, 16, 0, 28, 54), "Greenland's melting ice sheet has 'passed the point of no return'", 'en')
(10, 'SCIENCE', 'https://www.thehindubusinessline.com/news/science/nasa-invites-engineering-students-to-help-harvest-water-on-mars-moon/article32352915.ece', 'thehindubusinessline.com', datetime.datetime(2020, 8, 14, 7, 43, 25), 'NASA invites engineering students to help harvest water on Mars, Moon', 'en')
(11, 'SCIENCE', 'https://www.azoquantum.com/News.aspx?newsID=7321', 'azoquantum.com', datetime.datetime(2020, 8, 4, 14, 2), 'Astronomers Detect Electromagnetic Signal Caused by Unequal Neutron-Star Collision', 'en')
(12, 'SCIENCE', 'https://interestingengineering.com/nasa-finds-ammonia-linked-mushballs-and-shallow-lightning-on-jupiter', 'interestingengineering.com', datetime.datetime(2020, 8, 7, 9, 23, 57), "NASA Finds Ammonia-Linked 'Mushballs' and 'Shallow Lightning' on Jupiter", 'en')
(13, 'SCIENCE', 'https://menafn.com/1100601885/Russia-targets-returning-to-Venus-build-reusable-rocket', 'menafn.com', datetime.datetime(2020, 8, 7, 22, 5, 55), 'Russia targets returning to Venus, build reusable rocket', 'en')
(14, 'SCIENCE', 'https://www.nasa.gov/press-release/goddard/2020/mars-nightglow/', 'nasa.gov', datetime.datetime(2020, 8, 6, 16, 28, 32), 'Martian Night Sky Pulses in Ultraviolet Light', 'en')
(15, 'SCIENCE', 'https://scitechdaily.com/energy-efficient-tuning-of-spintronic-neurons-to-imitate-the-non-linear-oscillatory-neural-networks-of-the-human-brain/', 'scitechdaily.com', datetime.datetime(2020, 8, 17, 14, 23, 19), 'Energy-Efficient Tuning of Spintronic Neurons to Imitate the Non-linear Oscillatory Neural Networks of the Human Brain', 'en')
(16, 'SCIENCE', 'https://www.theladders.com/career-advice/scientists-may-have-discovered-the-achilles-heel-of-the-coronavirus', 'theladders.com', datetime.datetime(2020, 8, 14, 19, 58, 55), "Scientists may have discovered the Achilles' heel of the coronavirus", 'en')
(17, 'SCIENCE', 'https://www.eurekalert.org/pub_releases/2020-08/e-tbt080420.php', 'eurekalert.org', datetime.datetime(2020, 8, 4, 16, 2, 36), 'Tradeoff between the eyes and nose helps flies find their niche', 'en')
(18, 'SCIENCE', 'https://kearneyhub.com/news/national/2020s-final-mars-mission-poised-for-blastoff-from-florida/article_241d8506-ac89-56f5-8472-6c5f8423523d.html', 'kearneyhub.com', datetime.datetime(2020, 8, 8, 17, 13, 7), "2020's final Mars mission poised for blastoff from Florida", 'en')
(19, 'SCIENCE', 'https://www.washingtonpost.com/science/ant-behavior-evolution-fossil/2020/08/14/a246197c-dcd6-11ea-809e-b8be57ba616e_story.html', 'washingtonpost.com', datetime.datetime(2020, 8, 15, 12, 0), 'In rare find, fossil shows how Cretaceous-era ‘hell ant’ ate its prey with weird jaws', 'en')
(20, 'SCIENCE', 'https://www.rnz.co.nz/news/world/422607/nasa-spacex-crew-return-dragon-capsule-splashes-down', 'rnz.co.nz', datetime.datetime(2020, 8, 2, 18, 50, 38), 'Nasa SpaceX crew return: Dragon capsule splashes down', 'en')
(21, 'SCIENCE', 'https://www.techexplorist.com/look-mars-eerie-nightglow/34341/', 'techexplorist.com', datetime.datetime(2020, 8, 7, 11, 17), 'Take a look at Mar’s eerie nightglow', 'en')
(22, 'SCIENCE', 'https://interestingengineering.com/cern-scientists-discover-rare-higgs-boson-process', 'interestingengineering.com', datetime.datetime(2020, 8, 5, 13, 8, 5), 'CERN Scientists Discover Rare Higgs Boson Process', 'en')
(23, 'SCIENCE', 'https://www.liverpoolecho.co.uk/news/liverpool-news/beautiful-healthy-young-woman-died-18747884', 'liverpoolecho.co.uk', datetime.datetime(2020, 8, 11, 4, 0), "'Beautiful and healthy' young woman died suddenly on dream work trip in Australia", 'en')
(24, 'SCIENCE', 'https://scitechdaily.com/hubble-uses-moon-as-mirror-to-study-earths-atmosphere-proxy-in-search-of-potentially-habitable-planets-around-other-stars/', 'scitechdaily.com', datetime.datetime(2020, 8, 6, 14, 28, 45), 'Hubble Uses Moon As “Mirror” to Study Earth’s Atmosphere – Proxy in Search of Potentially Habitable Planets Around Other Stars', 'en')
(25, 'SCIENCE', 'https://www.daijiworld.com/news/newsDisplay.aspx?newsID=737478', 'daijiworld.com', datetime.datetime(2020, 8, 4, 10, 7, 36), 'Indian researchers show how Covid-19 PPE can turn into biofuel', 'en')
(26, 'SCIENCE', 'https://www.thechronicleherald.ca/lifestyles/regional-lifestyles/atlantic-skies-young-astronomers-and-the-perseid-meteors-481695/', 'thechronicleherald.ca', datetime.datetime(2020, 8, 7, 10, 11, 8), 'ATLANTIC SKIES: Young astronomers and the Perseid meteors', 'en')
(27, 'SCIENCE', 'https://www.clickorlando.com/news/local/2020/08/04/nasa-astronauts-to-talk-about-historic-spacex-splashdown/', 'clickorlando.com', datetime.datetime(2020, 8, 4, 23, 21), '‘It came alive:’ NASA astronauts describe experiencing splashdown in SpaceX Dragon', 'en')
(28, 'SCIENCE', 'https://www.sproutwired.com/when-did-humans-find-out-how-to-use-fire/', 'sproutwired.com', datetime.datetime(2020, 8, 8, 15, 0), 'When did humans find out how to use fire?', 'en')
(29, 'SCIENCE', 'https://futurism.com/the-byte/sourdough-exoplanet-surprisingly-dense', 'futurism.com', datetime.datetime(2020, 8, 4, 7, 0), 'Like Your First Quarantine Sourdough Attempt, This Exoplanet Is "Surprisingly Dense"', 'en')
(30, 'SCIENCE', 'https://www.heritagedaily.com/2020/08/ring-like-structure-on-ganymede-may-have-been-caused-by-a-violent-impact/134643', 'heritagedaily.com', datetime.datetime(2020, 8, 7, 22, 11, 40), 'Ring-like Structure on Ganymede May Have Been Caused by a Violent Impact', 'en')
(31, 'SCIENCE', 'https://www.cbsnews.com/news/nasa-drops-insensitive-nicknames-cosmic-objects/', 'cbsnews.com', datetime.datetime(2020, 8, 8, 18, 39), 'NASA drops "insensitive" nicknames for cosmic objects', 'en')
(32, 'SCIENCE', 'https://www.express.co.uk/news/science/1323379/Archaeology-news-Jerusalem-Siloam-Tunnel-inscription-Hezekiah-Bible-accurate', 'express.co.uk', datetime.datetime(2020, 8, 16, 9, 1), 'Archaeology: A 2,700-year-old inscription in Jerusalem proves Bible RIGHT, expert claims', 'en')
(33, 'SCIENCE', 'https://www.cbsnews.com/news/mars-helicopter-ingenuity-milestone-perseverance-rover/', 'cbsnews.com', datetime.datetime(2020, 8, 17, 11, 22), 'Mars helicopter reaches "big milestone" on flight to planet', 'en')
(34, 'SCIENCE', 'https://www.dailymail.co.uk/sciencetech/article-8612449/Sunspot-size-Mars-turning-Earth-solar-flares-affect-electronics.html', 'dailymail.co.uk', datetime.datetime(2020, 8, 10, 15, 51, 55), 'Sunspot the size of Mars is turning towards Earth', 'en')
(35, 'SCIENCE', 'https://www.space.com/jupiter-moon-ganymede-giant-impact-scar.html', 'space.com', datetime.datetime(2020, 8, 7, 20, 44), "Jupiter's huge moon Ganymede may have the largest impact scar in the solar system", 'en')
(36, 'SCIENCE', 'https://www.mirror.co.uk/science/man-posts-mind-blowing-tiktok-22521686', 'mirror.co.uk', datetime.datetime(2020, 8, 14, 11, 58), 'Man posts mind-blowing TikTok from highest point in Canada to disprove Flat Earth theory', 'en')
(37, 'SCIENCE', 'https://www.27east.com/southampton-press/cause-of-massive-fish-kill-in-shinnecock-canal-not-clear-2-1479054/', '27east.com', datetime.datetime(2019, 11, 23, 16, 7, 14), 'Cause Of Massive Fish Kill In Shinnecock Canal Not Clear - 27 East', 'en')
(38, 'SCIENCE', 'https://www.eurekalert.org/pub_releases/2020-08/ps-unm080320.php', 'eurekalert.org', datetime.datetime(2020, 8, 3, 20, 17, 32), 'Unequal neutron-star mergers create unique "bang" in simulations', 'en')
(39, 'SCIENCE', 'https://www.cnn.com/2020/08/03/us/zombie-cicadas-west-virginia-fungus-scn-trnd/index.html', 'cnn.com', datetime.datetime(2020, 8, 3, 21, 59), "'Zombie cicadas' under the influence of a mind controlling fungus have returned to West Virginia", 'en')
(40, 'SCIENCE', 'https://www.sciencealert.com/astronomers-may-have-just-found-a-missing-baby-neutron-star', 'sciencealert.com', datetime.datetime(2020, 8, 4, 6, 1, 29), "Astronomers May Have Found a Lost Neutron Star That's Been Missing For Decades", 'en')
(41, 'SCIENCE', 'https://www.somagnews.com/spacexs-starship-spacecraft-saw-150-meters-high/', 'somagnews.com', datetime.datetime(2020, 8, 5, 17, 12), "SpaceX's Starship spacecraft saw 150 meters high", 'en')
(42, 'SCIENCE', 'https://www.sciencealert.com/these-orbs-look-like-candy-but-they-re-actually-different-flavours-of-a-martian-moon', 'sciencealert.com', datetime.datetime(2020, 8, 13, 23, 23, 31), "These Orbs Look Like Candy, But They're Actually Different Flavours of Phobos", 'en')
(48, 'SCIENCE', 'https://www.digitaltrends.com/news/nasa-insight-mars-subsurface-boundaries/', 'digitaltrends.com', datetime.datetime(2020, 8, 9, 13, 24), 'NASA’s InSight lander shows what’s beneath Mars’ surface', 'en')
(53, 'SCIENCE', 'https://mybigplunge.com/tech-plunge/spacex-crew-1-mission-with-nasa-first-fully-operational-crewed-mission-to-space-to-launch-in-october/', 'mybigplunge.com', datetime.datetime(2020, 8, 17, 0, 3, 42), 'SpaceX Crew-1 mission with NASA, first fully operational crewed mission to space to launch in October', 'en')
(59, 'SCIENCE', 'https://pledgetimes.com/asteroid-29075-1950-da-would-be-the-greatest-catastrophe-for-earth-tsunami-of-400-toes-excessive-waves/', 'pledgetimes.com', datetime.datetime(2020, 8, 7, 11, 6, 50), 'Asteroid 29075 1950 DA would be the greatest catastrophe for Earth, Tsunami of 400 toes excessive waves', 'en')
(61, 'SCIENCE', 'http://spaceref.com/news/viewpr.html?pid=56068', 'spaceref.com', datetime.datetime(2020, 8, 3, 23, 1, 12), 'ATLAS Space Operations Awarded NASA SBIR Phase II Award to Advance Satellite Constellation Management Scheduling', 'en')
(63, 'SCIENCE', 'https://www.ndtv.com/world-news/greenland-ice-glaciers-melting-past-tipping-point-amid-climate-change-study-2280983', 'ndtv.com', datetime.datetime(2020, 8, 17, 17, 14, 35), 'Greenland Ice Melting Now Irreversible, Has Passed "Tipping Point": Study', 'en')
(70, 'SCIENCE', 'https://www.thequint.com/news/world/nasa-astronauts-in-spacex-capsule-make-touchdow-in-in-gulf-of-mexico', 'thequint.com', datetime.datetime(2020, 8, 3, 3, 2, 32), 'NASA Astronauts in SpaceX Capsule Splashdown in Gulf Of Mexico', 'en')
(76, 'SCIENCE', 'https://www.express.co.uk/news/weird/1323720/alien-base-ufo-mercury-space-news-conspiracy-theory-aliens', 'express.co.uk', datetime.datetime(2020, 8, 17, 8, 39, 37), 'Alien base on Mercury: ET hunters claim to find huge UFO', 'en')
(77, 'SCIENCE', 'https://www.brisbanetimes.com.au/national/australia-s-small-yet-crucial-part-in-the-mission-to-find-life-on-mars-20200803-p55i31.html?ref=rss&utm_medium=rss&utm_source=rss_feed', 'brisbanetimes.com.au', datetime.datetime(2020, 8, 3, 7, 23), "Australia's small yet crucial part in the mission to find life on Mars", 'en')

ANALYSIS:
- Articles for the topic "Science" include titles such as "A closer look at water-splitting's solar fuel potential", "An irresistible scent makes locusts swarm, study finds", "Energy-Efficient Tuning of Spintronic Neurons to Imitate the Non-linear Oscillatory Neural Networks of the Human Brain".
- These articles cover a range of topics within the field of science, from environmental studies to neuroscience, showcasing the diversity of research being conducted in the scientific community.
- The articles were published on various domains such as eurekalert.org, pulse.ng, scitechdaily.com, highlighting the global reach and impact of scientific research in today's world.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: What is the most interesting topic?

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC LIMIT 50;

Results:
('BUSINESS', 15000)
('HEALTH', 15000)
('WORLD', 15000)
('SPORTS', 15000)
('TECHNOLOGY', 15000)
('ENTERTAINMENT', 15000)
('NATION', 15000)
('SCIENCE', 3774)

ANALYSIS:
- Based on the data, the most interesting topic appears to be SCIENCE, as it has a significantly lower count compared to the other topics.
- All other topics, such as BUSINESS, HEALTH, WORLD, SPORTS, TECHNOLOGY, ENTERTAINMENT, and NATION, have an equal count of 15000, indicating similar levels of interest in those subjects.
- The lower count for SCIENCE may suggest that it is a more niche or specialized topic that may appeal to a smaller audience compared to the more popular topics.
- However, it cannot be conclusively determined from the data alone why SCIENCE has a lower count compared to the other topics.
(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: which topic should I read?

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic LIMIT 50;

Results:
('BUSINESS', 15000)
('HEALTH', 15000)
('WORLD', 15000)
('SPORTS', 15000)
('TECHNOLOGY', 15000)
('ENTERTAINMENT', 15000)
('NATION', 15000)
('SCIENCE', 3774)

ANALYSIS:
Based on the data, you should consider reading about the topic of Science.
- Science has a lower count compared to other topics, suggesting that it may be a less common or popular topic among readers.
- This could indicate that there may be some unique or valuable information within the Science topic that is worth exploring.
- However, since all other topics have an equal count, it is not possible to determine a definitive reason why Science stands out in terms of count.

(.venv) (base) mahesh@mahesh-Victus-by-HP-Gaming-Laptop-16-s0xxx:~/cloned_site$ python3 query_testing.py 
Enter your question: Why is business so popular? 

Generated SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC;
Executing SQL: SELECT topic, COUNT(*) AS count
FROM news
GROUP BY topic
ORDER BY count DESC LIMIT 50;

Results:
('BUSINESS', 15000)
('HEALTH', 15000)
('WORLD', 15000)
('SPORTS', 15000)
('TECHNOLOGY', 15000)
('ENTERTAINMENT', 15000)
('NATION', 15000)
('SCIENCE', 3774)

ANALYSIS:
- Based on the data provided, business is popular because it has the highest count compared to other topics such as health, world, sports, technology, entertainment, and nation. 
- The data shows that business is equally as popular as the other major topics, indicating a general interest across a diverse range of subjects.
- We cannot determine the exact reason why business is popular based solely on the data provided, as there may be additional factors at play that are not reflected in the counts.
