#!/usr/bin/env python3
"""
Annotate unannotated rows in validation_sheets_v9 CSVs.
Only fills in rows where is_correct is empty.
Uses utf-8-sig encoding for Turkish text compatibility.
"""
import csv
import os

BASE_DIR = r"C:\Users\ahk79\Downloads\msp_extractor_modular\validation_sheets_v9"

# ============================================================
# ANNOTATIONS DICTIONARY
# Key: (filename_without_ext, row_id) -> (is_correct, is_relevant, error_type, notes)
# Only unannotated rows are included.
# ============================================================

ANNOTATIONS = {
    # =============================================
    # validate_legal_reference.csv (33 unannotated)
    # =============================================
    ("validate_legal_reference", 2): ("y", "n", "", "Article 18 of Law 4373; about land ownership rights transfer and valuation procedures with Agriculture/Forestry and Environment ministries - general land law not marine"),
    ("validate_legal_reference", 3): ("y", "n", "", "Article 34 of Mekansal Planlar Yapim Yonetmeligi; about spatial plan revision and announcement procedures - general zoning not marine"),
    ("validate_legal_reference", 4): ("y", "y", "", "Article 31 of Cevre Kanunu 2872 (Environment Law); Right to Access Environmental Information including breeding areas and rare species - includes marine environmental information"),
    ("validate_legal_reference", 5): ("y", "y", "", "Law 7261 referenced in Cevre Kanunu context; about environmental governance including Yuksek Cevre Kurulu (High Environmental Council) - environmental governance relevant to marine"),
    ("validate_legal_reference", 6): ("y", "y", "", "Article 14 of Ozel Cevre Koruma Bolgeleri Mevzuati; about land transactions in Special Environmental Protection Zones which include coastal/marine areas"),
    ("validate_legal_reference", 7): ("y", "y", "", "Article 23 of CED (EIA) Regulation 2022; about cooperation in environmental impact assessment education and programs - relevant to marine environmental governance"),
    ("validate_legal_reference", 8): ("y", "n", "", "Article 55 of Law 6200 (DSI); about DSI (State Hydraulic Works) administrative procedures with other agencies - inland water infrastructure not marine"),
    ("validate_legal_reference", 9): ("y", "y", "", "Article 1 of Su Urunleri Yetistiriciligi Yonetmeligi (Aquaculture Regulation); about the purpose of regulating aquaculture - directly marine/coastal"),
    ("validate_legal_reference", 12): ("y", "y", "", "Article 5 of CED (EIA) Regulation 2022; definitions including Cevresel Etki Degerlendirmesi Olumlu (positive EIA decision) for projects - environmental governance relevant to marine"),
    ("validate_legal_reference", 14): ("y", "y", "", "Article 5 of Cevre Kanunu 2872; about atomic energy regulation and Yuksek Cevre Kurulu - environmental governance relevant to marine"),
    ("validate_legal_reference", 18): ("y", "y", "", "Article 57 of Law 7221; about coastal discharge dilution criteria for wastewater - directly relevant to marine water quality"),
    ("validate_legal_reference", 21): ("y", "n", "", "Article 40 of Mekansal Planlar Yapim Yonetmeligi; about GIS digitization and plan processing numbers for spatial plans - general planning administration"),
    ("validate_legal_reference", 23): ("y", "y", "", "Article 6 of Su Urunleri Kanunu 1380 (Fisheries Law); about fisheries production area boundary determination - directly marine/coastal"),
    ("validate_legal_reference", 24): ("y", "y", "", "Article 2 of Su Urunleri Yetistiriciligi Yonetmeligi; about aquaculture sustainability and environmental protection - directly marine"),
    ("validate_legal_reference", 25): ("y", "y", "", "Article 10 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; about prohibition on physical interventions in protected areas and sites - includes coastal heritage sites"),
    ("validate_legal_reference", 26): ("y", "y", "", "Law 820 referenced in Su Urunleri Kanunu 1380 context; about fisheries enforcement and anti-smuggling regulations - directly marine"),
    ("validate_legal_reference", 28): ("y", "y", "", "Article 3 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; definitions of cultural properties covering immovable cultural and natural heritage - includes coastal/marine heritage"),
    ("validate_legal_reference", 29): ("y", "y", "", "Article 3 of CED (EIA) Regulation 2022 referencing Cevre Kanunu; about EIA system definitions and environmental management - includes marine project assessments"),
    ("validate_legal_reference", 30): ("y", "y", "", "Law 4737 (Endustri Bolgeleri Kanunu) referenced in Kiyi Kanunu Implementation Regulation; about industrial zones in coastal law context - directly marine/coastal"),
    ("validate_legal_reference", 31): ("y", "y", "", "Article 12 of CED Regulation 2022; about EIA report review and public participation procedures - includes marine project assessments"),
    ("validate_legal_reference", 32): ("y", "y", "", "Article 49 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; about underwater diving compensation and excavation costs - references su alti (underwater) operations"),
    ("validate_legal_reference", 33): ("y", "n", "", "Article 18 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; about urban transformation and transfer area procedures - general heritage/planning not specifically marine"),
    ("validate_legal_reference", 34): ("y", "n", "", "Article 10 of Mekansal Planlar Yapim Yonetmeligi; about mixed land use ratios, parking, green areas in spatial plans - general urban planning not marine"),
    ("validate_legal_reference", 38): ("y", "y", "", "Law 6745 Article 26 referenced in Kultur ve Tabiat Varliklari Koruma Kanunu; about heritage site management plans and coordination committees - may include coastal heritage"),
    ("validate_legal_reference", 39): ("y", "n", "", "Article 37 of Law 6200 (DSI); about DSI budget and financial provisions - inland water infrastructure administration"),
    ("validate_legal_reference", 40): ("y", "y", "", "Article 26 of Limanlar Yonetmeligi; about port inspection and enforcement for vessels violating regulations - directly marine"),
    ("validate_legal_reference", 41): ("y", "y", "", "Article 54 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; about appeals to Koruma Yuksek Kurulu (Conservation High Council) - heritage governance potentially includes coastal sites"),
    ("validate_legal_reference", 43): ("y", "n", "", "Article 17 of Law 6200 (DSI); series of repealed articles - administrative organizational law with no specific marine content"),
    ("validate_legal_reference", 45): ("y", "y", "", "Law 7201 (Tebligat Kanunu / Notification Law) referenced in Cevre Kanunu 2872; about environmental inspection notifications and enforcement - environmental governance relevant to marine"),
    ("validate_legal_reference", 46): ("y", "y", "", "Article 18 of Limanlar Yonetmeligi; about seaplane landing/takeoff areas in ports requiring harbor master permission - directly marine"),
    ("validate_legal_reference", 47): ("y", "n", "", "Article 39 of Law 6200 (DSI); about DSI financial regulations amended by presidential decree - inland water administration"),
    ("validate_legal_reference", 48): ("y", "y", "", "Article 20 of CED Regulation 2022 referencing Cevre Kanunu 2872; about EIA enforcement and suspension obligations - environmental governance relevant to marine"),
    ("validate_legal_reference", 50): ("y", "y", "", "Article 62 of Kultur ve Tabiat Varliklari Koruma Kanunu 2863; about appeals to Koruma Yuksek Kurulu with time limits - heritage governance including coastal/marine heritage"),

    # =============================================
    # validate_data_source.csv (23 unannotated)
    # =============================================
    ("validate_data_source", 1): ("y", "y", "", "ERA5 reanalysis dataset used for wind-wave modelling in offshore wind farm management context"),
    ("validate_data_source", 2): ("y", "y", "", "AIS data used for ship route planning near Miami waters - marine vessel tracking data"),
    ("validate_data_source", 4): ("y", "y", "", "GEBCO bathymetric data used alongside shipping fairways and marine conservation boundaries in Greater Bay Area"),
    ("validate_data_source", 5): ("y", "y", "", "Copernicus climate data (ECMWF ERA5) used for wind/wave environmental parameters in vessel trajectory prediction"),
    ("validate_data_source", 7): ("y", "y", "", "Global Fishing Watch used for fishing activity spatial analysis in Argentine Sea - marine fisheries tracking data"),
    ("validate_data_source", 8): ("y", "y", "", "AIS data used for traffic pattern extraction and grid-based spatial analysis of maritime traffic"),
    ("validate_data_source", 9): ("y", "y", "", "OpenStreetMap used for shipping fairways and marine conservation area boundaries in spatial vessel footprint analysis"),
    ("validate_data_source", 10): ("y", "y", "", "Copernicus ocean data used for current field information in dynamic ship path planning"),
    ("validate_data_source", 12): ("y", "y", "", "VMS (Vessel Monitoring System) used for commercial fishing intensity analysis in Algoa Bay conservation planning"),
    ("validate_data_source", 15): ("y", "y", "", "ICES data from underwater video survey (EVHOE) for MSP conflict resolution study in marine environment"),
    ("validate_data_source", 20): ("n", "n", "wrong_extraction", "Garbled extraction; 'the South China Sea with a sudden risk scenario and for the t' is a sentence fragment from body text, not a named data source"),
    ("validate_data_source", 25): ("n", "n", "wrong_extraction", "Garbled extraction; 'the study area' is a generic phrase, not a named data source or database"),
    ("validate_data_source", 26): ("y", "y", "", "AIS data used for analyzing transboundary shipping and cross-sectoral integration in HELCOM Baltic SCOPE MSP"),
    ("validate_data_source", 28): ("y", "y", "", "GBIF (Global Biodiversity Information Facility) data used for species occurrence and fishing effort analysis"),
    ("validate_data_source", 30): ("y", "y", "", "Sentinel satellite data used in spatial data infrastructure for marine spatial planning web services"),
    ("validate_data_source", 32): ("n", "n", "wrong_extraction", "Garbled extraction; 'Indonesia with a continuous risk scenario' is a sentence fragment from simulation description, not a named data source"),
    ("validate_data_source", 33): ("y", "y", "", "Copernicus regional wave hindcast product used for deriving spatial wave data from buoy networks - marine wave data"),
    ("validate_data_source", 34): ("y", "y", "", "MarineTraffic used as data source for maritime activity tracking in Northwestern Mediterranean MSP initiatives"),
    ("validate_data_source", 35): ("n", "n", "wrong_extraction", "Garbled extraction; 'approximately 15' is a number fragment from body text, not a named data source"),
    ("validate_data_source", 38): ("n", "n", "wrong_extraction", "Garbled extraction; 'the U' is a truncated fragment, not a named data source"),
    ("validate_data_source", 40): ("y", "y", "", "EMODnet used for data sharing across European countries for MSFD and MSPD implementation - marine spatial data"),
    ("validate_data_source", 41): ("y", "y", "", "GBIF used for dugong and seagrass species occurrence data in the Indo-West Pacific for conservation planning"),
    ("validate_data_source", 43): ("y", "y", "", "AIS data used for Yangtze River traffic flow analysis with ship trajectory data at folding points"),
    ("validate_data_source", 50): ("y", "y", "", "EMODnet data used for collaborative European marine data infrastructure and cumulative effects assessment"),

    # =============================================
    # validate_stakeholder.csv (22 unannotated)
    # =============================================
    ("validate_stakeholder", 1): ("y", "y", "", "Fishing community identified as marine stakeholder in gender and fishery economy discussion"),
    ("validate_stakeholder", 8): ("y", "y", "", "Local community identified as stakeholder in MPA decision-making with GIS fuzzy set modelling"),
    ("validate_stakeholder", 9): ("y", "y", "", "Recreational fishers identified as marine stakeholder using local ecological knowledge for demersal species trends"),
    ("validate_stakeholder", 10): ("y", "y", "", "Government agencies identified as stakeholder in South African heritage and marine spatial planning"),
    ("validate_stakeholder", 13): ("y", "y", "", "Local fishers identified as marine stakeholders concerned about spatial distribution impacts from offshore activities"),
    ("validate_stakeholder", 16): ("y", "y", "", "Indigenous community identified as stakeholder in Northern Shelf Bio-region MSP with aboriginal rights"),
    ("validate_stakeholder", 18): ("y", "y", "", "Local communities identified as stakeholders in Australian marine and offshore MSP context"),
    ("validate_stakeholder", 19): ("y", "y", "", "Fishing industry as stakeholder with permitting role in offshore wind energy planning - valid marine stakeholder"),
    ("validate_stakeholder", 22): ("y", "y", "", "Environmental organizations identified as stakeholders in offshore wind security and surveillance context"),
    ("validate_stakeholder", 27): ("n", "n", "wrong_extraction", "Garbled extraction; 'Scientific and Cultural' is a fragment of UNESCO's full name (United Nations Educational, Scientific and Cultural Organization) - incomplete extraction"),
    ("validate_stakeholder", 30): ("y", "y", "", "Indigenous community identified as stakeholder in salutogenic MSP approach for self-determination and governance"),
    ("validate_stakeholder", 31): ("y", "y", "", "Recreational fishers identified as marine stakeholders with catch distribution data for species management"),
    ("validate_stakeholder", 35): ("y", "y", "", "Government agencies as stakeholders in Rhode Island marine access infrastructure and boat management"),
    ("validate_stakeholder", 37): ("y", "y", "", "Tourism operators identified as stakeholders in blue economy and sustainable ocean zone engagement"),
    ("validate_stakeholder", 39): ("y", "y", "", "Local community identified as stakeholder in salutogenic MSP approach - underserved community engagement"),
    ("validate_stakeholder", 40): ("y", "y", "", "Maritime industry identified as stakeholder in China's ocean productive forces and transformative potential"),
    ("validate_stakeholder", 42): ("y", "y", "", "Maritime authorities identified as stakeholders in maritime accident spatial analysis and prediction"),
    ("validate_stakeholder", 44): ("y", "y", "", "Fishing industry identified as stakeholder in aquaculture MSP with fish as primary animal protein source"),
    ("validate_stakeholder", 45): ("y", "y", "", "Offshore wind industry as stakeholder in multi-use planning workshops with fishing and state agencies"),
    ("validate_stakeholder", 46): ("y", "y", "", "Fishing industry identified as stakeholder addressing heterogeneity of fishing practices across vessels"),
    ("validate_stakeholder", 47): ("y", "y", "", "Indigenous peoples identified as stakeholder challenging generic marine protected area model"),
    ("validate_stakeholder", 50): ("y", "y", "", "Recreational fisher identified as marine stakeholder with overfishing concerns and protected species impact"),

    # =============================================
    # validate_species.csv (19 unannotated)
    # =============================================
    ("validate_species", 3): ("y", "y", "", "Valid marine fish species; snapper referenced alongside Pacific seastar in marine ecosystem context"),
    ("validate_species", 4): ("y", "y", "", "Valid marine/anadromous fish species; Atlantic salmon in aquaculture concessions context with foreign capital operations"),
    ("validate_species", 6): ("y", "y", "", "Valid marine taxon; Elasmobranch (sharks and rays) listed with multiple species in NE Atlantic fisheries context"),
    ("validate_species", 7): ("y", "y", "", "Valid marine species; Squalus acanthias (spiny dogfish) with scientific name in Black Sea biodiversity context"),
    ("validate_species", 8): ("y", "y", "", "Valid marine fish species; Dicentrarchus labrax (European sea bass) with scientific name in catch frequency data"),
    ("validate_species", 9): ("y", "y", "", "Valid marine/anadromous fish species; salmon with southern hake and hoki in commercial fisheries landings"),
    ("validate_species", 18): ("y", "y", "", "Valid marine fish species; bluefish referenced in recreational fisheries and tourism multi-use context"),
    ("validate_species", 19): ("y", "y", "", "Valid marine mammal species; minke whale in marine mammal policy and conservation context"),
    ("validate_species", 22): ("y", "y", "", "Valid marine species; Carcharodon carcharias (great white shark) with scientific name in international marine cooperation"),
    ("validate_species", 23): ("y", "y", "", "Valid marine organism group; benthic fauna in MSP scheme evaluation with raster analysis classification"),
    ("validate_species", 31): ("y", "y", "", "Valid marine organism; seagrass in emerging intersection of MSP and recreational fisheries context"),
    ("validate_species", 33): ("y", "y", "", "Valid marine species; Raja clavata (thornback ray) with scientific name in Black Sea biodiversity conservation"),
    ("validate_species", 37): ("y", "y", "", "Valid marine species; sea cucumber in Indigenous marine plan with habitat management zones"),
    ("validate_species", 39): ("y", "y", "", "Valid marine species; Chelonia mydas (green sea turtle) with IUCN-listed cetaceans in Greater Bay Area MSP"),
    ("validate_species", 40): ("y", "y", "", "Valid marine fish species; Diplodus sargus (white seabream) with scientific name in catch frequency professional fisheries data"),
    ("validate_species", 44): ("y", "y", "", "Valid marine species; Chelonia mydas (green sea turtle) in Karimunjawa reef biodiversity and MPA zoning"),
    ("validate_species", 45): ("y", "y", "", "Valid marine fish species; Merluccius merluccius (European hake) with scientific name in catch species list"),
    ("validate_species", 46): ("y", "y", "", "Valid marine species; seahorse in marine biodiversity context alongside seagrass, coral, and extractive species"),
    ("validate_species", 47): ("y", "y", "", "Valid marine species; Chelonia mydas (green sea turtle) with scientific name in fast-developing coastal region MSP"),

    # =============================================
    # validate_institution.csv (18 unannotated)
    # =============================================
    ("validate_institution", 6): ("n", "n", "false_positive", "Garbled extraction; 'Marine Raster 2025 Commission' is not a real institution; appears to be a GIS data layer label merged with a year and table header"),
    ("validate_institution", 8): ("y", "y", "", "Joint Nature Conservation Committee (JNCC); genuine UK statutory body advising on nature conservation including marine"),
    ("validate_institution", 11): ("y", "y", "", "The European Commission; genuine EU executive institution central to marine policy and MSP directive"),
    ("validate_institution", 17): ("n", "y", "extraction_error", "Garbled extraction; 'The Convention on Biological Commission' is incorrect - likely a corruption of 'Convention on Biological Diversity' (CBD)"),
    ("validate_institution", 18): ("y", "y", "", "European Environmental Agency (EEA); genuine EU agency for environmental information; correctly identified"),
    ("validate_institution", 19): ("n", "n", "extraction_error", "Garbled extraction; 'Ensure a minimum reserve diameter Environmental Law Institute' merges a bullet point with an institution name"),
    ("validate_institution", 23): ("y", "n", "", "Environmental Protection Agency (US EPA); genuine government agency but not specifically a marine governance institution"),
    ("validate_institution", 26): ("y", "y", "", "European Environment Agency (EEA); genuine EU agency monitoring environmental status including marine MSFD"),
    ("validate_institution", 30): ("n", "n", "false_positive", "Garbled extraction; 'Artie McFerrin Department' is a university department name (Artie McFerrin Dept of Chemical Engineering at Texas A&M), not a standalone institution"),
    ("validate_institution", 31): ("n", "n", "extraction_error", "Garbled extraction; 'Burdwood Hoc Committee' is corrupted - likely 'Ad Hoc Committee' for Burdwood Bank MPA in Argentina"),
    ("validate_institution", 35): ("n", "n", "extraction_error", "Garbled extraction; 'Yuwono and Geospatial Information Agency' includes author name 'Yuwono' merged with Badan Informasi Geospasial (BIG) of Indonesia"),
    ("validate_institution", 36): ("n", "n", "extraction_error", "Garbled extraction; 'These results will help policy Italian Ministry' merges body text with an institution name"),
    ("validate_institution", 37): ("n", "y", "extraction_error", "Truncated extraction; 'Department of Conservation and Ministry' is incomplete - likely NZ DOC and Ministry for Primary Industries"),
    ("validate_institution", 40): ("y", "y", "", "European Environmental Agency (EEA); genuine EU environmental agency in North Sea MSP context"),
    ("validate_institution", 41): ("n", "n", "false_positive", "Garbled extraction; 'Shipping Raster 2025 Commission' is not a real institution; GIS data layer label merged with table header"),
    ("validate_institution", 43): ("y", "y", "", "Ocean and Marine Institute; plausible South African research institution in MSP context"),
    ("validate_institution", 47): ("y", "y", "", "European Environmental Agency (EEA); genuine EU agency for ecosystem monitoring and policy"),
    ("validate_institution", 48): ("n", "n", "extraction_error", "Garbled extraction; 'After tabulating Ireland Towards a Marine Spatial Plan The Department' merges body text with institution reference"),
    ("validate_institution", 50): ("y", "y", "", "Water Research Institute; plausible Italian research institution (IRSA-CNR) in aquaculture MSP context"),

    # =============================================
    # validate_environmental.csv (16 unannotated)
    # =============================================
    ("validate_environmental", 4): ("y", "y", "", "Valid cumulative environmental impact from shipping and overfishing causing habitat loss in Shanghai Port area"),
    ("validate_environmental", 11): ("y", "y", "", "Valid cumulative impact on focal species' habitat under climate and marine policy scenarios in Yangtze River Estuary"),
    ("validate_environmental", 14): ("y", "y", "", "Valid water quality assessment; trend of gradually improving water quality from inshore waters in ecological environment evaluation"),
    ("validate_environmental", 15): ("y", "y", "", "Valid eutrophication model reference with nitrogen, phosphorus, chlorophyll a, and oxygen debt as water quality parameters"),
    ("validate_environmental", 16): ("y", "y", "", "Valid environmental condition; Ocean Acidification Network including Mexico in Latin American regional marine context"),
    ("validate_environmental", 17): ("y", "y", "", "Valid marine pollution; discharge definition from ITOPF with oil spill response in Irish Sea context"),
    ("validate_environmental", 26): ("y", "y", "", "Valid water quality and biological quality assessment with restoration zone adjustments due to poor water quality in Maluan Bay"),
    ("validate_environmental", 28): ("y", "y", "", "Valid cumulative impact on focal species' habitat under different policy scenarios in Yangtze River Estuary"),
    ("validate_environmental", 29): ("y", "y", "", "Valid water quality monitoring using robotic sampling for surface water quality monitoring including chlorophyll concentration"),
    ("validate_environmental", 30): ("y", "y", "", "Valid cumulative impact areas with quantitative threshold (>=0) showing spatial differences in species habitat distribution"),
    ("validate_environmental", 32): ("y", "y", "", "Valid marine pollution definition; discharge of pollutants with ITOPF data quantifying approximately 164 incidents"),
    ("validate_environmental", 35): ("y", "y", "", "Valid environmental condition; Ocean Acidification Network (LAOCA) and North American network with regional funding context"),
    ("validate_environmental", 37): ("y", "y", "", "Valid habitat condition; biodiversity loss and habitat degradation driven by anthropogenic disturbance in dugong conservation"),
    ("validate_environmental", 44): ("y", "y", "", "Valid environmental measurement; water temperature 5.0 in stratification and coastal habitat context for MSFD indicators"),
    ("validate_environmental", 46): ("y", "y", "", "Valid marine pollution; marine pollution receiving relatively little attention in transboundary MSP"),
    ("validate_environmental", 48): ("y", "y", "", "Valid water quality in Wenzhou city seasonal monitoring (May, August) linked to fish density and fishery resource capacity"),
    ("validate_environmental", 50): ("y", "y", "", "Valid environmental regulation; wastewater quantity proportional contribution obligation in Turkish Cevre Kanunu 2872"),

    # =============================================
    # validate_gap.csv (13 unannotated)
    # =============================================
    ("validate_gap", 1): ("y", "y", "", "Genuine methodological gap: lack of monitoring of plan implementation effects in MSP with SEA"),
    ("validate_gap", 9): ("y", "y", "", "Genuine data gap: sensor measurements are limited and costly for ocean wave height field reconstruction"),
    ("validate_gap", 10): ("y", "y", "", "Genuine research gap in MSP methodology; gap identified through bibliometric assessment of MSP progress"),
    ("validate_gap", 15): ("y", "y", "", "Genuine data gap: lack of data on women's role in fisheries sector is fundamental problem for policy design"),
    ("validate_gap", 18): ("y", "y", "", "Genuine knowledge gap: limited to small-scale or short-duration studies in offshore wind farm modelling and management"),
    ("validate_gap", 25): ("y", "y", "", "Genuine governance gap: lack of transparency in stakeholder engagement concealing ineffective communication in MSP"),
    ("validate_gap", 27): ("n", "y", "false_positive", "Garbled text from bibliography; 'Future studies should integrate spatial [8] M' merges a recommendation with a reference citation"),
    ("validate_gap", 28): ("y", "y", "", "Genuine methodological gap: lack of emphasis on biodiversity promotion within wind farms in interview-based research"),
    ("validate_gap", 37): ("y", "y", "", "Genuine data gap: limited data sharing for USV development; shared standards needed for real-world deployment"),
    ("validate_gap", 38): ("y", "y", "", "Genuine data gap: lack of information on fishery management has profound implications including for women's participation"),
    ("validate_gap", 40): ("y", "y", "", "Genuine knowledge gap: limited understanding outside territorial waters regarding securitizing tools in offshore wind"),
    ("validate_gap", 49): ("y", "y", "", "Genuine knowledge gap: limited accessibility along Greece's coasts impacting recreational beach value assessment"),
    ("validate_gap", 50): ("y", "y", "", "Genuine knowledge gap: limited survey evidence for enrichment and sediment organic carbon effects of OWF expansion"),

    # =============================================
    # validate_policy.csv (10 unannotated)
    # =============================================
    ("validate_policy", 1): ("y", "y", "", "National MSP Framework is a real named policy framework; referenced in context of Australian marine conservation and ocean accounts"),
    ("validate_policy", 7): ("y", "y", "", "Convention on the International Regulations for Preventing Collisions at Sea (COLREGs); real named international maritime regulation"),
    ("validate_policy", 17): ("y", "y", "", "EU MSP Directive (2014/89/EU) correctly identified by standard abbreviated form"),
    ("validate_policy", 18): ("y", "y", "", "The MSP Directive (2014/89/EU) correctly identified; real named EU directive for maritime spatial planning"),
    ("validate_policy", 21): ("y", "y", "", "Report on the Blue Growth Strategy is a real named EU document (COM/2012/0494); correctly identified in bibliography"),
    ("validate_policy", 24): ("n", "y", "false_positive", "Sentence fragment; 'Through the implementation of the SEA Directive' is body text clause, not a policy title"),
    ("validate_policy", 27): ("y", "y", "", "EU MSP Directive (2014/89/EU) correctly identified for large coastal cities in Northwestern Mediterranean"),
    ("validate_policy", 32): ("y", "y", "", "The EBA Guideline (HELCOM-VASAB Ecosystem-Based Approach Guideline); real named MSP guidance document"),
    ("validate_policy", 39): ("y", "y", "", "Implementation guideline for the European SEA Directive; real named reference document for EBA key elements in MSP"),
    ("validate_policy", 46): ("y", "y", "", "European MSP Directive (2014/89/EU) correctly identified for sustainable marine management"),

    # =============================================
    # validate_method.csv (9 unannotated)
    # =============================================
    ("validate_method", 12): ("y", "y", "", "Participatory approach used as method for cross-border MSP cooperation in European Green Belt"),
    ("validate_method", 14): ("n", "n", "reference_only", "EBM appears in bibliographic reference citation (IOC Manual and Guides); not a method applied in the study"),
    ("validate_method", 19): ("y", "y", "", "EBM used for cetacean habitat modelling within MSP framework in Indonesia for conservation management"),
    ("validate_method", 30): ("y", "y", "", "InVEST used for cetacean conservation management to assess overlap between human activities and cetacean distribution"),
    ("validate_method", 32): ("n", "n", "reference_only", "EBM appears in bibliography citation (Halpern et al., Managing for cumulative impacts); not a method applied in the study"),
    ("validate_method", 33): ("y", "y", "", "InVEST HRA (Habitat Risk Assessment) model used for offshore renewable cumulative effects assessment"),
    ("validate_method", 47): ("y", "y", "", "Survey method used in Barbuda for stakeholder-guided marine zoning plan with spatial data collection from expert mapping"),
    ("validate_method", 49): ("y", "y", "", "SeaSketch participatory mapping tool proposed for enhancing accessibility data in Greek marine spatial planning"),
    ("validate_method", 50): ("y", "y", "", "Participatory mapping using ArcGIS Fuzzy Overlay tool for integrating social-ecological data in PSGLMP"),

    # =============================================
    # validate_distance.csv (1 unannotated)
    # =============================================
    ("validate_distance", 21): ("n", "y", "wrong_extraction", "Range '200-500 m' from wastewater discharge regulation; value field is empty because range was not captured as single numeric. Extraction error for the value."),
}


def annotate_file(filename):
    """Read a CSV, fill in unannotated rows, write back."""
    filepath = os.path.join(BASE_DIR, filename)
    base = os.path.splitext(filename)[0]

    # Read all rows
    with open(filepath, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    annotated_count = 0
    skipped_count = 0

    for row in rows:
        row_id = int(row["id"])
        key = (base, row_id)

        # Only annotate if is_correct is empty
        if row.get("is_correct", "").strip() != "":
            continue  # Already annotated

        if key in ANNOTATIONS:
            is_correct, is_relevant, error_type, notes = ANNOTATIONS[key]
            row["is_correct"] = is_correct
            row["is_relevant"] = is_relevant
            row["error_type"] = error_type
            row["notes"] = notes
            annotated_count += 1
        else:
            skipped_count += 1
            print(f"  WARNING: No annotation for {base} row {row_id}")

    # Write back
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {filename}: {annotated_count} rows annotated, {skipped_count} rows missing annotation")
    return annotated_count, skipped_count


def main():
    files = [
        "validate_legal_reference.csv",
        "validate_data_source.csv",
        "validate_stakeholder.csv",
        "validate_species.csv",
        "validate_institution.csv",
        "validate_environmental.csv",
        "validate_gap.csv",
        "validate_policy.csv",
        "validate_method.csv",
        "validate_distance.csv",
    ]

    total_annotated = 0
    total_missing = 0

    print("Annotating validation sheets v9...")
    print("=" * 60)

    for filename in files:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIPPED: {filename} not found")
            continue
        a, m = annotate_file(filename)
        total_annotated += a
        total_missing += m

    print("=" * 60)
    print(f"Total annotated: {total_annotated}")
    print(f"Total missing:   {total_missing}")
    print("Done.")


if __name__ == "__main__":
    main()
