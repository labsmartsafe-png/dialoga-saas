"""
Script para recriar os 8 templates JSON corretamente.
Rode: python fix_templates.py
"""
import json
import os

TEMPLATES = {
    "academias": {
        "slug": "academias", "name": "Academia / Est\u00fat\u00fadio",
        "description": "Academias, est\u00fadios de pilates, crossfit e personal training. Mostra planos, agenda aulas e captura leads.",
        "category": "Fitness", "icon": "\U0001F3CB\uFE0F",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F3CB\uFE0F Bem-vindo \u00e0 *Academia Power Fit* \U0001F4AA\n\nAqui voc\u00ea vai encontrar o plano perfeito para atingir seus objetivos!\n\nComo posso te ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F4AA Conhecer planos","value":"planos","next":"info_planos"},
                {"label":"\U0001F938 Aulas experimentais","value":"aula_experimental","next":"tipo_aula"},
                {"label":"\U0001F4CD Hor\u00e1rio e localiza\u00e7\u00e3o","value":"localizacao","next":"info_localizacao"},
                {"label":"\U0001F4AC Falar com consultor","value":"consultor","next":"captura_nome"}
            ]},
            {"id":"info_planos","type":"message","content":"\U0001F4AA *Nossos planos:*\n\n*B\u00e1sico* - R$ 99/m\u00eas\n\u2022 Muscula\u00e7\u00e3o\n\u2022 Acesso 6h \u00e0s 22h\n\n\u2B50 *Premium* - R$ 169/m\u00eas\n\u2022 Muscula\u00e7\u00e3o + aulas coletivas\n\u2022 Acesso 24h\n\u2022 Avalia\u00e7\u00e3o f\u00edsica mensal\n\n\U0001F451 *VIP* - R$ 299/m\u00eas\n\u2022 Tudo do Premium\n\u2022 Personal trainer 2x/semana\n\u2022 Nutricionista\n\n\U0001F381 *1\u00aa semana gr\u00e1tis em qualquer plano!*","next":"tipo_plano"},
            {"id":"tipo_plano","type":"question","content":"Qual plano te interessou?","variable":"plano","options":[
                {"label":"B\u00e1sico - R$ 99","value":"basico","next":"captura_nome"},
                {"label":"Premium - R$ 169","value":"premium","next":"captura_nome"},
                {"label":"VIP - R$ 299","value":"vip","next":"captura_nome"},
                {"label":"Ainda em d\u00favidas","value":"duvida","next":"captura_nome"}
            ]},
            {"id":"tipo_aula","type":"question","content":"Que tipo de aula voc\u00ea quer experimentar?","variable":"tipo_aula","options":[
                {"label":"\U0001F3CB\uFE0F Muscula\u00e7\u00e3o","value":"musculacao","next":"captura_nome"},
                {"label":"\U0001F9D8 Pilates","value":"pilates","next":"captura_nome"},
                {"label":"\u26A1 Crossfit","value":"crossfit","next":"captura_nome"},
                {"label":"\U0001F483 Zumba","value":"zumba","next":"captura_nome"}
            ]},
            {"id":"info_localizacao","type":"message","content":"\U0001F4CD *Nossa unidade:*\n\n\U0001F3E2 Av. Paulista, 1000 - Bela Vista\nS\u00e3o Paulo - SP\nCEP 01310-100\n\n\u23F0 *Funcionamento:*\nSeg a Sex: 6h \u00e0s 23h\nS\u00e1bado: 8h \u00e0s 18h\nDomingo: 8h \u00e0s 14h\n\n\U0001F697 Estacionamento gr\u00e1tis!","next":"menu_principal"},
            {"id":"captura_nome","type":"input","content":"\u00d3timo! Para finalizar, me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"{{nome}}, agora me informe seu *WhatsApp com DDD*:","variable":"telefone","next":"captura_objetivo"},
            {"id":"captura_objetivo","type":"question","content":"Qual \u00e9 seu principal objetivo?","variable":"objetivo","options":[
                {"label":"\U0001F4AA Ganhar massa","value":"massa","next":"confirmacao"},
                {"label":"\U0001F3C3 Emagrecer","value":"emagrecer","next":"confirmacao"},
                {"label":"\u2764\uFE0F Sa\u00fade e bem-estar","value":"saude","next":"confirmacao"},
                {"label":"\U0001F3C6 Performance","value":"performance","next":"confirmacao"}
            ]},
            {"id":"confirmacao","type":"message","content":"\u2705 *Cadastro realizado!*\n\n\U0001F464 {{nome}}\n\U0001F4F1 {{telefone}}\n\U0001F3AF Objetivo: {{objetivo}}\n\nNosso consultor te ligar\u00e1 em at\u00e9 24h para agendar uma visita e te mostrar a academia!\n\nAt\u00e9 logo! \U0001F3CB\uFE0F","next":"end"},
            {"id":"end","type":"end","content":"Bem-vindo \u00e0 fam\u00edlia Power Fit! \U0001F3CB\uFE0F"}
        ]
    },
    "clinica": {
        "slug": "clinica", "name": "Cl\u00ednica M\u00e9dica / Dentista",
        "description": "Atendimento para cl\u00ednicas e consult\u00f3rios odontol\u00f3gicos. Agenda consultas, captura sintomas e envia lembretes.",
        "category": "Sa\u00fade", "icon": "\U0001F9B7",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! Bem-vindo \u00e0 *Cl\u00ednica Sorriso+* \U0001F9B7\n\nSou a assistente virtual. Posso ajudar com agendamento, d\u00favidas sobre conv\u00eanios e informa\u00e7\u00f5es sobre tratamentos.\n\nComo posso te ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F4C5 Agendar consulta","value":"agendar","next":"tipo_consulta"},
                {"label":"\U0001F9B7 Tratamentos","value":"tratamentos","next":"lista_tratamentos"},
                {"label":"\U0001F3E8 Conv\u00eanios","value":"convenios","next":"info_convenios"},
                {"label":"\U0001F6A8 Emerg\u00eancia","value":"emergencia","next":"emergencia"}
            ]},
            {"id":"tipo_consulta","type":"question","content":"Que tipo de consulta voc\u00ea precisa?","variable":"tipo_consulta","options":[
                {"label":"Avalia\u00e7\u00e3o geral","value":"avaliacao","next":"captura_nome"},
                {"label":"Limpeza","value":"limpeza","next":"captura_nome"},
                {"label":"Clareamento","value":"clareamento","next":"captura_nome"},
                {"label":"Canal","value":"canal","next":"captura_nome"}
            ]},
            {"id":"lista_tratamentos","type":"message","content":"\U0001F9B7 *Nossos tratamentos:*\n\n\u2705 Limpeza e profilaxia\n\u2705 Clareamento dental\n\u2705 Implantes\n\u2705 Ortodontia (aparelhos)\n\u2705 Endodontia (canal)\n\u2705 Pr\u00f3teses e facetas\n\u2705 Urg\u00eancia 24h\n\nTodos com tecnologia de ponta e profissionais especializados.","next":"menu_principal"},
            {"id":"info_convenios","type":"message","content":"\U0001F3E8 *Conv\u00eanios aceitos:*\n\n\u2022 Amil\n\u2022 Bradesco Sa\u00fade\n\u2022 SulAm\u00e9rica\n\u2022 Unimed\n\u2022 Odontoprev\n\u2022 Hapvida\n\nAceitamos tamb\u00e9m particular com parcelamento em at\u00e9 10x.\n\nPosso ajudar com mais alguma coisa?","next":"menu_principal"},
            {"id":"emergencia","type":"message","content":"\U0001F6A8 *EMERG\u00caNCIA ODONTOL\u00d3GICA*\n\nPara emerg\u00eancias fora do hor\u00e1rio comercial, ligue diretamente para:\n\U0001F4DE (11) 99999-9999\n\nAtendemos urg\u00eancias 24h!","next":"captura_nome"},
            {"id":"captura_nome","type":"input","content":"Para agendar sua consulta de {{tipo_consulta}}, por favor me informe seu *nome completo*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"Obrigada, {{nome}}! \n\nAgora me informe seu *telefone com DDD*:","variable":"telefone","next":"captura_data"},
            {"id":"captura_data","type":"question","content":"Qual per\u00edodo voc\u00ea prefere para a consulta?","variable":"periodo","options":[
                {"label":"Manh\u00e3","value":"manha","next":"confirmacao"},
                {"label":"Tarde","value":"tarde","next":"confirmacao"},
                {"label":"Noite","value":"noite","next":"confirmacao"}
            ]},
            {"id":"confirmacao","type":"message","content":"\u2705 *Agendamento solicitado!*\n\n\U0001F4CB *Resumo:*\n\U0001F464 Paciente: {{nome}}\n\U0001F4DE Contato: {{telefone}}\n\U0001F9B7 Tipo: {{tipo_consulta}}\n\u23F0 Per\u00edodo: {{periodo}}\n\nNossa recepcionista entrar\u00e1 em contato em at\u00e9 1 hora para confirmar o hor\u00e1rio exato.","next":"end"},
            {"id":"end","type":"end","content":"Obrigado por escolher a Cl\u00ednica Sorriso+! \U0001F9B7\u2728"}
        ]
    },
    "e-commerce": {
        "slug": "e-commerce", "name": "E-commerce",
        "description": "Lojas online de diversos segmentos. Mostra cat\u00e1logo, processa pedidos e acompanha entregas.",
        "category": "E-commerce", "icon": "\U0001F6CD\uFE0F",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F6CD\uFE0F Bem-vindo \u00e0 *Shop Online Brasil* \U0001F680\n\nAqui voc\u00ea encontra de tudo com entrega r\u00e1pida!\n\nComo posso te ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F6CD\uFE0F Ver produtos","value":"produtos","next":"categoria"},
                {"label":"\U0001F4E6 Rastrear pedido","value":"rastrear","next":"rastreio_input"},
                {"label":"\U0001F4B3 Formas de pagamento","value":"pagamento","next":"info_pagamento"},
                {"label":"\U0001F504 Trocas e devolu\u00e7\u00f5es","value":"trocas","next":"info_trocas"}
            ]},
            {"id":"categoria","type":"question","content":"Que categoria voc\u00ea quer ver?","variable":"categoria","options":[
                {"label":"\U0001F4F1 Eletr\u00f4nicos","value":"eletronicos","next":"info_categoria"},
                {"label":"\U0001F455 Moda","value":"moda","next":"info_categoria"},
                {"label":"\U0001F3E0 Casa","value":"casa","next":"info_categoria"},
                {"label":"\U0001F381 Promo\u00e7\u00f5es","value":"promocoes","next":"info_promocoes"}
            ]},
            {"id":"info_categoria","type":"message","content":"\U0001F6CD\uFE0F *{{categoria}} em destaque:*\n\n\U0001F4F1 Smartphones a partir de R$ 1.299\n\U0001F455 Camisetas premium R$ 79\n\U0001F3E0 Decora\u00e7\u00e3o R$ 49\n\U0001F3A7 Fones bluetooth R$ 159\n\n\U0001F69A Frete gr\u00e1tis acima de R$ 199\n\U0001F4B3 Parcelamento em at\u00e9 12x sem juros\n\n\U0001F517 Acesse: shop.com.br/{{categoria}}","next":"quer_comprar"},
            {"id":"info_promocoes","type":"message","content":"\U0001F381 *Promo\u00e7\u00f5es imperd\u00edveis:*\n\n\u26A1 Black Friday antecipada: at\u00e9 70% off\n\U0001F3AF Compre 2, leve 3 em selecionados\n\U0001F4B0 Cupom DIALOGA10: 10% off na primeira compra\n\U0001F69A Frete gr\u00e1tis acima de R$ 99\n\n\u23F0 V\u00e1lido at\u00e9 domingo ou enquanto durar o estoque!","next":"quer_comprar"},
            {"id":"info_pagamento","type":"message","content":"\U0001F4B3 *Formas de pagamento:*\n\n\u2705 Cart\u00e3o de cr\u00e9dito (at\u00e9 12x sem juros)\n\u2705 Cart\u00e3o de d\u00e9bito\n\u2705 PIX (5% de desconto)\n\u2705 Boleto banc\u00e1rio\n\u2705 PayPal\n\n\U0001F512 Ambiente 100% seguro!","next":"menu_principal"},
            {"id":"info_trocas","type":"message","content":"\U0001F504 *Trocas e devolu\u00e7\u00f5es:*\n\n\u2022 Prazo de 7 dias ap\u00f3s o recebimento\n\u2022 Produto deve estar na embalagem original\n\u2022 Frete de devolu\u00e7\u00e3o por nossa conta\n\u2022 Reembolso em at\u00e9 10 dias \u00fateis\n\n\U0001F4E6 Saiba mais em: shop.com.br/trocas","next":"menu_principal"},
            {"id":"rastreio_input","type":"input","content":"\U0001F4E6 Para rastrear seu pedido, me informe o *n\u00famero do pedido* (ex: #12345):","variable":"numero_pedido","next":"info_rastreio"},
            {"id":"info_rastreio","type":"message","content":"\U0001F4E6 Pedido #{{numero_pedido}}\n\n\U0001F4CD Status: Em tr\u00e2nsito\n\U0001F4C5 Previs\u00e3o de entrega: 2 a 4 dias \u00fateis\n\U0001F3D8\uFE0F Origem: S\u00e3o Paulo - SP\n\nVoc\u00ea receber\u00e1 atualiza\u00e7\u00f5es autom\u00e1ticas!\n\nPosso ajudar com mais alguma coisa?","next":"menu_principal"},
            {"id":"quer_comprar","type":"question","content":"Quer aproveitar as ofertas?","variable":"quer_comprar","options":[
                {"label":"Sim! Quero comprar","value":"sim","next":"captura_nome"},
                {"label":"Agora n\u00e3o","value":"nao","next":"despedida"}
            ]},
            {"id":"despedida","type":"message","content":"Tudo bem! \U0001F60A\n\nNosso cupom *DIALOGA10* est\u00e1 sempre dispon\u00edvel para voc\u00ea. Salve nosso contato para ofertas exclusivas!\n\nAt\u00e9 a pr\u00f3xima! \U0001F6CD\uFE0F","next":"end"},
            {"id":"captura_nome","type":"input","content":"\u00d3timo! \U0001F389 Me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"{{nome}}, agora seu *WhatsApp com DDD*:","variable":"telefone","next":"captura_email"},
            {"id":"captura_email","type":"input","content":"E seu *e-mail* para envio do pedido:","variable":"email","next":"confirmacao"},
            {"id":"confirmacao","type":"message","content":"\u2705 *Quase l\u00e1!*\n\n\U0001F464 {{nome}}\n\U0001F4F1 {{telefone}}\n\U0001F4E7 {{email}}\n\U0001F381 Cupom *DIALOGA10* aplicado (10% off)\n\nNossa equipe entrar\u00e1 em contato com o link de pagamento exclusivo para voc\u00ea!\n\n\U0001F6CD\uFE0F Boas compras!","next":"end"},
            {"id":"end","type":"end","content":"Obrigado por escolher a Shop Online Brasil! \U0001F6CD\uFE0F\u2728"}
        ]
    },
    "imobiliaria": {
        "slug": "imobiliaria", "name": "Imobili\u00e1ria",
        "description": "Atendimento imobili\u00e1rio para compra, aluguel e venda de im\u00f3veis. Filtra prefer\u00eancias e qualifica leads.",
        "category": "Im\u00f3veis", "icon": "\U0001F3E0",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F3E0 Bem-vindo \u00e0 *Imobili\u00e1ria Casa Nova* \U0001F3E1\n\nSou o assistente virtual. Posso te ajudar a encontrar o im\u00f3vel ideal ou anunciar o seu!\n\nComo posso ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F511 Comprar im\u00f3vel","value":"comprar","next":"tipo_imovel"},
                {"label":"\U0001F4DD Alugar im\u00f3vel","value":"alugar","next":"tipo_imovel"},
                {"label":"\U0001F4E2 Anunciar im\u00f3vel","value":"anunciar","next":"anuncio_dados"},
                {"label":"\u2753 Tirar d\u00favidas","value":"duvidas","next":"duvidas_info"}
            ]},
            {"id":"tipo_imovel","type":"question","content":"Que tipo de im\u00f3vel voc\u00ea procura?","variable":"tipo_imovel","options":[
                {"label":"\U0001F3E4 Apartamento","value":"apartamento","next":"quartos"},
                {"label":"\U0001F3E0 Casa","value":"casa","next":"quartos"},
                {"label":"\U0001F3EA Sala comercial","value":"sala","next":"captura_nome"},
                {"label":"\U0001F333 Terreno","value":"terreno","next":"captura_nome"}
            ]},
            {"id":"quartos","type":"question","content":"Quantos quartos voc\u00ea precisa?","variable":"quartos","options":[
                {"label":"1 quarto","value":"1","next":"orcamento"},
                {"label":"2 quartos","value":"2","next":"orcamento"},
                {"label":"3 quartos","value":"3","next":"orcamento"},
                {"label":"4+ quartos","value":"4+","next":"orcamento"}
            ]},
            {"id":"orcamento","type":"question","content":"Qual \u00e9 a sua faixa de valor?","variable":"orcamento","options":[
                {"label":"At\u00e9 R$ 1.500/m\u00eas ou R$ 200k","value":"baixo","next":"captura_nome"},
                {"label":"R$ 1.500 - 3.000/m\u00eas ou R$ 200-500k","value":"medio","next":"captura_nome"},
                {"label":"R$ 3.000 - 6.000/m\u00eas ou R$ 500k-1M","value":"alto","next":"captura_nome"},
                {"label":"Acima disso","value":"premium","next":"captura_nome"}
            ]},
            {"id":"duvidas_info","type":"message","content":"\u2753 *Como funciona:*\n\n\u2022 Trabalhamos com compra, venda e aluguel\n\u2022 Mais de 5.000 im\u00f3veis cadastrados\n\u2022 Equipe de corretores credenciados (CRECI)\n\u2022 Visitas agendadas em at\u00e9 24h\n\nPosso continuar te ajudando?","next":"menu_principal"},
            {"id":"anuncio_dados","type":"message","content":"\U0001F4E2 *Para anunciar seu im\u00f3vel:*\n\nVamos precisar de algumas informa\u00e7\u00f5es. Um corretor entrar\u00e1 em contato para tirar fotos profissionais e cadastrar seu im\u00f3vel gratuitamente.","next":"captura_nome"},
            {"id":"captura_nome","type":"input","content":"Para enviar op\u00e7\u00f5es personalizadas, me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"Obrigado, {{nome}}! \n\nAgora me informe seu *WhatsApp com DDD*:","variable":"telefone","next":"captura_cidade"},
            {"id":"captura_cidade","type":"input","content":"Em qual *cidade e bairro* voc\u00ea prefere? (Ex: S\u00e3o Paulo - Vila Mariana)","variable":"cidade","next":"resumo"},
            {"id":"resumo","type":"message","content":"\u2705 *Lead capturado!*\n\n\U0001F464 Nome: {{nome}}\n\U0001F4F1 Contato: {{telefone}}\n\U0001F3D6\uFE0F Prefer\u00eancia: {{tipo_imovel}}\n\U0001F6CF\uFE0F Quartos: {{quartos}}\n\U0001F4B0 Or\u00e7amento: {{orcamento}}\n\U0001F4CD Localiza\u00e7\u00e3o: {{cidade}}\n\nEm at\u00e9 2 horas um corretor entrar\u00e1 em contato com op\u00e7\u00f5es selecionadas para voc\u00ea!","next":"end"},
            {"id":"end","type":"end","content":"Obrigado por escolher a Imobili\u00e1ria Casa Nova! \U0001F3E1"}
        ]
    },
    "petshop": {
        "slug": "petshop", "name": "Pet Shop / Veterin\u00e1ria",
        "description": "Pet shops, cl\u00ednicas veterin\u00e1rias e banho/tosa. Agenda servi\u00e7os, vende produtos e tira d\u00favidas.",
        "category": "Pet", "icon": "\U0001F43E",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F43E Bem-vindo ao *Pet Shop Amigo Fiel* \U0001F436\U0001F431\n\nAmor e cuidado para seu melhor amigo!\n\nComo posso ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F6C1 Banho e tosa","value":"banho_tosa","next":"porte_pet"},
                {"label":"\U0001F3E5 Consulta veterin\u00e1ria","value":"veterinaria","next":"tipo_consulta"},
                {"label":"\U0001F6D2 Produtos","value":"produtos","next":"info_produtos"},
                {"label":"\U0001F489 Vacina\u00e7\u00e3o","value":"vacinacao","next":"captura_pet"}
            ]},
            {"id":"porte_pet","type":"question","content":"Qual \u00e9 o porte do seu pet?","variable":"porte_pet","options":[
                {"label":"Pequeno","value":"pequeno","next":"captura_pet"},
                {"label":"M\u00e9dio","value":"medio","next":"captura_pet"},
                {"label":"Grande","value":"grande","next":"captura_pet"}
            ]},
            {"id":"tipo_consulta","type":"question","content":"Que tipo de consulta?","variable":"tipo_consulta","options":[
                {"label":"Consulta de rotina","value":"rotina","next":"captura_pet"},
                {"label":"Vacina\u00e7\u00e3o","value":"vacinacao","next":"captura_pet"},
                {"label":"Exames","value":"exames","next":"captura_pet"},
                {"label":"Emerg\u00eancia","value":"emergencia","next":"emergencia"}
            ]},
            {"id":"info_produtos","type":"message","content":"\U0001F6D2 *Nossos produtos:*\n\n\U0001F356 *Ra\u00e7\u00e3o:*\n\u2022 Premium (15kg) - R$ 180\n\u2022 Standard (15kg) - R$ 120\n\n\U0001F9B4 *Petiscos:*\n\u2022 Ossinhos naturais - R$ 25\n\u2022 Biscoitos variados - R$ 18\n\n\U0001F9F4 *Higiene:*\n\u2022 Shampoo - R$ 35\n\u2022 Tapete higi\u00eanico - R$ 65\n\n\U0001F3BE *Brinquedos e acess\u00f3rios*\n\n\U0001F6F5 Entrega em domic\u00edlio!","next":"menu_principal"},
            {"id":"emergencia","type":"message","content":"\U0001F6A8 *EMERG\u00caNCIA VETERIN\u00c1RIA 24H*\n\n\U0001F4DE Ligue agora: (11) 99999-9999\n\nEstamos prontos para atender seu pet a qualquer hora!","next":"captura_pet"},
            {"id":"captura_pet","type":"input","content":"Qual \u00e9 o *nome do seu pet*? \U0001F43E","variable":"nome_pet","next":"captura_nome"},
            {"id":"captura_nome","type":"input","content":"Que fofo(a)! \U0001F970\n\nAgora me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"E seu *WhatsApp com DDD*:","variable":"telefone","next":"confirmacao"},
            {"id":"confirmacao","type":"message","content":"\u2705 *Agendamento confirmado!*\n\n\U0001F43E Pet: {{nome_pet}}\n\U0001F464 Tutor: {{nome}}\n\U0001F4F1 Contato: {{telefone}}\n\nEm at\u00e9 1 hora entraremos em contato para confirmar data e hor\u00e1rio do servi\u00e7o.\n\nAt\u00e9 logo! \U0001F43E\u2764\uFE0F","next":"end"},
            {"id":"end","type":"end","content":"Cuide do seu pet com muito amor! \U0001F43E\u2764\uFE0F"}
        ]
    },
    "restaurante": {
        "slug": "restaurante", "name": "Restaurante / Delivery",
        "description": "Restaurantes, pizzarias e lanchonetes. Mostra card\u00e1pio, recebe pedidos e acompanha entrega.",
        "category": "Alimenta\u00e7\u00e3o", "icon": "\U0001F355",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F355 Bem-vindo \u00e0 *Pizzaria Forno a Lenha* \U0001F525\n\nEstou aqui para te ajudar com:\n\u2022 Card\u00e1pio\n\u2022 Pedidos delivery\n\u2022 Reservas\n\u2022 Hor\u00e1rio de funcionamento\n\nO que voc\u00ea deseja?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F355 Fazer pedido","value":"pedido","next":"tipo_pedido"},
                {"label":"\U0001F4CB Ver card\u00e1pio","value":"cardapio","next":"cardapio_info"},
                {"label":"\U0001F37D\uFE0F Reservar mesa","value":"reserva","next":"reserva_dados"},
                {"label":"\U0001F550 Hor\u00e1rio","value":"horario","next":"horario_info"}
            ]},
            {"id":"tipo_pedido","type":"question","content":"Como voc\u00ea quer receber seu pedido?","variable":"tipo_entrega","options":[
                {"label":"\U0001F6F5 Delivery","value":"delivery","next":"captura_endereco"},
                {"label":"\U0001F3EA Retirada no local","value":"retirada","next":"captura_nome"}
            ]},
            {"id":"cardapio_info","type":"message","content":"\U0001F4CB *Nosso card\u00e1pio:*\n\n\U0001F355 *Pizzas Salgadas:*\n\u2022 Mussarela R$ 45\n\u2022 Calabresa R$ 48\n\u2022 Portuguesa R$ 52\n\u2022 Quatro Queijos R$ 58\n\n\U0001F36B *Pizzas Doces:*\n\u2022 Chocolate R$ 48\n\u2022 Banana R$ 46\n\n\U0001F954 *Bebidas:*\n\u2022 Coca-Cola 2L R$ 12\n\u2022 Suco natural R$ 8\n\n\U0001F517 Ver card\u00e1pio completo: link.cardapio.com.br","next":"tipo_pedido"},
            {"id":"horario_info","type":"message","content":"\U0001F550 *Hor\u00e1rio de funcionamento:*\n\n\U0001F4C5 Segunda a quinta: 18h \u00e0s 23h\n\U0001F4C5 Sexta e s\u00e1bado: 18h \u00e0s 00h\n\U0001F4C5 Domingo: 18h \u00e0s 22h\n\nDelivery at\u00e9 30 minutos antes do fechamento!","next":"menu_principal"},
            {"id":"captura_endereco","type":"input","content":"\U0001F6F5 Para delivery, preciso do seu *endere\u00e7o completo com CEP*:","variable":"endereco","next":"captura_nome"},
            {"id":"reserva_dados","type":"input","content":"\U0001F37D\uFE0F Para reservar uma mesa, me diga a *data e hora* (ex: 25/12 \u00e0s 20h):","variable":"data_reserva","next":"captura_pessoas"},
            {"id":"captura_pessoas","type":"question","content":"Quantas pessoas?","variable":"pessoas","options":[
                {"label":"2 pessoas","value":"2","next":"captura_nome"},
                {"label":"3-4 pessoas","value":"3-4","next":"captura_nome"},
                {"label":"5-6 pessoas","value":"5-6","next":"captura_nome"},
                {"label":"Mais de 6","value":"6+","next":"captura_nome"}
            ]},
            {"id":"captura_nome","type":"input","content":"Me informe seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"E seu *WhatsApp com DDD*:","variable":"telefone","next":"confirmacao"},
            {"id":"confirmacao","type":"message","content":"\u2705 *Pedido/Reserva registrado!*\n\n\U0001F464 {{nome}}\n\U0001F4F1 {{telefone}}\n\nEm instantes nossa equipe confirmar\u00e1 seu pedido/reserva e te enviar\u00e1 o link de pagamento ou detalhes.","next":"end"},
            {"id":"end","type":"end","content":"Obrigado pela prefer\u00eancia! \U0001F355 Bom apetite!"}
        ]
    },
    "salao-beleza": {
        "slug": "salao-beleza", "name": "Sal\u00e3o de Beleza",
        "description": "Sal\u00f5es de beleza, barbearias e esmalterias. Agenda hor\u00e1rios, mostra servi\u00e7os e captura clientes.",
        "category": "Beleza", "icon": "\U0001F487\u200D\u2640\uFE0F",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F487\u200D\u2640\uFE0F Bem-vindo ao *Sal\u00e3o Glamour* \u2728\n\nAqui sua beleza \u00e9 nossa prioridade!\n\nComo posso te ajudar?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma op\u00e7\u00e3o:","variable":"interesse","options":[
                {"label":"\U0001F4C5 Agendar hor\u00e1rio","value":"agendar","next":"tipo_servico"},
                {"label":"\U0001F4B0 Ver servi\u00e7os","value":"servicos","next":"info_servicos"},
                {"label":"\U0001F381 Promo\u00e7\u00f5es","value":"promocoes","next":"info_promocoes"},
                {"label":"\U0001F4CD Localiza\u00e7\u00e3o","value":"localizacao","next":"info_localizacao"}
            ]},
            {"id":"tipo_servico","type":"question","content":"Qual servi\u00e7o voc\u00ea quer agendar?","variable":"servico","options":[
                {"label":"\U0001F487 Corte de cabelo","value":"corte","next":"captura_data"},
                {"label":"\U0001F3A8 Colora\u00e7\u00e3o","value":"coloracao","next":"captura_data"},
                {"label":"\U0001F485 Manicure/Pedicure","value":"manicure","next":"captura_data"},
                {"label":"\u2728 Escova progressiva","value":"progressiva","next":"captura_data"}
            ]},
            {"id":"info_servicos","type":"message","content":"\U0001F4B0 *Nossos servi\u00e7os:*\n\n\U0001F487 *Cabelo:*\n\u2022 Corte feminino - R$ 80\n\u2022 Corte masculino - R$ 50\n\u2022 Escova - R$ 60\n\u2022 Colora\u00e7\u00e3o - R$ 200 a R$ 500\n\u2022 Progressiva - R$ 350\n\n\U0001F485 *Unhas:*\n\u2022 Manicure - R$ 40\n\u2022 Pedicure - R$ 45\n\u2022 Gel/Unha de fibra - R$ 120\n\n\U0001F484 *Maquiagem:*\n\u2022 Maquiagem social - R$ 150\n\n\u2728 Pacotes com 15% de desconto!","next":"tipo_servico"},
            {"id":"info_promocoes","type":"message","content":"\U0001F381 *Promo\u00e7\u00f5es do m\u00eas:*\n\n\u2728 Ter\u00e7a da Beleza: 20% off em todos os servi\u00e7os\n\U0001F485 Quarta de Manicure: combo m\u00e3o + p\u00e9 por R$ 70\n\U0001F470 Noivas: pacote completo com 30% off\n\U0001F382 Aniversariante do m\u00eas: ganhe uma hidrata\u00e7\u00e3o gr\u00e1tis!\n\n\U0001F4F7 Siga @salaoglamour para mais novidades","next":"menu_principal"},
            {"id":"info_localizacao","type":"message","content":"\U0001F4CD *Nossa localiza\u00e7\u00e3o:*\n\n\U0001F3E2 Rua Augusta, 1500 - Cerqueira C\u00e9sar\nS\u00e3o Paulo - SP\n\n\u23F0 *Funcionamento:*\nSeg a Sex: 9h \u00e0s 20h\nS\u00e1bado: 9h \u00e0s 18h\nDomingo: Fechado\n\n\U0001F697 Estacionamento conveniado!","next":"menu_principal"},
            {"id":"captura_data","type":"question","content":"Para qual per\u00edodo voc\u00ea quer agendar?","variable":"periodo","options":[
                {"label":"Manh\u00e3","value":"manha","next":"captura_nome"},
                {"label":"Tarde","value":"tarde","next":"captura_nome"},
                {"label":"Noite","value":"noite","next":"captura_nome"}
            ]},
            {"id":"captura_nome","type":"input","content":"Me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"{{nome}}, me informe seu *WhatsApp com DDD*:","variable":"telefone","next":"confirmacao"},
            {"id":"confirmacao","type":"message","content":"\u2705 *Agendamento solicitado!*\n\n\U0001F487 Servi\u00e7o: {{servico}}\n\u23F0 Per\u00edodo: {{periodo}}\n\U0001F464 {{nome}}\n\U0001F4F1 {{telefone}}\n\nConfirmaremos o hor\u00e1rio exato em at\u00e9 30 minutos pelo WhatsApp.\n\nAt\u00e9 breve! \u2728","next":"end"},
            {"id":"end","type":"end","content":"Obrigado por escolher o Sal\u00e3o Glamour! \U0001F487\u200D\u2640\uFE0F\u2728"}
        ]
    },
    "veiculos": {
        "slug": "veiculos", "name": "Loja de Ve\u00edculos",
        "description": "Atendimento para lojas de carros e motos. Apresenta o estoque, qualifica o cliente e encaminha para o vendedor.",
        "category": "Ve\u00edculos", "icon": "\U0001F697",
        "nodes": [
            {"id":"boas_vindas","type":"message","content":"Ol\u00e1! \U0001F697 Bem-vindo \u00e0 *AutoShow Ve\u00edculos* \U0001F3CD\uFE0F\n\nSou a Bia, assistente virtual. Posso te ajudar a encontrar o ve\u00edculo dos seus sonhos!\n\nComo posso te ajudar hoje?","next":"menu_principal"},
            {"id":"menu_principal","type":"question","content":"Escolha uma das op\u00e7\u00f5es abaixo:","variable":"interesse","options":[
                {"label":"\U0001F697 Ver carros","value":"carro","next":"tipo_carro"},
                {"label":"\U0001F3CD\uFE0F Ver motos","value":"moto","next":"tipo_moto"},
                {"label":"\U0001F4B0 Financiamento","value":"financiamento","next":"captura_nome"},
                {"label":"\U0001F4DE Falar com vendedor","value":"vendedor","next":"captura_nome"}
            ]},
            {"id":"tipo_carro","type":"question","content":"Que tipo de carro voc\u00ea procura?","variable":"tipo_veiculo","options":[
                {"label":"SUV","value":"suv","next":"orcamento"},
                {"label":"Sedan","value":"sedan","next":"orcamento"},
                {"label":"Hatch","value":"hatch","next":"orcamento"},
                {"label":"Picape","value":"picape","next":"orcamento"}
            ]},
            {"id":"tipo_moto","type":"question","content":"Que tipo de moto voc\u00ea quer?","variable":"tipo_veiculo","options":[
                {"label":"Esportiva","value":"esportiva","next":"orcamento"},
                {"label":"Scooter","value":"scooter","next":"orcamento"},
                {"label":"Custom","value":"custom","next":"orcamento"}
            ]},
            {"id":"orcamento","type":"question","content":"Qual \u00e9 a sua faixa de or\u00e7amento?","variable":"orcamento","options":[
                {"label":"At\u00e9 R$ 40.000","value":"ate_40k","next":"captura_nome"},
                {"label":"R$ 40.000 - R$ 80.000","value":"40k_80k","next":"captura_nome"},
                {"label":"R$ 80.000 - R$ 150.000","value":"80k_150k","next":"captura_nome"},
                {"label":"Acima de R$ 150.000","value":"acima_150k","next":"captura_nome"}
            ]},
            {"id":"captura_nome","type":"input","content":"Excelente! J\u00e1 temos op\u00e7\u00f5es perfeitas para voc\u00ea. \n\nPara enviar a proposta, por favor me diga seu *nome*:","variable":"nome","next":"captura_telefone"},
            {"id":"captura_telefone","type":"input","content":"Prazer, {{nome}}! \n\nAgora me passe seu *WhatsApp com DDD* para que um de nossos vendedores entre em contato:","variable":"telefone","next":"resumo"},
            {"id":"resumo","type":"message","content":"Perfeito, {{nome}}! \u2705\n\nResumo do seu interesse:\n\U0001F697 Ve\u00edculo: {{tipo_veiculo}}\n\U0001F4B0 Or\u00e7amento: {{orcamento}}\n\U0001F4F1 Contato: {{telefone}}\n\nEm at\u00e9 30 minutos um vendedor entrar\u00e1 em contato com voc\u00ea!\n\nEnquanto isso, pode nos seguir no Instagram @autoshowveiculos","next":"humano"},
            {"id":"humano","type":"human","content":""}
        ]
    }
}

os.makedirs("templates", exist_ok=True)
os.makedirs("backend/templates", exist_ok=True)

for slug, data in TEMPLATES.items():
    # Salva na pasta templates/
    path1 = f"templates/{slug}.json"
    with open(path1, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK: {path1}")

    # Salva tambem em backend/templates/ (para o Render)
    path2 = f"backend/templates/{slug}.json"
    with open(path2, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"OK: {path2}")

print("\nTodos os 8 templates criados com sucesso!")
