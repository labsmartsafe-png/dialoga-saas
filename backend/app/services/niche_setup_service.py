"""
Fase D.1 — Pacotes de nicho prontos.

Cria fluxos guiados iniciais por nicho e retorna sugestões de tags,
pipeline, tipos de agendamento e base de conhecimento exemplo.

A primeira versão é propositalmente segura:
- cria apenas um novo Flow;
- não altera fluxos existentes;
- não indexa IA automaticamente;
- não conecta WhatsApp automaticamente.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import Flow, User


def _node(node_id: str, ntype: str, content: str = "", **extra) -> dict:
    data = {"id": node_id, "type": ntype, "content": content}
    data.update(extra)
    return data


def _input(node_id: str, content: str, variable: str, next_id: str) -> dict:
    return _node(node_id, "input", content, variable=variable, next=next_id)


def _msg(node_id: str, content: str, next_id: Optional[str] = None) -> dict:
    data = _node(node_id, "message", content)
    if next_id:
        data["next"] = next_id
    return data


def _question(node_id: str, content: str, variable: str, options: list[dict]) -> dict:
    return _node(node_id, "question", content, variable=variable, options=options)


PACKAGES: Dict[str, Dict[str, Any]] = {
    "clinica": {
        "title": "Clínica / Odonto",
        "description": "Qualifica interessados e conduz para avaliação/consulta.",
        "pipeline_type": "clinica",
        "appointment_types": ["avaliacao", "consulta"],
        "suggested_tags": ["avaliacao", "procedimento", "urgente", "retorno", "lead_quente"],
        "knowledge_base_seed": """Informações base para clínica/odontologia:\n- Nome da clínica: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Procedimentos principais: limpeza, clareamento, harmonização, avaliação, implantes, estética facial.\n- Formas de pagamento: Pix, cartão, dinheiro.\n- Política de agendamento: confirmar data e horário com atendente.\n- Caso a IA não saiba responder, encaminhar para atendimento humano.""",
        "flow_name": "Clínica - Triagem e Avaliação",
        "flow_description": "Fluxo pronto para clínicas e odontologia: qualifica o lead e encaminha para agendamento.",
        "nodes": [
            _msg("inicio", "Olá! Seja bem-vindo(a). Vou fazer uma triagem rápida para te direcionar ao melhor atendimento.", "procedimento"),
            _input("procedimento", "Qual procedimento ou atendimento você procura?", "procedimento_interesse", "nome"),
            _input("nome", "Perfeito. Qual é o seu nome?", "nome", "telefone"),
            _input("telefone", "Informe um telefone para contato, por favor.", "telefone", "horario"),
            _input("horario", "Você tem preferência de dia ou horário para uma avaliação/consulta?", "preferencia_horario", "resumo"),
            _msg("resumo", "Obrigado, {{nome}}!\n\nResumo:\nProcedimento: {{procedimento_interesse}}\nTelefone: {{telefone}}\nPreferência: {{preferencia_horario}}\n\nVou encaminhar para um atendente confirmar disponibilidade e valores.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "petshop": {
        "title": "Petshop",
        "description": "Agenda banho/tosa e organiza dados do pet.",
        "pipeline_type": "petshop",
        "appointment_types": ["banho_tosa", "retorno"],
        "suggested_tags": ["banho_tosa", "vacina", "retorno", "cliente_recorrente", "urgente"],
        "knowledge_base_seed": """Informações base para petshop:\n- Nome do petshop: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Serviços: banho, tosa, tosa higiênica, hidratação, vacina, consulta parceira.\n- Informe preços aproximados por porte, se desejar.\n- Política: confirmar agenda com atendente antes de concluir.\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Petshop - Banho e Tosa",
        "flow_description": "Fluxo pronto para petshop: coleta serviço, pet, porte e preferência de horário.",
        "nodes": [
            _msg("inicio", "Olá! Seja bem-vindo(a). Vou te ajudar com o atendimento do seu pet. 🐾", "servico"),
            _question("servico", "Qual serviço você procura?", "servico_pet", [
                {"label": "Banho", "value": "banho", "next": "nome_pet"},
                {"label": "Tosa", "value": "tosa", "next": "nome_pet"},
                {"label": "Banho e tosa", "value": "banho_tosa", "next": "nome_pet"},
                {"label": "Outro", "value": "outro", "next": "nome_pet"},
            ]),
            _input("nome_pet", "Qual é o nome do pet?", "nome_pet", "porte"),
            _question("porte", "Qual é o porte do pet?", "porte_pet", [
                {"label": "Pequeno", "value": "pequeno", "next": "preferencia"},
                {"label": "Médio", "value": "medio", "next": "preferencia"},
                {"label": "Grande", "value": "grande", "next": "preferencia"},
            ]),
            _input("preferencia", "Qual dia/horário você prefere para o atendimento?", "preferencia_horario", "resumo"),
            _msg("resumo", "Obrigado!\n\nResumo:\nServiço: {{servico_pet}}\nPet: {{nome_pet}}\nPorte: {{porte_pet}}\nPreferência: {{preferencia_horario}}\n\nVou encaminhar para confirmar a agenda.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "veiculos": {
        "title": "Veículos",
        "description": "Qualifica interesse e agenda visita/test-drive.",
        "pipeline_type": "veiculos",
        "appointment_types": ["visita", "test_drive"],
        "suggested_tags": ["test_drive", "financiamento", "troca", "lead_quente", "proposta"],
        "knowledge_base_seed": """Informações base para loja de veículos:\n- Nome da loja: [preencher]\n- Endereço: [preencher]\n- Horário de atendimento: [preencher]\n- Estoque principal: [preencher modelos]\n- Aceita financiamento? [sim/não]\n- Aceita veículo na troca? [sim/não]\n- Condições e documentos necessários: [preencher]\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Veículos - Interesse e Visita",
        "flow_description": "Fluxo pronto para loja de veículos: qualifica interesse e agenda visita/test-drive.",
        "nodes": [
            _msg("inicio", "Olá! Vou te ajudar a encontrar o veículo ideal e, se fizer sentido, agendar uma visita/test-drive.", "modelo"),
            _input("modelo", "Qual veículo ou modelo você está procurando?", "modelo_interesse", "compra"),
            _question("compra", "Você pretende comprar de qual forma?", "forma_compra", [
                {"label": "À vista", "value": "avista", "next": "troca"},
                {"label": "Financiamento", "value": "financiamento", "next": "troca"},
                {"label": "Ainda estou pesquisando", "value": "pesquisa", "next": "troca"},
            ]),
            _question("troca", "Você tem veículo para dar na troca?", "tem_troca", [
                {"label": "Sim", "value": "sim", "next": "prazo"},
                {"label": "Não", "value": "nao", "next": "prazo"},
            ]),
            _input("prazo", "Qual seu prazo para compra ou visita?", "prazo_compra", "resumo"),
            _msg("resumo", "Resumo do interesse:\nVeículo: {{modelo_interesse}}\nForma: {{forma_compra}}\nTroca: {{tem_troca}}\nPrazo: {{prazo_compra}}\n\nVou encaminhar para um consultor verificar disponibilidade e agendar.", "humano"),
            _node("humano", "human"),
        ],
        "start_node_id": "inicio",
    },
    "suporte_tecnico": {
        "title": "Suporte técnico",
        "description": "Triagem de técnico/cliente com chamado, local e dúvida.",
        "pipeline_type": "suporte_tecnico",
        "appointment_types": ["suporte"],
        "suggested_tags": ["chamado", "urgente", "campo", "aguardando_humano", "suporte_n2"],
        "knowledge_base_seed": """Informações base para suporte técnico:\n- Contatos do suporte operacional: [preencher]\n- Horário de atendimento: [preencher]\n- Procedimento para abertura de chamado: [preencher]\n- Dados necessários: número do chamado, local, descrição da dúvida/problema.\n- Casos urgentes: [preencher regra]\n- Caso a IA não saiba responder, encaminhar para humano.""",
        "flow_name": "Suporte Técnico - Triagem de Campo",
        "flow_description": "Fluxo pronto para suporte técnico: valida contato com suporte, coleta chamado, local e dúvida.",
        "nodes": [
            _msg("recepcao", "Olá! Recebemos sua solicitação. Antes de encaminhar o atendimento, vamos fazer uma triagem rápida.", "pergunta_suporte"),
            _question("pergunta_suporte", "Você já fez contato com o setor de Suporte Operacional?", "fez_contato_suporte", [
                {"label": "Sim, já fiz contato", "value": "sim", "next": "pede_chamado"},
                {"label": "Não, ainda não fiz contato", "value": "nao", "next": "contatos_suporte"},
            ]),
            _input("pede_chamado", "Perfeito. Informe o número do chamado que você está atendendo.", "numero_chamado", "pede_local"),
            _input("pede_local", "Agora informe o local do atendimento.", "local_atendimento", "pede_duvida"),
            _input("pede_duvida", "Descreva qual é a dúvida ou dificuldade encontrada.", "duvida_tecnica", "resumo"),
            _msg("resumo", "Obrigado pelas informações.\n\nChamado: {{numero_chamado}}\nLocal: {{local_atendimento}}\nDúvida: {{duvida_tecnica}}\n\nAguarde. Sua solicitação será encaminhada para atendimento humano.", "humano"),
            _node("humano", "human"),
            _msg("contatos_suporte", "Para seguir, é necessário primeiro fazer contato com o Suporte Operacional.\n\nWhatsApp/Telefone: (XX) XXXXX-XXXX\nE-mail: suporte@suaempresa.com.br\n\nApós abrir o chamado, envie nova mensagem informando número do chamado, local e dúvida.", "fim"),
            _node("fim", "end"),
        ],
        "start_node_id": "recepcao",
    },
}


def list_packages() -> List[Dict[str, Any]]:
    return [
        {
            "id": key,
            "title": pkg["title"],
            "description": pkg["description"],
            "pipeline_type": pkg["pipeline_type"],
            "appointment_types": pkg["appointment_types"],
            "suggested_tags": pkg["suggested_tags"],
        }
        for key, pkg in PACKAGES.items()
    ]


def get_package(package_id: str) -> Dict[str, Any]:
    if package_id not in PACKAGES:
        raise KeyError(package_id)
    return PACKAGES[package_id]


def apply_package(db: Session, user: User, package_id: str, business_name: Optional[str] = None) -> Dict[str, Any]:
    pkg = get_package(package_id)
    name_suffix = f" - {business_name.strip()}" if business_name else ""
    flow = Flow(
        owner_id=user.id,
        name=f"{pkg['flow_name']}{name_suffix}",
        description=pkg["flow_description"],
        nodes=deepcopy(pkg["nodes"]),
        start_node_id=pkg["start_node_id"],
        active=True,
        template_slug=f"niche:{package_id}",
        mode="guided",
    )
    db.add(flow)
    db.commit()
    db.refresh(flow)
    return {
        "ok": True,
        "package_id": package_id,
        "flow_id": flow.id,
        "flow_name": flow.name,
        "pipeline_type": pkg["pipeline_type"],
        "appointment_types": pkg["appointment_types"],
        "suggested_tags": pkg["suggested_tags"],
        "knowledge_base_seed": pkg["knowledge_base_seed"],
        "next_steps": [
            "Revise o fluxo criado no Builder.",
            "Cole o texto sugerido em IA > Base de conhecimento e adapte ao negócio.",
            "Conecte ou selecione este fluxo na conexão WhatsApp.",
            "Configure ticket médio no Dashboard para ROI.",
            "Crie agendamentos usando os tipos sugeridos para atualizar o pipeline.",
        ],
    }
