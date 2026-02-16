"""
MSP Keywords Module

Comprehensive MSP keyword dictionaries in Turkish and English,
organized by category with weights for activity classification.

Extracted from msp_extractor_v8_complete.py
"""


class MSPKeywords:
    """
    Comprehensive MSP keyword dictionaries in Turkish and English.

    Organized by category with weights for activity classification.
    """

    # =========================================================================
    # MARINE ACTIVITIES
    # =========================================================================

    ACTIVITIES = {
        'aquaculture': {
            'turkish': [
                'su ürünleri', 'su ürünleri yetiştiriciliği', 'yetiştiricilik',
                'balık çiftliği', 'balık yetiştiriciliği', 'balık üretimi',
                'midye', 'istiridye', 'kabuklu', 'karides', 'kafes', 'balık kafesi',
                'ağ kafes', 'yüzer kafes', 'yetiştirme tesisi', 'kuluçkahane',
                'marikultur', 'akvakültür', 'deniz yetiştiriciliği',
                'alabalık', 'levrek', 'çipura', 'ton balığı', 'orkinos',
                'yemleme', 'stoklama', 'hasat', 'yavru balık'
            ],
            'english': [
                'aquaculture', 'fish farm', 'fish farming', 'mariculture',
                'cage culture', 'net pen', 'shellfish', 'mussel', 'oyster',
                'shrimp', 'hatchery', 'finfish', 'salmon', 'sea bass',
                'sea bream', 'trout', 'tuna', 'feeding', 'stocking'
            ],
            'weight': 4
        },
        'fishing': {
            'turkish': [
                'balıkçılık', 'balıkçı', 'avcılık', 'su ürünleri avcılığı',
                'ticari balıkçılık', 'kıyı balıkçılığı', 'açık deniz balıkçılığı',
                'trol', 'gırgır', 'paragat', 'uzatma ağı', 'olta', 'dalyan',
                'avlanma', 'av sahası', 'av bölgesi', 'avlak',
                'yumurtlama alanı', 'üreme alanı', 'balık stoku', 'kota',
                'av yasağı', 'boy limiti', 'göz açıklığı',
                'balıkçı barınağı', 'balıkçı teknesi'
            ],
            'english': [
                'fishing', 'fishery', 'fisheries', 'trawling', 'trawl',
                'seine', 'purse seine', 'gillnet', 'longline', 'driftnet',
                'artisanal fishing', 'commercial fishing', 'recreational fishing',
                'catch', 'quota', 'stock', 'overfishing', 'bycatch',
                'spawning area', 'breeding ground', 'fishing ground'
            ],
            'weight': 4
        },
        'shipping_navigation': {
            'turkish': [
                'denizcilik', 'gemi', 'seyrüsefer', 'seyir', 'deniz taşımacılığı',
                'gemi trafiği', 'seyir hattı', 'trafik ayrım', 'TAS',
                'geçiş', 'boğaz geçişi', 'kanal', 'demirleme', 'demirleme alanı',
                'yanaşma', 'kılavuzluk', 'pilotaj', 'römorkaj',
                'feribot', 'ro-ro', 'konteyner gemisi', 'tanker', 'yük gemisi'
            ],
            'english': [
                'shipping', 'maritime transport', 'navigation', 'vessel',
                'ship', 'maritime traffic', 'shipping lane', 'traffic separation',
                'TSS', 'passage', 'strait', 'channel', 'anchorage',
                'berthing', 'pilotage', 'towage', 'ferry', 'container ship',
                'tanker', 'cargo ship', 'bulk carrier'
            ],
            'weight': 3
        },
        'ports_harbors': {
            'turkish': [
                'liman', 'iskele', 'rıhtım', 'terminal', 'yanaşma yeri',
                'ticari liman', 'konteyner terminali', 'kruvaziyer limanı',
                'yat limanı', 'marina', 'barınak', 'sığınak',
                'dalgakıran', 'mendirek', 'liman tesisi', 'liman havzası'
            ],
            'english': [
                'port', 'harbor', 'harbour', 'terminal', 'berth',
                'commercial port', 'container terminal', 'cruise terminal',
                'marina', 'yacht harbor', 'fishing harbor', 'shelter',
                'breakwater', 'jetty', 'pier', 'quay', 'wharf'
            ],
            'weight': 3
        },
        'tourism': {
            'turkish': [
                'turizm', 'turistik', 'rekreasyon', 'kıyı turizmi', 'deniz turizmi',
                'dalış', 'tüplü dalış', 'dalgıç', 'şnorkel',
                'plaj', 'kumsal', 'sahil', 'yüzme', 'yüzme alanı',
                'yat', 'yelken', 'tekne turu', 'mavi yolculuk',
                'su sporları', 'sörf', 'kano', 'jet ski'
            ],
            'english': [
                'tourism', 'coastal tourism', 'marine tourism', 'recreation',
                'diving', 'scuba diving', 'snorkeling', 'beach', 'swimming',
                'yacht', 'yachting', 'sailing', 'boat tour', 'cruise',
                'water sports', 'surfing', 'kayaking', 'jet ski',
                'ecotourism', 'whale watching'
            ],
            'weight': 3
        },
        'offshore_energy': {
            'turkish': [
                'açık deniz rüzgar', 'deniz üstü rüzgar', 'rüzgar enerjisi',
                'rüzgar türbini', 'rüzgar santrali', 'dalga enerjisi',
                'deniz enerjisi', 'yenilenebilir enerji', 'enerji platformu'
            ],
            'english': [
                'offshore wind', 'wind farm', 'wind turbine', 'wind energy',
                'wave energy', 'tidal energy', 'marine energy',
                'renewable energy', 'offshore renewable', 'OWEZ'
            ],
            'weight': 4
        },
        'oil_gas': {
            'turkish': [
                'petrol', 'doğalgaz', 'doğal gaz', 'hidrokarbon',
                'sondaj', 'arama sondajı', 'üretim platformu', 'petrol platformu',
                'denizaltı boru hattı', 'sismik', 'TPAO'
            ],
            'english': [
                'oil', 'gas', 'petroleum', 'hydrocarbon', 'drilling',
                'exploration', 'production platform', 'oil platform',
                'subsea pipeline', 'seismic survey', 'offshore drilling'
            ],
            'weight': 4
        },
        'military': {
            'turkish': [
                'askeri', 'donanma', 'savunma', 'milli savunma', 'TSK',
                'deniz kuvvetleri', 'deniz üssü', 'askeri bölge', 'yasak bölge',
                'güvenlik bölgesi', 'tatbikat alanı', 'sahil güvenlik'
            ],
            'english': [
                'military', 'naval', 'defense', 'defence', 'navy',
                'naval base', 'military zone', 'restricted area',
                'security zone', 'exercise area', 'coast guard'
            ],
            'weight': 5
        },
        'cables_pipelines': {
            'turkish': [
                'kablo', 'denizaltı kablosu', 'elektrik kablosu', 'fiber optik',
                'boru hattı', 'gaz boru hattı', 'denizaltı altyapısı'
            ],
            'english': [
                'cable', 'submarine cable', 'subsea cable', 'fiber optic',
                'pipeline', 'gas pipeline', 'subsea infrastructure',
                'interconnector', 'power cable'
            ],
            'weight': 3
        },
        'dredging_mining': {
            'turkish': [
                'tarama', 'kum çıkarımı', 'çakıl çıkarımı', 'agrega',
                'deniz madenciliği', 'dip taraması'
            ],
            'english': [
                'dredging', 'sand extraction', 'gravel extraction', 'aggregate',
                'marine mining', 'seabed mining', 'deep sea mining'
            ],
            'weight': 3
        },
        'conservation': {
            'turkish': [
                'koruma', 'doğa koruma', 'habitat koruma', 'ekosistem',
                'biyoçeşitlilik', 'nesli tehlike', 'endemik', 'restorasyon'
            ],
            'english': [
                'conservation', 'protection', 'habitat protection', 'ecosystem',
                'biodiversity', 'endangered', 'endemic', 'restoration',
                'rehabilitation', 'marine conservation'
            ],
            'weight': 3
        },
        'research': {
            'turkish': [
                'araştırma', 'bilimsel', 'izleme', 'ölçüm', 'oşinografi'
            ],
            'english': [
                'research', 'scientific', 'monitoring', 'survey',
                'oceanography', 'marine science', 'study', 'sampling'
            ],
            'weight': 2
        }
    }

    # =========================================================================
    # PROTECTED AREAS
    # =========================================================================

    PROTECTED_AREAS = {
        'turkish': [
            'koruma alanı', 'deniz koruma alanı', 'DKA', 'milli park',
            'ÖÇKB', 'özel çevre koruma bölgesi', 'özel koruma alanı',
            'sit alanı', 'doğal sit', 'arkeolojik sit', 'tabiat parkı',
            'yaban hayatı koruma sahası', 'sulak alan', 'biyosfer rezervi',
            'mutlak koruma alanı', 'tampon bölge', 'hassas alan',
            'su ürünleri istihsal sahası', 'yumurtlama alanı'
        ],
        'english': [
            'marine protected area', 'MPA', 'marine reserve', 'marine park',
            'Natura 2000', 'SAC', 'SPA', 'SCI', 'IUCN',
            'world heritage', 'biosphere reserve', 'Ramsar', 'wetland',
            'sanctuary', 'no-take zone', 'conservation area', 'protected area',
            'nature reserve', 'wildlife refuge', 'critical habitat',
            'essential fish habitat', 'EFH', 'spawning ground'
        ]
    }

    # =========================================================================
    # ENVIRONMENTAL PARAMETERS
    # =========================================================================

    ENVIRONMENTAL_PARAMS = {
        'water_quality': {
            'turkish': [
                'pH', 'sıcaklık', 'su sıcaklığı', 'tuzluluk', 'salinite',
                'oksijen', 'çözünmüş oksijen', 'azot', 'toplam azot',
                'fosfor', 'toplam fosfor', 'nitrat', 'nitrit', 'amonyak',
                'BOİ', 'BOİ5', 'KOİ', 'AKM', 'askıda katı madde',
                'bulanıklık', 'klorofil', 'koliform', 'ağır metal',
                'kurşun', 'civa', 'kadmiyum', 'arsenik', 'yağ', 'gres'
            ],
            'english': [
                'pH', 'temperature', 'water temperature', 'salinity',
                'oxygen', 'dissolved oxygen', 'DO', 'nitrogen', 'total nitrogen',
                'phosphorus', 'total phosphorus', 'nitrate', 'nitrite', 'ammonia',
                'BOD', 'BOD5', 'COD', 'TSS', 'suspended solids',
                'turbidity', 'chlorophyll', 'coliform', 'heavy metal',
                'lead', 'mercury', 'cadmium', 'arsenic', 'oil', 'grease'
            ]
        },
        'units': [
            'mg/L', 'mg/l', 'ppm', 'ppb', 'µg/L', '°C', 'PSU', 'psu',
            'NTU', 'JTU', '%', 'dB', 'm³/s', 'm³/gün', 'm³/day',
            'kg/day', 'ton/year', 'CFU/100ml'
        ]
    }

    # =========================================================================
    # DISTANCE/SPATIAL TERMS
    # =========================================================================

    DISTANCE_TERMS = {
        'units': {
            'turkish': ['metre', 'metrelik', 'mt', 'm', 'km', 'kilometre', 'deniz mili', 'mil'],
            'english': ['meter', 'metre', 'meters', 'metres', 'm', 'km',
                       'kilometer', 'kilometre', 'nautical mile', 'nm', 'nmi', 'mile', 'miles']
        },
        'qualifiers': {
            'turkish': {
                'minimum': ['en az', 'asgari', 'minimum'],
                'maximum': ['en fazla', 'en çok', 'azami', 'maksimum', 'geçemez', 'aşamaz'],
                'approximately': ['yaklaşık', 'civarında', 'kadar', 'dolayında']
            },
            'english': {
                'minimum': ['at least', 'minimum', 'not less than', 'no less than'],
                'maximum': ['at most', 'maximum', 'not more than', 'up to', 'not exceed', 'shall not exceed'],
                'approximately': ['approximately', 'about', 'around', 'circa', 'roughly']
            }
        },
        'reference_points': {
            'turkish': [
                'kıyı', 'kıyıdan', 'kıyı çizgisi', 'kıyı kenar çizgisi',
                'sahil', 'sahilden', 'deniz', 'denizden',
                'liman', 'limandan', 'liman sınırı',
                'iskele', 'iskeleden', 'tesis', 'tesisten',
                'koruma alanı', 'koruma alanından', 'ada', 'adadan'
            ],
            'english': [
                'coast', 'coastline', 'shore', 'shoreline',
                'high water mark', 'HWM', 'low water mark', 'LWM',
                'baseline', 'mean high water', 'MHW',
                'port', 'harbor', 'harbour', 'facility',
                'protected area', 'MPA boundary', 'island'
            ]
        }
    }

    # =========================================================================
    # LEGAL TERMS
    # =========================================================================

    LEGAL_TERMS = {
        'turkish': {
            'prohibition': [
                'yasak', 'yasaktır', 'yasaklanmış', 'yasaklanmıştır',
                'yapılamaz', 'edilemez', 'girilmez', 'geçilemez',
                'izin verilmez', 'müsaade edilmez'
            ],
            'requirement': [
                'zorunlu', 'zorunludur', 'gerekli', 'gereklidir',
                'şart', 'şarttır', 'mecburi', 'mecburidir',
                'alınmalı', 'alınması gerekir', 'olmadan'
            ],
            'permit': [
                'izin', 'ruhsat', 'lisans', 'belge', 'onay', 'muvafakat',
                'ÇED', 'çevresel etki değerlendirmesi', 'çevre izni',
                'işletme izni', 'faaliyet izni', 'yapı izni'
            ],
            'penalty': [
                'ceza', 'para cezası', 'idari para cezası', 'adli para cezası',
                'hapis', 'hapis cezası', 'yaptırım', 'müeyyide'
            ]
        },
        'english': {
            'prohibition': [
                'prohibited', 'forbidden', 'not allowed', 'banned',
                'restricted', 'shall not', 'must not', 'may not'
            ],
            'requirement': [
                'required', 'mandatory', 'shall', 'must', 'obligatory',
                'necessary', 'compulsory', 'need to', 'have to'
            ],
            'permit': [
                'permit', 'license', 'licence', 'authorization', 'authorisation',
                'approval', 'consent', 'EIA', 'environmental impact assessment',
                'operating permit', 'construction permit'
            ],
            'penalty': [
                'penalty', 'fine', 'sanction', 'punishment',
                'infringement', 'violation', 'offense', 'offence'
            ]
        }
    }

    # =========================================================================
    # STAKEHOLDERS
    # =========================================================================

    STAKEHOLDERS = {
        'government': {
            'turkish': [
                'bakanlık', 'genel müdürlük', 'müdürlük', 'valilik', 'kaymakamlık',
                'belediye', 'il özel idaresi', 'Tarım ve Orman Bakanlığı',
                'Çevre Bakanlığı', 'Çevre, Şehircilik ve İklim Değişikliği Bakanlığı',
                'Ulaştırma Bakanlığı', 'Ulaştırma ve Altyapı Bakanlığı',
                'Enerji Bakanlığı', 'Kültür ve Turizm Bakanlığı',
                'Sahil Güvenlik', 'Liman Başkanlığı', 'SHOD'
            ],
            'english': [
                'ministry', 'department', 'agency', 'authority',
                'government', 'administration', 'directorate',
                'coast guard', 'port authority', 'maritime authority',
                'environmental agency', 'fisheries department'
            ]
        },
        'industry': {
            'turkish': [
                'balıkçı', 'balıkçılar', 'yatırımcı', 'işletmeci',
                'şirket', 'firma', 'sektör', 'üretici'
            ],
            'english': [
                'fisher', 'fisherman', 'fishermen', 'operator',
                'company', 'industry', 'developer', 'investor',
                'business', 'producer', 'stakeholder'
            ]
        },
        'community': {
            'turkish': [
                'halk', 'toplum', 'yerel halk', 'kıyı toplulukları',
                'köylüler', 'vatandaş'
            ],
            'english': [
                'community', 'local community', 'coastal community',
                'public', 'residents', 'citizens', 'villagers'
            ]
        },
        'ngo': {
            'turkish': [
                'sivil toplum', 'STK', 'dernek', 'vakıf',
                'çevre örgütü', 'koruma derneği'
            ],
            'english': [
                'NGO', 'non-governmental organization', 'civil society',
                'conservation organization', 'environmental group',
                'association', 'foundation'
            ]
        }
    }

    # =========================================================================
    # RESEARCH METHODS (for scientific papers)
    # =========================================================================

    METHODS = {
        'gis_remote_sensing': [
            'GIS', 'geographic information system', 'spatial analysis',
            'mapping', 'remote sensing', 'satellite imagery',
            'Landsat', 'Sentinel', 'MODIS', 'SAR', 'radar',
            'ArcGIS', 'QGIS', 'geospatial', 'raster', 'vector'
        ],
        'modeling': [
            'model', 'modeling', 'modelling', 'simulation', 'scenario',
            'prediction', 'forecast', 'Marxan', 'Ecopath', 'Ecosim',
            'hydrodynamic model', 'species distribution model', 'SDM',
            'MaxEnt', 'habitat suitability', 'connectivity model'
        ],
        'survey': [
            'survey', 'questionnaire', 'interview', 'focus group',
            'participatory', 'consultation', 'workshop', 'Delphi method',
            'stakeholder analysis', 'social survey'
        ],
        'field_sampling': [
            'field survey', 'sampling', 'transect', 'quadrat',
            'SCUBA', 'underwater visual census', 'UVC',
            'acoustic survey', 'tagging', 'CTD', 'water sampling',
            'sediment sampling', 'trawl survey', 'ichthyoplankton'
        ],
        'statistical': [
            'statistical analysis', 'statistics', 'regression',
            'correlation', 'ANOVA', 'multivariate', 'PCA',
            'cluster analysis', 'ordination', 'NMDS', 'PERMANOVA',
            'significance', 'p-value', 'confidence interval'
        ]
    }

    # =========================================================================
    # SPECIES (for scientific papers)
    # =========================================================================

    SPECIES = {
        'fish': {
            'turkish': [
                'levrek', 'çipura', 'hamsi', 'sardalya', 'lüfer', 'palamut',
                'orkinos', 'kılıç balığı', 'barbunya', 'mezgit', 'istavrit',
                'kalkan', 'dil balığı', 'kefal', 'mercan'
            ],
            'english': [
                'sea bass', 'sea bream', 'anchovy', 'sardine', 'tuna',
                'swordfish', 'mackerel', 'cod', 'herring', 'hake',
                'sole', 'turbot', 'mullet', 'snapper', 'grouper'
            ]
        },
        'mammals': [
            'dolphin', 'whale', 'seal', 'porpoise', 'cetacean',
            'marine mammal', 'monk seal', 'bottlenose dolphin'
        ],
        'habitats': {
            'turkish': [
                'mercan', 'deniz çayırı', 'posidonia', 'kayalık',
                'kumul', 'çamur', 'alg'
            ],
            'english': [
                'coral', 'coral reef', 'seagrass', 'Posidonia', 'kelp',
                'mangrove', 'salt marsh', 'mudflat', 'sandbank',
                'seamount', 'canyon', 'rocky reef'
            ]
        }
    }

    # =========================================================================
    # TEMPORAL TERMS
    # =========================================================================

    TEMPORAL_TERMS = {
        'months': {
            'turkish': {
                'ocak': 1, 'şubat': 2, 'mart': 3, 'nisan': 4,
                'mayıs': 5, 'haziran': 6, 'temmuz': 7, 'ağustos': 8,
                'eylül': 9, 'ekim': 10, 'kasım': 11, 'aralık': 12
            },
            'english': {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
        },
        'duration': {
            'turkish': ['yıl', 'yıllık', 'sene', 'ay', 'aylık', 'gün', 'günlük', 'hafta', 'saat'],
            'english': ['year', 'years', 'month', 'months', 'day', 'days', 'week', 'weeks', 'hour', 'hours']
        },
        'seasonal': {
            'turkish': ['sezon', 'dönem', 'mevsim', 'yaz', 'kış', 'ilkbahar', 'sonbahar'],
            'english': ['season', 'seasonal', 'period', 'summer', 'winter', 'spring', 'autumn', 'fall', 'spawning season']
        }
    }

    # =========================================================================
    # CONFLICT TERMS
    # =========================================================================

    CONFLICTS = {
        'turkish': [
            'çatışma', 'rekabet', 'uyuşmazlık', 'anlaşmazlık',
            'çakışma', 'karşıtlık', 'sorun', 'problem', 'gerilim'
        ],
        'english': [
            'conflict', 'competition', 'dispute', 'disagreement',
            'overlap', 'tension', 'trade-off', 'tradeoff', 'incompatible',
            'competing use', 'multi-use conflict', 'interaction'
        ]
    }

    # =========================================================================
    # DATA SOURCES
    # =========================================================================

    DATA_SOURCES = {
        'satellite': [
            'satellite', 'Landsat', 'Sentinel', 'Sentinel-2', 'MODIS',
            'remote sensing', 'imagery', 'SAR', 'radar', 'Copernicus'
        ],
        'database': [
            'database', 'OBIS', 'GBIF', 'EMODnet', 'Copernicus Marine',
            'World Ocean Atlas', 'NOAA', 'FAO', 'ICES', 'FishBase',
            'SeaLifeBase', 'IUCN Red List'
        ],
        'monitoring': [
            'monitoring data', 'survey data', 'field data', 'census',
            'catch data', 'VMS', 'AIS', 'logbook', 'observer data'
        ]
    }
