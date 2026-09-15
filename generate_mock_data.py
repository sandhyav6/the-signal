"""
generate_mock_data.py — Generates data/mock_articles.json with 75 articles.

Run once from the project root:
    python generate_mock_data.py

Produces articles across 7 categories, 4 sources, timestamps spanning 10 days,
including exact duplicates, near-duplicates, and missing optional fields.
"""

import json
import os
import datetime
import random

random.seed(42)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(BASE_DIR, "data", "mock_articles.json")
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

NOW = datetime.datetime(2026, 9, 13, 12, 0, 0)

SOURCES = ["TechCrunch", "BBC News", "Reuters", "The Guardian"]

ARTICLES_RAW = [
    # ── Technology (15 articles) ────────────────────────────────────────────
    {"title": "OpenAI Releases GPT-5 with Multimodal Reasoning",
     "description": "GPT-5 can process images, audio, and text simultaneously, setting a new benchmark in AI capability.",
     "content": "OpenAI has announced the release of GPT-5, its most advanced language model to date. The model supports multimodal inputs including images, audio, and text, and demonstrates significant improvements in reasoning and instruction following across hundreds of benchmarks.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Sarah Chen", "topics": ["artificial intelligence", "openai", "gpt-5", "machine learning"],
     "popularity_score": 0.92, "days_ago": 0.5},

    {"title": "Apple Unveils M4 MacBook Pro with 48-Hour Battery Life",
     "description": "The new MacBook Pro features Apple's M4 chip and dramatically improved battery performance.",
     "content": "Apple has announced the next generation MacBook Pro lineup powered by the M4 chip. The new machines boast up to 48 hours of battery life and a 40% improvement in GPU performance over M3 models. Pricing starts at $1,999.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Mark Rivera", "topics": ["apple", "macbook", "m4 chip", "laptops"],
     "popularity_score": 0.88, "days_ago": 1.2},

    {"title": "Google DeepMind Achieves Breakthrough in Protein Folding",
     "description": "DeepMind's latest model can predict protein structures with unprecedented accuracy.",
     "content": "Google DeepMind has published research showing a new version of its AlphaFold system that predicts protein structures with near-experimental accuracy. Scientists say this could drastically accelerate drug discovery timelines.",
     "category_slug": "technology", "source_name": "The Guardian",
     "author": "Priya Nair", "topics": ["deepmind", "protein folding", "alphafold", "biotechnology"],
     "popularity_score": 0.85, "days_ago": 2.0},

    {"title": "Meta's AR Glasses Ship to Developers Worldwide",
     "description": "Meta begins shipping its long-awaited augmented reality glasses to registered developers.",
     "content": "Meta has begun fulfilling developer kit orders for its augmented reality glasses. The device offers a 120-degree field of view, spatial audio, and six hours of active use battery life. The consumer version is expected in 2027.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Jordan Lee", "topics": ["meta", "augmented reality", "wearables", "ar glasses"],
     "popularity_score": 0.79, "days_ago": 3.1},

    {"title": "Quantum Computing Startup IonQ Signs $500M Government Contract",
     "description": "IonQ will build quantum systems for U.S. national laboratory infrastructure.",
     "content": "IonQ announced a landmark $500 million multi-year contract with the U.S. Department of Energy to supply quantum computing systems to three national laboratories. The deal is the largest commercial quantum contract in history.",
     "category_slug": "technology", "source_name": "Reuters",
     "author": "Daniel Park", "topics": ["quantum computing", "ionq", "government contracts"],
     "popularity_score": 0.74, "days_ago": 4.0},

    {"title": "Tesla's Full Self-Driving Beta Rolls Out to All U.S. Customers",
     "description": "Tesla FSD v13 is now available to all North American customers without a waitlist.",
     "content": "Tesla has removed the waitlist for its Full Self-Driving software in North America. Version 13 includes significant improvements to intersection handling and lane merging. Regulators continue to monitor safety statistics.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Amy Zhang", "topics": ["tesla", "self-driving", "electric vehicles", "autonomous cars"],
     "popularity_score": 0.83, "days_ago": 5.0},

    {"title": "Microsoft Azure Outage Affects Millions of Users Globally",
     "description": "A six-hour Azure outage disrupted services for businesses across 30 countries.",
     "content": "Microsoft's Azure cloud platform experienced a major outage lasting approximately six hours on Tuesday, affecting services including Teams, Office 365, and numerous third-party applications. Microsoft attributed the issue to a failed configuration update.",
     "category_slug": "technology", "source_name": "BBC News",
     "author": "Chris Morton", "topics": ["microsoft", "azure", "cloud computing", "outage"],
     "popularity_score": 0.81, "days_ago": 6.0},

    {"title": "New Ransomware Strain Targets Hospital Networks in Europe",
     "description": "Security researchers warn of a sophisticated ransomware campaign hitting healthcare facilities.",
     "content": "Cybersecurity firm CrowdStrike has identified a new ransomware strain called BlackMedic targeting hospital IT systems in Germany, France, and the UK. At least 14 hospitals have reported disruptions. Authorities urge immediate patching.",
     "category_slug": "technology", "source_name": "BBC News",
     "author": None, "topics": ["cybersecurity", "ransomware", "healthcare", "europe"],
     "popularity_score": 0.77, "days_ago": 7.0},

    {"title": "Nvidia RTX 5090 Benchmarks Leaked Ahead of CES Reveal",
     "description": "Leaked benchmark scores suggest the RTX 5090 is 60% faster than the 4090.",
     "content": "Ahead of CES, benchmark scores for Nvidia's unreleased RTX 5090 have appeared online. The results, if genuine, indicate a 60% performance improvement over the RTX 4090 in rasterization workloads and 80% in ray tracing.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Kevin Wu", "topics": ["nvidia", "gpu", "rtx 5090", "gaming hardware"],
     "popularity_score": 0.86, "days_ago": 1.8},

    {"title": "SpaceX Starship Completes First Full Orbital Flight",
     "description": "SpaceX's Starship successfully completed a full orbital mission and returned to its launch site.",
     "content": "SpaceX's Starship vehicle completed its first full orbital mission, splashing down safely in the Gulf of Mexico and returning the booster to its Texas launch site via catch. The milestone marks a major step toward Moon and Mars missions.",
     "category_slug": "technology", "source_name": "Reuters",
     "author": "Laura Gomez", "topics": ["spacex", "starship", "space exploration", "rockets"],
     "popularity_score": 0.95, "days_ago": 2.5},

    {"title": "5G Coverage Reaches 80% of Global Urban Population",
     "description": "GSMA reports 5G now covers four-fifths of urban dwellers worldwide.",
     "content": "The GSMA's annual report reveals that 5G networks now cover 80% of the world's urban population, up from 55% last year. Asia-Pacific leads in deployment speed while Africa shows the fastest year-on-year growth rate.",
     "category_slug": "technology", "source_name": "Reuters",
     "author": "Wei Liu", "topics": ["5g", "telecommunications", "mobile networks", "gsma"],
     "popularity_score": 0.65, "days_ago": 8.0},

    {"title": "EU Passes Landmark AI Liability Directive",
     "description": "The European Union finalises rules making AI companies liable for damages caused by their systems.",
     "content": "The European Parliament voted 412 to 148 to adopt the AI Liability Directive, which allows individuals harmed by AI systems to seek compensation more easily. Companies must now document AI decision-making processes and face fines up to 6% of global revenue.",
     "category_slug": "technology", "source_name": "The Guardian",
     "author": "Elena Russo", "topics": ["european union", "ai regulation", "artificial intelligence", "law"],
     "popularity_score": 0.72, "days_ago": 9.0},

    {"title": "Open-Source LLM Mistral 3 Outperforms GPT-4 on Key Benchmarks",
     "description": "French AI startup Mistral releases a powerful open-source LLM rivalling proprietary models.",
     "content": "Mistral AI has released Mistral 3, a 70-billion parameter open-source language model that surpasses GPT-4 on several academic benchmarks while running on consumer hardware. The model is available under the Apache 2.0 licence.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Isabelle Dupont", "topics": ["mistral", "open source", "large language models", "artificial intelligence"],
     "popularity_score": 0.89, "days_ago": 3.5},

    # Near-duplicate of article 1 (same story, slightly different wording)
    {"title": "OpenAI Launches GPT-5: A New Era for Multimodal AI",
     "description": "GPT-5 processes images, audio, and text at once, outperforming all existing models.",
     "content": "OpenAI today launched GPT-5, a multimodal AI model capable of simultaneously understanding text, images, and audio. The model sets new records on reasoning benchmarks and marks a significant advancement in large language model capability.",
     "category_slug": "technology", "source_name": "BBC News",
     "author": "Tom Harris", "topics": ["artificial intelligence", "openai", "gpt-5"],
     "popularity_score": 0.90, "days_ago": 0.7},

    {"title": "GitHub Copilot Now Supports 30 Programming Languages",
     "description": "GitHub's AI coding assistant adds support for Rust, Julia, and 28 other languages.",
     "content": "GitHub has updated Copilot to support 30 programming languages including Rust, Julia, Elixir, and Haskell. The update also introduces a new command-line interface mode for terminal-based workflows.",
     "category_slug": "technology", "source_name": "TechCrunch",
     "author": "Raj Patel", "topics": ["github", "copilot", "developer tools", "artificial intelligence"],
     "popularity_score": 0.76, "days_ago": 4.5},

    # ── Science (12 articles) ────────────────────────────────────────────────
    {"title": "James Webb Telescope Discovers Oldest Galaxy Ever Observed",
     "description": "JWST detects a galaxy formed just 290 million years after the Big Bang.",
     "content": "Astronomers using the James Webb Space Telescope have identified a galaxy designated JADES-GS-z14-0 that formed approximately 290 million years after the Big Bang. It is the oldest and most distant galaxy ever confirmed.",
     "category_slug": "science", "source_name": "BBC News",
     "author": "Dr. Alicia Torres", "topics": ["james webb telescope", "astronomy", "galaxies", "cosmology"],
     "popularity_score": 0.91, "days_ago": 1.5},

    {"title": "Scientists Develop Biodegradable Plastic That Dissolves in Seawater",
     "description": "A rice-based polymer breaks down in ocean conditions within 30 days.",
     "content": "Researchers at the University of Tokyo have created a new biodegradable plastic derived from rice husks that completely dissolves in seawater within 30 days without producing microplastics. The material matches conventional plastic in tensile strength.",
     "category_slug": "science", "source_name": "The Guardian",
     "author": "Kenji Tanaka", "topics": ["biodegradable plastic", "ocean pollution", "materials science", "environment"],
     "popularity_score": 0.84, "days_ago": 2.8},

    {"title": "CRISPR Gene Therapy Cures Sickle Cell Disease in Clinical Trial",
     "description": "All 45 patients in a Phase III trial showed complete remission after CRISPR treatment.",
     "content": "A Phase III clinical trial published in the New England Journal of Medicine reports that 45 out of 45 patients with sickle cell disease achieved complete remission following CRISPR-based gene therapy. Patients have been symptom-free for up to three years.",
     "category_slug": "science", "source_name": "Reuters",
     "author": "Dr. Fatima Al-Rashid", "topics": ["crispr", "gene therapy", "sickle cell disease", "medicine"],
     "popularity_score": 0.93, "days_ago": 3.8},

    {"title": "New Evidence Suggests Mars Had Liquid Water 500 Million Years Ago",
     "description": "Perseverance rover data reveals ancient river deltas in unexpected regions of Mars.",
     "content": "Analysis of data from NASA's Perseverance rover has revealed sedimentary rock formations in the Jezero Crater region consistent with ancient river deltas. Scientists now believe flowing water may have persisted on Mars until as recently as 500 million years ago.",
     "category_slug": "science", "source_name": "BBC News",
     "author": "Dr. Carl Simmons", "topics": ["mars", "perseverance rover", "water", "planetary science"],
     "popularity_score": 0.87, "days_ago": 5.5},

    {"title": "Climate Scientists Warn Arctic Could Be Ice-Free by 2035",
     "description": "Updated climate models project an ice-free Arctic summer within the decade.",
     "content": "A consortium of climate research institutions has published a study in Nature Climate Change warning that the Arctic Ocean could experience its first completely ice-free summer as early as 2035. The timeline is a decade earlier than previous projections.",
     "category_slug": "science", "source_name": "The Guardian",
     "author": "Dr. Ingrid Holm", "topics": ["climate change", "arctic", "sea ice", "global warming"],
     "popularity_score": 0.88, "days_ago": 4.2},

    {"title": "New Antibiotic Effective Against Drug-Resistant Superbugs Discovered",
     "description": "A soil bacterium yields a compound that kills MRSA and other resistant pathogens.",
     "content": "Scientists at Northeastern University have isolated a novel antibiotic compound from a previously unstudied soil bacterium. Laboratory tests show the compound, named clovibactin, is effective against MRSA, drug-resistant Streptococcus, and several other superbugs.",
     "category_slug": "science", "source_name": "Reuters",
     "author": None, "topics": ["antibiotics", "superbugs", "mrsa", "drug resistance"],
     "popularity_score": 0.86, "days_ago": 6.5},

    {"title": "Physicists Detect Gravitational Waves from Neutron Star Merger",
     "description": "LIGO and Virgo detect the closest neutron star merger ever recorded.",
     "content": "The LIGO-Virgo-KAGRA collaboration has confirmed the detection of gravitational waves from a neutron star merger just 130 million light-years away — the closest ever recorded. The event, designated GW250910, will allow unprecedented study of heavy element formation.",
     "category_slug": "science", "source_name": "BBC News",
     "author": "Dr. Noah White", "topics": ["gravitational waves", "ligo", "neutron stars", "physics"],
     "popularity_score": 0.82, "days_ago": 7.5},

    {"title": "Deep-Sea Expedition Discovers 20 New Species Near Galapagos",
     "description": "A research vessel finds never-before-seen organisms at 2,000-meter depths.",
     "content": "An international research team conducting a deep-sea survey near Ecuador's Galapagos Islands has documented 20 previously unknown species including bizarre sponges, worms, and a cephalopod with unprecedented bioluminescent patterns.",
     "category_slug": "science", "source_name": "The Guardian",
     "author": "Dr. Marina Costa", "topics": ["deep sea", "new species", "marine biology", "galapagos"],
     "popularity_score": 0.79, "days_ago": 8.5},

    {"title": "Solar Cycle 25 Peaks Ahead of Schedule with Record Sunspot Activity",
     "description": "The sun's current cycle is more active than any in 50 years, affecting GPS and radio.",
     "content": "NOAA reports that Solar Cycle 25 has exceeded all predictions, reaching its maximum with the highest sustained sunspot numbers in half a century. The heightened activity has disrupted GPS accuracy and shortwave radio communications on multiple occasions.",
     "category_slug": "science", "source_name": "Reuters",
     "author": "Peter Holt", "topics": ["solar cycle", "sunspots", "space weather", "gps"],
     "popularity_score": 0.71, "days_ago": 9.0},

    {"title": "Breakthrough in Nuclear Fusion: Ignition Maintained for 100 Seconds",
     "description": "ITER partner lab sustains fusion ignition for the first time beyond a single pulse.",
     "content": "Scientists at the Korea Institute of Fusion Energy (KIFE) have maintained nuclear fusion ignition for 100 consecutive seconds in their KSTAR tokamak. Previous records were limited to brief pulses. Sustained fusion power is described as a watershed moment.",
     "category_slug": "science", "source_name": "BBC News",
     "author": "Dr. Ji-Hoon Kim", "topics": ["nuclear fusion", "kstar", "tokamak", "clean energy"],
     "popularity_score": 0.94, "days_ago": 0.3},

    # Near-duplicate of CRISPR article
    {"title": "CRISPR Treatment Eliminates Sickle Cell Symptoms in All Trial Patients",
     "description": "The gene-editing therapy achieved complete remission in a landmark Phase III study.",
     "content": "A landmark clinical study shows that CRISPR Cas9 gene editing has eliminated sickle cell disease symptoms in every participant of a Phase III trial. All 45 patients remain in remission up to three years post-treatment, researchers report.",
     "category_slug": "science", "source_name": "The Guardian",
     "author": "Miriam Stone", "topics": ["crispr", "gene therapy", "sickle cell disease"],
     "popularity_score": 0.91, "days_ago": 4.0},

    {"title": "Researchers Create Self-Healing Concrete That Repairs Own Cracks",
     "description": "Bacteria-infused concrete can seal cracks autonomously, extending bridge lifespans.",
     "content": "A team at Delft University has created concrete embedded with spore-forming bacteria and calcium lactate capsules. When cracks form, water activates the bacteria which produce calcite, sealing gaps up to 0.8mm. Field tests show bridges lasting three times longer.",
     "category_slug": "science", "source_name": "Reuters",
     "author": "Anna Van Der Berg", "topics": ["construction materials", "bio-concrete", "civil engineering"],
     "popularity_score": 0.73, "days_ago": 5.0},

    # ── Politics (10 articles) ───────────────────────────────────────────────
    {"title": "UN Security Council Passes Resolution on AI Governance",
     "description": "A rare unanimous vote calls for global standards on military use of AI.",
     "content": "The United Nations Security Council unanimously passed Resolution 2875, which calls on member states to develop binding international standards governing the military use of artificial intelligence. The resolution follows concerns about autonomous weapons systems.",
     "category_slug": "politics", "source_name": "BBC News",
     "author": "Ambassador Chen Wei", "topics": ["united nations", "ai governance", "international law", "security council"],
     "popularity_score": 0.78, "days_ago": 2.0},

    {"title": "India and EU Sign Free Trade Agreement After 15 Years of Talks",
     "description": "The landmark trade deal eliminates tariffs on 90% of goods between India and Europe.",
     "content": "After more than 15 years of negotiations, India and the European Union have signed a comprehensive Free Trade Agreement. The deal eliminates tariffs on 90% of traded goods and opens services markets for professional visa-holders.",
     "category_slug": "politics", "source_name": "Reuters",
     "author": "Suresh Kumar", "topics": ["india", "european union", "trade deal", "international trade"],
     "popularity_score": 0.80, "days_ago": 3.0},

    {"title": "U.S. Senate Passes Infrastructure Modernisation Bill",
     "description": "A bipartisan $1.2 trillion bill funds roads, broadband, and clean energy across all 50 states.",
     "content": "The U.S. Senate voted 68-32 to pass the Infrastructure Modernisation Act, allocating $1.2 trillion over eight years. Funds are earmarked for highway repair, nationwide broadband expansion, water system upgrades, and clean energy grid improvements.",
     "category_slug": "politics", "source_name": "BBC News",
     "author": "Sandra Mills", "topics": ["united states", "infrastructure", "congress", "bipartisan"],
     "popularity_score": 0.75, "days_ago": 4.5},

    {"title": "Brazil Holds Runoff Election Amid Record Voter Turnout",
     "description": "Brazilians head to polls for a tightly contested presidential runoff.",
     "content": "Brazil's presidential runoff election saw record turnout as two candidates separated by under two percentage points in the first round face a final vote. Early projections show results too close to call with 60% of votes counted.",
     "category_slug": "politics", "source_name": "Reuters",
     "author": "Carlos Ferreira", "topics": ["brazil", "elections", "democracy", "south america"],
     "popularity_score": 0.83, "days_ago": 1.0},

    {"title": "Germany Announces €50 Billion Green Energy Investment Package",
     "description": "Berlin commits to accelerating renewable energy to reach 100% clean power by 2033.",
     "content": "The German government announced a €50 billion investment fund to accelerate wind, solar, and hydrogen energy production. The goal is 100% renewable electricity by 2033, six years ahead of the previous target.",
     "category_slug": "politics", "source_name": "The Guardian",
     "author": "Klaus Bauer", "topics": ["germany", "green energy", "renewable energy", "climate policy"],
     "popularity_score": 0.76, "days_ago": 6.0},

    {"title": "NATO Summit Agrees to Raise Defence Spending to 2.5% of GDP",
     "description": "Alliance members commit to a higher military spending target at Warsaw summit.",
     "content": "At the Warsaw NATO Summit, all 32 member states agreed to raise their defence spending commitments from 2% to 2.5% of GDP within three years. The decision follows ongoing security concerns along the eastern flank.",
     "category_slug": "politics", "source_name": "BBC News",
     "author": "Richard Forbes", "topics": ["nato", "defence spending", "military", "europe"],
     "popularity_score": 0.81, "days_ago": 7.0},

    {"title": "IMF Raises Global Growth Forecast to 3.4% for 2026",
     "description": "The International Monetary Fund revises upward on stronger-than-expected emerging market performance.",
     "content": "The IMF upgraded its global growth outlook to 3.4% for 2026, citing stronger performance in India, Southeast Asia, and Sub-Saharan Africa. It cautioned about risks from high debt levels in advanced economies.",
     "category_slug": "politics", "source_name": "Reuters",
     "author": "Jean-Pierre Moreau", "topics": ["imf", "global economy", "growth forecast", "emerging markets"],
     "popularity_score": 0.69, "days_ago": 8.0},

    {"title": "Japan Passes Historic Defence Policy Revision",
     "description": "Japan's Diet approves a shift that allows offensive military strike capabilities for the first time.",
     "content": "Japan's parliament, the Diet, has approved a historic revision to the country's defence policy that allows the Japanese Self-Defence Forces to develop offensive strike capabilities. The shift marks the most significant change to Japan's pacifist constitution-era defence posture in 70 years.",
     "category_slug": "politics", "source_name": "BBC News",
     "author": "Yuki Tanaka", "topics": ["japan", "defence policy", "military", "asia"],
     "popularity_score": 0.77, "days_ago": 5.5},

    {"title": "WHO Declares End to mpox Global Health Emergency",
     "description": "The World Health Organization says the 2024 mpox outbreak is no longer a global emergency.",
     "content": "The WHO Director-General announced the end of the mpox public health emergency of international concern, citing declining case counts globally. The declaration was welcomed by health officials but experts warn continued surveillance is needed.",
     "category_slug": "politics", "source_name": "Reuters",
     "author": None, "topics": ["who", "mpox", "public health", "global health"],
     "popularity_score": 0.70, "days_ago": 9.0},

    {"title": "COP31 Agreement Sets 1.3°C Carbon Pathway, NGOs Call It Insufficient",
     "description": "Nations reach a climate deal in Dubai but environmental groups say pledges fall short.",
     "content": "COP31 delegates finalised an agreement committing signatories to a 1.3°C carbon pathway with binding five-year emissions reviews. Environmental NGOs immediately criticised the deal as insufficient, while fossil-fuel producing nations called it an overreach.",
     "category_slug": "politics", "source_name": "The Guardian",
     "author": "Amira Hassan", "topics": ["cop31", "climate change", "carbon emissions", "paris agreement"],
     "popularity_score": 0.85, "days_ago": 2.5},

    # ── Business (10 articles) ───────────────────────────────────────────────
    {"title": "Amazon Reports Record Q2 Revenue of $590 Billion",
     "description": "AWS growth and advertising revenue drive Amazon to its best quarter ever.",
     "content": "Amazon reported record-breaking Q2 revenue of $590 billion, surpassing analyst expectations by 8%. AWS grew 35% year-over-year and advertising revenue reached $65 billion, reflecting the growing dominance of Amazon's non-retail business segments.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Patricia Lawson", "topics": ["amazon", "revenue", "aws", "cloud computing"],
     "popularity_score": 0.84, "days_ago": 1.5},

    {"title": "Bitcoin Hits $150,000 as Institutional Adoption Soars",
     "description": "Bitcoin reaches a new all-time high driven by ETF inflows and corporate treasury buying.",
     "content": "Bitcoin surpassed $150,000 for the first time, driven by record ETF inflows and announcements from three Fortune 500 companies adding BTC to their corporate treasuries. The total cryptocurrency market cap crossed $5 trillion.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Alex Kim", "topics": ["bitcoin", "cryptocurrency", "etf", "institutional investment"],
     "popularity_score": 0.91, "days_ago": 0.8},

    {"title": "OPEC+ Agrees to Cut Production by 2 Million Barrels Per Day",
     "description": "The oil cartel reduces output targets, pushing Brent crude above $95 per barrel.",
     "content": "OPEC+ member nations agreed to cut collective oil production by 2 million barrels per day effective October 1. Brent crude prices jumped 4% on the news to $95.40 per barrel. The cut reflects concerns about weakening global demand growth.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Hana Al-Mansoori", "topics": ["opec", "oil prices", "crude oil", "energy"],
     "popularity_score": 0.79, "days_ago": 3.0},

    {"title": "Startups Raise $80 Billion in VC Funding in First Half of 2026",
     "description": "Venture capital activity rebounds sharply led by AI and biotech companies.",
     "content": "Global venture capital investment reached $80 billion in the first half of 2026, a 45% increase over the same period last year. AI infrastructure startups attracted $28 billion of that total, while biotech companies raised $18 billion.",
     "category_slug": "business", "source_name": "TechCrunch",
     "author": "Monica Reyes", "topics": ["venture capital", "startups", "funding", "artificial intelligence"],
     "popularity_score": 0.76, "days_ago": 4.0},

    {"title": "Global Supply Chain Disruptions Ease as Red Sea Shipping Returns to Normal",
     "description": "Shipping route normalisation cuts container freight costs by 40% from 2025 peaks.",
     "content": "After 18 months of disruption, shipping through the Red Sea has returned to near-normal volumes following a US-led naval deterrence operation. Container freight rates have fallen 40% from their 2025 peaks, benefiting importers and retailers worldwide.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Stephen Walsh", "topics": ["supply chain", "shipping", "red sea", "freight"],
     "popularity_score": 0.71, "days_ago": 5.0},

    {"title": "Apple Becomes First $4 Trillion Company",
     "description": "Apple's market capitalisation crosses $4 trillion, a first for any listed company.",
     "content": "Apple Inc. became the first publicly listed company in history to reach a $4 trillion market capitalisation, driven by strong iPhone 17 sales and growing services revenue. The milestone is a testament to the company's diversification beyond hardware.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Linda Zhao", "topics": ["apple", "stock market", "market cap", "technology stocks"],
     "popularity_score": 0.89, "days_ago": 2.0},

    {"title": "India Overtakes Japan to Become World's Third Largest Economy",
     "description": "IMF data confirms India's GDP has surpassed Japan's in nominal terms.",
     "content": "According to the latest IMF World Economic Outlook data, India's nominal GDP has surpassed Japan's, making India the world's third-largest economy. India's rapid growth has been fuelled by a booming services sector and domestic consumption.",
     "category_slug": "business", "source_name": "The Guardian",
     "author": "Anand Krishnamurthy", "topics": ["india", "gdp", "economy", "japan"],
     "popularity_score": 0.86, "days_ago": 6.0},

    {"title": "Airbus Secures 500-Aircraft Order from Saudi Arabian Airlines",
     "description": "The deal, worth $75 billion, is the largest single aircraft order in aviation history.",
     "content": "Airbus announced a $75 billion agreement to supply 500 aircraft to Saudi Arabian Airlines, the largest single aircraft purchase order in aviation industry history. The order includes A320neo, A350, and the new A380X wide-body jets.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Francois Leblond", "topics": ["airbus", "aviation", "aircraft", "saudi arabia"],
     "popularity_score": 0.78, "days_ago": 7.0},

    {"title": "Global Inflation Falls to 2.8%, Lowest Since 2020",
     "description": "Cooling energy prices and tighter monetary policy bring inflation back toward central bank targets.",
     "content": "Global consumer price inflation fell to 2.8% in August, the lowest level since March 2020, according to World Bank data. Central banks in major economies signal possible rate cuts as inflation nears their 2% targets.",
     "category_slug": "business", "source_name": "BBC News",
     "author": "Margaret Price", "topics": ["inflation", "monetary policy", "interest rates", "central banks"],
     "popularity_score": 0.75, "days_ago": 8.0},

    # Exact duplicate of Bitcoin article (to test dedup)
    {"title": "Bitcoin Hits $150,000 as Institutional Adoption Soars",
     "description": "Bitcoin reaches a new all-time high driven by ETF inflows and corporate treasury buying.",
     "content": "Bitcoin surpassed $150,000 for the first time, driven by record ETF inflows and announcements from three Fortune 500 companies adding BTC to their corporate treasuries. The total cryptocurrency market cap crossed $5 trillion.",
     "category_slug": "business", "source_name": "Reuters",
     "author": "Alex Kim", "topics": ["bitcoin", "cryptocurrency", "etf"],
     "popularity_score": 0.91, "days_ago": 0.8},

    # ── Sports (10 articles) ─────────────────────────────────────────────────
    {"title": "India Wins ICC Cricket World Cup Final Against Australia",
     "description": "India clinches the World Cup by 6 wickets in a thrilling final at Wankhede Stadium.",
     "content": "India defeated Australia by six wickets in the ICC Cricket World Cup final played at Wankhede Stadium, Mumbai. Virat Kohli's unbeaten 87 guided India's chase of 241, securing the nation's third 50-over World Cup title.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": "Deepak Sharma", "topics": ["cricket", "icc world cup", "india", "australia"],
     "popularity_score": 0.97, "days_ago": 1.0},

    {"title": "Real Madrid Clinch La Liga Title with Three Games to Spare",
     "description": "Vinicius Jr's hat-trick seals the Spanish league title for Real Madrid.",
     "content": "Real Madrid clinched the La Liga championship with three games remaining in the season, following a 4-1 victory over Atletico Madrid. Vinicius Jr. scored a hat-trick and provided an assist, cementing his status as the world's best player.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": "Carlos Gomez", "topics": ["real madrid", "la liga", "football", "vinicius jr"],
     "popularity_score": 0.88, "days_ago": 2.5},

    {"title": "Novak Djokovic Wins 25th Grand Slam at US Open",
     "description": "Djokovic clinches a record-extending 25th major title in straight sets at Flushing Meadows.",
     "content": "Novak Djokovic defeated Carlos Alcaraz 6-3, 7-6, 6-2 to win the US Open and claim his record-extending 25th Grand Slam title. The victory silenced questions about his competitiveness at age 39 and extends his all-time record.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": "Tom Bradley", "topics": ["novak djokovic", "us open", "tennis", "grand slam"],
     "popularity_score": 0.92, "days_ago": 3.5},

    {"title": "Paris 2024 Olympics Legacy: France Reports 15% Rise in Sport Participation",
     "description": "Two years on, French citizens are playing more sport than ever following the Paris Games.",
     "content": "France's sports ministry has published data showing a 15% increase in sports club registrations nationally since the 2024 Paris Olympics. Swimming, athletics, and cycling have seen the largest gains, attributing the rise to the Games' inspiration effect.",
     "category_slug": "sports", "source_name": "The Guardian",
     "author": "Sophie Martin", "topics": ["olympics", "paris 2024", "sports", "france"],
     "popularity_score": 0.72, "days_ago": 4.5},

    {"title": "Formula 1 Introduces Hydrogen-Powered Test Cars for 2028 Season",
     "description": "FIA and F1 announce a hydrogen prototype programme running parallel to the main championship.",
     "content": "Formula 1 and the FIA unveiled a hydrogen-powered racing car concept targeted at competing alongside the main championship from the 2028 season. The prototype, tested at Silverstone, achieved speeds of 220 mph in initial performance runs.",
     "category_slug": "sports", "source_name": "Reuters",
     "author": "James Whitmore", "topics": ["formula 1", "hydrogen", "motorsport", "green racing"],
     "popularity_score": 0.79, "days_ago": 5.5},

    {"title": "NBA Finals: Golden State Warriors Defeat Boston Celtics 4-2",
     "description": "Stephen Curry wins his fifth ring as Warriors claim another championship.",
     "content": "The Golden State Warriors defeated the Boston Celtics four games to two in the NBA Finals. Stephen Curry averaged 32 points per game throughout the series and was named Finals MVP for the fourth time. The Warriors claim their seventh franchise title.",
     "category_slug": "sports", "source_name": "Reuters",
     "author": "Marcus Green", "topics": ["nba", "golden state warriors", "stephen curry", "basketball"],
     "popularity_score": 0.90, "days_ago": 6.5},

    {"title": "Tiger Woods Announces Retirement from Professional Golf",
     "description": "Golf legend Tiger Woods, 50, announces he will no longer compete on tour.",
     "content": "Tiger Woods has announced his retirement from professional competitive golf at the age of 50. In a statement posted to social media, Woods said repeated knee surgeries have made competition at the highest level no longer tenable. He plans to remain involved in course design.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": "Amanda Clarke", "topics": ["tiger woods", "golf", "retirement", "pga tour"],
     "popularity_score": 0.95, "days_ago": 7.5},

    {"title": "Women's World Cup 2027 to Be Hosted Jointly by Brazil and Colombia",
     "description": "FIFA awards the 2027 Women's World Cup co-hosting rights to Brazil and Colombia.",
     "content": "FIFA has confirmed Brazil and Colombia as the joint hosts of the 2027 FIFA Women's World Cup. The decision was announced at FIFA Congress, with the tournament expanding to 48 teams for the first time. Eight cities across the two nations will host matches.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": None, "topics": ["fifa", "womens world cup", "football", "brazil", "colombia"],
     "popularity_score": 0.82, "days_ago": 8.5},

    # Exact duplicate of India Cricket article (to test dedup)
    {"title": "India Wins ICC Cricket World Cup Final Against Australia",
     "description": "India clinches the World Cup by 6 wickets in a thrilling final at Wankhede Stadium.",
     "content": "India defeated Australia by six wickets in the ICC Cricket World Cup final played at Wankhede Stadium, Mumbai. Virat Kohli's unbeaten 87 guided India's chase of 241, securing the nation's third 50-over World Cup title.",
     "category_slug": "sports", "source_name": "BBC News",
     "author": "Deepak Sharma", "topics": ["cricket", "icc world cup", "india", "australia"],
     "popularity_score": 0.97, "days_ago": 1.0},

    {"title": "Manchester City Sign Erling Haaland Contract Extension Until 2032",
     "description": "Haaland commits his future to City, ending speculation about a move to Real Madrid.",
     "content": "Erling Haaland has signed a contract extension with Manchester City keeping him at the club until 2032. The Norwegian striker, who has scored over 200 Premier League goals in five seasons, rejected an overture from Real Madrid.",
     "category_slug": "sports", "source_name": "The Guardian",
     "author": "Pete Henderson", "topics": ["manchester city", "erling haaland", "football", "premier league"],
     "popularity_score": 0.87, "days_ago": 9.0},

    # ── Health (10 articles) ─────────────────────────────────────────────────
    {"title": "WHO Approves First Malaria Vaccine for Sub-Saharan Africa",
     "description": "R21/Matrix-M achieves 80% efficacy and begins rollout across 20 African nations.",
     "content": "The World Health Organization has granted full approval for the R21/Matrix-M malaria vaccine following trials demonstrating 80% efficacy. The vaccine programme begins immediate rollout in 20 Sub-Saharan African countries, where malaria kills over 600,000 people annually.",
     "category_slug": "health", "source_name": "Reuters",
     "author": "Dr. James Okonkwo", "topics": ["malaria", "vaccine", "who", "africa", "public health"],
     "popularity_score": 0.92, "days_ago": 0.5},

    {"title": "Ozempic Study Finds 40% Reduction in Cardiovascular Events",
     "description": "A large clinical trial confirms semaglutide's cardiovascular benefits beyond weight loss.",
     "content": "A 10,000-patient clinical trial published in the Lancet reports that semaglutide (Ozempic/Wegovy) reduces major adverse cardiovascular events by 40% independent of its weight loss effects. The finding significantly expands the drug's potential therapeutic indications.",
     "category_slug": "health", "source_name": "Reuters",
     "author": "Dr. Linda Peterson", "topics": ["ozempic", "semaglutide", "weight loss", "cardiovascular"],
     "popularity_score": 0.89, "days_ago": 2.0},

    {"title": "Study Links Ultra-Processed Foods to 50 Adverse Health Outcomes",
     "description": "Analysis of 45 meta-analyses finds ultra-processed foods raise risk of cancer, diabetes, and dementia.",
     "content": "A review published in the BMJ covering 45 meta-analyses and nearly 10 million people found that high consumption of ultra-processed foods is associated with 50 adverse health outcomes including a 21% higher risk of all-cause mortality.",
     "category_slug": "health", "source_name": "The Guardian",
     "author": "Dr. Hannah Moore", "topics": ["ultra-processed food", "diet", "cancer", "nutrition"],
     "popularity_score": 0.85, "days_ago": 3.0},

    {"title": "AI System Detects Alzheimer's 10 Years Before Symptoms Appear",
     "description": "A deep-learning model trained on MRI scans identifies Alzheimer's biomarkers a decade early.",
     "content": "Researchers at UCL and Stanford have developed an AI model that analyses MRI brain scans and can identify Alzheimer's disease biomarkers up to 10 years before clinical symptoms manifest. The system showed 94% sensitivity and 89% specificity on a validation cohort.",
     "category_slug": "health", "source_name": "BBC News",
     "author": "Dr. Raj Iyer", "topics": ["alzheimers", "artificial intelligence", "mri", "early detection"],
     "popularity_score": 0.88, "days_ago": 4.0},

    {"title": "Global Life Expectancy Reaches New High of 76 Years",
     "description": "UN data shows global average life expectancy recovered and improved post-pandemic.",
     "content": "The United Nations Population Division reports that global average life expectancy has recovered from COVID-19 lows and reached a new high of 76.3 years. Gains are largest in Sub-Saharan Africa where malaria vaccines and improved maternal care are credited.",
     "category_slug": "health", "source_name": "Reuters",
     "author": None, "topics": ["life expectancy", "global health", "united nations"],
     "popularity_score": 0.74, "days_ago": 5.0},

    {"title": "Mental Health Apps Prove Effective in NHS Pilot, Study Finds",
     "description": "A UK trial of digital CBT apps shows comparable outcomes to in-person therapy for mild depression.",
     "content": "An NHS England pilot programme of 20 digital cognitive behavioural therapy apps found that patients with mild to moderate depression achieved clinical outcomes comparable to six sessions of in-person therapy. Cost per patient was 85% lower.",
     "category_slug": "health", "source_name": "The Guardian",
     "author": "Dr. Emily Shaw", "topics": ["mental health", "nhs", "cbt", "digital health"],
     "popularity_score": 0.76, "days_ago": 6.0},

    {"title": "New Drug Combination Reduces HIV Viral Load to Undetectable in 95% of Patients",
     "description": "A once-monthly injectable regimen simplifies HIV treatment and improves adherence.",
     "content": "Clinical results published in the New England Journal of Medicine show that a once-monthly injectable combination of lenacapavir and islatravir achieved undetectable HIV viral loads in 95% of participants after six months, outperforming daily oral regimens.",
     "category_slug": "health", "source_name": "Reuters",
     "author": "Dr. Sandra Osei", "topics": ["hiv", "antiretrovirals", "infectious disease"],
     "popularity_score": 0.83, "days_ago": 7.0},

    {"title": "Childhood Obesity Rates Decline for First Time Since Records Began",
     "description": "WHO data shows a statistically significant fall in childhood obesity prevalence globally.",
     "content": "The World Health Organization reports the first ever statistically significant decline in global childhood obesity rates, falling from 8.7% in 2022 to 7.9% in 2025. Researchers credit sugar taxes, school nutrition policies, and increased physical activity programmes.",
     "category_slug": "health", "source_name": "BBC News",
     "author": "Dr. Claire Bennett", "topics": ["childhood obesity", "nutrition", "who", "public health"],
     "popularity_score": 0.81, "days_ago": 8.0},

    {"title": "Gene Therapy Restores Hearing in Children Born Deaf",
     "description": "A one-time gene injection restores functional hearing in children with OTOF gene mutations.",
     "content": "A clinical trial at Mass Eye and Ear and multiple European centres reports that a single injection of gene therapy targeting the OTOF gene restored functional hearing in 18 of 20 children born with profound deafness due to that mutation. Results hold at 18-month follow-up.",
     "category_slug": "health", "source_name": "BBC News",
     "author": "Dr. Michael Lawson", "topics": ["gene therapy", "hearing loss", "deafness", "otof"],
     "popularity_score": 0.91, "days_ago": 1.5},

    {"title": "Coffee Consumption Linked to Lower Risk of Type 2 Diabetes",
     "description": "A 25-year study of 500,000 people finds drinking 3-4 cups of coffee daily reduces diabetes risk by 25%.",
     "content": "A prospective study of 500,000 participants published in Diabetes Care found that drinking three to four cups of coffee daily is associated with a 25% lower risk of developing type 2 diabetes, regardless of caffeination. The protective effect is attributed to polyphenols.",
     "category_slug": "health", "source_name": "The Guardian",
     "author": "Dr. Anna Christensen", "topics": ["coffee", "type 2 diabetes", "nutrition", "diet"],
     "popularity_score": 0.77, "days_ago": 10.5},

    # ── Entertainment (8 articles) ───────────────────────────────────────────
    {"title": "Oppenheimer Sequel 'Trinity' Greenlit by Universal Pictures",
     "description": "Christopher Nolan confirms a follow-up to his Oscar-winning nuclear biopic.",
     "content": "Universal Pictures has officially greenlit 'Trinity', a sequel to Christopher Nolan's 2023 Oscar-winning 'Oppenheimer'. The film will focus on the post-war period of the atomic age and is expected to begin production in 2026 with Cillian Murphy returning.",
     "category_slug": "entertainment", "source_name": "BBC News",
     "author": "Rebecca Walsh", "topics": ["oppenheimer", "christopher nolan", "movies", "universal pictures"],
     "popularity_score": 0.88, "days_ago": 1.0},

    {"title": "Netflix Announces 10 Original Indian Language Series",
     "description": "Netflix commits $1 billion to produce 10 original Indian regional language series over three years.",
     "content": "Netflix has announced a $1 billion investment to produce 10 original series in Indian regional languages including Tamil, Telugu, Malayalam, and Bengali. The investment underscores India's growing importance as one of Netflix's largest markets.",
     "category_slug": "entertainment", "source_name": "TechCrunch",
     "author": "Arun Menon", "topics": ["netflix", "india", "streaming", "original content"],
     "popularity_score": 0.82, "days_ago": 3.0},

    {"title": "Taylor Swift Breaks Record with 'Eras Tour' Grossing $2.5 Billion",
     "description": "The Eras Tour is confirmed as the highest-grossing concert tour in history.",
     "content": "Taylor Swift's Eras Tour has officially become the highest-grossing concert tour in history, surpassing $2.5 billion in total revenue. The tour, now concluded after 22 months, sold over 10 million tickets across 151 shows on six continents.",
     "category_slug": "entertainment", "source_name": "BBC News",
     "author": "Jessica Brown", "topics": ["taylor swift", "eras tour", "music", "concert"],
     "popularity_score": 0.95, "days_ago": 2.0},

    {"title": "Oscar 2027 Voters Now Includes 50% International Members",
     "description": "The Academy of Motion Picture Arts and Sciences reaches its international membership goal.",
     "content": "The Academy of Motion Picture Arts and Sciences announced that its voting membership is now 50% international for the first time. The change is expected to have significant effects on the types of films that receive Oscar nominations going forward.",
     "category_slug": "entertainment", "source_name": "The Guardian",
     "author": "Dana Rivera", "topics": ["oscars", "academy awards", "hollywood", "international film"],
     "popularity_score": 0.73, "days_ago": 5.0},

    {"title": "Minecraft Movie Opens to $250 Million Global Weekend",
     "description": "The live-action Minecraft adaptation smashes box office records on its opening weekend.",
     "content": "The live-action Minecraft movie opened to a $250 million global box office weekend, the largest debut for a video game adaptation in film history. Critics gave mixed reviews but audiences gave it an A+ CinemaScore rating.",
     "category_slug": "entertainment", "source_name": "BBC News",
     "author": None, "topics": ["minecraft", "movies", "box office", "gaming"],
     "popularity_score": 0.86, "days_ago": 4.0},

    {"title": "Spotify Reports 700 Million Monthly Active Users",
     "description": "Spotify's subscriber count grows 18% year-on-year driven by podcast and audiobook growth.",
     "content": "Spotify reported a record 700 million monthly active users in its Q2 earnings, representing 18% year-on-year growth. The platform's podcast and audiobook divisions, launched in 2023, now account for 25% of total listening time.",
     "category_slug": "entertainment", "source_name": "TechCrunch",
     "author": "Lars Erikson", "topics": ["spotify", "streaming", "music", "podcasts"],
     "popularity_score": 0.80, "days_ago": 6.0},

    {"title": "GTA VI Breaks Pre-Order Records with 50 Million Copies Reserved",
     "description": "Rockstar Games' Grand Theft Auto VI becomes the most pre-ordered game in history.",
     "content": "Rockstar Games announced that Grand Theft Auto VI has accumulated 50 million pre-orders ahead of its scheduled October 2026 release, making it the most pre-ordered video game in history. The game is set in a fictional Miami and surrounding state.",
     "category_slug": "entertainment", "source_name": "TechCrunch",
     "author": "Ryan Blake", "topics": ["gta vi", "rockstar games", "video games", "gaming"],
     "popularity_score": 0.97, "days_ago": 7.0},

    # Near-duplicate of Taylor Swift article
    {"title": "Taylor Swift's Eras Tour Becomes Highest-Grossing Tour Ever at $2.5 Billion",
     "description": "The record-breaking Eras Tour wraps as the most lucrative concert tour of all time.",
     "content": "Taylor Swift has completed the Eras Tour, now confirmed as the highest-grossing concert tour ever with $2.5 billion in revenue. The 22-month, 151-show tour sold over 10 million tickets to fans on six continents.",
     "category_slug": "entertainment", "source_name": "The Guardian",
     "author": "Katie Simmons", "topics": ["taylor swift", "eras tour", "music"],
     "popularity_score": 0.94, "days_ago": 2.3},
]

# ── Build final article list with computed URLs and properly formatted timestamps
articles = []
for i, raw in enumerate(ARTICLES_RAW):
    delta = datetime.timedelta(days=raw["days_ago"])
    published_at = (NOW - delta).isoformat()
    source_slug = raw["source_name"].lower().replace(" ", "-")
    title_slug = raw["title"][:40].lower().replace(" ", "-").replace("'", "")
    url = f"https://{source_slug}.com/articles/{i+1}-{title_slug}"

    articles.append({
        "title": raw["title"],
        "description": raw.get("description"),
        "content": raw["content"],
        "url": url,
        "image_url": None if i % 9 == 0 else f"https://picsum.photos/seed/{i+1}/800/450",
        "source_name": raw["source_name"],
        "author": raw.get("author"),
        "category_slug": raw["category_slug"],
        "topics": raw.get("topics", []),
        "popularity_score": raw["popularity_score"],
        "published_at": published_at,
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print(f"Generated {len(articles)} articles -> {OUT_PATH}")
