# logic.py
# The "brain" of the Smart AI Healthcare Assistant.
# Features: symptom matching, emergency alert, self-care tips,
# typo handling, synonyms, and English / Marathi / Hindi support.
# No API key needed. Everything is plain Python.

import re
import sys
from difflib import SequenceMatcher

# ---------------------------------------------------------------
# 1. CONDITIONS AND THEIR SYMPTOMS (20 conditions)
# ---------------------------------------------------------------
CONDITION_SYMPTOMS = {
    "Common Cold": ["runny nose", "sneezing", "sore throat", "cough"],
    "Flu": ["fever", "body ache", "fatigue", "cough", "headache"],
    "Migraine": ["headache", "dizziness", "nausea"],
    "Food Poisoning": ["nausea", "vomiting", "diarrhea", "stomach pain"],
    "Seasonal Allergy": ["sneezing", "itchy eyes", "runny nose"],
    "Gastritis/Acid Reflux": ["stomach pain", "heartburn", "nausea"],
    "UTI": ["burning urination", "frequent urination", "fatigue"],
    "Viral Fever": ["fever", "body ache", "fatigue", "headache"],
    "Dehydration": ["dizziness", "fatigue", "headache"],
    "Anxiety/Stress": ["difficulty sleeping", "fatigue", "headache", "restlessness"],
    "Sinusitis": ["facial pain", "blocked nose", "headache", "runny nose"],
    "Bronchitis": ["cough", "chest congestion", "fatigue", "sore throat"],
    "Conjunctivitis": ["red eyes", "itchy eyes", "watery eyes", "eye discharge"],
    "Tonsillitis": ["sore throat", "fever", "difficulty swallowing", "swollen glands"],
    "Diarrhea/IBS": ["diarrhea", "stomach pain", "bloating"],
    "Constipation": ["constipation", "stomach pain", "bloating"],
    "Skin Allergy": ["skin rash", "itching"],
    "Insomnia": ["difficulty sleeping", "fatigue", "irritability"],
    "Muscle Strain": ["muscle pain", "body ache", "joint stiffness"],
    "Heat Exhaustion": ["excessive sweating", "dizziness", "weakness", "headache", "nausea"],
}

EMERGENCY_SYMPTOMS = [
    "chest pain",
    "difficulty breathing",
    "severe bleeding",
    "loss of consciousness",
]

# ---------------------------------------------------------------
# 2. SYNONYMS: other ways people say the same symptom
#    (English, spelling mistakes, Hinglish, Marathi, Hindi)
# ---------------------------------------------------------------
SYMPTOM_ALIASES = {
    "fever": ["fever", "fevar", "fevr", "feaver", "high temperature", "temperature",
              "feverish", "bukhar", "bukhaar", "taap", "ताप", "बुखार"],
    "cough": ["cough", "coff", "couph", "coughing", "khansi", "khokla",
              "खोकला", "खांसी", "खासी"],
    "sore throat": ["sore throat", "throat pain", "throat ache", "throat hurts",
                    "gala dukhne", "gale mein dard", "घसा", "घसा दुखणे",
                    "घसा खवखवणे", "गले में दर्द", "गले में खराश", "गला खराब"],
    "runny nose": ["runny nose", "running nose", "nose running", "nak vahne",
                   "naak behna", "sardi", "zukam", "jukam", "सर्दी", "जुकाम",
                   "नाक वाहणे", "नाक वाहत", "नाक गळणे", "नाक बहना", "नाक बह"],
    "blocked nose": ["blocked nose", "stuffy nose", "nose blocked", "nose block",
                     "nak band", "naak band", "नाक बंद", "नाक चोंदणे", "नाक चोंदले"],
    "headache": ["headache", "head ache", "head pain", "head hurts", "sar dard",
                 "sardard", "dokedukhi", "डोकेदुखी", "डोके दुखणे", "डोके दुखत",
                 "डोकं दुखत", "सिरदर्द", "सर दर्द", "सिर दर्द", "सिर में दर्द"],
    "body ache": ["body ache", "body pain", "badan dard", "angdukhi", "अंगदुखी",
                  "अंग दुखणे", "अंग दुखत", "अंगात कणकण", "बदन दर्द", "बदन में दर्द",
                  "शरीर दर्द"],
    "fatigue": ["fatigue", "tired", "tiredness", "exhausted", "thakan", "thakwa",
                "थकवा", "थकान", "थकल", "थकावट"],
    "nausea": ["nausea", "nauseous", "queasy", "feel like vomiting", "malmal",
               "मळमळ", "जी मिचलाना", "मिचली"],
    "vomiting": ["vomiting", "vomit", "vomited", "throwing up", "ulti", "ultya",
                 "उलटी", "उलट्या", "उल्टी"],
    "diarrhea": ["diarrhea", "diarrhoea", "loose motion", "loose stools", "julab",
                 "dast", "जुलाब", "दस्त", "पातळ शौच"],
    "stomach pain": ["stomach pain", "stomach ache", "stomachache", "tummy ache",
                     "tummy pain", "belly pain", "abdominal pain", "pet dard",
                     "पोटदुखी", "पोट दुखणे", "पोट दुखत", "पोटात दुखणे",
                     "पेट दर्द", "पेट में दर्द", "पेट दुखना"],
    "sneezing": ["sneezing", "sneeze", "chheenk", "shinka", "शिंका", "शिंक", "छींक"],
    "itchy eyes": ["itchy eyes", "eyes itching", "itching in eyes", "eye itching",
                   "डोळ्यांना खाज", "डोळे खाजणे", "आंखों में खुजली"],
    "heartburn": ["heartburn", "acidity", "acid reflux", "burning in chest",
                  "seene me jalan", "छातीत जळजळ", "अॅसिडिटी", "एसिडिटी", "पित्त",
                  "सीने में जलन"],
    "burning urination": ["burning urination", "burning while urinating",
                          "burning during urination", "painful urination",
                          "burning urine", "urine burning", "laghvi jalan",
                          "peshab me jalan", "लघवीत जळजळ", "लघवी करताना जळजळ",
                          "लघवीला जळजळ", "पेशाब में जलन", "पेशाब करते समय जलन"],
    "frequent urination": ["frequent urination", "urinating frequently",
                           "urinate frequently", "peeing a lot", "frequent urine",
                           "baar baar peshab", "vaaravaar laghvi", "वारंवार लघवी",
                           "सारखी लघवी", "बार बार पेशाब"],
    "dizziness": ["dizziness", "dizzy", "giddy", "lightheaded", "light headed",
                  "chakkar", "चक्कर", "भोवळ"],
    "difficulty sleeping": ["difficulty sleeping", "cant sleep", "cannot sleep",
                            "unable to sleep", "trouble sleeping", "not able to sleep",
                            "sleeplessness", "insomnia", "neend nahi", "nind nahi",
                            "झोप येत नाही", "झोप लागत नाही", "झोप न लागणे",
                            "नींद नहीं", "नींद न आना"],
    "restlessness": ["restless", "restlessness", "uneasy", "anxious", "anxiety",
                     "nervous", "bechaini", "अस्वस्थ", "बेचैन", "घाबरल्यासारखे"],
    "facial pain": ["facial pain", "face pain", "pain in face", "cheek pain",
                    "pressure in face", "चेहऱ्यावर वेदना", "चेहरा दुखणे", "चेहरे में दर्द"],
    "chest congestion": ["chest congestion", "congested chest", "phlegm", "mucus",
                         "kaf", "छातीत कफ", "कफ", "छाती में कफ", "बलगम"],
    "red eyes": ["red eyes", "eyes red", "red eye", "lal aankhen", "लाल डोळे",
                 "डोळे लाल", "लाल आंखें", "आंखें लाल"],
    "watery eyes": ["watery eyes", "eyes watering", "eye watering", "डोळ्यांतून पाणी",
                    "डोळ्यातून पाणी", "डोळे पाणावणे", "आंखों से पानी"],
    "eye discharge": ["eye discharge", "discharge from eye", "sticky eyes",
                      "pus in eye", "डोळ्यातून चिकट", "डोळ्यांतून चिकट",
                      "आंखों से चिपचिपा", "कीचड़"],
    "difficulty swallowing": ["difficulty swallowing", "painful swallowing",
                              "pain while swallowing", "hard to swallow", "cant swallow",
                              "गिळण्यास त्रास", "गिळताना त्रास", "गिळताना दुखते",
                              "निगलने में तकलीफ", "निगलने में दर्द"],
    "swollen glands": ["swollen glands", "swollen neck glands", "swollen lymph nodes",
                       "neck swelling", "गाठी सूजणे", "गळ्यात गाठ", "गिल्टी"],
    "bloating": ["bloating", "bloated", "gas problem", "gas in stomach",
                 "pet phulna", "पोट फुगणे", "पोट फुगले", "पोटात गॅस",
                 "पेट फूलना", "पेट में गैस", "गैस"],
    "constipation": ["constipation", "constipated", "hard stool", "kabz", "kabj",
                     "बद्धकोष्ठता", "शौचास होत नाही", "पोट साफ होत नाही",
                     "कब्ज", "पेट साफ नहीं"],
    "skin rash": ["skin rash", "rash", "rashes", "red patches", "त्वचेवर पुरळ",
                  "अंगावर पुरळ", "पुरळ", "त्वचा पर चकत्ते", "चकत्ते", "लाल चट्टे"],
    "itching": ["itching", "itchy", "itchy skin", "scratching", "khujli", "khaj",
                "खाज", "खुजली", "खाजवणे", "खुजलाना"],
    "irritability": ["irritable", "irritability", "short tempered", "chidchid",
                     "चिडचिड", "चिडचिडेपणा", "चिड़चिड़ापन"],
    "muscle pain": ["muscle pain", "muscle ache", "muscle soreness", "muscles hurt",
                    "sore muscles", "muscle cramp", "स्नायू दुखणे", "स्नायू दुखत",
                    "स्नायूंमध्ये वेदना", "मांसपेशियों में दर्द", "मांसपेशी में दर्द"],
    "joint stiffness": ["joint stiffness", "stiff joints", "stiffness", "stiff",
                        "joint pain", "सांधे जखडणे", "सांधे दुखणे", "जोड़ों में अकड़न",
                        "जोड़ों में दर्द"],
    "excessive sweating": ["excessive sweating", "sweating a lot", "too much sweating",
                           "sweating", "sweat", "pasina", "पसीना", "बहुत पसीना",
                           "खूप घाम", "घाम"],
    "weakness": ["weakness", "weak", "feeling weak", "kamzori", "अशक्तपणा",
                 "अशक्त", "कमजोरी"],
}

EMERGENCY_ALIASES = {
    "chest pain": ["chest pain", "pain in chest", "chest tightness", "tight chest",
                   "seene me dard", "छातीत दुखणे", "छातीत दुखत", "छातीत कळ",
                   "छातीत वेदना", "सीने में दर्द", "छाती में दर्द"],
    "difficulty breathing": ["difficulty breathing", "cant breathe", "cannot breathe",
                             "short of breath", "shortness of breath", "breathless",
                             "trouble breathing", "hard to breathe",
                             "श्वास घेण्यास त्रास", "श्वास घेता येत नाही", "दम लागतो",
                             "दम लागणे", "सांस लेने में तकलीफ", "सांस नहीं ले",
                             "सांस फूलना"],
    "severe bleeding": ["severe bleeding", "heavy bleeding", "bleeding a lot",
                        "bleeding heavily", "wont stop bleeding", "जास्त रक्तस्राव",
                        "खूप रक्त", "रक्तस्राव", "ज्यादा खून", "खून बहना"],
    "loss of consciousness": ["loss of consciousness", "unconscious", "fainted",
                              "passed out", "blacked out", "fainting", "बेशुद्ध",
                              "बेहोश", "बेहोशी"],
}

# ---------------------------------------------------------------
# 3. TRANSLATIONS: (English, Marathi, Hindi)
# ---------------------------------------------------------------
LANG_INDEX = {"en": 0, "mr": 1, "hi": 2}

CONDITION_NAMES = {
    "Common Cold": ("Common Cold", "सर्दी", "सर्दी-जुकाम"),
    "Flu": ("Flu", "फ्लू", "फ्लू"),
    "Migraine": ("Migraine", "मायग्रेन", "माइग्रेन"),
    "Food Poisoning": ("Food Poisoning", "अन्नातून विषबाधा", "फूड पॉइज़निंग"),
    "Seasonal Allergy": ("Seasonal Allergy", "हंगामी अॅलर्जी", "मौसमी एलर्जी"),
    "Gastritis/Acid Reflux": ("Gastritis/Acid Reflux", "गॅस्ट्रायटिस / अॅसिड रिफ्लक्स", "गैस्ट्राइटिस / एसिड रिफ्लक्स"),
    "UTI": ("UTI", "मूत्रमार्गाचा संसर्ग (UTI)", "मूत्र मार्ग संक्रमण (UTI)"),
    "Viral Fever": ("Viral Fever", "विषाणूजन्य ताप", "वायरल बुखार"),
    "Dehydration": ("Dehydration", "शरीरातील पाण्याची कमतरता", "पानी की कमी (डिहाइड्रेशन)"),
    "Anxiety/Stress": ("Anxiety/Stress", "चिंता / तणाव", "चिंता / तनाव"),
    "Sinusitis": ("Sinusitis", "सायनस", "साइनस"),
    "Bronchitis": ("Bronchitis", "ब्राँकायटिस", "ब्रोंकाइटिस"),
    "Conjunctivitis": ("Conjunctivitis", "डोळे येणे", "आंख आना (कंजंक्टिवाइटिस)"),
    "Tonsillitis": ("Tonsillitis", "टॉन्सिलायटिस", "टॉन्सिलाइटिस"),
    "Diarrhea/IBS": ("Diarrhea/IBS", "जुलाब / आयबीएस", "दस्त / आईबीएस"),
    "Constipation": ("Constipation", "बद्धकोष्ठता", "कब्ज"),
    "Skin Allergy": ("Skin Allergy", "त्वचेची अॅलर्जी", "त्वचा की एलर्जी"),
    "Insomnia": ("Insomnia", "निद्रानाश", "अनिद्रा"),
    "Muscle Strain": ("Muscle Strain", "स्नायूंचा ताण", "मांसपेशियों में खिंचाव"),
    "Heat Exhaustion": ("Heat Exhaustion", "उष्णतेमुळे थकवा", "गर्मी से थकावट"),
}

SYMPTOM_NAMES = {
    "fever": ("fever", "ताप", "बुखार"),
    "cough": ("cough", "खोकला", "खांसी"),
    "sore throat": ("sore throat", "घसा दुखणे", "गले में दर्द"),
    "runny nose": ("runny nose", "नाक वाहणे", "नाक बहना"),
    "blocked nose": ("blocked nose", "नाक बंद होणे", "नाक बंद"),
    "headache": ("headache", "डोकेदुखी", "सिरदर्द"),
    "body ache": ("body ache", "अंगदुखी", "बदन दर्द"),
    "fatigue": ("fatigue", "थकवा", "थकान"),
    "nausea": ("nausea", "मळमळ", "जी मिचलाना"),
    "vomiting": ("vomiting", "उलट्या", "उल्टी"),
    "diarrhea": ("diarrhea", "जुलाब", "दस्त"),
    "stomach pain": ("stomach pain", "पोटदुखी", "पेट दर्द"),
    "sneezing": ("sneezing", "शिंका", "छींक"),
    "itchy eyes": ("itchy eyes", "डोळ्यांना खाज", "आंखों में खुजली"),
    "heartburn": ("heartburn", "छातीत जळजळ", "सीने में जलन"),
    "burning urination": ("burning urination", "लघवीत जळजळ", "पेशाब में जलन"),
    "frequent urination": ("frequent urination", "वारंवार लघवी", "बार-बार पेशाब"),
    "dizziness": ("dizziness", "चक्कर", "चक्कर आना"),
    "difficulty sleeping": ("difficulty sleeping", "झोप न लागणे", "नींद न आना"),
    "restlessness": ("restlessness", "अस्वस्थता", "बेचैनी"),
    "facial pain": ("facial pain", "चेहऱ्यावर वेदना", "चेहरे में दर्द"),
    "chest congestion": ("chest congestion", "छातीत कफ", "छाती में कफ"),
    "red eyes": ("red eyes", "लाल डोळे", "लाल आंखें"),
    "watery eyes": ("watery eyes", "डोळ्यांतून पाणी", "आंखों से पानी"),
    "eye discharge": ("eye discharge", "डोळ्यांतून चिकट स्राव", "आंखों से चिपचिपा स्राव"),
    "difficulty swallowing": ("difficulty swallowing", "गिळण्यास त्रास", "निगलने में कठिनाई"),
    "swollen glands": ("swollen glands", "गाठी सूजणे", "गिल्टियां सूजना"),
    "bloating": ("bloating", "पोट फुगणे", "पेट फूलना"),
    "constipation": ("constipation", "बद्धकोष्ठता", "कब्ज"),
    "skin rash": ("skin rash", "त्वचेवर पुरळ", "त्वचा पर चकत्ते"),
    "itching": ("itching", "खाज", "खुजली"),
    "irritability": ("irritability", "चिडचिड", "चिड़चिड़ापन"),
    "muscle pain": ("muscle pain", "स्नायू दुखणे", "मांसपेशियों में दर्द"),
    "joint stiffness": ("joint stiffness", "सांधे जखडणे", "जोड़ों में अकड़न"),
    "excessive sweating": ("excessive sweating", "खूप घाम", "बहुत पसीना"),
    "weakness": ("weakness", "अशक्तपणा", "कमज़ोरी"),
    # emergency symptoms
    "chest pain": ("chest pain", "छातीत दुखणे", "सीने में दर्द"),
    "difficulty breathing": ("difficulty breathing", "श्वास घेण्यास त्रास", "सांस लेने में तकलीफ"),
    "severe bleeding": ("severe bleeding", "जास्त रक्तस्राव", "ज्यादा खून बहना"),
    "loss of consciousness": ("loss of consciousness", "बेशुद्ध होणे", "बेहोशी"),
}

# Basic self-care tips (no medicine names, no doses).
CARE_TIPS = {
    "Common Cold": ("Rest well, drink warm fluids, and inhale steam.",
                    "भरपूर विश्रांती घ्या, कोमट पेये प्या आणि वाफ घ्या.",
                    "भरपूर आराम करें, गुनगुने पेय पिएं और भाप लें।"),
    "Flu": ("Rest, drink plenty of fluids, and stay home to avoid spreading it.",
            "विश्रांती घ्या, भरपूर द्रव पदार्थ प्या आणि इतरांना संसर्ग होऊ नये म्हणून घरीच थांबा.",
            "आराम करें, खूब तरल पदार्थ पिएं और दूसरों को संक्रमण से बचाने के लिए घर पर रहें।"),
    "Migraine": ("Rest in a quiet, dark room and drink water.",
                 "शांत, अंधाऱ्या खोलीत विश्रांती घ्या आणि पाणी प्या.",
                 "शांत, अंधेरे कमरे में आराम करें और पानी पिएं।"),
    "Food Poisoning": ("Sip water often and eat light, bland food.",
                       "थोडे थोडे पाणी प्या आणि हलके, सौम्य अन्न खा.",
                       "थोड़ा-थोड़ा पानी पिएं और हल्का, सादा खाना खाएं।"),
    "Seasonal Allergy": ("Avoid dust and pollen, and keep windows closed.",
                         "धूळ आणि परागकण टाळा आणि खिडक्या बंद ठेवा.",
                         "धूल और पराग से बचें और खिड़कियां बंद रखें।"),
    "Gastritis/Acid Reflux": ("Avoid spicy and oily food, eat small meals, and do not lie down right after eating.",
                              "तिखट आणि तेलकट पदार्थ टाळा, थोडे थोडे जेवा आणि जेवणानंतर लगेच झोपू नका.",
                              "तीखा और तैलीय खाना न खाएं, थोड़ा-थोड़ा खाएं और खाने के तुरंत बाद न लेटें।"),
    "UTI": ("Drink plenty of water and do not hold your urine.",
            "भरपूर पाणी प्या आणि लघवी रोखून धरू नका.",
            "खूब पानी पिएं और पेशाब को रोककर न रखें।"),
    "Viral Fever": ("Rest, drink plenty of fluids, and eat light food.",
                    "विश्रांती घ्या, भरपूर द्रव प्या आणि हलके अन्न खा.",
                    "आराम करें, खूब तरल पदार्थ पिएं और हल्का खाना खाएं।"),
    "Dehydration": ("Drink water often and rest in a cool place.",
                    "वारंवार पाणी प्या आणि थंड जागी विश्रांती घ्या.",
                    "बार-बार पानी पिएं और ठंडी जगह पर आराम करें।"),
    "Anxiety/Stress": ("Try slow deep breathing, take short breaks, and sleep on time.",
                       "हळू आणि दीर्घ श्वास घ्या, थोडे थोडे ब्रेक घ्या आणि वेळेवर झोपा.",
                       "धीरे-धीरे गहरी सांस लें, छोटे ब्रेक लें और समय पर सोएं।"),
    "Sinusitis": ("Inhale steam and drink warm fluids.",
                  "वाफ घ्या आणि कोमट पेये प्या.",
                  "भाप लें और गुनगुने पेय पिएं।"),
    "Bronchitis": ("Rest, drink warm fluids, and avoid smoke and dust.",
                   "विश्रांती घ्या, कोमट पेये प्या आणि धूर व धूळ टाळा.",
                   "आराम करें, गुनगुने पेय पिएं और धुएं व धूल से बचें।"),
    "Conjunctivitis": ("Wash hands often, do not rub your eyes, and keep your towel separate.",
                       "हात वारंवार धुवा, डोळे चोळू नका आणि स्वतःचा रुमाल वेगळा ठेवा.",
                       "हाथ बार-बार धोएं, आंखें न रगड़ें और अपना तौलिया अलग रखें।"),
    "Tonsillitis": ("Gargle with warm salt water and drink warm fluids.",
                    "कोमट मिठाच्या पाण्याने गुळण्या करा आणि कोमट पेये प्या.",
                    "गुनगुने नमक के पानी से गरारे करें और गुनगुने पेय पिएं।"),
    "Diarrhea/IBS": ("Drink plenty of fluids and eat light food like rice and banana.",
                     "भरपूर द्रव प्या आणि भात, केळी यांसारखे हलके अन्न खा.",
                     "खूब तरल पदार्थ पिएं और चावल, केला जैसा हल्का खाना खाएं।"),
    "Constipation": ("Eat fibre-rich food, drink more water, and walk daily.",
                     "फायबरयुक्त अन्न खा, जास्त पाणी प्या आणि रोज चाला.",
                     "फाइबर वाला खाना खाएं, ज़्यादा पानी पिएं और रोज़ टहलें।"),
    "Skin Allergy": ("Avoid scratching, keep the skin clean and dry, and stay away from whatever triggered it.",
                     "खाजवू नका, त्वचा स्वच्छ व कोरडी ठेवा आणि ज्यामुळे त्रास झाला ते टाळा.",
                     "खुजलाएं नहीं, त्वचा को साफ और सूखा रखें और जिस चीज़ से हुआ उससे बचें।"),
    "Insomnia": ("Keep a fixed sleep time and avoid phone screens before bed.",
                 "झोपेची वेळ ठरवा आणि झोपण्यापूर्वी मोबाईल स्क्रीन टाळा.",
                 "सोने का समय तय रखें और सोने से पहले मोबाइल स्क्रीन से बचें।"),
    "Muscle Strain": ("Rest the muscle and apply a warm or cold pack.",
                      "त्या स्नायूला विश्रांती द्या आणि गरम किंवा थंड शेक द्या.",
                      "उस मांसपेशी को आराम दें और गर्म या ठंडी सिकाई करें।"),
    "Heat Exhaustion": ("Move to a cool, shaded place and sip water slowly.",
                        "थंड, सावलीच्या जागी जा आणि हळूहळू पाणी प्या.",
                        "ठंडी, छायादार जगह पर जाएं और धीरे-धीरे पानी पिएं।"),
}

MESSAGES = {
    "en": {
        "ask_more": "I couldn't recognize any symptoms in your message. Please describe how you feel, for example: 'I have fever and headache'.",
        "emergency": "🚨 Possible emergency: {sym}.\nThis may be serious. Please call your local emergency number or go to the nearest hospital immediately. Do not wait for online advice.",
        "no_match": "I recognized these symptoms: {syms}, but they don't clearly match any condition I know. Please consult a doctor.",
        "noticed": "I noticed these symptoms: {syms}.",
        "possible": "Possible condition: {cond} (match: {score}%)",
        "others": "Other possibilities: {others}",
        "care": "🩹 Basic self-care: {tip}",
        "disclaimer": "⚠️ This is not a medical diagnosis. Please consult a doctor.",
    },
    "mr": {
        "ask_more": "तुमच्या संदेशातील लक्षणे मला ओळखता आली नाहीत. कृपया तुम्हाला काय होत आहे ते सांगा, उदा. 'मला ताप आणि डोकेदुखी आहे'.",
        "emergency": "🚨 संभाव्य आणीबाणी: {sym}.\nही गंभीर समस्या असू शकते. कृपया त्वरित जवळच्या रुग्णालयात जा किंवा आपत्कालीन क्रमांकावर संपर्क करा. ऑनलाइन सल्ल्याची वाट पाहू नका.",
        "no_match": "मला ही लक्षणे ओळखता आली: {syms}, पण ती माझ्याकडे असलेल्या कोणत्याही आजाराशी स्पष्टपणे जुळत नाहीत. कृपया डॉक्टरांचा सल्ला घ्या.",
        "noticed": "मला ही लक्षणे आढळली: {syms}.",
        "possible": "संभाव्य आजार: {cond} (जुळणी: {score}%)",
        "others": "इतर शक्यता: {others}",
        "care": "🩹 घरगुती काळजी: {tip}",
        "disclaimer": "⚠️ हे वैद्यकीय निदान नाही. कृपया डॉक्टरांचा सल्ला घ्या.",
    },
    "hi": {
        "ask_more": "मैं आपके संदेश में लक्षण पहचान नहीं पाया। कृपया बताइए कि आपको क्या हो रहा है, जैसे 'मुझे बुखार और सिरदर्द है'।",
        "emergency": "🚨 संभावित आपातकाल: {sym}।\nयह गंभीर हो सकता है। कृपया तुरंत नज़दीकी अस्पताल जाएं या आपातकालीन नंबर पर कॉल करें। ऑनलाइन सलाह का इंतज़ार न करें।",
        "no_match": "मैंने ये लक्षण पहचाने: {syms}, लेकिन ये मेरी जानकारी के किसी भी रोग से साफ़ मेल नहीं खाते। कृपया डॉक्टर से सलाह लें।",
        "noticed": "मुझे ये लक्षण मिले: {syms}।",
        "possible": "संभावित रोग: {cond} (मेल: {score}%)",
        "others": "अन्य संभावनाएं: {others}",
        "care": "🩹 बुनियादी घरेलू देखभाल: {tip}",
        "disclaimer": "⚠️ यह चिकित्सा निदान नहीं है। कृपया डॉक्टर से सलाह लें।",
    },
}

# ---------------------------------------------------------------
# 4. LANGUAGE DETECTION
# ---------------------------------------------------------------
MARATHI_WORDS = {"आहे", "आहेत", "मला", "नाही", "आणि", "होत", "होतो", "होतोय",
                 "होतेय", "वाटतंय", "वाटते", "माझे", "माझी", "माझा", "मी", "खूप",
                 "येत", "येतो", "येते", "दुखत", "दुखतो", "दुखते", "दुखतंय",
                 "ताप", "डोकेदुखी", "खोकला", "उलट्या", "जुलाब", "पोट", "घाम",
                 "अशक्तपणा", "थकवा", "खाज", "शिंका", "पोटदुखी"}
HINDI_WORDS = {"है", "हैं", "मुझे", "नहीं", "और", "रहा", "रही", "रहे", "मेरे",
               "मेरा", "मेरी", "मैं", "बहुत", "बुखार", "सिरदर्द", "खांसी", "उल्टी",
               "दस्त", "कब्ज", "पेट", "पसीना", "थकान", "दर्द", "खुजली", "छींक",
               "बलगम", "बदन"}


def detect_language(text):
    """Returns 'en', 'mr' or 'hi' based on the script and common words."""
    if not re.search(r"[\u0900-\u097F]", text):
        return "en"
    tokens = _normalize(text).split()
    marathi_score = sum(1 for t in tokens if t in MARATHI_WORDS)
    hindi_score = sum(1 for t in tokens if t in HINDI_WORDS)
    return "hi" if hindi_score > marathi_score else "mr"


# ---------------------------------------------------------------
# 5. TEXT CLEANING AND SMART MATCHING
# ---------------------------------------------------------------
def _normalize(text):
    """Lowercase, remove punctuation, and make Devanagari spelling uniform."""
    text = text.lower()
    text = text.replace("\u200d", "").replace("\u200c", "")   # invisible joiners
    text = text.replace("ँ", "ं").replace("़", "")              # spelling variants
    text = text.replace("।", " ").replace("॥", " ")
    text = re.sub(r"['’`]", "", text)                          # can't -> cant
    text = re.sub(r"[^a-z0-9\s\u0900-\u097F]", " ", text)      # punctuation -> space
    return re.sub(r"\s+", " ", text).strip()


def _build_alias_list(alias_dict):
    items = []
    for symptom, phrases in alias_dict.items():
        for phrase in set(phrases + [symptom]):
            items.append((_normalize(phrase), symptom))
    return items


SYMPTOM_ALIAS_LIST = _build_alias_list(SYMPTOM_ALIASES)
EMERGENCY_ALIAS_LIST = _build_alias_list(EMERGENCY_ALIASES)


def _find_symptoms(text, alias_list):
    """
    Finds symptoms in text. Handles:
      - exact words and plurals       ("headaches")
      - spelling mistakes             ("hedache", "diarhea")
      - synonyms and other languages  ("tummy ache", "ताप", "bukhar")
    """
    norm = _normalize(text)
    tokens = [(m.group(), m.start(), m.end()) for m in re.finditer(r"\S+", norm)]
    candidates = []  # (start, end, symptom)

    for alias, symptom in alias_list:
        if alias.isascii():
            # exact match (allows plural s / es)
            pattern = r"(?<![a-z])" + re.escape(alias) + r"(?:s|es)?(?![a-z])"
            for m in re.finditer(pattern, norm):
                candidates.append((m.start(), m.end(), symptom))
            # typo match (only for longer words, to avoid wrong guesses)
            if len(alias) >= 6:
                n = len(alias.split())
                for i in range(len(tokens) - n + 1):
                    window = tokens[i:i + n]
                    guess = " ".join(t[0] for t in window)
                    if (guess != alias and guess[0] == alias[0]
                            and abs(len(guess) - len(alias)) <= 2
                            and SequenceMatcher(None, guess, alias).ratio() >= 0.8):
                        candidates.append((window[0][1], window[-1][2], symptom))
        else:
            # Marathi / Hindi: simple text search
            start = 0
            while True:
                idx = norm.find(alias, start)
                if idx == -1:
                    break
                candidates.append((idx, idx + len(alias), symptom))
                start = idx + 1

    # Longest phrase wins, so "eyes itching" is not also counted as "itching".
    candidates.sort(key=lambda c: c[1] - c[0], reverse=True)
    taken, found = [], []
    for start, end, symptom in candidates:
        if any(start < t_end and end > t_start for t_start, t_end in taken):
            continue
        taken.append((start, end))
        if symptom not in found:
            found.append(symptom)
    return found


def extract_symptoms(user_text):
    """Returns the list of normal symptoms found in the user's text."""
    return _find_symptoms(user_text, SYMPTOM_ALIAS_LIST)


def find_emergency(user_text):
    """Returns the list of emergency symptoms found in the user's text."""
    return _find_symptoms(user_text, EMERGENCY_ALIAS_LIST)


def match_conditions(found_symptoms):
    """Scores every condition and returns them, best match first."""
    results = []
    for condition, symptoms in CONDITION_SYMPTOMS.items():
        overlap = set(found_symptoms) & set(symptoms)
        if overlap:
            score = len(overlap) / len(symptoms)
            results.append((condition, round(score * 100, 1), list(overlap)))
    results.sort(key=lambda x: (x[1], len(x[2])), reverse=True)
    return results


def _name(table, key, lang):
    return table[key][LANG_INDEX[lang]]


# ---------------------------------------------------------------
# 6. MAIN FUNCTION (this is what app.py calls)
# ---------------------------------------------------------------
def get_response(user_text):
    lang = detect_language(user_text)
    msg = MESSAGES[lang]

    # Step 1: emergency check first
    emergencies = find_emergency(user_text)
    if emergencies:
        names = ", ".join(_name(SYMPTOM_NAMES, s, lang) for s in emergencies)
        return msg["emergency"].format(sym=names)

    # Step 2: find normal symptoms
    found = extract_symptoms(user_text)
    if not found:
        return msg["ask_more"]

    symptom_text = ", ".join(_name(SYMPTOM_NAMES, s, lang) for s in found)

    # Step 3: match with conditions
    matches = match_conditions(found)
    if not matches:
        return msg["no_match"].format(syms=symptom_text)

    top, score, _ = matches[0]
    parts = [
        msg["noticed"].format(syms=symptom_text),
        msg["possible"].format(cond=_name(CONDITION_NAMES, top, lang), score=score),
    ]

    if len(matches) > 1:
        others = ", ".join(
            f"{_name(CONDITION_NAMES, c, lang)} ({s}%)" for c, s, _ in matches[1:3]
        )
        parts.append(msg["others"].format(others=others))

    parts.append(msg["care"].format(tip=CARE_TIPS[top][LANG_INDEX[lang]]))
    parts.append(msg["disclaimer"])
    return "\n\n".join(parts)


# ---------------------------------------------------------------
# Quick test: run  python logic.py
# ---------------------------------------------------------------
if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for test in ["I have fevar and hedache",
                 "मला ताप आणि डोकेदुखी आहे",
                 "मुझे बुखार और सिरदर्द है"]:
        print("USER:", test)
        print(get_response(test))
        print("-" * 50)


       # CONDITION_SYMPTOMS: the 20 conditions and their symptoms.
#EMERGENCY_SYMPTOMS: 4 emergency symptoms.
#SYMPTOM_ALIASES and EMERGENCY_ALIASES: synonyms, spelling variants and Marathi/Hindi words for each symptom.
#CONDITION_NAMES and SYMPTOM_NAMES: names in English, Marathi and Hindi.
#CARE_TIPS: the self-care tip for each condition, in three languages.
#MESSAGES: the reply sentences in three languages.
#detect_language(): decides English, Marathi or Hindi.
#_normalize(): cleans the text.
#_find_symptoms(): finds symptoms in the text, including spelling mistakes (using difflib). The longest phrase wins.
#extract_symptoms() and find_emergency(): return the normal and emergency symptoms found.
#match_conditions(): scores each condition as matched ÷ total symptoms, best first.
#get_response(): the main function. It checks emergency, then symptoms, then matches, then builds the reply.