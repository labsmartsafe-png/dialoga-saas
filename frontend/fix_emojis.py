import os

EMOJIS_RAW = {
    "1F4CA": "128202", "1F4C8": "128200", "1F916": "129302",
    "1F3AF": "127919", "1F504": "128260", "26A1":  "9889",
    "1F697": "128663", "1F9B7": "129463", "1F3E0": "127968",
    "1F355": "127829", "1F4AA": "128170", "1F487": "128131",
    "1F436": "128054", "1F6D2": "128722", "2728":  "10024",
    "1F680": "128640", "1F525": "128293", "1F464": "128100",
    "1F4F1": "128241", "1F4AC": "128172", "1F3E5": "127973",
    "1F4CD": "128205", "23F0":  "9200",   "1F4DE": "128222",
    "1F393": "127891", "1F4BC": "128188", "1F4B0": "128176",
    "1F50D": "128269", "1F4DD": "128221", "1F44B": "128075",
    "1F4BE": "128190", "2705":  "9989",   "274C":  "10060",
    "2B50":  "11088",  "1F511": "128273", "1F4DA": "128218",
    "1F3A8": "127784", "1F3EA": "127978", "1F4C4": "128196",
    "1F4E4": "128228", "1F4E9": "128233", "1F465": "128101",
    "1F4CB": "128203", "270D":  "9997",   "1F4C1": "128193",
    "1F4A1": "128161", "1F4F7": "128247", "1F50A": "128266",
    "1F4E3": "128227", "1F381": "127745", "1F389": "127881",
    "1F6CD": "128717", "1F45F": "128095", "1F6BF": "128703",
    "1F43C": "128060", "1F439": "128057", "1F4B8": "128184",
    "1F4B5": "128181", "1F69A": "128666", "1F6E3": "128739",
    "1F6E4": "128740", "1F3C3": "127939", "1F3CB": "127947",
    "1F938": "129336", "26BD":  "9917",   "1F3B2": "127922",
    "1F4D6": "128214", "1F4F2": "128242", "1F4F8": "128248",
}

EMOJIS = {chr(int(k, 16)): "&#" + v + ";" for k, v in EMOJIS_RAW.items()}

files = [
    "index.html", "login.html", "dashboard.html",
    "builder.html", "leads.html", "simulator.html",
    "css/styles.css", "js/api.js", "js/auth.js",
    "js/builder.js", "js/dashboard.js", "js/simulator.js",
]

base = os.path.dirname(os.path.abspath(__file__))
count = 0
for f in files:
    path = os.path.join(base, f)
    if not os.path.exists(path):
        continue
    with open(path, "r", encoding="utf-8") as fp:
        content = fp.read()
    original = content
    for emoji, entity in EMOJIS.items():
        content = content.replace(emoji, entity)
    if content != original:
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(content)
        count += 1
        print("OK " + f)
    else:
        print("-- " + f)

print()
print("Total: " + str(count) + " arquivos corrigidos")