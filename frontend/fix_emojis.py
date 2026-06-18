"""
fix_emojis.py - Substitui emojis UTF-8 por HTML entities nos arquivos do frontend.

Uso: python fix_emojis.py
"""
import os
import sys

# Mapa: caractere emoji -> HTML entity (codepoint decimal)
EMOJIS = {
    "\U0001F4CA": "&#128202;",  # chart bars
    "\U0001F4C8": "&#128200;",  # chart up
    "\U0001F916": "&#129302;",  # robot
    "\U0001F3AF": "&#127919;",  # target
    "\U0001F504": "&#128260;",  # refresh
    "\u26A1": "&#9889;",        # zap
    "\U0001F697": "&#128663;",  # car
    "\U0001F9B7": "&#129463;",  # tooth
    "\U0001F3E0": "&#127968;",  # house
    "\U0001F355": "&#127829;",  # pizza
    "\U0001F4AA": "&#128170;",  # muscle
    "\U0001F487": "&#128131;",  # haircut
    "\U0001F436": "&#128054;",  # dog
    "\U0001F6D2": "&#128722;",  # cart
    "\u2728": "&#10024;",        # sparkles
    "\U0001F680": "&#128640;",  # rocket
    "\U0001F525": "&#128293;",  # fire
    "\U0001F464": "&#128100;",  # bust
    "\U0001F4F1": "&#128241;",  # phone
    "\U0001F4AC": "&#128172;",  # speech
    "\U0001F3E5": "&#127973;",  # hospital
    "\U0001F4CD": "&#128205;",  # pin
    "\u23F0": "&#9200;",        # clock
    "\U0001F4DE": "&#128222;",  # receiver
    "\U0001F393": "&#127891;",  # graduation cap
    "\U0001F4BC": "&#128188;",  # briefcase
    "\U0001F4B0": "&#128176;",  # money
    "\U0001F50D": "&#128269;",  # search
    "\U0001F4DD": "&#128221;",  # memo
    "\U0001F44B": "&#128075;",  # wave
    "\U0001F4BE": "&#128190;",  # floppy
    "\u2705": "&#9989;",        # white check
    "\u274C": "&#10060;",       # x
    "\u2B50": "&#11088;",       # star
    "\U0001F511": "&#128273;",  # key
    "\U0001F4DA": "&#128218;",  # books
    "\U0001F3A8": "&#127784;",  # palette
    "\U0001F3EA": "&#127978;",  # store
    "\U0001F4C4": "&#128196;",  # doc
    "\U0001F4E4": "&#128228;",  # outbox
    "\U0001F4E9": "&#128233;",  # inbox
    "\U0001F465": "&#128101;",  # users
    "\U0001F4CB": "&#128203;",  # clipboard
    "\u270D": "&#9997;",        # writing
    "\U0001F4C1": "&#128193;",  # file
    "\U0001F4A1": "&#128161;",  # bulb
    "\U0001F4F7": "&#128247;",  # camera
    "\U0001F50A": "&#128266;",  # speaker
    "\U0001F4E3": "&#128227;",  # megaphone
    "\U0001F381": "&#127745;",  # gift
    "\U0001F389": "&#127881;",  # party
    "\U0001F6CD": "&#128717;",  # shopping cart
    "\U0001F45F": "&#128095;",  # shoe
    "\U0001F6BF": "&#128703;",  # shower
    "\U0001F43C": "&#128060;",  # panda
    "\U0001F439": "&#128057;",  # mouse
    "\U0001F4B8": "&#128184;",  # money wings
    "\U0001F4B5": "&#128181;",  # dollar
    "\U0001F69A": "&#128666;",  # truck
    "\U0001F6E3": "&#128739;",  # motorway
    "\U0001F6E4": "&#128740;",  # railway
    "\U0001F3C3": "&#127939;",  # runner
    "\U0001F3CB": "&#127947;",  # weight lift
    "\U0001F938": "&#129336;",  # medit
    "\u26BD": "&#9917;",        # soccer
    "\U0001F3B2": "&#127922;",  # dice
    "\U0001F4D6": "&#128214;",  # book
    "\U0001F4F2": "&#128242;",  # phone arrow
    "\U0001F4F8": "&#128248;",  # camera flash
    "\u23F8": "&#9208;",        # pause
    "\u23F9": "&#9209;",        # stop
    "\u2935": "&#10581;",       # arrow
}

# Arquivos do frontend para corrigir
files = [
    "index.html", "login.html", "dashboard.html",
    "builder.html", "leads.html", "simulator.html",
    "css/styles.css", "js/api.js", "js/auth.js",
    "js/builder.js", "js/dashboard.js", "js/simulator.js",
]

# Diretorio do frontend (mesmo diretorio deste script)
base = os.path.dirname(os.path.abspath(__file__))

count = 0
for f in files:
    path = os.path.join(base, f)
    if not os.path.exists(path):
        print(f"-- {f} (nao existe)")
        continue
    with open(path, "r", encoding="utf-8") as fp:
        content = fp.read()
    original = content
    for emoji, entity in EMOJIS.items():
        content = content.replace(emoji, entity)
    if content != original:
        # Salva SEM BOM para evitar problemas de encoding
        with open(path, "w", encoding="utf-8") as fp:
            fp.write(content)
        count += 1
        # Conta quantos emojis foram substituidos
        diff = len(original) - len(content)
        print(f"OK {f} ({diff} caracteres substituidos)")
    else:
        print(f"-- {f} (sem mudancas)")

print()
print(f"Total: {count} arquivos corrigidos")
print("Agora faca Ctrl+Shift+R no navegador!")
