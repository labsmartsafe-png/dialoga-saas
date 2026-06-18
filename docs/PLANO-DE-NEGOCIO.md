# 📈 WhatsFlow SaaS — Plano de Negócio

## 1. Sumário Executivo

O WhatsFlow é uma plataforma SaaS que democratiza a criação de chatbots para WhatsApp no Brasil. Com templates prontos por nicho e uma interface visual simples, permite que empresas de qualquer porte automatizem atendimento, vendas e captação de leads em minutos — sem programação.

## 2. Análise de Mercado

### 2.1 Tamanho do Mercado
- **TAM (Total Addressable Market)**: R$ 8 bilhões/ano
  - Mercado global de automação de atendimento.
- **SAM (Serviceable Addressable Market)**: R$ 1.2 bilhões/ano
  - PMEs brasileiras que usam WhatsApp comercialmente.
- **SOM (Serviceable Obtainable Market)**: R$ 60 milhões/ano
  - Mercado realista nos primeiros 3 anos.

### 2.2 Tendências
- WhatsApp Business API crescendo 40% ao ano no Brasil.
- 92% dos consumidores brasileiros preferem WhatsApp a outros canais.
- Pandemia acelerou digitalização de PMEs em 3-5 anos.

### 2.3 Concorrentes
| Concorrente | Preço | Pontos fracos |
|-------------|-------|---------------|
| Take.blip | R$ 800+/mês | Complexo, exige treinamento |
| Landbot | R$ 400+/mês | Foco em chat web, pouco WhatsApp |
| Chatbot Brasil | R$ 200+/mês | Sem templates por nicho |
| Zenvia | R$ 500+/mês | Foco em call center |

## 3. Produto

### 3.1 Funcionalidades Core (MVP)
- ✅ Editor visual de fluxos
- ✅ 8 templates por nicho
- ✅ Simulador integrado
- ✅ Captura automática de leads
- ✅ Exportação CSV
- ✅ Dashboard de métricas
- ✅ Autenticação JWT
- 🔄 Integração WhatsApp Cloud API (em desenvolvimento)

### 3.2 Roadmap (12 meses)
| Trimestre | Entregas |
|-----------|----------|
| Q1 | MVP + landing page + primeiros clientes |
| Q2 | Integração WhatsApp real + editor drag-and-drop |
| Q3 | Marketplace de templates da comunidade |
| Q4 | Integração CRMs + analytics avançado |

### 3.3 Tecnologia
- **Backend**: Python + FastAPI + SQLAlchemy + PostgreSQL
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Hospedagem**: Render (baixo custo, fácil escala)
- **Autenticação**: JWT (stateless, escalável)
- **Integração**: WhatsApp Cloud API (Meta)

## 4. Modelo de Negócio

### 4.1 Pricing
| Plano | Preço Mensal | Clientes-Alvo | Margem |
|-------|--------------|---------------|--------|
| Básico | R$ 97 | Freelancers, MEI | 75% |
| Profissional | R$ 297 | PMEs | 80% |
| Enterprise | R$ 697 | Empresas médias | 85% |

### 4.2 Receita Recorrente Projetada
| Mês | Clientes Pagantes | MRR |
|-----|-------------------|-----|
| 3 | 5 | R$ 1.485 |
| 6 | 25 | R$ 7.425 |
| 9 | 100 | R$ 29.700 |
| 12 | 200 | R$ 59.400 |

### 4.3 Unit Economics
- **CAC (Custo de Aquisição)**: R$ 120
- **LTV (Lifetime Value)**: R$ 2.970 (30 meses × R$ 99 médio)
- **LTV/CAC**: 24.7x ✅
- **Payback**: 1.2 meses

## 5. Marketing e Vendas

### 5.1 Estratégia de Aquisição
1. **SEO**: Blog com conteúdo por nicho ("chatbot para clínica", "chatbot imobiliária").
2. **Anúncios pagos**: Google Ads + Meta Ads focados em PMEs.
3. **Parcerias**: Agências digitais, contadores, consultorias.
4. **Indicação**: Programa de afiliados (20% recorrente por 12 meses).

### 5.2 Funil de Conversão
```
Visitantes landing → Cadastro grátis → Uso (trial 7 dias) → Plano pago
        1000              100               40                15
```

### 5.3 Canais
- **Orgânico**: Blog, YouTube, LinkedIn.
- **Pago**: Google Ads, Meta Ads, TikTok Ads.
- **Direto**: Outbound para agências digitais.

## 6. Equipe

### 6.1 Estrutura Inicial (5 pessoas)
- 1 CEO/Founder
- 2 Engenheiros full-stack
- 1 Designer/Product
- 1 Growth Marketing

### 6.2 Estrutura em 12 meses (12 pessoas)
- Adicionar: Customer Success (2), DevOps, Vendas, Marketing, Suporte.

## 7. Projeção Financeira

### 7.1 Investimento Inicial
| Item | Valor |
|------|-------|
| Desenvolvimento MVP | R$ 80.000 |
| Marketing inicial | R$ 30.000 |
| Infraestrutura | R$ 20.000 |
| Jurídico/Contábil | R$ 10.000 |
| Reserva | R$ 60.000 |
| **Total** | **R$ 200.000** |

### 7.2 Custos Operacionais Mensais
| Item | Valor |
|------|-------|
| Salários (5 pessoas) | R$ 45.000 |
| Infraestrutura | R$ 2.000 |
| Marketing | R$ 8.000 |
| Ferramentas | R$ 1.500 |
| Outros | R$ 3.500 |
| **Total** | **R$ 60.000** |

### 7.3 Ponto de Equilíbrio
Com ticket médio de R$ 200/mês e margem de 80%:
- Break-even: **75 clientes pagantes** (mês 8-9).

## 8. Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Mudança na API do WhatsApp | Média | Alto | Manter equipe técnica atualizada, diversificar canais |
| Concorrente com mais recurso | Alta | Médio | Focar em nichos específicos, comunidade |
| Câmbio / inflação | Média | Médio | Pricing em BRL, plano anual |
| Dependência de Meta | Média | Alto | Diversificar para outros canais (Telegram, SMS) |

## 9. Conclusão

O WhatsFlow está posicionado para capturar uma fatia significativa do mercado brasileiro de automação de WhatsApp. Com um produto simples, templates prontos e preço acessível, oferece uma proposta de valor clara para PMEs que precisam automatizar atendimento sem investir em desenvolvimento customizado.

**Próximos passos**:
1. Lançar MVP e validar com 50 usuários.
2. Iterar com base em feedback.
3. Construir comunidade de templates.
4. Escalar para R$ 500k MRR em 18 meses.

---
*Documento atualizado em Junho/2026.*
