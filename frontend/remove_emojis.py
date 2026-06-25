import os
import re

# Mapa de emojis -> tag img com SVG
EMOJI_MAP = {
    "\U0001F697": '<img src="img/icons/car.svg" class="emoji-icon" alt="Veículos">',
    "\U0001F9B7": '<img src="img/icons/clinic.svg" class="emoji-icon" alt="Clínica">',
    "\U0001F3E0": '<img src="img/icons/house.svg" class="emoji-icon" alt="Imóveis">',
    "\U0001F355": '<img src="img/icons/food.svg" class="emoji-icon" alt="Restaurante">',
    "\U0001F4AA": '<img src="img/icons/fitness.svg" class="emoji-icon" alt="Academia">',
    "\U0001F487": '<img src="img/icons/salon.svg" class="emoji-icon" alt="Salão">',
    "\U0001F436": '<img src="img/icons/pet.svg" class="emoji-icon" alt="Pet Shop">',
    "\U0001F6D2": '<img src="img/icons/shop.svg" class="emoji-icon" alt="E-commerce">',
    "\U0001F4C8": '<img src="img/icons/chart.svg" class="emoji-icon" alt="Gráfico">',
    "\U0001F916": '<img src="img/icons/robot.svg" class="emoji-icon" alt="Bot">',
    "\U0001F3AF": '<img src="img/icons/target.svg" class="emoji-icon" alt="Alvo">',
    "\U0001F504": '<img src="img/icons/refresh.svg" class="emoji-icon" alt="Atualizar">',
    "\u26A1": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Raio">',
    "\U0001F464": '<img src="img/icons/user.svg" class="emoji-icon" alt="Usuário">',
    "\u2705": '<img src="img/icons/check.svg" class="emoji-icon" alt="OK">',
    "\U0001F9EA": '<img src="img/icons/test.svg" class="emoji-icon" alt="Teste">',
    "\U0001F4BE": '<img src="img/icons/save.svg" class="emoji-icon" alt="Salvar">',
    "\U0001F4DD": '<img src="img/icons/edit.svg" class="emoji-icon" alt="Editar">',
    "\U0001F4E5": '<img src="img/icons/inbox.svg" class="emoji-icon" alt="Importar">',
    "\U0001F5D1": '<img src="img/icons/trash.svg" class="emoji-icon" alt="Lixeira">',
    "\u25B6": '<img src="img/icons/play.svg" class="emoji-icon" alt="Play">',
    "\U0001F4CA": '<img src="img/icons/chart.svg" class="emoji-icon" alt="Stats">',
    "\U0001F680": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Rocket">',
    "\u2728": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Sparkle">',
    "\U0001F525": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Fire">',
    "\U0001F4AC": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Chat">',
    "\U0001F4F1": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Phone">',
    "\U0001F4DE": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Phone">',
    "\u23F0": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Clock">',
    "\U0001F4CD": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Pin">',
    "\U0001F50D": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Search">',
    "\U0001F4B0": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Money">',
    "\u2B50": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Star">',
    "\U0001F511": '<img src="img/icons/zap.svg" class="emoji-icon" alt="Key">',
}

# Arquivos para processar
files = [
    "index.html", "login.html", "dashboard.html",
    "builder.html", "leads.html", "simulator.html",
    "css/styles.css", "js/api.js", "js/auth.js",
    "js/builder.js", "js/dashboard.js", "js/simulator.js",
    "../templates/veiculos.json", "../templates/clinica.json",
    "../templates/imobiliaria.json", "../templates/restaurante.json",
    "../templates/academias.json", "../templates/salao-beleza.json",
    "../templates/petshop.json", "../templates/e-commerce.json",
]

base = os.path.dirname(os.path.abspath(__file__))
total = 0
total_fixes = 0

for f in files:
    path = os.path.join(base, f)
    if not os.path.exists(path):
        print("-- " + f + " (nao existe)")
        continue
    with open(path, "rb") as fp:
        raw = fp.read()
    original = raw

    # Para cada emoji, substitui por tag img
    for emoji_char, img_tag in EMOJI_MAP.items():
        emoji_bytes = emoji_char.encode("utf-8")
        img_bytes = img_tag.encode("utf-8")
        if emoji_bytes in raw:
            raw = raw.replace(emoji_bytes, img_bytes)
            total_fixes += raw.count(img_bytes)

    # Remove emojis que nao tem mapeamento (substitui por texto generico)
    # Substituir todos os 4-byte UTF-8 (F0 9F XX XX) que nao foram mapeados
    def remove_remaining(match):
        return ""
    raw = re.sub(rb'\xf0\x9f[\x90-\xbf][\x80-\xbf]', b'', raw)
    # Outros emojis comuns (3-byte)
    raw = re.sub(rb'\xe2[\x9c-\x9f][\x80-\xbf]', b'', raw)
    raw = re.sub(rb'\xe2\x9a[\x80-\xbf]', b'', raw)

    if raw != original:
        with open(path, "wb") as fp:
            fp.write(raw)
        total += 1
        print("OK " + f)
    else:
        print("-- " + f)

print()
print("Total: " + str(total) + " arquivos corrigidos (" + str(total_fixes) + " imagens)")