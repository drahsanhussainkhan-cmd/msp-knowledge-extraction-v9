"""
Annotation script for MSP Extractor v9 final validation sheets.
Processes all unannotated rows across 10 CSV files.
Only modifies empty annotation cells. Preserves all existing data.
Uses utf-8-sig encoding.
"""

import csv
import os

VALIDATION_DIR = r"C:\Users\ahk79\Downloads\msp_extractor_modular\validation_sheets_v9_final"

# ============================================================
# ANNOTATIONS DICTIONARY
# Keys: (filename, row_id) -> (is_correct, is_relevant, error_type, notes)
# ============================================================

ANNOTATIONS = {
    # ===================== validate_legal_reference.csv =====================
    # Row 1: MADDE 11 - environmental quality standards, mixing zones for fishery areas
    ("validate_legal_reference.csv", 1): ("y", "y", "", "Article 11 of water quality regulation; environmental quality standards and mixing zones relevant to fishery areas - marine water quality governance"),
    # Row 3: 3416 sayili Kanun - referenced in Cevre Kanunu context, enforcement/entry into force
    ("validate_legal_reference.csv", 3): ("y", "n", "", "Law 3416 referenced in Cevre Kanunu context; about entry into force and enforcement provisions - general administrative law not marine"),
    # Row 4: MADDE 75, Borclar Kanunu - obligations law, statute of limitations
    ("validate_legal_reference.csv", 4): ("y", "n", "", "Article 75 of Borclar Kanunu (Code of Obligations) referenced in Ozel Cevre Koruma Bolgeleri Mevzuati; about time limitation calculations - general civil law not marine"),
    # Row 5: MADDE 31 - procurement/tender decisions in environmental protection zones
    ("validate_legal_reference.csv", 5): ("y", "n", "", "Article 31 of Ozel Cevre Koruma Bolgeleri procurement regulation; about tender committee decisions - administrative procurement not marine"),
    # Row 6: Madde 33 - Su Urunleri Kanunu, fisheries inspection and enforcement
    ("validate_legal_reference.csv", 6): ("y", "y", "", "Article 33 of Su Urunleri Kanunu (Fisheries Law 1380); about ministry inspection authority over fishery equipment and enforcement - directly marine"),
    # Row 8: Madde 16, Turk Ceza Kanunu - Kiyi Kanunu penalty provisions
    ("validate_legal_reference.csv", 8): ("y", "y", "", "Article 16 of Kiyi Kanunu referencing Turk Ceza Kanunu; penalties for illegal construction on coastal zone - marine coastal governance"),
    # Row 9: Madde 10, Imar Kanunu 3194 - zoning law restrictions
    ("validate_legal_reference.csv", 9): ("y", "n", "", "Article 10 of Imar Kanunu 3194; about zoning restrictions and constitutional court rulings - general urban planning not marine"),
    # Row 13: MADDE 21 - procurement/tender procedures
    ("validate_legal_reference.csv", 13): ("y", "n", "", "Article 21 of Ozel Cevre Koruma Bolgeleri procurement regulation; about tender annulment and contract termination - administrative procurement not marine"),
    # Row 14: MADDE 50 - performance bonds, contract termination
    ("validate_legal_reference.csv", 14): ("y", "n", "", "Article 50 of Ozel Cevre Koruma Bolgeleri procurement regulation; about performance bond forfeiture - administrative procurement not marine"),
    # Row 17: MADDE 33 - fire safety at ports, referencing gas-free certificate regulation
    ("validate_legal_reference.csv", 17): ("y", "y", "", "Article 33 of Limanlar Yonetmeligi referencing Gemi ve Su Araclarinda Gazdan Arindirma Yonetmeligi; about fire safety and tugboat services at ports - directly marine"),
    # Row 18: Madde 3, Turizmi Tesvik Kanunu referenced in Imar Kanunu
    ("validate_legal_reference.csv", 18): ("y", "n", "", "Article 3 of Imar Kanunu referencing Turizmi Tesvik Kanunu; about scope of zoning law and tourism areas - general planning law not marine"),
    # Row 19: MADDE 25 - tender guarantees
    ("validate_legal_reference.csv", 19): ("y", "n", "", "Article 25 of Ozel Cevre Koruma Bolgeleri procurement regulation; about tender guarantee submission - administrative procurement not marine"),
    # Row 20: 7221 sayili Kanunun 11 - amendments to Imar Kanunu
    ("validate_legal_reference.csv", 20): ("y", "n", "", "Law 7221 Article 11 amending Imar Kanunu; about penalty refund provisions - general urban planning law not marine"),
    # Row 21: Madde 4, referencing Turkiye Atom Enerjisi Kurumu Kanunu
    ("validate_legal_reference.csv", 21): ("y", "n", "", "Article 4 of Cevre Kanunu referencing Atom Enerjisi Kurumu Kanunu; about coordination for environmental problems including nuclear - not specifically marine"),
    # Row 22: 5625 sayili Kanun - DSI water infrastructure finance
    ("validate_legal_reference.csv", 22): ("y", "n", "", "Law 5625 referenced in water supply law context; about DSI water infrastructure financing and municipal debt - inland water infrastructure not marine"),
    # Row 23: Madde 25 - Deniz Trafik Duzeni Tuzugu, anchorage regulations
    ("validate_legal_reference.csv", 23): ("y", "y", "", "Article 25 of Deniz Trafik Duzeni Tuzugu; about anchorage regulations for vessels - directly marine traffic governance"),
    # Row 24: Madde 12 - Imar Kanunu, afforestation of lands
    ("validate_legal_reference.csv", 24): ("y", "n", "", "Article 12 of Imar Kanunu 3194; about afforestation and zoning plan restrictions - general urban planning not marine"),
    # Row 25: Madde 8 - Elektrik Tesisatcilari Hakkinda Yonetmelik in Imar Kanunu
    ("validate_legal_reference.csv", 25): ("y", "n", "", "Article 8 of Imar Kanunu referencing Elektrik Tesisatcilari Yonetmeligi; about electrical and sanitary installation competencies - building regulations not marine"),
    # Row 26: Madde 17 - Deniz Trafik Duzeni Tuzugu, pilot vessel guidance
    ("validate_legal_reference.csv", 26): ("y", "y", "", "Article 17 of Deniz Trafik Duzeni Tuzugu; about pilot vessel navigation and TBGTH reporting for vessels not under command - directly marine traffic governance"),
    # Row 27: MADDE 14 - Amme Alacaklarinin Tahsil Usulu
    ("validate_legal_reference.csv", 27): ("y", "n", "", "Article 14 of Ozel Cevre Koruma regulation referencing Law 6183 Amme Alacaklarinin Tahsil Usulu; about overdue payments collection - general administrative law not marine"),
    # Row 28: Madde 23 - Kiyi Kanununun Uygulanmasina Dair Yonetmelik
    ("validate_legal_reference.csv", 28): ("y", "y", "", "Article 23 of Kiyi Kanunu Implementation Regulation; about coastal boundary line determination and approval by Ministry - directly marine coastal governance"),
    # Row 30: Madde 67 - Kultur ve Tabiat Varliklari Koruma Kanunu
    ("validate_legal_reference.csv", 30): ("y", "n", "", "Article 67 of Cultural and Natural Heritage Protection Law 2863; about criminal penalties for heritage violations - general heritage law not marine"),
    # Row 32: Madde 23 - Kultur ve Tabiat Varliklari Koruma Kanunu
    ("validate_legal_reference.csv", 32): ("y", "n", "", "Article 23 of Cultural and Natural Heritage Protection Law 2863; about building inspection exemption for registered cultural properties - general heritage law not marine"),
    # Row 33: 6785 sayili Kanunun 14 - old Imar Kanunu technical staff competencies
    ("validate_legal_reference.csv", 33): ("y", "n", "", "Law 6785 Article 14 about surveyor competencies and technical responsibilities - old zoning law not marine"),
    # Row 34: MADDE 29 - Mekansal Planlar Yapim Yonetmeligi
    ("validate_legal_reference.csv", 34): ("y", "y", "", "Article 29 of Mekansal Planlar Yapim Yonetmeligi; about planning area boundaries considering coastal geography and natural environment - spatial planning relevant to marine"),
    # Row 35: 3127 sayili kanun - DSI infrastructure valuation
    ("validate_legal_reference.csv", 35): ("y", "n", "", "Law 3127 referenced in DSI law context; about asset valuation for transferred facilities - inland water infrastructure not marine"),
    # Row 36: Madde 12 - water quality classification, lake eutrophication
    ("validate_legal_reference.csv", 36): ("y", "y", "", "Article 12 of water quality regulation (7221); about inland surface water quality classification and lake eutrophication control - water quality governance relevant to marine"),
    # Row 37: Madde 2 - Su Urunleri Kanunu, referencing Kara Avciligi Kanunu
    ("validate_legal_reference.csv", 37): ("y", "y", "", "Article 2 of Su Urunleri Kanunu (Fisheries Law 1380); scope and definitions of the fisheries law - directly marine"),
    # Row 38: Madde 64 - Kultur ve Tabiat Varliklari Koruma Kanunu
    ("validate_legal_reference.csv", 38): ("y", "n", "", "Article 64 of Cultural and Natural Heritage Protection Law 2863; about heritage board regulations and responsibilities - general heritage law not marine"),
    # Row 39: 4737 sayili Kanun - Kiyi Kanunu referencing Turizmi Tesvik Kanunu
    ("validate_legal_reference.csv", 39): ("y", "y", "", "Law 4737 referenced in Kiyi Kanunu; about coastal zone planning under Imar Kanunu and Turizmi Tesvik Kanunu - coastal governance relevant to marine"),
    # Row 40: 7261 sayili Kanunun 12 nci maddesi - Cevre Kanunu amendments
    ("validate_legal_reference.csv", 40): ("y", "n", "", "Law 7261 Article 12 amending Cevre Kanunu; about Yuksek Cevre Kurulu establishment and duties - general environmental governance"),
    # Row 41: Madde 28 - Kultur ve Tabiat Varliklari Koruma Kanunu, dealer licenses
    ("validate_legal_reference.csv", 41): ("y", "n", "", "Article 28 of Cultural and Natural Heritage Protection Law 2863; about cultural property dealer licensing - general heritage law not marine"),
    # Row 42: MADDE 19 - Limanlar Yonetmeligi, dangerous cargo maritime transport
    ("validate_legal_reference.csv", 42): ("y", "y", "", "Article 19 of Limanlar Yonetmeligi referencing Tehlikeli Yuklerin Denizyoluyla Tasinmasi Yonetmeligi; about dangerous cargo maritime transport regulations - directly marine"),
    # Row 43: Madde 47 - DSI law, repealed articles
    ("validate_legal_reference.csv", 43): ("y", "n", "", "Article 47 of DSI law (6200); series of repealed articles by KHK 662 - general administrative law not marine"),
    # Row 44: 4857 sayili Kanun - labour law in DSI context
    ("validate_legal_reference.csv", 44): ("y", "n", "", "Law 4857 (Labour Law) referenced in DSI context; about land consolidation staff provisions - general labour law not marine"),
    # Row 45: MADDE 40 - procurement tender records
    ("validate_legal_reference.csv", 45): ("y", "n", "", "Article 40 of Ozel Cevre Koruma procurement regulation; about tender decision records and rationale - administrative procurement not marine"),
    # Row 46: Madde 28 - Cevre Kanunu, other laws penalties
    ("validate_legal_reference.csv", 46): ("y", "y", "", "Article 28 of Cevre Kanunu; about administrative penalties for environmental violations and other law provisions - environmental governance relevant to marine"),
    # Row 47: Madde 1 - Kiyi Kanunu, purpose and scope
    ("validate_legal_reference.csv", 47): ("y", "y", "", "Article 1 of Kiyi Kanunu (Coastal Law 3621); purpose and scope article of the coastal zone law - directly marine coastal governance"),
    # Row 49: 2560 sayili Kanun - Cevre Kanunu referencing water authority
    ("validate_legal_reference.csv", 49): ("y", "n", "", "Law 2560 referenced in water quality regulation; about metropolitan water and sewage authority jurisdiction - inland water management not specifically marine"),
    # Row 50: Madde 35 - Kultur ve Tabiat Varliklari Koruma Kanunu
    ("validate_legal_reference.csv", 50): ("y", "n", "", "Article 35 of Cultural and Natural Heritage Protection Law 2863; about photography and reproduction permits for cultural properties - general heritage law not marine"),

    # ===================== validate_data_source.csv =====================
    # Row 2: VMS - mentioned in geospatial technologies review for MSP
    ("validate_data_source.csv", 2): ("y", "y", "", "VMS (Vessel Monitoring System) referenced as a geospatial technology for marine spatial planning activities"),
    # Row 4: AIS data - ship avoidance patterns during typhoons
    ("validate_data_source.csv", 4): ("y", "y", "", "AIS data used for spatial-temporal analysis of ship avoidance patterns during typhoons in South Korea"),
    # Row 5: AIS - cetacean habitat modelling and vessel tracking
    ("validate_data_source.csv", 5): ("y", "y", "", "AIS used for tracking large vessels in cetacean habitat modelling for MSP conservation management"),
    # Row 6: Copernicus - wave and wind data for route planning
    ("validate_data_source.csv", 6): ("y", "y", "", "Copernicus data used for wave direction, wind speed, and temperature in ship route planning"),
    # Row 7: AIS - Argentine Sea uses and activities analysis
    ("validate_data_source.csv", 7): ("y", "y", "", "AIS referenced alongside MarineTraffic for maritime traffic analysis in Argentine Sea MSP baseline study"),
    # Row 9: vessel movements dataset - maritime vessel spatial footprint
    ("validate_data_source.csv", 9): ("y", "y", "", "Named dataset of vessel movements used for assessing maritime vessel spatial footprint and habitat disturbance"),
    # Row 12: AIS - systematic conservation planning in Algoa Bay
    ("validate_data_source.csv", 12): ("y", "y", "", "AIS referenced alongside ship-to-ship bunkering and shipping lanes for conservation planning in Algoa Bay"),
    # Row 14: database of marine incidents - collision validation
    ("validate_data_source.csv", 14): ("y", "y", "", "Database of marine casualties and incidents from US navigable waters used to validate collision risk domain analysis"),
    # Row 16: AIS data - conflict resolution in coastal Taiwan
    ("validate_data_source.csv", 16): ("y", "y", "", "AIS data used for maritime traffic analysis in Anping Port area for marine conflict resolution"),
    # Row 19: AIS data - dynamic current path planning
    ("validate_data_source.csv", 19): ("y", "y", "", "AIS data used in ship path planning algorithms with emission optimization"),
    # Row 20: MarineTraffic - Argentine Sea vessel traffic 2005-2020
    ("validate_data_source.csv", 20): ("y", "y", "", "MarineTraffic data for vessel traffic analysis in Argentine Sea with temporal coverage 2005-2020"),
    # Row 21: GEBCO - bathymetry data for Reunion Island cetacean study
    ("validate_data_source.csv", 21): ("y", "y", "", "GEBCO bathymetric data used for marine traffic and cetacean pressure assessment around Reunion Island"),
    # Row 22: COPERNICUS - physical characteristics for MSP
    ("validate_data_source.csv", 22): ("y", "y", "", "COPERNICUS data for physical oceanographic characteristics in marine spatial planning and cultural-natural asset integration"),
    # Row 25: dataset of vary-kernel - interpolation method artifact
    ("validate_data_source.csv", 25): ("n", "n", "false_positive", "Garbled extraction; 'dataset of vary- kernel' is fragmented text about interpolation matrices and kernel methods, not a named dataset"),
    # Row 26: EMODnet - Black Sea geophysical/geotechnical data
    ("validate_data_source.csv", 26): ("y", "y", "", "EMODnet used for geophysical and geotechnical parameter data (bathymetry, sediment) in Eastern Black Sea study"),
    # Row 27: AIS - whale conservation shipping data 2018-2020
    ("validate_data_source.csv", 27): ("y", "y", "", "AIS data with temporal coverage 2018-2020 used for shipping and whale conservation MSP study"),
    # Row 28: ICES - offshore wind and fisheries data 2022-2024
    ("validate_data_source.csv", 28): ("y", "y", "", "ICES data used for offshore wind energy and fisheries policy analysis with 2022-2024 coverage"),
    # Row 31: AIS - conflict resolution at sea
    ("validate_data_source.csv", 31): ("y", "y", "", "AIS referenced in abstract for ocean space conflict resolution and marine regulatory analysis"),
    # Row 35: VMS - cetacean habitat modelling
    ("validate_data_source.csv", 35): ("y", "y", "", "VMS referenced alongside AIS for vessel tracking in cetacean habitat modelling and conservation management"),
    # Row 38: AIS - ship path planning survey
    ("validate_data_source.csv", 38): ("y", "y", "", "AIS referenced as key data source in comprehensive ship path planning methods survey"),
    # Row 41: OBIS - dugong conservation spatial planning
    ("validate_data_source.csv", 41): ("y", "y", "", "OBIS (Ocean Biodiversity Information System) used alongside GBIF for dugong species occurrence data in conservation planning"),
    # Row 44: sea wind dataset - unmanned vehicle energy planning
    ("validate_data_source.csv", 44): ("n", "y", "false_positive", "Generic term; 'dataset of sea wind' is not a named database or monitoring system but a generic description of sea wind observations for Hainan Province"),
    # Row 49: VMS - geospatial technology barriers
    ("validate_data_source.csv", 49): ("y", "y", "", "VMS referenced as a fishery data source with practitioners reporting shortage in geospatial technology implementation"),

    # ===================== validate_stakeholder.csv =====================
    # Row 1: fishing communities - marine fisheries women
    ("validate_stakeholder.csv", 1): ("y", "y", "", "Fishing communities identified as stakeholder in marine fisheries women research context"),
    # Row 10: Maritime Authorities - MSP management
    ("validate_stakeholder.csv", 10): ("y", "y", "", "Maritime Authorities identified as effective MSP management authority through SSM methodology"),
    # Row 16: indigenous peoples - Marine Plan Partnership
    ("validate_stakeholder.csv", 16): ("y", "y", "", "Indigenous peoples as key stakeholder in Marine Plan Partnership for community-based marine planning"),
    # Row 18: Prevention and Protection Agency - Italian aquaculture MSP
    ("validate_stakeholder.csv", 18): ("n", "y", "extraction_error", "Truncated name; 'Prevention and Protection' is incomplete institutional name from author affiliations, not a stakeholder role description"),
    # Row 22: offshore wind developers - Swedish MSP
    ("validate_stakeholder.csv", 22): ("y", "y", "", "Offshore wind developers identified as stakeholder in Swedish geological survey and MSP context"),
    # Row 26: government agencies - marine data for MSP
    ("validate_stakeholder.csv", 26): ("y", "y", "", "Government agencies as stakeholder providing official documents on shipping routes and submerged reef data for MSP"),
    # Row 27: shipping companies - adaptive path planning
    ("validate_stakeholder.csv", 27): ("y", "y", "", "Shipping companies identified as stakeholder in adaptive path planning for bulk carriers in maritime operations"),
    # Row 29: shipping companies - intelligent route planning
    ("validate_stakeholder.csv", 29): ("y", "y", "", "Shipping companies identified as stakeholder in route planning for carbon emission reduction and fuel cost optimization"),
    # Row 33: shipping industry - marine benthic habitat impacts
    ("validate_stakeholder.csv", 33): ("y", "y", "", "Shipping industry as stakeholder affecting marine benthic habitats around anchorage areas and reef distribution"),
    # Row 34: Analysis and Research Association - EBSA governance
    ("validate_stakeholder.csv", 34): ("n", "y", "extraction_error", "Truncated name; 'Analysis and Research Association' is incomplete - likely cut from longer institutional name in bibliography reference section"),
    # Row 38: indigenous people - geospatial technology review
    ("validate_stakeholder.csv", 38): ("y", "y", "", "Indigenous people identified as stakeholder in geospatial technologies review for MSP including aquaculture monitoring"),
    # Row 40: recreational fisher - MPA gear restrictions
    ("validate_stakeholder.csv", 40): ("y", "y", "", "Recreational fisher identified as stakeholder in MPA gear restriction analysis across Spanish Mediterranean regions"),
    # Row 41: indigenous people - GIS fuzzy set modelling
    ("validate_stakeholder.csv", 41): ("y", "y", "", "Indigenous people identified as stakeholder in cultural practices and social-ecological integration for marine planning"),
    # Row 42: maritime authorities - GIS spatial pattern analysis
    ("validate_stakeholder.csv", 42): ("y", "y", "", "Maritime authorities as stakeholder in global maritime accident spatial pattern analysis for traffic safety"),
    # Row 44: recreational fishers - systematic conservation planning
    ("validate_stakeholder.csv", 44): ("y", "y", "", "Recreational fishers identified as stakeholder in Algoa Bay systematic conservation planning"),
    # Row 46: fishing communities - ocean grabbing and sustainability
    ("validate_stakeholder.csv", 46): ("y", "y", "", "Fishing communities as stakeholder in ocean grabbing and sustainable development goals for marine protected areas"),
    # Row 47: Government agencies - Galapagos DPNG research
    ("validate_stakeholder.csv", 47): ("y", "y", "", "Government agencies as stakeholder promoting fisheries research with CGREG authority in Galapagos marine governance"),
    # Row 49: Port authorities - Taiwan marine conflict resolution
    ("validate_stakeholder.csv", 49): ("y", "y", "", "Port authorities as stakeholder in typhoon season management and marine user conflict resolution in Taiwan"),

    # ===================== validate_species.csv =====================
    # Row 4: Humpback Whale - Chilean Patagonia ecosystem services
    ("validate_species.csv", 4): ("y", "y", "", "Valid marine mammal species; Humpback Whale in Chilean Patagonia ecosystem services and species distribution analysis"),
    # Row 6: Cetorhinus maximus - Mediterranean elasmobranch conservation
    ("validate_species.csv", 6): ("y", "y", "", "Valid marine species (basking shark); Cetorhinus maximus listed among Mediterranean elasmobranchs for conservation assessment"),
    # Row 7: Leatherback turtle - biodiversity features in Marxan
    ("validate_species.csv", 7): ("y", "y", "", "Valid marine reptile species; Leatherback turtle as biodiversity feature in Marxan conservation planning analysis"),
    # Row 9: sea urchin - Chilean fishery landings
    ("validate_species.csv", 9): ("y", "y", "", "Valid marine invertebrate species; sea urchin alongside southern king crab and scallop in Chilean fishery landings"),
    # Row 12: Hamsi - Turkish maritime traffic regulation
    ("validate_species.csv", 12): ("n", "n", "false_positive", "Not a species extraction; 'Hamsi' (anchovy) appears as a substring match in Turkish maritime traffic regulation text about container and ro-ro vessels - not describing a species in context"),
    # Row 17: Nephrops norvegicus - offshore renewable energy impact
    ("validate_species.csv", 17): ("y", "y", "", "Valid marine crustacean species (Norway lobster); Nephrops norvegicus in otter trawl fisheries and offshore wind impact context"),
    # Row 22: Petrel - biodiversity features in Marxan analysis
    ("validate_species.csv", 22): ("y", "y", "", "Valid marine seabird species; Petrel among biodiversity features in Marxan conservation planning alongside Biscuit Skate and Leatherback turtle"),
    # Row 31: Mytilus galloprovincialis - aquaculture MSP
    ("validate_species.csv", 31): ("y", "y", "", "Valid marine bivalve species (Mediterranean mussel); Mytilus galloprovincialis in shellfish aquaculture and TRIX water quality assessment"),
    # Row 33: hake - biodiversity in Marxan analysis
    ("validate_species.csv", 33): ("y", "y", "", "Valid marine fish species; hake alongside kelp harvesting, gillnetting, and rock lobster in South African marine biodiversity analysis"),
    # Row 34: Mediterranean mussel - aquaculture production
    ("validate_species.csv", 34): ("y", "y", "", "Valid marine species; Mediterranean mussel alongside European seabass in aquaculture production context"),
    # Row 39: mangrove - vessel footprint and porpoise habitat
    ("validate_species.csv", 39): ("y", "y", "", "Valid marine/coastal organism; mangrove referenced alongside finless porpoise and green turtle in vessel footprint marine habitat context"),
    # Row 44: plaice - MSFD fauna composition thresholds
    ("validate_species.csv", 44): ("y", "y", "", "Valid marine fish species; plaice (European flatfish) alongside grey gurnard in MSFD seascape fauna composition analysis"),
    # Row 47: dugong - conservation spatial planning
    ("validate_species.csv", 47): ("y", "y", "", "Valid marine mammal species; dugong as focal species for conservation spatial planning and habitat suitability assessment"),
    # Row 49: Posidonia - aquaculture MSP ecological indicators
    ("validate_species.csv", 49): ("y", "y", "", "Valid marine seagrass genus; Posidonia referenced in Gulf of Manfredonia aquaculture MSP natural characterization"),

    # ===================== validate_institution.csv =====================
    # Row 3: HELCOM Helsinki Commission - Baltic Sea marine governance
    ("validate_institution.csv", 3): ("y", "y", "", "HELCOM Helsinki Commission; genuine Baltic Sea marine governance body; correctly identified"),
    # Row 5: Rural Shipping Deputy Ministry - Greek marine governance
    ("validate_institution.csv", 5): ("y", "y", "", "Rural Shipping Deputy Ministry; genuine Greek government entity involved in maritime spatial planning governance"),
    # Row 6: Norwegian Environment Agency - marine governance
    ("validate_institution.csv", 6): ("y", "y", "", "Norwegian Environment Agency (Miljodirektoratet); genuine Norwegian government agency involved in MSP"),
    # Row 7: Maritime and Port Authority - Singapore
    ("validate_institution.csv", 7): ("y", "y", "", "Maritime and Port Authority of Singapore (MPA); genuine government agency for maritime and port governance"),
    # Row 8: ABNJ and AUNJ garbled extraction
    ("validate_institution.csv", 8): ("n", "n", "extraction_error", "Garbled extraction; 'ABNJ and AUNJ differ in terms of their prevailing management eries Commission' merges body text about areas beyond national jurisdiction with a commission name"),
    # Row 10: Environmental Hydraulics Institute - Spanish wind resource assessment
    ("validate_institution.csv", 10): ("y", "y", "", "Environmental Hydraulics Institute (IHCantabria); genuine Spanish research institute for marine renewable energy and wind resource assessment"),
    # Row 14: National Expert Committee - MSFD/MSPD implementation
    ("validate_institution.csv", 14): ("y", "y", "", "National Expert Committee for MSFD and MSPD implementation; genuine governance body identified in marine policy context"),
    # Row 19: Diversification and Carried out by the Institute - garbled
    ("validate_institution.csv", 19): ("n", "n", "extraction_error", "Garbled extraction; 'Diversification and Carried out by the Institute' merges IDAE (Institute for Diversification and Energy Saving) with body text"),
    # Row 20: MSP Technical Committee - marine spatial planning governance
    ("validate_institution.csv", 20): ("y", "y", "", "MSP Technical Committee; genuine governance body for coordinating MSP activities across competent authorities"),
    # Row 26: European Economic and Social Committee
    ("validate_institution.csv", 26): ("y", "y", "", "European Economic and Social Committee (EESC); genuine EU consultative body involved in marine policy communications"),
    # Row 27: United Nations Statistical Commission
    ("validate_institution.csv", 27): ("y", "n", "", "United Nations Statistical Commission; genuine UN body but primarily statistical governance, not specifically marine"),
    # Row 30: Fisheries and Marine Institute - Memorial University
    ("validate_institution.csv", 30): ("y", "y", "", "Fisheries and Marine Institute of Memorial University; genuine Canadian marine research institution"),
    # Row 31: Burdwood Hoc Committee - garbled extraction
    ("validate_institution.csv", 31): ("n", "n", "extraction_error", "Garbled extraction confirmed; 'Burdwood Hoc Committee' corrupts Ad Hoc Committee for Burdwood Bank MPA in Argentina"),
    # Row 32: International Energy Agency
    ("validate_institution.csv", 32): ("y", "n", "", "International Energy Agency (IEA); genuine intergovernmental organization but not specifically a marine governance institution"),
    # Row 35: Ministry of Fisheries and Department - truncated
    ("validate_institution.csv", 35): ("n", "y", "extraction_error", "Truncated extraction; 'Ministry of Fisheries and Department' cuts off mid-name - likely Ministry of Fisheries and Department of Conservation of New Zealand"),
    # Row 36: Technology Research Institute - generic
    ("validate_institution.csv", 36): ("n", "n", "generic_term", "Generic term; 'Technology Research Institute' is too vague to identify a specific institution - context mentions Chinese maritime technology"),
    # Row 37: Indonesian Geospatial Information Agency
    ("validate_institution.csv", 37): ("y", "y", "", "BIG (Badan Informasi Geospasial); genuine Indonesian government agency providing geospatial data for cetacean habitat modelling"),
    # Row 40: Incidents published by EMSA - garbled
    ("validate_institution.csv", 40): ("n", "y", "extraction_error", "Garbled extraction; 'Incidents published by European Maritime Safety Agency' includes body text as part of the institution name"),
    # Row 41: Sweden Swedish Agency - garbled
    ("validate_institution.csv", 41): ("n", "y", "extraction_error", "Garbled extraction; 'Sweden Swedish Agency' is truncated and duplicated - likely Swedish Agency for Marine and Water Management (SwAM)"),
    # Row 43: The European Commission - EU marine governance
    ("validate_institution.csv", 43): ("y", "y", "", "The European Commission; genuine EU executive institution involved in fisheries quota and PO management"),
    # Row 44: The Competent Authority - generic
    ("validate_institution.csv", 44): ("n", "y", "generic_term", "Generic term; 'The Competent Authority' is a legal concept referring to any designated authority, not a specific named institution"),
    # Row 48: South African Heritage Resources Agency
    ("validate_institution.csv", 48): ("y", "n", "", "SAHRA (South African Heritage Resources Agency); genuine government agency but heritage-focused, not specifically marine governance"),
    # Row 50: South African Heritage Resources Agency
    ("validate_institution.csv", 50): ("y", "n", "", "SAHRA; genuine government agency referenced in Sardinia Bay MPA context but heritage-focused, not specifically marine governance"),

    # ===================== validate_environmental.csv =====================
    # Row 9: cumulative impacts on focal species habitats - YRE scenarios
    ("validate_environmental.csv", 9): ("y", "y", "", "Valid environmental condition; cumulative impacts on focal species habitats under different scenarios in Yangtze River Estuary"),
    # Row 11: cumulative impacts on global marine ecosystems
    ("validate_environmental.csv", 11): ("y", "y", "", "Valid environmental condition; cumulative impacts on global marine ecosystems including river estuary impacts on aquatic species"),
    # Row 13: atiksu altyapi tesislerine verilmesi yasaktir
    ("validate_environmental.csv", 13): ("y", "y", "", "Valid environmental regulation; wastewater collection, treatment, and disposal fee requirements for polluters"),
    # Row 14: water quality poor in sea area
    ("validate_environmental.csv", 14): ("y", "y", "", "Valid marine water quality condition; poor water quality in dense functional zones of sea area with environmental assessment"),
    # Row 23: salinity 4000 - Estonian maritime data
    ("validate_environmental.csv", 23): ("y", "y", "", "Valid environmental measurement; salinity 4000 (likely mg/L or PSU units) from Estonian Maritime Administration spatial data for marine planning"),
    # Row 26: noise pollution in marine ecosystems
    ("validate_environmental.csv", 26): ("y", "y", "", "Valid environmental condition; noise pollution in dynamically evolving marine ecosystems from digital twin decision support system"),
    # Row 28: cumulative impact areas for species habitats under scenarios
    ("validate_environmental.csv", 28): ("y", "y", "", "Valid environmental impact; cumulative impact areas for species habitats under fishing and infrastructure scenarios in YRE"),
    # Row 29: water quality monitoring with robotic sampling
    ("validate_environmental.csv", 29): ("y", "y", "", "Valid water quality monitoring; referenced in robotic sampling of marine microplastics with AUV platforms"),
    # Row 39: water quality monitoring and algorithm
    ("validate_environmental.csv", 39): ("y", "y", "", "Valid water quality monitoring; referenced in ship path planning method for seawolf navigation and marine quality assessment"),
    # Row 41: cumulative impact scores
    ("validate_environmental.csv", 41): ("y", "y", "", "Valid environmental condition; cumulative impact scores with vulnerability weight randomization for scenario policy assessment"),

    # ===================== validate_gap.csv =====================
    # Row 4: lack of communication and stakeholder participation
    ("validate_gap.csv", 4): ("y", "y", "", "Genuine governance gap; lack of communication and stakeholder participation in MSP and marine park management"),
    # Row 12: absent from MSP documents, implicitly considered
    ("validate_gap.csv", 12): ("y", "y", "", "Genuine policy gap; blue economy absent from MSP documents or only implicitly considered within broader maritime management"),
    # Row 17: limited to these areas - offshore wind energy zones
    ("validate_gap.csv", 17): ("y", "y", "", "Genuine knowledge gap; offshore wind energy zone evaluation limited to specific areas rather than comprehensive spatial assessment"),
    # Row 21: gap in grey and primary literature
    ("validate_gap.csv", 21): ("y", "y", "", "Genuine data gap; knowledge gap in both grey and primary literature on offshore wind disturbance impacts on marine ecosystems"),
    # Row 23: limited to land spaces and relevant sectors
    ("validate_gap.csv", 23): ("y", "y", "", "Genuine policy gap; MSP limited to land spaces with lack of legal articulation between MSP and blue economy in LATAM countries"),
    # Row 30: limited social and economic evidence specific to marine area
    ("validate_gap.csv", 30): ("y", "y", "", "Genuine data gap; limited social and economic evidence specific to the marine area for integrated MSP"),
    # Row 34: lack of understanding and appreciation
    ("validate_gap.csv", 34): ("y", "y", "", "Genuine governance gap; lack of understanding and appreciation of cross-border MSP leadership needs"),
    # Row 37: lack of knowledge and interest in marine issues
    ("validate_gap.csv", 37): ("y", "y", "", "Genuine knowledge gap; lack of knowledge and interest in marine issues among coastal communities and municipalities in MSP"),
    # Row 38: limited by operational range of sonar systems
    ("validate_gap.csv", 38): ("y", "y", "", "Genuine methodological gap; path planning limited by operational range of sonar systems in unexplored ocean settings"),
    # Row 40: limited transparency and decisive veto power
    ("validate_gap.csv", 40): ("y", "y", "", "Genuine governance gap; limited transparency in offshore wind MSP with local actors facing decisive veto power from security interests"),
    # Row 46: limited legitimacy to coordinate trade-offs
    ("validate_gap.csv", 46): ("y", "y", "", "Genuine governance gap; limited legitimacy to coordinate trade-offs in marine planning with public not consulted"),
    # Row 49: lack of some quantified pressure-state relationships
    ("validate_gap.csv", 49): ("y", "y", "", "Genuine knowledge gap; lack of quantified pressure-state relationships for Baltic Sea environmental objectives within analysis"),

    # ===================== validate_policy.csv =====================
    # Row 1: EU Habitat Directive
    ("validate_policy.csv", 1): ("y", "y", "", "EU Habitats Directive (92/43/EEC); real named EU directive for habitat and species conservation including marine habitats"),
    # Row 6: European level via amendments to the of EU Directive - garbled
    ("validate_policy.csv", 6): ("n", "y", "extraction_error", "Sentence fragment; 'European level via amendments to the of EU Directive' is garbled body text about EU-level coastal zone management, not a policy title"),
    # Row 7: Revised GHG Strategy
    ("validate_policy.csv", 7): ("y", "y", "", "IMO Revised GHG Strategy (2023); real named international maritime strategy for greenhouse gas emission reduction from shipping"),
    # Row 12: European Union Directive - too generic
    ("validate_policy.csv", 12): ("n", "y", "extraction_error", "Too generic; 'European Union Directive' does not identify which specific EU directive is referenced - context mentions MPAs and conservation objectives"),
    # Row 14: EU Water Policy
    ("validate_policy.csv", 14): ("y", "y", "", "EU Water Policy referencing Water Framework Directive and MSFD; legitimate named EU policy framework for water quality in marine territorial waters"),
    # Row 23: The EU Strategy - too generic
    ("validate_policy.csv", 23): ("n", "y", "extraction_error", "Too generic; 'The EU Strategy' does not identify which specific EU strategy - context discusses Adriatic Sea boundary issues and MSFD/WFD"),
    # Row 31: Montreal Global Biodiversity Framework
    ("validate_policy.csv", 31): ("y", "y", "", "Kunming-Montreal Global Biodiversity Framework; real named international framework for biodiversity conservation including marine targets"),
    # Row 40: The National Strategy - too generic
    ("validate_policy.csv", 40): ("n", "y", "extraction_error", "Too generic; 'The National Strategy' does not identify which country or strategy - context discusses Thailand marine environment management"),
    # Row 45: The Common Agricultural Policy
    ("validate_policy.csv", 45): ("y", "n", "", "EU Common Agricultural Policy (CAP); real named EU policy but primarily agricultural, not marine; context discusses water quality improvement"),
    # Row 49: EU MSP Directive
    ("validate_policy.csv", 49): ("y", "y", "", "EU MSP Directive (2014/89/EU); real named EU directive for maritime spatial planning; correctly identified"),
    # Row 50: EU Biodiversity Strategy
    ("validate_policy.csv", 50): ("y", "y", "", "EU Biodiversity Strategy (2030); real named EU strategy for nature-based solutions and marine biodiversity conservation"),

    # ===================== validate_method.csv =====================
    # Row 7: Ecosystem-based management - actively discussed
    ("validate_method.csv", 7): ("y", "y", "", "EBM actively discussed as management approach requiring MSFD Member States to implement; used as core method concept"),
    # Row 9: InVEST - ecosystem service assessments
    ("validate_method.csv", 9): ("y", "y", "", "InVEST referenced as conservation planning tool used with scenario narratives for ecosystem service assessments in MSP"),
    # Row 12: EBM - MSP scheme evaluation
    ("validate_method.csv", 12): ("y", "y", "", "EBM referenced as management approach for MSP scheme evaluation and effectiveness analysis"),
    # Row 26: ecosystem-based management - MPA and MSP relationship
    ("validate_method.csv", 26): ("y", "y", "", "EBM actively discussed as core management paradigm for eco-system-based sea use management in MPA-MSP relationship"),
    # Row 43: overlap analysis - GIS MSP application
    ("validate_method.csv", 43): ("y", "y", "", "GIS overlap analysis used for marine spatial planning with geographic information and transport/fisheries/aquaculture data"),
    # Row 50: participatory mapping - GIS fuzzy set modelling
    ("validate_method.csv", 50): ("y", "y", "", "Participatory mapping used with semi-structured interviews for social-ecological data collection in marine GIS fuzzy set modelling"),

    # ===================== validate_distance.csv =====================
    # Row 7: 6 deniz mili - Canakkale Strait vessel passage
    ("validate_distance.csv", 7): ("y", "y", "", "6 nautical mile distance defining vessel separation in Canakkale Strait passage rules from Deniz Trafik Duzeni Tuzugu. Correct maritime navigation spatial rule."),
    # Row 12: 40 metre minimum aquaculture distance
    ("validate_distance.csv", 12): ("y", "y", "", "Minimum 40m distance specification for aquaculture installations from Su Urunleri Yetistiriciligi Yonetmeligi. Correct marine aquaculture spatial planning distance."),
    # Row 26: 15 metre - Istanbul and Canakkale harbours
    ("validate_distance.csv", 26): ("y", "y", "", "15m ship draft threshold referenced for Istanbul and Canakkale harbour provisions. Correct navigation spatial dimension from Deniz Trafik Duzeni Tuzugu."),
    # Row 28: 10-15 metre range - vessel draft
    ("validate_distance.csv", 28): ("y", "y", "", "10-15m vessel draft range for SP-1 reporting requirements in Turkish Straits. Correct navigation spatial dimension; range value correctly captures the threshold band."),
    # Row 32: 15 metre - Imar Kanunu telecommunications masts
    ("validate_distance.csv", 32): ("n", "n", "false_positive", "Telecommunications mast height threshold (15m) from Imar Kanunu. Terrestrial infrastructure regulation, not a marine or coastal distance."),
    # Row 38: 6 mil - vessel speed and passage restrictions
    ("validate_distance.csv", 38): ("y", "y", "", "6 nautical mile distance related to vessel speed/current restrictions at Bosphorus from Deniz Trafik Duzeni Tuzugu. Correct maritime spatial rule."),
}


def process_file(filepath, filename):
    """Process a single CSV file and annotate unannotated rows."""
    rows = []
    annotated_count = 0

    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row_id = int(row['id'])
            key = (filename, row_id)

            # Only annotate if is_correct is empty
            if row.get('is_correct', '').strip() == '' and key in ANNOTATIONS:
                is_correct, is_relevant, error_type, notes = ANNOTATIONS[key]
                row['is_correct'] = is_correct
                row['is_relevant'] = is_relevant
                row['error_type'] = error_type
                row['notes'] = notes
                annotated_count += 1

            rows.append(row)

    # Write back
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return annotated_count


def main():
    files_to_process = [
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
    for filename in files_to_process:
        filepath = os.path.join(VALIDATION_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  SKIP: {filename} not found")
            continue

        count = process_file(filepath, filename)
        total_annotated += count
        print(f"  {filename}: {count} rows annotated")

    print(f"\nTotal rows annotated: {total_annotated}")

    # Verification pass: count remaining unannotated rows
    print("\n--- Verification: remaining unannotated rows ---")
    remaining_total = 0
    for filename in files_to_process:
        filepath = os.path.join(VALIDATION_DIR, filename)
        if not os.path.exists(filepath):
            continue
        remaining = 0
        with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('is_correct', '').strip() == '':
                    remaining += 1
        if remaining > 0:
            print(f"  {filename}: {remaining} still unannotated")
            remaining_total += remaining

    if remaining_total == 0:
        print("  All rows annotated successfully!")
    else:
        print(f"\n  WARNING: {remaining_total} rows still unannotated")


if __name__ == "__main__":
    main()
