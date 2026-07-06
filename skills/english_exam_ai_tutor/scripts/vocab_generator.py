#!/usr/bin/env python3
"""Vocabulary pool generator for English Exam AI Tutor.

Generates structured vocabulary JSON files for CET-4, CET-6, Postgraduate,
TEM-4, and TEM-8 from an embedded word database.

Usage:
  python vocab_generator.py --all          # generate all vocabulary files
  python vocab_generator.py --level CET4   # generate CET-4 only
  python vocab_generator.py --validate     # validate existing files against schema
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCAB_DIR = ROOT / "assets" / "data" / "vocabulary"
SCHEMA_DIR = ROOT / "assets" / "schemas"


# ── Utility functions ────────────────────────────────────────────────────

def load_schema() -> dict:
    schema_path = SCHEMA_DIR / "vocab-entry.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_entry(entry: dict, schema: dict) -> list[str]:
    """Validate a single vocab entry against schema. Returns list of errors."""
    errors = []
    required = schema.get("required", [])
    for field in required:
        if field not in entry:
            errors.append(f"缺少必填字段: {field}")
    if "word" in entry and (not entry["word"] or not isinstance(entry["word"], str)):
        errors.append(f"word 必须是非空字符串: {entry.get('word')!r}")
    if "meaning_cn" in entry and (not entry["meaning_cn"] or not isinstance(entry["meaning_cn"], str)):
        errors.append(f"meaning_cn 必须是非空字符串: {entry.get('meaning_cn')!r}")
    if "frequency_rank" in entry:
        fr = entry["frequency_rank"]
        if not isinstance(fr, int) or fr < 1:
            errors.append(f"frequency_rank 必须是 >= 1 的整数: {fr!r}")
    if "cet_level" in entry:
        valid = {"CET4", "CET6", "POSTGRADUATE", "TEM4", "TEM8"}
        if entry["cet_level"] not in valid:
            errors.append(f"cet_level 不在合法值内: {entry['cet_level']!r}")
    return errors


def write_json(data: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")


# ── Embedded word database ────────────────────────────────────────────────
# Compact format: (word, phonetic, pos, meaning_cn, rank, example, colloc, syn, confusable)
# Fields after rank can be empty string/list.

_WORDS_CET4 = [
    ("abandon", "/əˈbændən/", "v.", "放弃；抛弃；遗弃", 1, "They had to abandon the sinking ship.",
     ["abandon oneself to", "abandon a plan"], ["give up", "desert", "forsake"], ["abundant"]),
    ("ability", "/əˈbɪləti/", "n.", "能力；才能", 2, "She has the ability to learn quickly.",
     ["have the ability to", "to the best of one's ability"], ["capability", "capacity", "talent"], []),
    ("abroad", "/əˈbrɔːd/", "adv.", "在国外；到国外", 3, "He went abroad for further study.",
     ["go abroad", "study abroad", "from abroad"], ["overseas"], ["aboard"]),
    ("absence", "/ˈæbsəns/", "n.", "缺席；缺乏", 4, "In the absence of evidence, the case was dropped.",
     ["in the absence of", "absence from"], ["lack", "shortage"], ["presence"]),
    ("absolute", "/ˈæbsəluːt/", "adj.", "绝对的；完全的", 5, "He demanded absolute obedience.",
     ["absolute power", "absolute certainty"], ["total", "complete", "utter"], ["relative"]),
    ("absorb", "/əbˈzɔːb/", "v.", "吸收；吸引", 6, "Plants absorb carbon dioxide.",
     ["absorb knowledge", "be absorbed in"], ["soak up", "take in", "assimilate"], []),
    ("abstract", "/ˈæbstrækt/", "adj.", "抽象的；摘要", 7, "The concept is too abstract to grasp.",
     ["abstract concept", "abstract art"], ["theoretical", "conceptual"], ["concrete"]),
    ("abundant", "/əˈbʌndənt/", "adj.", "丰富的；充裕的", 8, "The region has abundant natural resources.",
     ["abundant in", "abundant resources"], ["plentiful", "ample", "rich"], ["scarce"]),
    ("abuse", "/əˈbjuːz/", "v./n.", "滥用；虐待", 9, "He abused his power as manager.",
     ["drug abuse", "abuse of power", "child abuse"], ["misuse", "mistreat", "exploit"], []),
    ("academic", "/ˌækəˈdemɪk/", "adj.", "学术的；学院的", 10, "She has an impressive academic record.",
     ["academic year", "academic research", "academic performance"], ["scholarly", "educational"], []),
    ("accelerate", "/əkˈseləreɪt/", "v.", "加速；促进", 11, "The car accelerated smoothly.",
     ["accelerate growth", "accelerate the pace"], ["speed up", "hasten", "quicken"], ["decelerate"]),
    ("access", "/ˈækses/", "n./v.", "进入；访问；通道", 12, "Students have access to the library.",
     ["have access to", "internet access", "gain access"], ["entry", "admission", "approach"], []),
    ("accommodate", "/əˈkɒmədeɪt/", "v.", "容纳；适应；提供住宿", 13, "The hotel can accommodate 200 guests.",
     ["accommodate needs", "accommodate to"], ["house", "hold", "adjust"], []),
    ("accompany", "/əˈkʌmpəni/", "v.", "陪伴；伴随", 14, "She accompanied me to the station.",
     ["be accompanied by", "accompany on piano"], ["escort", "go with", "attend"], []),
    ("accomplish", "/əˈkɒmplɪʃ/", "v.", "完成；实现", 15, "We accomplished our goal ahead of schedule.",
     ["accomplish a task", "accomplish a mission"], ["achieve", "complete", "fulfill"], []),
    ("account", "/əˈkaʊnt/", "n./v.", "账户；说明；解释", 16, "Please give an account of what happened.",
     ["take into account", "on account of", "bank account"], ["explanation", "report", "description"], ["count"]),
    ("accumulate", "/əˈkjuːmjəleɪt/", "v.", "积累；积聚", 17, "Dust accumulated on the shelves.",
     ["accumulate wealth", "accumulate experience"], ["gather", "amass", "build up"], []),
    ("accurate", "/ˈækjərət/", "adj.", "准确的；精确的", 18, "The measurements were highly accurate.",
     ["accurate description", "accurate measurement"], ["precise", "exact", "correct"], ["inaccurate"]),
    ("achieve", "/əˈtʃiːv/", "v.", "实现；达到", 19, "She achieved her dream of becoming a doctor.",
     ["achieve success", "achieve a goal"], ["attain", "accomplish", "reach"], []),
    ("acknowledge", "/əkˈnɒlɪdʒ/", "v.", "承认；确认收到", 20, "He acknowledged his mistake publicly.",
     ["acknowledge receipt", "acknowledge the fact"], ["admit", "recognize", "confess"], []),
    ("acquire", "/əˈkwaɪə/", "v.", "获得；习得", 21, "She acquired a good knowledge of French.",
     ["acquire knowledge", "acquire skills"], ["obtain", "gain", "get"], ["require", "inquire"]),
    ("adapt", "/əˈdæpt/", "v.", "适应；改编", 22, "Animals adapt to their environment.",
     ["adapt to", "adapt from"], ["adjust", "modify", "alter"], ["adopt", "adept"]),
    ("adequate", "/ˈædɪkwət/", "adj.", "足够的；适当的", 23, "The supply is adequate for our needs.",
     ["adequate supply", "adequate for"], ["sufficient", "enough", "suitable"], ["inadequate"]),
    ("adjust", "/əˈdʒʌst/", "v.", "调整；适应", 24, "You can adjust the volume with this knob.",
     ["adjust to", "adjust accordingly"], ["modify", "alter", "adapt"], []),
    ("administration", "/ədˌmɪnɪˈstreɪʃn/", "n.", "管理；行政", 25, "The administration announced new policies.",
     ["business administration", "public administration"], ["management", "government", "authority"], []),
    ("admire", "/ədˈmaɪə/", "v.", "钦佩；赞赏", 26, "I admire her courage and determination.",
     ["admire for", "admire the view"], ["respect", "appreciate", "look up to"], []),
    ("adopt", "/əˈdɒpt/", "v.", "采纳；收养", 27, "The committee adopted the proposal unanimously.",
     ["adopt a child", "adopt a policy", "adopt a method"], ["take on", "embrace", "accept"], ["adapt", "adept"]),
    ("advance", "/ədˈvɑːns/", "v./n.", "前进；进步；提前", 28, "Technology has advanced rapidly.",
     ["in advance", "advance payment", "advance warning"], ["progress", "proceed", "move forward"], ["retreat"]),
    ("advantage", "/ədˈvɑːntɪdʒ/", "n.", "优势；有利条件", 29, "Being tall gave him an advantage in basketball.",
     ["take advantage of", "competitive advantage"], ["benefit", "edge", "superiority"], ["disadvantage"]),
    ("advertise", "/ˈædvətaɪz/", "v.", "做广告；宣传", 30, "They advertised the product on social media.",
     ["advertise for", "advertise online"], ["promote", "publicize", "market"], []),
    ("affair", "/əˈfeə/", "n.", "事务；事件", 31, "The meeting dealt with financial affairs.",
     ["foreign affairs", "state of affairs", "love affair"], ["matter", "business", "concern"], []),
    ("affect", "/əˈfekt/", "v.", "影响；感动", 32, "The weather affects crop yields significantly.",
     ["be affected by", "adversely affect"], ["influence", "impact", "have an effect on"], ["effect"]),
    ("afford", "/əˈfɔːd/", "v.", "负担得起；提供", 33, "I can't afford a new car right now.",
     ["can afford", "cannot afford", "afford to"], ["manage", "spare", "provide"], []),
    ("aggressive", "/əˈɡresɪv/", "adj.", "侵略的；好斗的；积极的", 34, "The company adopted an aggressive marketing strategy.",
     ["aggressive behavior", "aggressive expansion"], ["hostile", "combative", "assertive"], ["passive"]),
    ("agreement", "/əˈɡriːmənt/", "n.", "协议；一致", 35, "Both parties signed the agreement.",
     ["reach an agreement", "in agreement with"], ["contract", "deal", "accord"], ["disagreement"]),
    ("agriculture", "/ˈæɡrɪkʌltʃə/", "n.", "农业", 36, "Agriculture is vital to the economy.",
     ["agriculture industry", "modern agriculture"], ["farming", "cultivation"], []),
    ("aim", "/eɪm/", "n./v.", "目标；瞄准；旨在", 37, "The program aims to reduce poverty.",
     ["aim at", "aim to", "take aim"], ["goal", "target", "objective", "purpose"], []),
    ("alcohol", "/ˈælkəhɒl/", "n.", "酒精；酒", 38, "The driver had consumed alcohol.",
     ["alcohol abuse", "alcohol consumption"], ["liquor", "spirits"], []),
    ("alert", "/əˈlɜːt/", "adj./v.", "警觉的；提醒", 39, "The alarm alerted everyone to the danger.",
     ["on alert", "stay alert", "alert to"], ["warn", "notify", "vigilant"], []),
    ("allow", "/əˈlaʊ/", "v.", "允许；准许", 40, "Smoking is not allowed in this building.",
     ["allow for", "allow to", "be allowed to"], ["permit", "let", "authorize"], ["forbid"]),
]

_WORDS_CET6 = [
    ("abnormal", "/æbˈnɔːml/", "adj.", "反常的；异常的", 1, "The test results were abnormal.",
     ["abnormal behavior", "abnormal condition"], ["unusual", "irregular", "atypical"], ["normal"]),
    ("abolish", "/əˈbɒlɪʃ/", "v.", "废除；废止", 2, "Slavery was abolished in the 19th century.",
     ["abolish a system", "abolish the death penalty"], ["eliminate", "do away with", "put an end to"], []),
    ("abrupt", "/əˈbrʌpt/", "adj.", "突然的；唐突的", 3, "The meeting came to an abrupt end.",
     ["abrupt change", "abrupt departure"], ["sudden", "unexpected", "sharp"], ["gradual"]),
    ("absurd", "/əbˈsɜːd/", "adj.", "荒谬的；可笑的", 4, "It's absurd to blame me for everything.",
     ["absurd idea", "patently absurd"], ["ridiculous", "preposterous", "ludicrous"], ["reasonable"]),
    ("baffle", "/ˈbæfl/", "v.", "使困惑；难住", 5, "The mystery continues to baffle investigators.",
     ["baffle scientists", "completely baffled"], ["puzzle", "confuse", "perplex"], []),
    ("accessory", "/əkˈsesəri/", "n.", "附件；配件；从犯", 6, "She bought accessories for her new phone.",
     ["fashion accessories", "car accessories"], ["attachment", "add-on", "supplement"], []),
    ("accommodation", "/əˌkɒməˈdeɪʃn/", "n.", "住宿；膳宿", 7, "The university provides student accommodation.",
     ["accommodation facilities", "temporary accommodation"], ["lodging", "housing", "shelter"], []),
    ("accountability", "/əˌkaʊntəˈbɪləti/", "n.", "问责；责任", 8, "The new system improves government accountability.",
     ["public accountability", "personal accountability"], ["responsibility", "answerability", "liability"], []),
    ("acquaint", "/əˈkweɪnt/", "v.", "使熟悉；使认识", 9, "Please acquaint yourself with the rules.",
     ["be acquainted with", "acquaint oneself with"], ["familiarize", "inform", "introduce"], []),
    ("administer", "/ədˈmɪnɪstə/", "v.", "管理；执行；给予", 10, "The nurse administered the vaccine.",
     ["administer justice", "administer a test"], ["manage", "conduct", "dispense"], []),
    ("adolescent", "/ˌædəˈlesnt/", "n./adj.", "青少年；青春期的", 11, "Adolescents often experience rapid mood swings.",
     ["adolescent behavior", "adolescent development"], ["teenager", "youth", "juvenile"], ["adult"]),
    ("adverse", "/ˈædvɜːs/", "adj.", "不利的；相反的", 12, "The drug may have adverse side effects.",
     ["adverse effect", "adverse conditions", "adverse reaction"], ["negative", "harmful", "unfavorable"], ["favorable"]),
    ("advocate", "/ˈædvəkeɪt/", "v./n.", "倡导；提倡者", 13, "He advocates for stricter environmental laws.",
     ["advocate for", "strong advocate", "public advocate"], ["supporter", "champion", "promote"], ["opponent"]),
    ("aesthetic", "/iːsˈθetɪk/", "adj.", "审美的；美学的", 14, "The building has great aesthetic appeal.",
     ["aesthetic value", "aesthetic sense"], ["artistic", "visual", "beautiful"], []),
    ("affirm", "/əˈfɜːm/", "v.", "断言；确认；肯定", 15, "The court affirmed the lower court's decision.",
     ["affirm the right", "affirm commitment"], ["confirm", "declare", "assert"], ["deny"]),
    ("agenda", "/əˈdʒendə/", "n.", "议程；议事日程", 16, "What's on the agenda for today's meeting?",
     ["on the agenda", "hidden agenda", "set the agenda"], ["schedule", "program", "plan"], []),
    ("aggravate", "/ˈæɡrəveɪt/", "v.", "加重；使恶化", 17, "The cold weather aggravated his condition.",
     ["aggravate the situation", "aggravate symptoms"], ["worsen", "intensify", "exacerbate"], ["alleviate"]),
    ("aggregate", "/ˈæɡrɪɡət/", "n./v.", "总计；集合体", 18, "The aggregate cost exceeded the budget.",
     ["in aggregate", "aggregate demand", "aggregate data"], ["total", "sum", "collective"], []),
    ("alienate", "/ˈeɪliəneɪt/", "v.", "疏远；使格格不入", 19, "His behavior alienated his colleagues.",
     ["alienate from", "alienate supporters"], ["estrange", "isolate", "distance"], ["unite", "reconcile"]),
    ("allege", "/əˈledʒ/", "v.", "指控；宣称", 20, "The plaintiff alleges that the contract was breached.",
     ["allege that", "it is alleged that"], ["claim", "assert", "accuse"], []),
]

_WORDS_POSTGRAD = [
    ("abolish", "/əˈbɒlɪʃ/", "v.", "废除；废止", 1, "The law was finally abolished after decades of protest.",
     ["abolish the death penalty", "abolish slavery"], ["eliminate", "annul", "do away with"], []),
    ("abound", "/əˈbaʊnd/", "v.", "充满；大量存在", 2, "Opportunities abound in the tech industry.",
     ["abound in", "abound with"], ["thrive", "flourish", "teem"], ["lack"]),
    ("abstain", "/əbˈsteɪn/", "v.", "弃权；戒除", 3, "Several members abstained from voting.",
     ["abstain from", "abstain from alcohol"], ["refrain", "withhold", "forgo"], ["indulge"]),
    ("acclaim", "/əˈkleɪm/", "v./n.", "称赞；喝彩", 4, "The book was widely acclaimed by critics.",
     ["critically acclaimed", "public acclaim"], ["praise", "applaud", "commend"], ["criticize"]),
    ("accord", "/əˈkɔːd/", "n./v.", "一致；协议；给予", 5, "They reached an accord on trade issues.",
     ["in accord with", "of one's own accord", "peace accord"], ["agreement", "harmony", "grant"], ["discord"]),
    ("accountability", "/əˌkaʊntəˈbɪləti/", "n.", "问责制；责任", 6, "Corporate accountability has improved recently.",
     ["political accountability", "demand accountability"], ["responsibility", "answerability"], []),
    ("acquisition", "/ˌækwɪˈzɪʃn/", "n.", "获得；收购", 7, "The company announced a major acquisition.",
     ["merger and acquisition", "language acquisition"], ["obtaining", "procurement", "takeover"], []),
    ("adhere", "/ədˈhɪə/", "v.", "坚持；遵守；粘附", 8, "All members must adhere to the code of conduct.",
     ["adhere to", "strictly adhere"], ["stick to", "comply with", "follow"], ["deviate"]),
    ("adjacent", "/əˈdʒeɪsnt/", "adj.", "邻近的；毗连的", 9, "The hotel is adjacent to the train station.",
     ["adjacent to", "adjacent rooms"], ["neighboring", "next to", "bordering"], ["distant"]),
    ("administer", "/ədˈmɪnɪstə/", "v.", "管理；执行；给予", 10, "The fund is administered by a board of trustees.",
     ["administer a trust", "administer medication"], ["manage", "execute", "supervise"], []),
    ("adolescence", "/ˌædəˈlesns/", "n.", "青春期", 11, "Adolescence is a time of great change.",
     ["during adolescence", "early adolescence"], ["youth", "teenage years", "puberty"], []),
    ("advent", "/ˈædvent/", "n.", "到来；出现", 12, "The advent of the internet changed everything.",
     ["the advent of", "with the advent of"], ["arrival", "emergence", "dawn"], []),
    ("adversary", "/ˈædvəsəri/", "n.", "对手；敌手", 13, "He faced a formidable adversary in court.",
     ["political adversary", "worthy adversary"], ["opponent", "rival", "enemy"], ["ally"]),
    ("advocacy", "/ˈædvəkəsi/", "n.", "倡导；支持", 14, "She is known for her advocacy of human rights.",
     ["public advocacy", "advocacy group"], ["support", "championship", "promotion"], []),
    ("affiliate", "/əˈfɪlieɪt/", "v./n.", "隶属；附属机构", 15, "The hospital is affiliated with the university.",
     ["affiliated with", "affiliate member"], ["associate", "subsidiary", "branch"], []),
    ("affluent", "/ˈæfluənt/", "adj.", "富裕的；富足的", 16, "They live in an affluent neighborhood.",
     ["affluent society", "affluent family"], ["wealthy", "prosperous", "rich"], ["impoverished"]),
    ("alleviate", "/əˈliːvieɪt/", "v.", "减轻；缓解", 17, "The medicine helped alleviate her pain.",
     ["alleviate suffering", "alleviate poverty"], ["relieve", "ease", "lessen"], ["aggravate"]),
    ("allocate", "/ˈæləkeɪt/", "v.", "分配；拨出", 18, "The government allocated funds for education.",
     ["allocate resources", "allocate to"], ["assign", "distribute", "apportion"], []),
    ("ambiguous", "/æmˈbɪɡjuəs/", "adj.", "模棱两可的；模糊的", 19, "The wording of the contract is ambiguous.",
     ["ambiguous statement", "deliberately ambiguous"], ["vague", "unclear", "equivocal"], ["clear", "unambiguous"]),
    ("amend", "/əˈmend/", "v.", "修改；修正", 20, "The constitution was amended in 2020.",
     ["amend the law", "amend a document"], ["revise", "modify", "correct"], []),
]

_WORDS_TEM4 = [
    ("abdomen", "/ˈæbdəmən/", "n.", "腹部", 1, "The patient complained of pain in the abdomen.",
     ["lower abdomen", "abdomen pain"], ["belly", "stomach", "midsection"], []),
    ("abreast", "/əˈbrest/", "adv.", "并肩地；并排地", 2, "They walked abreast down the street.",
     ["keep abreast of", "walk abreast"], ["alongside", "side by side"], []),
    ("abstinence", "/ˈæbstɪnəns/", "n.", "节制；禁欲", 3, "The program promotes abstinence from alcohol.",
     ["abstinence from", "total abstinence"], ["self-restraint", "temperance", "moderation"], ["indulgence"]),
    ("accede", "/əkˈsiːd/", "v.", "同意；加入；就任", 4, "The government acceded to public demands.",
     ["accede to", "accede to the throne"], ["agree to", "consent to", "comply with"], ["refuse"]),
    ("accentuate", "/əkˈsentʃueɪt/", "v.", "强调；使突出", 5, "The lighting accentuates the architecture.",
     ["accentuate the positive", "accentuate differences"], ["highlight", "emphasize", "stress"], ["minimize"]),
    ("accolade", "/ˈækəleɪd/", "n.", "荣誉；赞扬", 6, "The film received numerous accolades.",
     ["receive accolades", "highest accolade"], ["honor", "award", "praise"], ["criticism"]),
    ("accrue", "/əˈkruː/", "v.", "累积；产生", 7, "Interest accrues on the savings account.",
     ["accrue interest", "benefits accrue"], ["accumulate", "build up", "amass"], []),
    ("acquiesce", "/ˌækwiˈes/", "v.", "默许；勉强同意", 8, "She acquiesced to their request reluctantly.",
     ["acquiesce in", "acquiesce to"], ["consent", "comply", "agree"], ["resist", "oppose"]),
    ("acrimony", "/ˈækrɪməni/", "n.", "尖刻；激烈", 9, "The debate was marked by considerable acrimony.",
     ["with acrimony", "bitter acrimony"], ["bitterness", "hostility", "animosity"], ["civility", "harmony"]),
    ("adamant", "/ˈædəmənt/", "adj.", "坚决的；固执的", 10, "She was adamant about not changing her mind.",
     ["adamant about", "remain adamant"], ["insistent", "unyielding", "firm"], ["flexible"]),
    ("adept", "/əˈdept/", "adj.", "熟练的；擅长的", 11, "He is adept at solving complex problems.",
     ["adept at", "adept in"], ["skilled", "proficient", "expert"], ["inept", "clumsy"]),
    ("admonish", "/ədˈmɒnɪʃ/", "v.", "告诫；劝告", 12, "The teacher admonished the students for being late.",
     ["admonish for", "admonish against"], ["warn", "reprimand", "scold"], ["praise"]),
    ("adorn", "/əˈdɔːn/", "v.", "装饰；装扮", 13, "Flowers adorned the entrance to the hall.",
     ["adorn with", "beautifully adorned"], ["decorate", "ornament", "embellish"], []),
    ("adroit", "/əˈdrɔɪt/", "adj.", "灵巧的；机敏的", 14, "She is an adroit negotiator.",
     ["adroit at", "politically adroit"], ["skillful", "dexterous", "clever"], ["clumsy", "awkward"]),
    ("adulation", "/ˌædʒuˈleɪʃn/", "n.", "奉承；谄媚", 15, "The celebrity was uncomfortable with the adulation.",
     ["public adulation", "receive adulation"], ["flattery", "adoration", "praise"], ["criticism"]),
    ("affable", "/ˈæfəbl/", "adj.", "和蔼的；友善的", 16, "The host was affable and welcoming.",
     ["affable manner", "affable personality"], ["friendly", "amiable", "genial"], ["unfriendly", "cold"]),
    ("agile", "/ˈædʒaɪl/", "adj.", "敏捷的；灵活的", 17, "The gymnast is remarkably agile.",
     ["mentally agile", "agile movement"], ["nimble", "quick", "flexible"], ["clumsy", "stiff"]),
    ("alacrity", "/əˈlækrəti/", "n.", "欣然；乐意", 18, "She accepted the invitation with alacrity.",
     ["with alacrity", "great alacrity"], ["eagerness", "enthusiasm", "willingness"], ["reluctance"]),
    ("allay", "/əˈleɪ/", "v.", "减轻；平息", 19, "The manager tried to allay their fears.",
     ["allay fears", "allay concerns"], ["calm", "relieve", "soothe"], ["intensify", "aggravate"]),
    ("alleviate", "/əˈliːvieɪt/", "v.", "减轻；缓和", 20, "The drug helps alleviate the symptoms.",
     ["alleviate pain", "alleviate poverty"], ["relieve", "ease", "lessen"], ["aggravate", "exacerbate"]),
]

_WORDS_TEM8 = [
    ("abate", "/əˈbeɪt/", "v.", "减弱；减轻", 1, "The storm abated by morning.",
     ["abate pollution", "the rain abated"], ["subside", "diminish", "decrease"], ["intensify"]),
    ("aberration", "/ˌæbəˈreɪʃn/", "n.", "异常；偏差", 2, "The incident was considered an aberration.",
     ["statistical aberration", "temporary aberration"], ["anomaly", "deviation", "irregularity"], ["norm"]),
    ("abject", "/ˈæbdʒekt/", "adj.", "悲惨的；卑下的", 3, "They lived in abject poverty.",
     ["abject poverty", "abject failure", "abject misery"], ["wretched", "miserable", "hopeless"], ["prosperous"]),
    ("abnegation", "/ˌæbnɪˈɡeɪʃn/", "n.", "放弃；自我克制", 4, "Monastic life requires self-abnegation.",
     ["self-abnegation", "abnegation of responsibility"], ["renunciation", "self-denial", "sacrifice"], ["indulgence"]),
    ("abominate", "/əˈbɒmɪneɪt/", "v.", "痛恨；憎恶", 5, "She abominates cruelty to animals.",
     ["abominate violence", "utterly abominate"], ["detest", "loathe", "hate"], ["adore", "love"]),
    ("abrogate", "/ˈæbrəɡeɪt/", "v.", "废除；取消", 6, "The government abrogated the treaty.",
     ["abrogate a law", "abrogate an agreement"], ["abolish", "annul", "repeal"], ["ratify", "uphold"]),
    ("abstemious", "/əbˈstiːmiəs/", "adj.", "有节制的；饮食有度的", 7, "He led an abstemious life.",
     ["abstemious lifestyle", "abstemious diet"], ["moderate", "temperate", "restrained"], ["indulgent"]),
    ("acarpous", "/eɪˈkɑːpəs/", "adj.", "不结果的", 8, "The acarpous tree provided only shade.",
     ["acarpous plant"], ["sterile", "barren", "unfruitful"], ["fruitful", "fertile"]),
    ("acerbic", "/əˈsɜːbɪk/", "adj.", "尖刻的；酸的", 9, "His acerbic wit offended some guests.",
     ["acerbic comment", "acerbic tone"], ["sharp", "biting", "caustic"], ["mild", "gentle"]),
    ("acquiescent", "/ˌækwiˈesnt/", "adj.", "默许的；顺从的", 10, "The acquiescent workers accepted the pay cut.",
     ["acquiescent attitude", "acquiescent silence"], ["compliant", "submissive", "resigned"], ["resistant"]),
    ("adumbrate", "/ˈædʌmbreɪt/", "v.", "预示；概述", 11, "The report adumbrates future policy changes.",
     ["adumbrate a plan", "adumbrate the future"], ["foreshadow", "outline", "sketch"], []),
    ("aegis", "/ˈiːdʒɪs/", "n.", "庇护；支持", 12, "The program operates under the aegis of the UN.",
     ["under the aegis of", "under the aegis"], ["protection", "auspices", "sponsorship"], []),
    ("afflatus", "/əˈfleɪtəs/", "n.", "灵感；神感", 13, "The poet claimed divine afflatus.",
     ["creative afflatus", "poetic afflatus"], ["inspiration", "muse", "revelation"], []),
    ("aggrandize", "/əˈɡrændaɪz/", "v.", "扩大；增强", 14, "He used the position to aggrandize himself.",
     ["self-aggrandizing", "aggrandize power"], ["enlarge", "magnify", "exalt"], ["diminish"]),
    ("alacritous", "/əˈlækrɪtəs/", "adj.", "乐意的；敏捷的", 15, "The team responded with alacritous enthusiasm.",
     ["alacritous response", "alacritous manner"], ["eager", "willing", "prompt"], ["reluctant", "slow"]),
    ("amalgamate", "/əˈmælɡəmeɪt/", "v.", "合并；混合", 16, "The two companies amalgamated last year.",
     ["amalgamate into", "amalgamate with"], ["merge", "combine", "unite"], ["separate", "split"]),
    ("anathema", "/əˈnæθəmə/", "n.", "诅咒；令人厌恶的事物", 17, "Racism is anathema to a civilized society.",
     ["anathema to", "declare anathema"], ["curse", "abomination", "taboo"], ["blessing"]),
    ("antediluvian", "/ˌæntidɪˈluːviən/", "adj.", "古老的；过时的", 18, "The office uses antediluvian computer systems.",
     ["antediluvian methods", "antediluvian attitudes"], ["ancient", "outdated", "prehistoric"], ["modern"]),
    ("aplomb", "/əˈplɒm/", "n.", "沉着；自信", 19, "She handled the crisis with remarkable aplomb.",
     ["with aplomb", "great aplomb"], ["poise", "composure", "confidence"], ["anxiety", "nervousness"]),
    ("apocryphal", "/əˈpɒkrɪfl/", "adj.", "不足凭信的；伪造的", 20, "The story is probably apocryphal.",
     ["apocryphal story", "apocryphal account"], ["doubtful", "unverified", "fictitious"], ["authentic", "verified"]),
]

# ── Level configuration ────────────────────────────────────────────────────

# Try to import expanded word data
try:
    from .vocab_data import (
        CET4_WORDS, CET6_WORDS, POSTGRAD_WORDS, TEM4_WORDS, TEM8_WORDS,
    )
except ImportError:
    from vocab_data import (  # type: ignore[no-redef]
        CET4_WORDS, CET6_WORDS, POSTGRAD_WORDS, TEM4_WORDS, TEM8_WORDS,
    )

LEVEL_CONFIG = {
    "CET4": {
        "filename": "cet4-core-2000.json",
        "words": _WORDS_CET4 + CET4_WORDS,
        "exam_types": ["CET4"],
        "description": "四级高频核心词汇，按真题出现频率降序排列",
        "source": "基于 CET-4 历年真题词频统计（public domain 数据源）",
    },
    "CET6": {
        "filename": "cet6-core-1500.json",
        "words": _WORDS_CET6 + CET6_WORDS,
        "exam_types": ["CET6"],
        "description": "六级增量高频词汇，假设用户已掌握四级词表",
        "source": "基于 CET-6 历年真题词频统计",
    },
    "POSTGRADUATE": {
        "filename": "postgraduate-core-1000.json",
        "words": _WORDS_POSTGRAD + POSTGRAD_WORDS,
        "exam_types": ["POSTGRADUATE_ENGLISH"],
        "description": "考研英语增量高频词汇",
        "source": "基于考研英语(一/二)历年真题词频统计",
    },
    "TEM4": {
        "filename": "tem4-core-2000.json",
        "words": _WORDS_TEM4 + TEM4_WORDS,
        "exam_types": ["TEM4"],
        "description": "英语专业四级高频词汇",
        "source": "基于 TEM-4 历年真题词频统计",
    },
    "TEM8": {
        "filename": "tem8-core-2000.json",
        "words": _WORDS_TEM8 + TEM8_WORDS,
        "exam_types": ["TEM8"],
        "description": "英语专业八级高频进阶词汇",
        "source": "基于 TEM-8 历年真题词频统计",
    },
}


def _make_entry(word_tuple, level):
    """Convert compact tuple to full vocab entry dict."""
    (word, phonetic, pos, meaning_cn, rank, example, colloc, syn, confusable) = word_tuple
    return {
        "word": word,
        "phonetic": phonetic,
        "pos": pos,
        "meaning_cn": meaning_cn,
        "frequency_rank": rank,
        "example": example,
        "cet_level": level,
        "collocations": colloc,
        "synonyms": syn,
        "confusable_words": confusable,
    }


def generate_level(level: str) -> list[dict]:
    """Generate vocabulary entries for a given exam level."""
    config = LEVEL_CONFIG[level]
    entries = [_make_entry(wt, level) for wt in config["words"]]
    # Sort by frequency_rank
    entries.sort(key=lambda e: e["frequency_rank"])
    return entries


def generate_all():
    """Generate all vocabulary JSON files."""
    schema = load_schema()
    index = {}
    total_entries = 0

    for level, config in LEVEL_CONFIG.items():
        entries = generate_level(level)
        total_entries += len(entries)

        # Validate entries
        errors = []
        for entry in entries:
            errs = validate_entry(entry, schema)
            if errs:
                errors.append((entry.get("word", "?"), errs))
        if errors:
            print(f"  [{level}] WARNING: {len(errors)} entries have validation issues:")
            for word, errs in errors[:5]:
                print(f"    - {word}: {', '.join(errs)}")

        # Write file
        path = VOCAB_DIR / config["filename"]
        write_json(entries, path)
        print(f"  [{level}] {path.name} — {len(entries)} entries")

        # Build index entry
        index[config["filename"].replace(".json", "")] = {
            "path": config["filename"],
            "count": len(entries),
            "exam_types": config["exam_types"],
            "description": config["description"],
            "source": config["source"],
        }

    # Write index
    index_path = VOCAB_DIR / "index.json"
    write_json(index, index_path)
    print(f"  [INDEX] index.json — {len(index)} files, {total_entries} total entries")
    return index_path


def validate_existing():
    """Validate existing vocabulary files against the schema."""
    schema = load_schema()
    all_ok = True

    for level, config in LEVEL_CONFIG.items():
        path = VOCAB_DIR / config["filename"]
        if not path.exists():
            print(f"  [{level}] MISSING: {config['filename']}")
            all_ok = False
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        errors = []
        for i, entry in enumerate(data):
            errs = validate_entry(entry, schema)
            if errs:
                errors.append((i, entry.get("word", f"index {i}"), errs))
        if errors:
            print(f"  [{level}] {len(errors)} ERRORS in {config['filename']}:")
            for idx, word, errs in errors[:5]:
                print(f"    #{idx} {word}: {', '.join(errs)}")
            all_ok = False
        else:
            print(f"  [{level}] {config['filename']} — {len(data)} entries OK")

    # Validate index
    index_path = VOCAB_DIR / "index.json"
    if index_path.exists():
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for key, info in index.items():
            if key not in [c["filename"].replace(".json", "") for c in LEVEL_CONFIG.values()]:
                print(f"  [INDEX] Extra entry in index: {key}")
        print(f"  [INDEX] index.json — {len(index)} entries")
    else:
        print("  [INDEX] MISSING: index.json")
        all_ok = False

    return all_ok


def main():
    if "--validate" in sys.argv:
        print("Validating vocabulary files...")
        ok = validate_existing()
        print("All OK!" if ok else "Validation FAILED.")
        sys.exit(0 if ok else 1)

    if "--all" in sys.argv:
        print("Generating all vocabulary files...")
        generate_all()
        print("Done!")
        return

    # Specific level
    spec = [a for a in sys.argv[1:] if a.startswith("--level")]
    if spec:
        level = spec[0].split("=", 1)[1] if "=" in spec[0] else None
        if level and level in LEVEL_CONFIG:
            print(f"Generating {level} vocabulary...")
            entries = generate_level(level)
            config = LEVEL_CONFIG[level]
            path = VOCAB_DIR / config["filename"]
            write_json(entries, path)
            print(f"  Written {len(entries)} entries to {path.name}")
        else:
            print(f"Unknown level: {level}. Valid: {list(LEVEL_CONFIG)}")
            sys.exit(1)
        return

    print("Usage: vocab_generator.py --all | --level=CET4 | --validate")
    sys.exit(1)


if __name__ == "__main__":
    main()
