#!/usr/bin/env python3
"""
Tarot card tag generator v2.
Reads all 78 card .txt files, generates themes/keywords/symbols/summary,
adds astrological data, writes one JSON tag file per card + master index.
"""

import json, re
from pathlib import Path
from collections import Counter

CARD_DIR = Path(__file__).parent.parent / "cards"
TAGS_DIR = Path(__file__).parent.parent / "tags"
ASTRO_FILE = TAGS_DIR / "astrological-correspondences.json"
TAGS_DIR.mkdir(exist_ok=True)

def load_astro():
    with open(ASTRO_FILE) as f:
        data = json.load(f)
    flat = {}
    for cid, info in data.get("major", {}).items():
        flat[cid] = info["primary"]
    for group in data.get("minor", {}).values():
        if isinstance(group, dict):
            for cid, info in group.items():
                if not cid.startswith("_"):
                    flat[cid] = f"{info['planet']} in {info['sign']}"
    for cid in data.get("aces", {}).keys():
        flat[cid] = None
    for group in data.get("court", {}).values():
        if isinstance(group, dict):
            for cid, info in group.items():
                if not cid.startswith("_"):
                    flat[cid] = info["primary"]
    return flat

ASTRO = load_astro()

def read_cards():
    cards = []
    for subdir in ["major", "minor", "court"]:
        sub = Path(CARD_DIR) / subdir
        if not sub.exists():
            continue
        for f in sorted(sub.glob("*.txt")):
            text = f.read_text(errors="replace")
            m = re.match(r'^---\n(.*?)\n---\n(.*)', text, re.DOTALL)
            if not m:
                continue
            front_raw, body = m.groups()
            front = {}
            for line in front_raw.splitlines():
                if ':' in line:
                    k, v = line.split(':', 1)
                    front[k.strip()] = v.strip().strip('"').strip("'")
            sections = {}
            current_title = None
            current_text = []
            for line in body.splitlines():
                bm = re.match(r'^\*\*([^\*]+)\*\*:?\s*$', line.strip())
                if bm:
                    title = bm.group(1).strip().replace(':', '')
                    if current_title:
                        sections[current_title.lower().replace(" ", "_")] = "\n".join(current_text).strip()
                    current_title = title
                    current_text = []
                else:
                    current_text.append(line)
            if current_title:
                sections[current_title.lower().replace(" ", "_")] = "\n".join(current_text).strip()
            cards.append({
                "card_id":     front.get("card_id", f.stem),
                "card_name":   front.get("card_name", f.stem),
                "card_type":   front.get("card_type", subdir),
                "suit":        front.get("suit", ""),
                "card_number": front.get("card_number", "") or front.get("court_position", ""),
                "sections":     sections,
            })
    return cards

STOPWORDS = set("""
the a an and or but is was were be been being have has had it its this that these
those i you he she we they what which who when where why how all each every both
some any no nor not only own same so than too very just can will could should would
may might must shall need do does did making made go going went gone come coming
came take took taken see saw seen look looked getting got become became feel felt
feeling think thought thinking know knew known remember remembered hold held holding
let being seem seemed seeming give gave given show showed shown tell told ask asked
asking answer answers reply replies say said want wanted wanting need needing use
used using find found into through during before after above below between under
within without along around about over out off down up from to upon because for
at by with if while although though unless until as even since however still anyway
therefore hence thus whenever wherever whetherwhichever something nothing everything
everyone anyone someone no one each other such many much few little big large small
tall short new old young good bad better best worst first last next previous current
latter other another same different similar whole part end ends tends also even most
least more less quite fairly rather well very too extremely almost nearly already yet
still always never often usually certainly perhaps possibly probably actually really
basically essentially simply exactly especially particularly specifically generally
typically apparently clearly obviously surely maybe merely cards card arcana major minor
court upright reversed meaning meanings querent reading readings position there here
where when what why how which whose whom across behind beyond inside outside under
over above beneath beside around through during after before within without alongside
amid amongst onto opposite toward towards pursuant regarding concerning according
following due regard considering forward subsequent prior earlier later further rather
quite fairly pretty somewhat many several both either neither each every any other
another identical comparable equal equivalent unlike opposite reverse contrary inverse
converse despite notwithstanding although though even if while whereas since because
provided assuming whether once whenever unless until whatever whatsoever whenever
whatever wherever whichever however are was were been being have has had do does did
shall will would could should may might must need dare ought cares worries want wishes
desires feels felt think thoughts thought knows knew remembers recall sees saw looked
seems seemed becoming became becomes make makes made do does done undo undoes creating
created creates go goes going came bring brings brought take takes took taking get
gets got keep keeps kept let letting put puts putting set giving give gives gave call
called asking answer send sends sent receive receives write wrote written learn hears
heard listen spending spend cost costing pay pays paid stay remained turn become become
becomes becoming begin begins began finish finishes ended leave left staying stop
stopped hold carries carry win won lose lost lead leads led follow meets meeting choose
chose select picks picked try tried attempt attempts work plays played move moves changed
change shift turned open opens close closes start started begin begins show showed hide
hides found discover realizes look feels touch grabbed pull pulls push pushes build built
create makes break broke fixed repair cleaned fill filled empty poured lift raises raise
lower drop falls fallen rise rose make letting allow allow stop keep hold try work need
want wish hope expect they them their yours yourself himself herself itself mine my our
us we me i him his she her hers it its they're them who've who'd who'd've that'll
would've isn't aren't wasn't weren't wasn't weren't won't wouldn't can't couldn't shouldn't
mightn't mustn't let's that's who'd who'd've she'll he'll they'll would've we've they've
would've i'd he'd she'd would've shouldn't doesn't wasn't weren't won't wouldn't can't
couldn't shouldn't may might must need dare ought cares worries wants wishes desires hopes
expects tries works needs wants wishes desires hopes expects working need needing want
wanting doesn't wasn't weren't won't wouldn't can't couldn't shouldn't may might must need
""".split())

THEME_WORDS = {
    "endings":         ["end","ending","ended","over","conclude","conclusion","finish","finished","close","closure","final","ultimately"],
    "beginnings":      ["new","beginning","start","starting","fresh","first","initial","dawn","initiate","initiation"],
    "love":            ["love","loving","loved","lover","romance","romantic","passion","heart","affection","desire","intimacy","couple","relationship","partner"],
    "conflict":        ["conflict","fight","fighting","battle","war","argue","argument","dispute","tension","opposition","opponent","enemy","struggle"],
    "money":           ["money","financial","finance","wealth","rich","cash","income","salary","bank","investment","business","prosper"],
    "career":          ["career","job","profession","vocation","ambition","success","promotion","office","coworker"],
    "health":          ["health","illness","sick","disease","healing","recovery","body","physical","medical","doctor"],
    "spiritual":       ["spiritual","soul","spirit","divine","sacred","prayer","meditation","higher self","god","deity"],
    "transformation":  ["transform","change","changing","changed","shift","evolve","evolution","grow","growth","rebirth","metamorphosis"],
    "fear":            ["fear","afraid","scared","anxiety","anxious","worried","worry","terror","phobia","dread","nightmare"],
    "creativity":      ["create","creative","creation","art","artist","imagination","inspired","inspiration"],
    "communication":   ["communicate","communication","speak","speaking","spoke","talk","talking","word","words","message","conversation"],
    "intuition":       ["intuition","intuitive","gut","instinct","instinctive","inner voice","sixth sense","premonition"],
    "family":          ["family","home","children","child","parent","mother","father","sibling","brother","sister"],
    "travel":          ["travel","traveling","journey","trip","voyage","adventure","abroad","overseas","moving","movement"],
    "decision":        ["decision","decide","choosing","choice","choose","dilemma","options","alternative"],
    "loss":            ["loss","lost","lose","grief","grieving","mourn","mourning","death","dying","sadness"],
    "hope":            ["hope","hopeful","optimism","optimistic","inspiring","encouragement","encouraging"],
    "betrayal":        ["betray","betrayal","deception","deceive","lie","lying","cheat","cheating","unfaithful","treachery"],
    "shadow":          ["shadow","dark","darkness","hidden","subconscious","unconscious","shadow self","repression"],
    "legal":           ["legal","law","lawsuit","court","judge","judicial","attorney","lawyer","contract","agreement"],
    "education":       ["study","studying","learn","learning","education","teacher","student","school","college","course"],
    "isolation":       ["alone","solitude","lonely","isolation","withdraw","withdrawal","secluded","exile"],
    "creativity_block":["creative block","stuck","blocked","procrastination","unmotivated","resistance"],
    "luxury":          ["luxury","luxuries","comfort","comfortable","indulgence","opulence","wealthy","lavish"],
    "joy":             ["joy","joyful","happiness","happy","pleasure","delight","celebrate","celebration"],
    "control":         ["control","controlling","controlled","power","powerful","dominate","dominance","authority"],
    "commitment":      ["commit","commitment","committed","devotion","dedication","faithful","faithfulness"],
    "fertility":       ["fertility","fertile","pregnancy","pregnant","childbearing","childbirth"],
    "ambition":        ["ambition","ambitious","driven","aspiration","aspirational","goal","goals"],
    "nostalgia":       ["nostalgia","nostalgic","past","memories","memory","remember","remembers","childhood","innocence"],
    "anger":           ["anger","angry","rage","frustration","frustrated","irritation","irritated","resentment"],
    "freedom":         ["freedom","free","liberation","liberate","liberated","escape","independent","independence"],
    "deception":       ["deception","deceptive","illusion","illusionary","false","falseness","mislead","misleading"],
    "stagnation":      ["stagnation","stagnant","stuck","idle","inactive","inactivity","complacent","complacency"],
    "revelation":      ["revelation","revelations","revelatory","awakening","awakened","truth revealed","reveal"],
}

SYMBOL_PATTERNS = {
    "skeleton":        ["skeleton","skeletal"],
    "white horse":     ["white horse"],
    "scythe":          ["scythe"],
    "crown":           ["crown"],
    "sword":           ["sword","swords"],
    "scales":          ["scales","scale"],
    "chalice":         ["chalice","cup","cups"],
    "wand":            ["wand","wands","rod","staff","staves"],
    "pentacle":        ["pentacle","pentacles","coin","coins","disk","disks"],
    "moon":            ["moon","lunar","crescent"],
    "sun":             ["sun","solar"],
    "star":            ["star","stars","stellar","starlight"],
    "angel":           ["angel"],
    "serpent":         ["serpent","snake"],
    "wolf":            ["wolf","wolves","dog","hound"],
    "lion":            ["lion","lioness"],
    "eagle":           ["eagle","eagles"],
    "child":           ["child","children","kid","kids"],
    "water":           ["water","sea","ocean","river","wave","waves","lake","pond"],
    "fire":            ["fire","flame","flames","blazing"],
    "tower":           ["tower","castle","spire"],
    "path":            ["path","paths","road","roads","way"],
    "chains":          ["chain","chains","chained"],
    "mountain":        ["mountain","mountains","hill","hills","peak","peaks"],
    "tree":            ["tree","trees","oak","elm","branch"],
    "rose":            ["rose","roses"],
    "heart":           ["heart","hearts"],
    "mirror":          ["mirror"],
    "key":             ["key","keys"],
    "ring":            ["ring","rings"],
    "veil":            ["veil"],
    "cloak":           ["cloak"],
    "lantern":         ["lantern","lamp"],
    "wheel":           ["wheel","wheels"],
    "bird":            ["bird","birds","raven","dove"],
    "butterfly":       ["butterfly"],
    "flowers":         ["flower","flowers","blossom","bloom"],
    "clouds":          ["cloud","clouds"],
    "graveyard":       ["grave","graveyard","graves"],
}

def extract_themes(text):
    text_lower = text.lower()
    found = []
    for theme, triggers in THEME_WORDS.items():
        score = sum(1 for t in triggers if t in text_lower)
        if score > 0:
            found.append((theme, score))
    found.sort(key=lambda x: -x[1])
    return [t[0] for t in found[:8]]

def extract_symbols(text):
    text_lower = text.lower()
    found = []
    for sym, patterns in SYMBOL_PATTERNS.items():
        if any(p in text_lower for p in patterns):
            found.append(sym)
    return list(dict.fromkeys(found))[:10]

def extract_keywords(text, card_name):
    text_lower = text.lower()
    name_words = {w.strip('.,') for w in card_name.lower().split()}
    tarot_noise = {"card","arcana","major","minor","court","upright","reversed",
                   "meaning","meanings","querent","reading","readings","position"}
    all_noise = STOPWORDS | name_words | tarot_noise
    words = re.findall(r'\b[a-z]{3,20}\b', text_lower)
    filtered = [w for w in words if w not in all_noise]
    seen = set()
    unique = []
    for w, _ in Counter(filtered).most_common(80):
        if w not in seen:
            seen.add(w)
            unique.append(w)
    return unique[:15]

def build_summary(sections, card_name):
    upright = sections.get("upright_meaning", "") or sections.get("upright", "")
    upright = re.sub(r'\s+', ' ', upright).strip()
    if upright:
        sentences = [s.strip() for s in upright.split('.') if 25 < len(s.strip()) < 135]
        if sentences:
            return (sentences[0] + '.').strip()
    if upright:
        words = upright.split()[:30]
        result = ' '.join(words)
        if not result.endswith('.'):
            result = result.rsplit(' ', 1)[0] + '...'
        return result
    return card_name + " — tarot card from aeclectic.net."

def build_tag(card):
    all_text = ' '.join(v for v in card["sections"].values() if v)
    return {
        "card_id":       card["card_id"],
        "card_name":     card["card_name"],
        "card_type":     card["card_type"],
        "suit":          card["suit"] or None,
        "card_number":   card["card_number"] or None,
        "astrological":  ASTRO.get(card["card_id"]),
        "themes":        extract_themes(all_text),
        "keywords":      extract_keywords(all_text, card["card_name"]),
        "symbols":       extract_symbols(all_text),
        "brief_summary": build_summary(card["sections"], card["card_name"]),
    }

def main():
    cards = read_cards()
    print(f"Read {len(cards)} cards")
    all_tags = {}
    for i, card in enumerate(cards, 1):
        tags = build_tag(card)
        all_tags[tags["card_id"]] = tags
        out_path = TAGS_DIR / f"{tags['card_id']}.json"
        with open(out_path, "w") as f:
            json.dump(tags, f, indent=2)
        astro_str = f"astro={tags['astrological']}" if tags['astrological'] else "astro=null"
        print(f"  [{i:02d}/78] {tags['card_id']}: {len(tags['themes'])} themes | {len(tags['symbols'])} sym | {astro_str}")

    index = {
        "total_cards": len(all_tags),
        "by_type": {
            "major": sorted([c["card_id"] for c in cards if c["card_type"] == "major"]),
            "minor": sorted([c["card_id"] for c in cards if c["card_type"] == "minor"]),
            "court": sorted([c["card_id"] for c in cards if c["card_type"] == "court"]),
        },
        "files": {cid: f"{cid}.json" for cid in sorted(all_tags.keys())},
    }
    with open(TAGS_DIR / "index.json", "w") as f:
        json.dump(index, f, indent=2)
    print(f"\nDone! {len(all_tags)} tag files -> {TAGS_DIR}")

if __name__ == "__main__":
    main()
