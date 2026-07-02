"""
Seed normalization vocabulary for GO DESi Consumer Insights.

Two things per field:
  CANONICAL[field]  -> ordered list of the "clean" category labels (dropdown
                        options). These are what charts group by, and what the
                        Review tab offers in its "map to" dropdown.
  ALIASES[field]    -> dict of {lowercased raw value : canonical label}. Seeded
                        from the messy variants actually seen in the sheets so
                        day-one unmapped count is small.

Anything not matched by canonical or alias falls into the "Unmapped" bucket and
shows up in the Review tab. Approving there appends to the *live* Mappings sheet
(see gsheets.py), which is layered on top of these seeds at runtime.

Special canonical values:
  "Not answered"  -> genuine non-answers (kept as a visible slice; not charted
                     as a real preference but not silently dropped either).
  Use the Review tab's "Ignore (drop)" to route junk here permanently.
"""

DROP = "Not answered"   # canonical sink for junk / non-answers

# =====================================================================
# SHARED FIELDS
# =====================================================================

CANONICAL = {}
ALIASES = {}

# ---- Age ----
CANONICAL["age"] = ["Under 20", "20-29", "30-39", "40-49", "50-59", DROP]
ALIASES["age"] = {
    "below 18": "Under 20",
    "under 20": "Under 20",
    "don't know": DROP,
    "dont know": DROP,
    "n/a": DROP,
    "not responded": DROP,
}

# ---- Gender ----
CANONICAL["gender"] = ["Male", "Female", DROP]
ALIASES["gender"] = {
    "m": "Male", "male": "Male",
    "f": "Female", "female": "Female",
    "n/a": DROP, "not responded": DROP,
}

# ---- Heard when ----
CANONICAL["heard_when"] = [
    "Just recently (past month)", "3-6 months", "About a year ago",
    "More than a year ago", DROP,
]
ALIASES["heard_when"] = {
    "just recently (the past month)": "Just recently (past month)",
    "3-6 months": "3-6 months",
    "about a year ago": "About a year ago",
    "more than a year ago": "More than a year ago",
    "i don't remember": DROP,
    "i dont remember": DROP,
}

# ---- Discovery channel (shared) ----
CANONICAL["discovery"] = [
    "Instagram", "Facebook", "YouTube", "Word of mouth", "Corporate gifting",
    "In-store / offline", "Quick commerce", "E-commerce", "GO DESi website",
    "Shark Tank", "Search / online", "Cred", "Restaurant", DROP,
]
ALIASES["discovery"] = {
    "instagram": "Instagram",
    "facebook": "Facebook",
    "youtube": "YouTube",
    "a friend or a family": "Word of mouth",
    "a friend of family member": "Word of mouth",
    "a friend or family member": "Word of mouth",
    "received it as a gift": "Word of mouth",
    "got it as a gift hamper": "Word of mouth",
    "not heard got gift from bro": "Word of mouth",
    "got it as gift from his company": "Corporate gifting",
    "collaboration": "Corporate gifting",
    "collaboration in your company": "Corporate gifting",
    "spotted in a store": "In-store / offline",
    "saw it in a store": "In-store / offline",
    "at resturant": "Restaurant",
    "blinkit/instamart/zepto": "Quick commerce",
    "swiggy instamart": "Quick commerce",
    "amazon/flipkart": "E-commerce",
    "amazon": "E-commerce",
    "go desi website": "GO DESi website",
    "shark tank": "Shark Tank",
    "google": "Search / online",
    "cred": "Cred",
    "cred app": "Cred",
    "got as a gift at an event": "Word of mouth",
    "other": DROP,
    "i don't remember": DROP,
    "i dont remember": DROP,
    "not remember": DROP,
    "she dont remember": DROP,
    "cx dont remember": DROP,
}

# ---- SKU (product family) — handled by keyword matcher, see normalize.py ----
CANONICAL["sku"] = [
    "Imli Popz", "Jamun Popz", "Spices & Jaggery Popz", "Popz Gift Basket",
    "Popz (other)", "Kaju Katli", "Barfi", "Chikki", "Date Bars",
    "Mysore Pak", "Laddoo", "Minis", "Ghevar", "Petha", "Other sweet", DROP,
]
ALIASES["sku"] = {}  # SKU uses keyword matching, not exact alias

# =====================================================================
# POPZ FIELDS
# =====================================================================

CANONICAL["popz_frequency"] = [
    "Daily", "2-3 times a week", "Once a week",
    "Occasionally (when cravings hit)", "First time buying", DROP,
]
ALIASES["popz_frequency"] = {
    "daily": "Daily",
    "2-3 times a week": "2-3 times a week",
    "once a week": "Once a week",
    "occasionally (when cravings hit)": "Occasionally (when cravings hit)",
    "first time buying": "First time buying",
    "not sure": DROP,
}

CANONICAL["popz_moment"] = [
    "After meals", "To curb chatpata cravings", "Whenever they feel like",
    "When bored", "While traveling", "During work / study breaks",
    "While watching content", "Any time", DROP,
]
ALIASES["popz_moment"] = {
    "after meals": "After meals",
    "to curb my chatpata cravings": "To curb chatpata cravings",
    "to curb chatpata cravings": "To curb chatpata cravings",
    "whenever the customer feels like": "Whenever they feel like",
    "when i'm bored": "When bored",
    "while traveling": "While traveling",
    "while travelling": "While traveling",
    "during work/study breaks": "During work / study breaks",
    "while watching content": "While watching content",
    "any time": "Any time",
    "anytime": "Any time",
    "all time": "Any time",
    "in the evening": "After meals",
    "ocassionally": "Whenever they feel like",
    "it depends on mood": DROP,
    "when will get mood": DROP,
    "other": DROP,
}

CANONICAL["popz_perception"] = [
    "Tamarind Pop", "Candy", "Lollipop", "Churan / digestive",
    "Chatpata snack", "Chocolate", "Healthy snack", "Refreshment", DROP,
]
ALIASES["popz_perception"] = {
    "tamrind pop": "Tamarind Pop",
    "tamarind pop": "Tamarind Pop",
    "candy": "Candy",
    "lollipop": "Lollipop",
    "churan": "Churan / digestive",
    "chatpata snack": "Chatpata snack",
    "chocolate": "Chocolate",
    "healthy snack": "Healthy snack",
    "refreshment": "Refreshment",
}

CANONICAL["popz_motivation"] = [
    "Better ingredients", "Guilt-free snacking", "Unique format",
    "Nostalgic vibes", "Chatpata cravings", "Fun to eat", "Good taste",
    "Good quality", "Just wanted to try", DROP,
]
ALIASES["popz_motivation"] = {
    "better ingredients": "Better ingredients",
    "natural": "Better ingredients",
    "guilt free snacking": "Guilt-free snacking",
    "guilt-free snacking": "Guilt-free snacking",
    "unique format": "Unique format",
    "nostalgic vibes": "Nostalgic vibes",
    "chapati cravings": "Chatpata cravings",       # known typo
    "chatpata cravings": "Chatpata cravings",
    "fun to eat": "Fun to eat",
    "taste": "Good taste",
    "quality is good": "Good quality",
    "good packaging": "Good quality",
    "just wanted to try": "Just wanted to try",
    "she just wanted to give it a try": "Just wanted to try",
    "he just wanted to give it a try": "Just wanted to try",
}

CANONICAL["sweets_linkage"] = ["Yes", "No", DROP]
ALIASES["sweets_linkage"] = {"yes": "Yes", "no": "No"}

# =====================================================================
# MEETHA FIELDS
# =====================================================================

CANONICAL["sweets_frequency"] = [
    "Daily", "2-3 times a week", "Once a week",
    "Occasionally (when cravings hit)", "First time buying", DROP,
]
ALIASES["sweets_frequency"] = {
    "daily": "Daily",
    "2-3 times a week": "2-3 times a week",
    "once a week": "Once a week",
    "occasionally (when cravings hit)": "Occasionally (when cravings hit)",
    "first time buying": "First time buying",
    "not sure": DROP,
    "never": DROP,
    "childhood memories": DROP,
}

CANONICAL["sweets_moment"] = [
    "After meals as dessert", "To curb sweet cravings",
    "During special occasions", "Festivals", "As a snack with tea / coffee",
    "While traveling", "When bored", "While watching content",
    "During work / study breaks", "Stress relief / mood", DROP,
]
ALIASES["sweets_moment"] = {
    "after meals as dessert": "After meals as dessert",
    "after meals as a dessert": "After meals as dessert",
    "after dinner": "After meals as dessert",
    "to curb my sweet cravings": "To curb sweet cravings",
    "during special occasions": "During special occasions",
    "festivals": "Festivals",
    "as a snack with tea/coffee": "As a snack with tea / coffee",
    "while traveling": "While traveling",
    "while travelling": "While traveling",
    "when i'm bored": "When bored",
    "boredom": "When bored",
    "while watching content(netflix, tv, amazon prime, sports)": "While watching content",
    "while watching content": "While watching content",
    "during work/study breaks": "During work / study breaks",
    "stress relief/mood upliftment": "Stress relief / mood",
    "hunger": DROP,
    "when required": DROP,
    "depends on mood": DROP,
    "no such specific timing": DROP,
    "she dont prefer sweets anymore": DROP,
    "for gifting purpose": "During special occasions",
}

# Brand vocabulary shared across the three brand fields
_BRANDS = [
    "GO DESi", "Haldiram's", "Amul", "Bikanervala", "Anand Sweets",
    "Daadi's", "Kanti Sweets", "Nandini Sweets", "Bhikharam Chandmal",
    "Lal", "Farmley", "MTR", "A2B", "Karachi Bakery",
    "Local / unbranded", "Prefers whatever's convenient", DROP,
]
_BRAND_ALIASES = {
    "go desi": "GO DESi", "godesi": "GO DESi", "only go desi": "GO DESi",
    "haldiram's": "Haldiram's", "haldirams": "Haldiram's", "haldiram": "Haldiram's",
    "amul": "Amul",
    "bikanervala": "Bikanervala", "bikaner": "Bikanervala", "bikano": "Bikanervala",
    "bikaji": "Bikanervala", "bikaji sweets": "Bikanervala",
    "anand sweets": "Anand Sweets", "anand": "Anand Sweets",
    "daadi's": "Daadi's", "daadi": "Daadi's", "daadis": "Daadi's",
    "kanti sweets": "Kanti Sweets", "kanthi": "Kanti Sweets",
    "nandini sweets": "Nandini Sweets", "nandini": "Nandini Sweets",
    "bhikharam chandmal & co.": "Bhikharam Chandmal", "bhikharam": "Bhikharam Chandmal",
    "lal": "Lal",
    "farmley": "Farmley",
    "mtr": "MTR", "a2b": "A2B",
    "karachi": "Karachi Bakery",
    "prefers whatever's convenient": "Prefers whatever's convenient",
    "not aware of brands": DROP,
    "not aware of any brands": DROP,
    "dont remember any brands": DROP,
    "na": DROP, "depends": DROP, "not sure": DROP,
    "disconnected in mid of the call": DROP,
}
# local-brand keyword catch handled in normalize.py

for _f in ("brand_awareness", "top3_recall", "brand_preference"):
    CANONICAL[_f] = list(_BRANDS)
    ALIASES[_f] = dict(_BRAND_ALIASES)

CANONICAL["sweet_format"] = [
    "Kaju Katli", "Barfi", "Mysore Pak", "Laddoo", "Rasgulla", "Peda",
    "Chikki", "Gulab Jamun", "Rasmalai", "Jalebi", "Halwa",
    "Other format", DROP,
]
ALIASES["sweet_format"] = {
    "kaju katli": "Kaju Katli",
    "barfi": "Barfi", "pista cocnut barfi from godesi": "Barfi",
    "mysore pak": "Mysore Pak",
    "ladoo's": "Laddoo", "ladoo": "Laddoo", "laddu": "Laddoo",
    "rasgula's": "Rasgulla", "rasgulla": "Rasgulla",
    "peda's": "Peda", "peda": "Peda",
    "chikki": "Chikki",
    "gulab jamun": "Gulab Jamun",
    "rasmalai": "Rasmalai",
    "jilebee": "Jalebi", "jalebi": "Jalebi",
    "halwa": "Halwa",
    "nothing such specific": DROP,
    "no such specific sweets": DROP,
    "for this question he hung up the call": DROP,
}

# SKU keyword -> product family (substring match, order matters: specific first)
# Covers BOTH Popz SKUs (candy/imli/jamun) and Meetha SKUs (katli/barfi/etc.)
SKU_KEYWORDS = [
    # --- Popz families ---
    ("imli", "Imli Popz"), ("tamarind", "Imli Popz"),
    ("jamun", "Jamun Popz"),
    ("spices & jaggery", "Spices & Jaggery Popz"),
    ("gift basket", "Popz Gift Basket"),
    ("popz gift", "Popz Gift Basket"),
    ("popz", "Popz (other)"),
    # --- Meetha families ---
    ("minis", "Minis"),
    ("kaju katli", "Kaju Katli"),
    ("kaju kishmish", "Barfi"),
    ("coconut barfi", "Barfi"),
    ("coconut burfi", "Barfi"),
    ("pista coconut", "Barfi"),
    ("pista barfi", "Barfi"),
    ("badam & cashews", "Barfi"),
    ("cashews and raisins", "Barfi"),
    ("barfi", "Barfi"), ("burfi", "Barfi"),
    ("chikki", "Chikki"),
    ("date bar", "Date Bars"), ("date bars", "Date Bars"),
    ("anjeer", "Date Bars"), ("dates", "Date Bars"),
    ("mysore pak", "Mysore Pak"),
    ("laddoo", "Laddoo"), ("laddu", "Laddoo"), ("ladoo", "Laddoo"),
    ("ghevar", "Ghevar"),
    ("petha", "Petha"),
    ("katli", "Kaju Katli"),
]

# local-brand keyword catch for brand fields
LOCAL_BRAND_KEYWORDS = [
    "local", "sweet shop", "sweet stall", "almond house", "rajpurohit",
    "agarwal", "asha", "tiwari", "tewari", "vijaya", "india sweet house",
]
