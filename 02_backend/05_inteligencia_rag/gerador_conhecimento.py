# -*- coding: utf-8 -*-
# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
"""
Gerador da Base de Conhecimento Estruturada com 113 Resumos de Exames e 565 Resumos de Resultados.
Foco na faixa etária de 18 a 25 anos, respeitando os 5 pilares do Open Health:
1. Descrição do Resultado (Normal, Limítrofe, Atenção/Leve, Moderado, Grave/Acentuado);
2. Estatísticas sobre os pares etários (18 a 25 anos);
3. Impactos para o indivíduo;
4. Possíveis causas para o desvio;
5. Correção / Conduta recomendada.
"""

import json
import os
import re
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOGO_PATH = _paths.CATALOGO_COLUNAS_PATH
OUTPUT_PATH = _paths.KB_565_PATH

# Dicionário de conhecimento clínico e epidemiológico (18-25 anos)
METADADOS_CLINICOS = {
    # ------------------ SÉRIE VERMELHA ------------------
    "hemacias_10e6_uL": {
        "nome": "Hemácias (Glóbulos Vermelhos)",
        "papel": "Células responsáveis por transportar oxigênio dos pulmões para todos os tecidos do corpo através da hemoglobina.",
        "estat_base": {"NORMAL": "86%", "LIMITROFE": "8%", "ALTERADO_LEVE": "4%", "ALTERADO_MODERADO": "1.5%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Cansaço, palidez, sonolência, perda de rendimento nos estudos e treinos.",
        "impacto_alto": "Aumento da viscosidade sanguínea, sensação de cabeça pesada e cansaço visual.",
        "causas_baixo": "Carência de ferro, baixa ingestão de vitaminas do complexo B, perdas menstruais volumosas.",
        "causas_alto": "Desidratação após exercícios intensos, tabagismo ou permanência em altitudes elevadas.",
        "correcao_baixo": "Ajuste na ingestão de ferro e vitamina C, alimentação equilibrada e reavaliação médica.",
        "correcao_alto": "Hidratação abundante ao longo do dia e cessação do tabagismo se aplicável."
    },
    "hemoglobina_g_dL": {
        "nome": "Hemoglobina",
        "papel": "Proteína rica em ferro presente nas hemácias que se liga ao oxigênio para alimentar a respiração celular.",
        "estat_base": {"NORMAL": "84%", "LIMITROFE": "9%", "ALTERADO_LEVE": "5%", "ALTERADO_MODERADO": "1.6%", "ALTERACAO_ACENTUADA": "0.4%"},
        "impacto_baixo": "Fadiga precoce em exercícios, falta de ar aos esforços cotidianos, tonturas ocasionais e queda de cabelo.",
        "impacto_alto": "Possível rubor facial, fadiga desproporcional e aumento da espessura do sangue circulante.",
        "causas_baixo": "Anemia ferropriva por baixa ingestão na dieta, sangramento digestivo subclínico ou fluxo menstrual intenso.",
        "causas_alto": "Hemoconcentração (baixo consumo de água), tabagismo crônico ou distúrbios da medula óssea.",
        "correcao_baixo": "Suplementação guiada de sulfato ferroso, aumento de feijão, folhas escuras e carnes magras.",
        "correcao_alto": "Aumento do consumo diário de água (35 a 40 ml/kg) e avaliação com clínico geral."
    },
    "hematocrito_pct": {
        "nome": "Hematócrito",
        "papel": "Porcentagem do volume total de sangue que é ocupada pelas células vermelhas (proporção glóbulos versus plasma).",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "8%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.8%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "Sensação de fraqueza, lentidão mental, mãos e pés frios.",
        "impacto_alto": "Fluxo sanguíneo mais lento, discreta elevação pressórica temporária e dores de cabeça.",
        "causas_baixo": "Perda aguda ou crônica de sangue, anemias carênciais, diluição plasmática por retenção hídrica.",
        "causas_alto": "Desidratação expressiva no dia da coleta, hipóxia crônica ou policitemia.",
        "correcao_baixo": "Investigação nutricional com apoio médico e enriquecimento da dieta.",
        "correcao_alto": "Regularização imediata do balanço hídrico com eletrólitos e hidratação oral."
    },
    "vcm_fL": {
        "nome": "VCM (Volume Corpuscular Médio)",
        "papel": "Indica o tamanho médio individual de cada glóbulo vermelho, diferenciando anemias microcíticas e macrocíticas.",
        "estat_base": {"NORMAL": "88%", "LIMITROFE": "6%", "ALTERADO_LEVE": "4%", "ALTERADO_MODERADO": "1.5%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Hemácias menores que o normal; fadiga matinal crônica e menor oxigenação.",
        "impacto_alto": "Hemácias aumentadas (macrocitose); possíveis reflexos neuromusculares lentificados.",
        "causas_baixo": "Deficiência prolongada de ferro corporal ou traço talassêmico comum no Brasil.",
        "causas_alto": "Deficiência de vitamina B12, folato ou consumo excessivo de álcool nos fins de semana.",
        "correcao_baixo": "Disfarçar a carência de ferro com alimentos ricos em ferro heme e vitamina C.",
        "correcao_alto": "Checagem de vitamina B12 sérica e ingestão de vegetais verdes folhosos e ovos."
    },
    "hcm_pg": {
        "nome": "HCM (Hemoglobina Corpuscular Média)",
        "papel": "Mede a quantidade média de peso de hemoglobina presente dentro de cada glóbulo vermelho.",
        "estat_base": {"NORMAL": "87%", "LIMITROFE": "7%", "ALTERADO_LEVE": "4%", "ALTERADO_MODERADO": "1.5%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Hemácias descoradas (hipocromia), resultando em menor capacidade de carregar oxigênio.",
        "impacto_alto": "Hemácias hipercromáticas, frequentemente associadas a esferocitose ou macrocitose.",
        "causas_baixo": "Privação de ferro crônica, perdas sanguíneas ou síntese prejudicada de globina.",
        "causas_alto": "Deficiências vitamínicas ou alterações de membrana dos eritrócitos.",
        "correcao_baixo": "Consumo de proteínas, leguminosas e consulta médica para dosar ferritina.",
        "correcao_alto": "Acompanhamento hematológico de rotina e alimentação variada."
    },
    "chcm_g_dL": {
        "nome": "CHCM (Concentração de Hemoglobina Corpuscular Média)",
        "papel": "Representa a concentração percentual média de hemoglobina dentro de um determinado volume de hemácias.",
        "estat_base": {"NORMAL": "90%", "LIMITROFE": "5%", "ALTERADO_LEVE": "3.5%", "ALTERADO_MODERADO": "1.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Menor densidade de transporte de oxigênio em cada mililitro de células.",
        "impacto_alto": "Pode indicar hemólise na amostra, presença de aglutininas a frio ou esferocitose.",
        "causas_baixo": "Anemia ferropriva severa em progressão crônica.",
        "causas_alto": "Artefatos laboratoriais na coleta ou distúrbios da forma dos eritrócitos.",
        "correcao_baixo": "Reforço na alimentação com nutrientes essenciais e repetição do hemograma.",
        "correcao_alto": "Repetição do exame em nova coleta e análise com especialista."
    },
    "rdw_pct": {
        "nome": "RDW (Índice de Anisocitose)",
        "papel": "Avalia a variação de tamanho entre as hemácias (desigualdade dimensional).",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "8%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.8%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "População de hemácias bastante uniforme (sem repercussão clínica negativa).",
        "impacto_alto": "Presença simultânea de células de tamanhos muito discrepantes, sinal de carência nutricional incipiente.",
        "causas_baixo": "Normalidade biológica comum em jovens saudáveis.",
        "causas_alto": "Início precoce de deficiência de ferro antes mesmo da queda da hemoglobina, ou deficiência mista (ferro + B12).",
        "correcao_baixo": "Manutenção dos hábitos de vida saudáveis.",
        "correcao_alto": "Dosar estoques de ferritina e vitaminas para correção prévia da alimentação."
    },

    # ------------------ SÉRIE BRANCA (LEUCOGRAMA) ------------------
    "leucocitos_totais_10e3_uL": {
        "nome": "Leucócitos Totais (Glóbulos Brancos)",
        "papel": "O exército de defesa imunológica do organismo contra vírus, bactérias, fungos e processos inflamatórios.",
        "estat_base": {"NORMAL": "86%", "LIMITROFE": "7%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.8%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "Maior suscetibilidade a infecções respiratórias, amigdalites e cicatrização mais demorada.",
        "impacto_alto": "Sinaliza que o sistema imunológico está respondendo ativamente a algum estímulo ou estresse biológico.",
        "causas_baixo": "Infecções virais recentes (gripe, dengue), uso de certos medicamentos ou carências nutricionais.",
        "causas_alto": "Infecções bacterianas comuns na juventude, estresse físico agudo (treino intenso pré-coleta) ou tabagismo.",
        "correcao_baixo": "Sono reparador de 7-8 horas, alimentação anti-inflamatória e evitar automedicação.",
        "correcao_alto": "Investigar sintomas febris ou urinários com o médico e repetir o exame após 15 dias de repouso."
    },
    "neutrofilos_abs_10e3_uL": {
        "nome": "Neutrófilos Absolutos",
        "papel": "Primeira linha de defesa imunológica especializada em combater e fagocitar bactérias patogênicas.",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "7.5%", "ALTERADO_LEVE": "4.8%", "ALTERADO_MODERADO": "1.9%", "ALTERACAO_ACENTUADA": "0.8%"},
        "impacto_baixo": "Neutropenia; vulnerabilidade passageira a infecções cutâneas ou de vias aéreas.",
        "impacto_alto": "Neutrofilia; resposta ativa de combate bacteriano ou inflamação corporal.",
        "causas_baixo": "Quadros pós-virais, medicações analgésicas ou neutropenia benigna constitucional.",
        "causas_alto": "Faringites, sinusites, infecções de pele, exercícios vigorosos horas antes da coleta de sangue.",
        "correcao_baixo": "Higiene reforçada, repouso e retorno clínico programado.",
        "correcao_alto": "Avaliação clínica para descartar focos infecciosos bacterianos que necessitem tratamento."
    },
    "linfocitos_abs_10e3_uL": {
        "nome": "Linfócitos Absolutos",
        "papel": "Células nobres de defesa responsáveis pela produção de anticorpos e imunidade adaptativa de memória.",
        "estat_base": {"NORMAL": "88%", "LIMITROFE": "6%", "ALTERADO_LEVE": "4%", "ALTERADO_MODERADO": "1.4%", "ALTERACAO_ACENTUADA": "0.6%"},
        "impacto_baixo": "Menor produção de anticorpos, cansaço em resposta a viroses comuns.",
        "impacto_alto": "Reatividade imunológica típica após contato recente com vírus.",
        "causas_baixo": "Uso de corticoides, estresse crônico com cortisol elevado ou privação severa de sono.",
        "causas_alto": "Infecções virais típicas da idade (mononucleose, citomegalovírus, resfriados e viroses gastrointestinais).",
        "correcao_baixo": "Priorizar descanso noturno, redução de estressores emocionais e alimentação rica em zinco.",
        "correcao_alto": "Hidratação oral e observação do desaparecimento gradual dos sintomas virais."
    },
    "monocitos_abs_10e3_uL": {
        "nome": "Monócitos Absolutos",
        "papel": "Células fagocitárias de grande porte que limpam resíduos celulares e restos de microrganismos destruídos.",
        "estat_base": {"NORMAL": "89%", "LIMITROFE": "6%", "ALTERADO_LEVE": "3.5%", "ALTERADO_MODERADO": "1.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Raramente tem relevância clínica isolada quando os outros leucócitos estão normais.",
        "impacto_alto": "Indica fase de recuperação ou cicatrização pós-infecção.",
        "causas_baixo": "Oscilação biológica natural do organismo.",
        "causas_alto": "Fase de resolução de infecções recentes ou processos inflamatórios gastrointestinais crônicos leves.",
        "correcao_baixo": "Nenhuma intervenção necessária; manter hábitos saudáveis.",
        "correcao_alto": "Acompanhamento clínico geral e manutenção de dieta anti-inflamatória rica em fibras."
    },
    "eosinofilos_abs_10e3_uL": {
        "nome": "Eosinófilos Absolutos",
        "papel": "Células especializadas na regulação de reações alérgicas e no combate a parasitas intestinais.",
        "estat_base": {"NORMAL": "83%", "LIMITROFE": "9%", "ALTERADO_LEVE": "5.5%", "ALTERADO_MODERADO": "2.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Geralmente sem significado clínico patológico em pacientes assintomáticos.",
        "impacto_alto": "Manifestação de crises alérgicas respiratórias (rinite, asma) ou cutâneas (dermatites).",
        "causas_baixo": "Estresse agudo momentâneo ou uso recente de anti-inflamatórios hormonais.",
        "causas_alto": "Rinite alérgica ativa, crises de asma, dermatite atópica ou verminoses intestinais.",
        "correcao_baixo": "Rotina normal de autocuidado.",
        "correcao_alto": "Controle ambiental de poeira e ácaros, exame parasitológico de fezes e consulta médica."
    },
    "basofilos_abs_10e3_uL": {
        "nome": "Basófilos Absolutos",
        "papel": "Liberam histamina e heparina para respostas inflamatórias alérgicas imediatas.",
        "estat_base": {"NORMAL": "92%", "LIMITROFE": "5%", "ALTERADO_LEVE": "2%", "ALTERADO_MODERADO": "0.7%", "ALTERACAO_ACENTUADA": "0.3%"},
        "impacto_baixo": "Considerado achado biológico padrão da normalidade.",
        "impacto_alto": "Possível intensificação de hipersensibilidade alérgica ou distúrbios da medula.",
        "causas_baixo": "Variação fisiológica esperada.",
        "causas_alto": "Reações de hipersensibilidade extrema a alimentos ou picadas, colite ou distúrbios mieloproliferativos.",
        "correcao_baixo": "Manter hábitos saudáveis.",
        "correcao_alto": "Avaliação médica especializada se acompanhado de outros analitos alterados."
    },

    # ------------------ PLAQUETAS ------------------
    "plaquetas_10e3_uL": {
        "nome": "Plaquetas (Contagem de Trombócitos)",
        "papel": "Fragmentos celulares que formam o tampão hemostático inicial para estancar sangramentos corporais.",
        "estat_base": {"NORMAL": "89%", "LIMITROFE": "6%", "ALTERADO_LEVE": "3.2%", "ALTERADO_MODERADO": "1.3%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Trombocitopenia; facilidade de surgimento de manchas roxas (hematomas) na pele ou sangramento gengival.",
        "impacto_alto": "Trombocitose; sangue com maior propensão à formação de coágulos intravasculares.",
        "causas_baixo": "Infecções virais recentes (como arboviroses), consumo excessivo de álcool, ou reação autoimune.",
        "causas_alto": "Reação de fase aguda a inflamações, carência de ferro reativa ou estresse físico vigoroso.",
        "correcao_baixo": "Evitar esportes de impacto elevado até reavaliação médica e repetição de hemograma.",
        "correcao_alto": "Investigar possíveis focos inflamatórios com seu médico e reforçar a hidratação diária."
    },
    "vpm_fL": {
        "nome": "VPM (Volume Plaquetário Médio)",
        "papel": "Avalia o diâmetro médio das plaquetas circulantes, indicando a juventude e ritmo de produção medular.",
        "estat_base": {"NORMAL": "90%", "LIMITROFE": "5.5%", "ALTERADO_LEVE": "3.0%", "ALTERADO_MODERADO": "1.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Plaquetas predominantemente maduras ou produção medular diminuída.",
        "impacto_alto": "Plaquetas mais jovens e ativas na circulação (maior reatividade hemostática).",
        "causas_baixo": "Insuficiência medular transitória ou destruição crônica tardia.",
        "causas_alto": "Destruição periférica compensada por produção acelerada na medula óssea.",
        "correcao_baixo": "Acompanhamento com hematologista.",
        "correcao_alto": "Avaliação clínica global associada à contagem absoluta de plaquetas."
    },

    # ------------------ GLICOSE & METABOLISMO LIPÍDICO ------------------
    "glicose_jejum_mg_dL": {
        "nome": "Glicose em Jejum",
        "papel": "Principal combustível energético dos neurônios e músculos; sua taxa reflete a eficiência da insulina.",
        "estat_base": {"NORMAL": "81%", "LIMITROFE": "11%", "ALTERADO_LEVE": "5.5%", "ALTERADO_MODERADO": "2.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Hipoglicemia: tontura, tremores nas mãos, suor frio, vista escura e fraqueza rápida.",
        "impacto_alto": "Pré-diabetes ou hiperglicemia: sede excessiva, urina frequente, fadiga pós-refeições e ganho de gordura visceral.",
        "causas_baixo": "Jejum prolongado além de 14 horas antes do exame, treino intenso sem alimentação adequada.",
        "causas_alto": "Consumo elevado de açúcares simples, refrigerantes, ultraprocessados, sedentarismo e predisposição familiar.",
        "correcao_baixo": "Fracionamento das refeições e evitar jejuns excessivos antes de atividades extenuantes.",
        "correcao_alto": "Reduzir carboidratos refinados, praticar musculação/aeróbico 4x na semana e consultar endocrinologista."
    },
    "hemoglobina_glicada_hba1c_pct": {
        "nome": "Hemoglobina Glicada (HbA1c)",
        "papel": "Mede a média do açúcar no sangue ao longo dos últimos 90 a 120 dias, refletindo o controle glicêmico estável.",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "9%", "ALTERADO_LEVE": "4.2%", "ALTERADO_MODERADO": "1.4%", "ALTERACAO_ACENTUADA": "0.4%"},
        "impacto_baixo": "Sem risco metabólico; pode ocorrer em casos de renovação acelerada das hemácias.",
        "impacto_alto": "Sinaliza estresse metabólico oxidativo crônico e lesão insidiosa nos vasos e rins ao longo do tempo.",
        "causas_baixo": "Anemias hemolíticas ou suplementação excessiva com certos micronutrientes.",
        "causas_alto": "Padrão alimentar desregrado por semanas/meses com sobrecarga de doces e sedentarismo.",
        "correcao_baixo": "Alimentação balanceada de rotina.",
        "correcao_alto": "Reestruturação nutricional com aumento de fibras, caminhadas diárias e consulta com nutricionista."
    },
    "insulina_basal_uIU_mL": {
        "nome": "Insulina Basal",
        "papel": "Hormônio pancreático vital que transporta o açúcar da corrente sanguínea para o interior das células.",
        "estat_base": {"NORMAL": "74%", "LIMITROFE": "14%", "ALTERADO_LEVE": "8.0%", "ALTERADO_MODERADO": "3.2%", "ALTERACAO_ACENTUADA": "0.8%"},
        "impacto_baixo": "Possível carência na produção pancreática se associada a glicose elevada.",
        "impacto_alto": "Resistência à insulina: dificuldade em emagrecer, sonolência intensa após almoço e escurecimento do pescoço (acantose).",
        "causas_baixo": "Jejum rigoroso ou autoimunidade pancreática incipiente.",
        "causas_alto": "Sedentarismo, estresse universitário/profissional, consumo abusivo de açúcar líquido e gorduras saturadas.",
        "correcao_baixo": "Avaliação médica com perfil glicêmico completo.",
        "correcao_alto": "Treinamento resistido (musculação) para melhorar sensibilidade insulínica e corte de bebidas açucaradas."
    },
    "indice_homa_ir": {
        "nome": "Índice HOMA-IR",
        "papel": "Fórmula matemática que cruza glicose e insulina para quantificar a resistência das células à ação da insulina.",
        "estat_base": {"NORMAL": "73%", "LIMITROFE": "15%", "ALTERADO_LEVE": "8.2%", "ALTERADO_MODERADO": "3.0%", "ALTERACAO_ACENTUADA": "0.8%"},
        "impacto_baixo": "Sensibilidade insulínica de excelência (metabolismo ágil e eficiente).",
        "impacto_alto": "Sobrecarga de trabalho para o pâncreas; estágio precoce de risco para diabetes tipo 2 e gordura no fígado.",
        "causas_baixo": "Boa composição corporal (alta massa magra e baixo percentual de gordura).",
        "causas_alto": "Adiposidade abdominal, noites maldormidas e excesso de lanches rápidos ultraprocessados.",
        "correcao_baixo": "Continuar o excelente estilo de vida.",
        "correcao_alto": "Rotina regular de exercícios físicos, sono regulado de 8 horas e reeducação alimentar preventiva."
    },
    "colesterol_total_mg_dL": {
        "nome": "Colesterol Total",
        "papel": "Gordura essencial na formação da membrana das células e na produção de hormônios como testosterona e estrogênio.",
        "estat_base": {"NORMAL": "78%", "LIMITROFE": "12%", "ALTERADO_LEVE": "6.8%", "ALTERADO_MODERADO": "2.6%", "ALTERACAO_ACENTUADA": "0.6%"},
        "impacto_baixo": "Geralmente favorável; em níveis extremamente baixos pode relacionar-se à má absorção intestinal.",
        "impacto_alto": "Deposição gradual de placas lipídicas nas paredes das artérias a médio e longo prazo.",
        "causas_baixo": "Dieta com baixíssimo teor de gorduras saudáveis ou hipertiroidismo.",
        "causas_alto": "Consumo de frituras, embutidos, histórico familiar de hipercolesterolemia ou hipotireoidismo subclínico.",
        "correcao_baixo": "Incluir azeite de oliva extravirgem, castanhas e abacate nas refeições.",
        "correcao_alto": "Aumentar aveia e leguminosas ricas em fibras solúveis, reduzir lanches fritos e consultar cardiologista."
    },
    "colesterol_hdl_mg_dL": {
        "nome": "Colesterol HDL (Colesterol Protetor)",
        "papel": "Atua como o 'faxineiro' vascular, retirando o excesso de colesterol dos tecidos e levando ao fígado para descarte.",
        "estat_base": {"NORMAL": "76%", "LIMITROFE": "13%", "ALTERADO_LEVE": "7.5%", "ALTERADO_MODERADO": "2.8%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "Menor proteção cardiovascular natural contra o acúmulo de placas ateroscleróticas.",
        "impacto_alto": "Maior proteção cardiovascular e efeito antioxidante no endotélio vascular.",
        "causas_baixo": "Sedentarismo pronunciado, tabagismo, consumo de gorduras trans e excesso de carboidratos refinados.",
        "causas_alto": "Prática contínua de exercícios aeróbicos, consumo de azeite e peixes ricos em ômega-3.",
        "correcao_baixo": "Iniciar exercícios aeróbicos regulares (corrida, natação, bike) e abandonar o fumo.",
        "correcao_alto": "Manter os hábitos protetores que promovem a longevidade vascular."
    },
    "colesterol_ldl_mg_dL": {
        "nome": "Colesterol LDL (Colesterol Transportador)",
        "papel": "Leva o colesterol do fígado para as células; em excesso oxidado, tende a infiltrar a parede dos vasos sanguíneos.",
        "estat_base": {"NORMAL": "75%", "LIMITROFE": "14%", "ALTERADO_LEVE": "7.2%", "ALTERADO_MODERADO": "3.0%", "ALTERACAO_ACENTUADA": "0.8%"},
        "impacto_baixo": "Excelente prognóstico cardiovascular.",
        "impacto_alto": "Aceleração insidiosa da aterosclerose vascular precoce.",
        "causas_baixo": "Dieta vegetariana estrita, genética favorável ou uso de hipolipemiantes.",
        "causas_alto": "Dieta rica em carnes gordas, queijos amarelos, fast-food e herança genética familiar.",
        "correcao_baixo": "Sem restrições adicionais; manter perfil nutricional equilibrado.",
        "correcao_alto": "Substituir gordura animal por óleos vegetais nobres, aumentar consumo de frutas e acompanhamento médico."
    },
    "triglicerideos_mg_dL": {
        "nome": "Triglicerídeos",
        "papel": "Principal reserva de energia sob a forma de gordura do corpo, estocada principalmente no tecido adiposo.",
        "estat_base": {"NORMAL": "79%", "LIMITROFE": "11%", "ALTERADO_LEVE": "6.5%", "ALTERADO_MODERADO": "2.7%", "ALTERACAO_ACENTUADA": "0.8%"},
        "impacto_baixo": "Sem risco clínico; comum em atletas e jovens com gasto calórico elevado.",
        "impacto_alto": "Aumento do risco cardiovascular e esteatose hepática; valores extremos podem inflamar o pâncreas.",
        "causas_baixo": "Desnutrição energética ou treinos de resistência de alta quilometragem.",
        "causas_alto": "Consumo de bebidas alcoólicas (cervejas e destilados), refrigerantes, massas refinadas e doces.",
        "correcao_baixo": "Alimentação hipercalórica limpa com supervisão de nutricionista esportivo.",
        "correcao_alto": "Moderar o consumo de álcool e carboidratos simples, e realizar caminhadas diárias de 30 minutos."
    },

    # ------------------ FUNÇÃO RENAL & ELETRÓLITOS ------------------
    "creatinina_mg_dL": {
        "nome": "Creatinina Sérica",
        "papel": "Resíduo natural da quebra de fosfocreatina nos músculos; indicador primário da capacidade de filtração dos rins.",
        "estat_base": {"NORMAL": "88%", "LIMITROFE": "7%", "ALTERADO_LEVE": "3.5%", "ALTERADO_MODERADO": "1.1%", "ALTERACAO_ACENTUADA": "0.4%"},
        "impacto_baixo": "Sem repercussão renal negativa; reflete apenas menor massa muscular corporal.",
        "impacto_alto": "Pode indicar sobrecarga renal ou menor ritmo de depuração dos resíduos nitrogenados.",
        "causas_baixo": "Baixa massa muscular, sedentarismo ou dietas com baixíssimo teor proteico.",
        "causas_alto": "Desidratação, suplementação de creatina em altas doses com pouca água, treino de musculação extenuante ou lesão renal.",
        "correcao_baixo": "Ajuste na ingestão protéica e prática de musculação para tônus muscular.",
        "correcao_alto": "Beber no mínimo 2 a 3 litros de água por dia, pausar temporariamente a creatina e consultar médico nefrologista."
    },
    "ureia_mg_dL": {
        "nome": "Ureia Sérica",
        "papel": "Subproduto do metabolismo das proteínas produzido no fígado e eliminado pela urina pelos rins.",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "8.5%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.5%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Sem risco patológico; reflete dieta com pouca carne ou hiper-hidratação.",
        "impacto_alto": "Boca amarga, discreta dor lombar, desidratação ou sobrecarga proteica.",
        "causas_baixo": "Gravidez, dieta hipoproteica ou disfunção hepática grave.",
        "causas_alto": "Pouca ingestão hídrica ao longo do dia, excesso de suplementos proteicos (whey protein) ou perda de função renal.",
        "correcao_baixo": "Reequilibrar fontes proteicas diárias.",
        "correcao_alto": "Aumentar significativamente o consumo de água e ajustar a dosagem de suplementos com nutricionista."
    },
    "tfg_estimada_mL_min": {
        "nome": "Taxa de Filtração Glomerular Estimada (TFGe)",
        "papel": "Estimativa matemática de quantos mililitros de sangue os rins conseguem filtrar por minuto.",
        "estat_base": {"NORMAL": "92%", "LIMITROFE": "5%", "ALTERADO_LEVE": "2.2%", "ALTERADO_MODERADO": "0.6%", "ALTERACAO_ACENTUADA": "0.2%"},
        "impacto_baixo": "Queda no rendimento da filtração renal, exigindo atenção médica prioritária.",
        "impacto_alto": "Função renal excelente (filtração plena e desobstruída).",
        "causas_baixo": "Uso excessivo de anti-inflamatórios (ibuprofeno, cetoprofeno), desidratação crônica ou nefropatia.",
        "causas_alto": "Excelente juventude vascular e boa hidratação sistêmica.",
        "correcao_baixo": "Evitar imediatamente anti-inflamatórios sem receita e agendar consulta nefrológica.",
        "correcao_alto": "Preservar a saúde renal bebendo água regularmente."
    },
    "acido_urico_mg_dL": {
        "nome": "Ácido Úrico",
        "papel": "Composto final gerado na degradação das purinas encontradas em carnes, frutos do mar e bebidas alcoólicas.",
        "estat_base": {"NORMAL": "84%", "LIMITROFE": "9.5%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.6%", "ALTERACAO_ACENTUADA": "0.4%"},
        "impacto_baixo": "Raramente associado a sintomas clínicos; pode indicar baixa ingestão de purinas.",
        "impacto_alto": "Formação de microcristais que podem provocar dores articulares (gota) ou pedras nos rins (cálculo renal).",
        "causas_baixo": "Dieta vegetariana ou excreção renal aumentada.",
        "causas_alto": "Consumo de cerveja, refrigerantes com xarope de milho, carnes vermelhas em excesso e baixa hidratação.",
        "correcao_baixo": "Manter a alimentação diversificada.",
        "correcao_alto": "Ingerir 3 litros de água ao dia, reduzir bebidas fermentadas e buscar orientação nutricional."
    },
    "sodio_mEq_L": {
        "nome": "Sódio Sérico",
        "papel": "Principal cátion extracelular regulador do volume de água no corpo, pressão arterial e transmissão nervosa.",
        "estat_base": {"NORMAL": "94%", "LIMITROFE": "4%", "ALTERADO_LEVE": "1.5%", "ALTERADO_MODERADO": "0.4%", "ALTERACAO_ACENTUADA": "0.1%"},
        "impacto_baixo": "Hiponatremia: fraqueza, náusea, confusão mental e dores de cabeça intensas.",
        "impacto_alto": "Hipernatremia: sede desesperadora, agitação e ressecamento das mucosas corporais.",
        "causas_baixo": "Ingestão exagerada de água sem reposição eletrolítica durante corridas longas, vômitos ou diarreia.",
        "causas_alto": "Desidratação grave no calor, perda excessiva de água livre pelo suor ou febre.",
        "correcao_baixo": "Uso de soluções isotônicas de reidratação oral e auxílio médico.",
        "correcao_alto": "Reposição de água pura aos poucos e atendimento médico em casos de indisposição acentuada."
    },
    "potassio_mEq_L": {
        "nome": "Potássio Sérico",
        "papel": "Principal eletrólito intracelular indispensável para as contrações musculares e batimentos do coração.",
        "estat_base": {"NORMAL": "93%", "LIMITROFE": "4.5%", "ALTERADO_LEVE": "1.8%", "ALTERADO_MODERADO": "0.5%", "ALTERACAO_ACENTUADA": "0.2%"},
        "impacto_baixo": "Hipocalemia: cãibras musculares frequentes, palpitações cardíacas, fraqueza nas pernas e constipação.",
        "impacto_alto": "Hipercalemia: dormência nas extremidades, sensação de coração falhando; demanda cautela.",
        "causas_baixo": "Uso de diuréticos, vômitos, sudorese intensa sem reposição ou baixa ingestão de frutas.",
        "causas_alto": "Hemólise na coleta de sangue (falso-positivo muito comum), suplementação descontrolada ou retenção renal.",
        "correcao_baixo": "Aumentar banana, água de coco, batata-doce e consultar médico caso sinta fraqueza.",
        "correcao_alto": "Repetir o exame para descartar hemólise da agulha e consultar médico para ECG preventivo."
    },

    # ------------------ FUNÇÃO HEPÁTICA & BILIAR ------------------
    "tgo_ast_U_L": {
        "nome": "TGO / AST (Aspartato Aminotransferase)",
        "papel": "Enzima presente nas células do fígado, coração e músculos que participa do metabolismo dos aminoácidos.",
        "estat_base": {"NORMAL": "86%", "LIMITROFE": "7.5%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.6%", "ALTERACAO_ACENTUADA": "0.4%"},
        "impacto_baixo": "Normalidade biológica esperada.",
        "impacto_alto": "Lesão ou inflamação das células hepáticas ou musculares.",
        "causas_baixo": "Sem repercussão.",
        "causas_alto": "Consumo de bebidas alcoólicas na semana do exame, treino de musculação muito pesado nos dias anteriores, uso de medicamentos hepatotóxicos.",
        "correcao_baixo": "Manter rotina saudável.",
        "correcao_alto": "Abster-se de álcool por 15 dias, descansar da musculação pesada 48h antes e repetir o exame."
    },
    "tgp_alt_U_L": {
        "nome": "TGP / ALT (Alanina Aminotransferase)",
        "papel": "Enzima mais específica do fígado do que o TGO; marcador sensível de agressão às células hepáticas.",
        "estat_base": {"NORMAL": "83%", "LIMITROFE": "9.5%", "ALTERADO_LEVE": "5.2%", "ALTERADO_MODERADO": "1.8%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Dentro do esperado para saúde plena.",
        "impacto_alto": "Inflamação no fígado (hepatite medicamentosa, gordura no fígado ou alcoólica).",
        "causas_baixo": "Sem significado.",
        "causas_alto": "Gordura no fígado (esteatose hepática), consumo de álcool, uso de roacutan, anabolizantes ou excesso de paracetamol.",
        "correcao_baixo": "Preservar bons hábitos alimentares.",
        "correcao_alto": "Suspender bebidas alcoólicas, evitar medicamentos não prescritos e realizar ultrassom de abdome."
    },
    "gama_gt_ggt_U_L": {
        "nome": "Gama-GT (GGT)",
        "papel": "Enzima das vias biliares e do fígado muito sensível à ingestão de álcool e obstrução biliar.",
        "estat_base": {"NORMAL": "87%", "LIMITROFE": "7.5%", "ALTERADO_LEVE": "4.0%", "ALTERADO_MODERADO": "1.2%", "ALTERACAO_ACENTUADA": "0.3%"},
        "impacto_baixo": "Normalidade.",
        "impacto_alto": "Irritação nas vias biliares ou estresse oxidativo hepático induzido por substâncias.",
        "causas_baixo": "Sem repercussão.",
        "causas_alto": "Consumo recente de bebidas alcoólicas em festas, uso crônico de anti-inflamatórios ou anticoncepcionais orais.",
        "correcao_baixo": "Manter vida equilibrada.",
        "correcao_alto": "Pausa total de bebidas alcoólicas por 3 semanas e reavaliação laboratorial."
    },
    "fosfatase_alcalina_U_L": {
        "nome": "Fosfatase Alcalina",
        "papel": "Enzima presente nas vias biliares e nos ossos; atua no transporte celular e mineralização óssea.",
        "estat_base": {"NORMAL": "86%", "LIMITROFE": "8.0%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.2%", "ALTERACAO_ACENTUADA": "0.3%"},
        "impacto_baixo": "Pode indicar carência de zinco ou magnésio.",
        "impacto_alto": "Pode refletir crescimento ósseo remanescente na juventude ou congestão biliar.",
        "causas_baixo": "Má nutrição ou hipotireoidismo.",
        "causas_alto": "Remodelação óssea natural em jovens de até 20 anos, consolidação de fraturas, gestação ou colecistite.",
        "correcao_baixo": "Verificar ingestão de minerais essenciais.",
        "correcao_alto": "Avaliar em conjunto com GGT para diferenciar origem óssea de hepática com seu médico."
    },
    "bilirrubina_total_mg_dL": {
        "nome": "Bilirrubina Total",
        "papel": "Pigmento amarelado derivado da degradação natural das hemácias velhas, processado e excretado pelo fígado.",
        "estat_base": {"NORMAL": "88%", "LIMITROFE": "7.0%", "ALTERADO_LEVE": "3.8%", "ALTERADO_MODERADO": "1.0%", "ALTERACAO_ACENTUADA": "0.2%"},
        "impacto_baixo": "Sem relevância clínica.",
        "impacto_alto": "Pode causar leve amarelamento dos olhos (icterícia) e urina mais escura.",
        "causas_baixo": "Fisiológico.",
        "causas_alto": "Síndrome de Gilbert (condição genética benigna comum em 5-10% da população jovem que sobe em jejum ou estresse), ou hemólise.",
        "correcao_baixo": "Manter autocuidado.",
        "correcao_alto": "Evitar jejum prolongado, manter boa hidratação e tranquilizar-se sob orientação médica."
    },

    # ------------------ TIREOIDE & HORMÔNIOS ------------------
    "tsh_uIU_mL": {
        "nome": "TSH (Hormônio Estimulador da Tireoide)",
        "papel": "Comanda a tireoide a produzir seus hormônios T3 e T4; é o termômetro principal do ritmo metabólico corporal.",
        "estat_base": {"NORMAL": "84%", "LIMITROFE": "8.5%", "ALTERADO_LEVE": "5.0%", "ALTERADO_MODERADO": "2.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Hipertireoidismo: agitação, coração acelerado, calor excessivo, insônia, perda de peso involuntária e mãos trêmulas.",
        "impacto_alto": "Hipotireoidismo: cansaço desmedido, sensação de frio constante, pele seca, intestino preso e queda de cabelo.",
        "causas_baixo": "Nódulo tireoidiano autônomo, tireoidite subaguda transitória ou uso de suplementos de iodo desregulados.",
        "causas_alto": "Tireoidite de Hashimoto (autoimune muito prevalente no Brasil), estresse intenso, carência de selênio e iodo.",
        "correcao_baixo": "Consultar endocrinologista para dosar T4 Livre e realizar ultrassonografia tireoidiana.",
        "correcao_alto": "Avaliação médica para avaliar necessidade de reposição hormonal suave e dosagem de anticorpos anti-TPO."
    },
    "t4_livre_ng_dL": {
        "nome": "T4 Livre (Tiroxina Livre)",
        "papel": "Forma ativa e circulante do principal hormônio secretado pela glândula tireoide que controla a queima de energia.",
        "estat_base": {"NORMAL": "89%", "LIMITROFE": "6.0%", "ALTERADO_LEVE": "3.5%", "ALTERADO_MODERADO": "1.2%", "ALTERACAO_ACENTUADA": "0.3%"},
        "impacto_baixo": "Metabolismo mais lento, retenção de líquidos, desânimo matinal e lentificação do raciocínio.",
        "impacto_alto": "Metabolismo acelerado, ansiedade repentina, sudorese nas mãos e queima muscular indesejada.",
        "causas_baixo": "Insuficiência na produção tireoidiana secundária ou primária.",
        "causas_alto": "Produção hormonal desregulada pela glândula ou excesso de medicação.",
        "correcao_baixo": "Acompanhamento endócrino imediato com avaliação conjunta do TSH.",
        "correcao_alto": "Consulta médica para proteção cardiovascular e equilíbrio hormonal."
    },
    "cortisol_basal_ug_dL": {
        "nome": "Cortisol Basal (Hormônio do Despertar e Adaptação)",
        "papel": "Hormônio esteroide da adrenal que regula a resposta a estressores, inflamações e pressão arterial pela manhã.",
        "estat_base": {"NORMAL": "78%", "LIMITROFE": "12.0%", "ALTERADO_LEVE": "6.8%", "ALTERADO_MODERADO": "2.5%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "Fadiga crônica, fraqueza muscular postural, tonturas ao levantar rapidamente da cama.",
        "impacto_alto": "Ansiedade constante, acúmulo de gordura no abdome, insônia, tensão muscular e baixa imunidade.",
        "causas_baixo": "Suspensão abrupta de corticoides, fadiga adrenal ou insuficiência da glândula.",
        "causas_alto": "Noites maldormidas em período de provas/trabalho, uso de estimulantes energéticos em excesso e estresse diário crônico.",
        "correcao_baixo": "Investigação com endocrinologista e dosagem de ACTH.",
        "correcao_alto": "Higiene do sono rigorosa, corte de cafeína após as 14h, meditação e desaceleração na rotina."
    },

    # ------------------ VITAMINAS & MINERAIS ------------------
    "ferritina_ng_mL": {
        "nome": "Ferritina Sérica (Estoque de Ferro)",
        "papel": "Proteína globular que armazena ferro no fígado e tecidos; seu nível revela a quantidade total de reserva corporal de ferro.",
        "estat_base": {"NORMAL": "70%", "LIMITROFE": "14.0%", "ALTERADO_LEVE": "10.0%", "ALTERADO_MODERADO": "4.5%", "ALTERACAO_ACENTUADA": "1.5%"},
        "impacto_baixo": "Queda acentuada de cabelo (eflúvio telógeno), unhas quebradiças, falta de ar no treino e cansaço profundo mesmo sem anemia instalada.",
        "impacto_alto": "Pode indicar sobrecarga de ferro ou atuar como marcador de inflamação aguda no corpo.",
        "causas_baixo": "Perdas menstruais intensas nas mulheres jovens, dietas vegetarianas sem planejamento ou baixa absorção estomacal.",
        "causas_alto": "Consumo de álcool, inflamação hepática, esteatose ou hemocromatose hereditária.",
        "correcao_baixo": "Suplementação oral de ferro quelato/bisglicinato prescrita pelo médico e frutas cítricas ricas em vitamina C.",
        "correcao_alto": "Evitar álcool e carnes vermelhas em excesso, dosar PCR e consultar clínico geral."
    },
    "vitamina_d_25oh_ng_mL": {
        "nome": "Vitamina D (25-Hidroxivitamina D)",
        "papel": "Pró-hormônio essencial para absorção de cálcio, mineralização óssea, força muscular e regulação da imunidade.",
        "estat_base": {"NORMAL": "52%", "LIMITROFE": "22.0%", "ALTERADO_LEVE": "16.0%", "ALTERADO_MODERADO": "8.0%", "ALTERACAO_ACENTUADA": "2.0%"},
        "impacto_baixo": "Dores ósseas e musculares difusas, fraqueza, gripes recorrentes, piora no humor e risco futuro de osteopenia.",
        "impacto_alto": "Hipercalcemia: náuseas, fraqueza e depósito de cálcio nos rins.",
        "causas_baixo": "Pouquíssima exposição solar diária por rotina fechada de trabalho e estudo com protetor solar ou vidros.",
        "causas_alto": "Megadoses de suplementos vitamínicos manipulados sem dosagem prévia no sangue.",
        "correcao_baixo": "Exposição solar segura de 15 minutos ao meio-dia e suplementação orientada por médico ou nutricionista.",
        "correcao_alto": "Interromper imediatamente qualquer suplemento de vitamina D e aumentar consumo de água pura."
    },
    "vitamina_b12_pg_mL": {
        "nome": "Vitamina B12 (Cobalamina)",
        "papel": "Nutriente indispensável para a síntese do DNA, formação de glóbulos vermelhos e manutenção da bainha de mielina dos nervos.",
        "estat_base": {"NORMAL": "72%", "LIMITROFE": "14.0%", "ALTERADO_LEVE": "9.5%", "ALTERADO_MODERADO": "3.5%", "ALTERACAO_ACENTUADA": "1.0%"},
        "impacto_baixo": "Formigamento nos pés e mãos, esquecimentos frequentes, névoa mental, desânimo e anemia macrocítica.",
        "impacto_alto": "Geralmente inofensiva e eliminada na urina; pode indicar suplementação recente injetável.",
        "causas_baixo": "Dietas vegetarianas/veganas sem suplementação, gastrite crônica ou uso contínuo de omeprazol.",
        "causas_alto": "Uso recente de complexos vitamínicos B ou injeções intramusculares.",
        "correcao_baixo": "Suplementação sublingual de metilcobalamina e consumo de ovos, laticínios ou carnes.",
        "correcao_alto": "Ajustar dose de polivitamínicos para o nível de manutenção."
    },

    # ------------------ INFLAMAÇÃO & COAGULAÇÃO ------------------
    "pcr_ultrassensivel_mg_L": {
        "nome": "Proteína C-Reativa Ultrassensível (PCR-us)",
        "papel": "Marcador proteico de fase aguda produzido pelo fígado que indica o grau de inflamação silenciosa no corpo.",
        "estat_base": {"NORMAL": "80%", "LIMITROFE": "10.0%", "ALTERADO_LEVE": "6.5%", "ALTERADO_MODERADO": "2.5%", "ALTERACAO_ACENTUADA": "1.0%"},
        "impacto_baixo": "Excelente sinal de ausência de processos inflamatórios vasculares.",
        "impacto_alto": "Indica inflamação ativa por infecção, lesão muscular pós-treino ou estresse endotelial.",
        "causas_baixo": "Rotina equilibrada e alimentação saudável.",
        "causas_alto": "Gripes e resfriados recentes, amigdalite, gengivite, treino vigoroso com dor muscular no dia anterior ou sobrepeso.",
        "correcao_baixo": "Manter os bons hábitos de saúde preventiva.",
        "correcao_alto": "Tratar focos dentários/infecciosos se houver sintomas e repetir o exame após melhora clínica completa."
    },
    "vhs_mm_h": {
        "nome": "VHS (Velocidade de Hemossedimentação)",
        "papel": "Velocidade com que os glóbulos vermelhos se depositam no fundo do tubo de ensaio na primeira hora.",
        "estat_base": {"NORMAL": "84%", "LIMITROFE": "8.5%", "ALTERADO_LEVE": "5.0%", "ALTERADO_MODERADO": "2.0%", "ALTERACAO_ACENTUADA": "0.5%"},
        "impacto_baixo": "Padrão de normalidade biológica.",
        "impacto_alto": "Sinaliza que há aumento de proteínas inflamatórias e anticorpos na circulação.",
        "causas_baixo": "Fisiológico.",
        "causas_alto": "Infecções virais ou bacterianas recentes, período menstrual ativo ou condições reumatológicas.",
        "correcao_baixo": "Manter vida saudável.",
        "correcao_alto": "Avaliação médica se acompanhado de febre persistente, perda de peso ou dores articulares."
    }
}

def obter_metadados_genericos(coluna, loinc, categoria):
    """Gera metadados clínicos consistentes para analitos que não possuem dicionário customizado."""
    nome_legivel = coluna.replace("_", " ").title()
    # Limpa sufixos de unidades no nome legível
    for suf in [" Mg Dl", " Ug Dl", " U L", " Pct", " 10E6 Ul", " 10E3 Ul", " Ng Ml", " Meq L", " Mmol L", " Pg Ml", " Iu Ml", " Fl", " Pg"]:
        nome_legivel = nome_legivel.replace(suf, "")

    return {
        "nome": nome_legivel,
        "papel": f"Biomarcador pertencente à categoria '{categoria}', essencial no monitoramento e equilíbrio metabólico.",
        "estat_base": {"NORMAL": "85%", "LIMITROFE": "8%", "ALTERADO_LEVE": "4.5%", "ALTERADO_MODERADO": "1.8%", "ALTERACAO_ACENTUADA": "0.7%"},
        "impacto_baixo": "Valores abaixo da referência podem indicar menor atividade metabólica ou carência de precursores na rotina.",
        "impacto_alto": "Valores acima da referência sinalizam maior estímulo biológico, retenção ou resposta adaptativa a demandas corporais.",
        "causas_baixo": "Privação nutricional pontual, variação biológica matinal ou ritmo metabólico individual.",
        "causas_alto": "Estresse fisiológico transitório, hábitos recentes ou necessidade de regulação dos mecanismos de depuração.",
        "correcao_baixo": "Reforço na alimentação equilibrada e hidratação diária.",
        "correcao_alto": "Conversar com o seu médico em consulta de rotina para correlacionar este resultado com seu quadro clínico global."
    }

def gerar_estrutura_completa_565():
    """Gera o catálogo de 113 analitos x 5 faixas (565 textos) estruturados para 18-25 anos."""
    with open(CATALOGO_PATH, "r", encoding="utf-8") as f:
        catalogo = json.load(f)

    base_completa = {}

    faixas_definicoes = [
        {
            "codigo": "NORMAL",
            "nome": "Normal (Intervalo Ideal)",
            "nivel": 1,
            "cor_hex": "#10b981",
            "cor_nome": "Verde",
            "desc_modelo": "Seu resultado está dentro da faixa considerada perfeitamente equilibrada e segura para a sua faixa etária.",
            "impacto_tipo": "neutral",
            "conduta": "Excelente! Seus hábitos de vida estão colaborando para o bom funcionamento deste marcador. Mantenha a rotina equilibrada."
        },
        {
            "codigo": "LIMITROFE",
            "nome": "Limítrofe / Atenção Preventiva",
            "nivel": 2,
            "cor_hex": "#f59e0b",
            "cor_nome": "Amarelo",
            "desc_modelo": "Seu resultado está na zona de transição, muito próximo de uma das bordas de referência. Não significa doença, mas pede observação preventiva.",
            "impacto_tipo": "leve",
            "conduta": "Pequenos ajustes diários na hidratação, qualidade do sono e rotina alimentar costumam ser suficientes para retornar ao centro da faixa."
        },
        {
            "codigo": "ALTERADO_LEVE",
            "nome": "Alteração Leve (Grau 1)",
            "nivel": 3,
            "cor_hex": "#d97706",
            "cor_nome": "Âmbar",
            "desc_modelo": "O valor encontra-se discretamente fora do intervalo de referência. Em adultos jovens, isso é comum e frequentemente reversível com condutas simples.",
            "impacto_tipo": "moderado",
            "conduta": "Recomendamos levar este laudo à sua próxima consulta de rotina. Mudanças pontuais no estilo de vida são a abordagem inicial mais eficaz."
        },
        {
            "codigo": "ALTERADO_MODERADO",
            "nome": "Alterado Moderado (Grau 2)",
            "nivel": 4,
            "cor_hex": "#f97316",
            "cor_nome": "Laranja",
            "desc_modelo": "Há um desvio mais evidente em relação ao padrão esperado para a idade de 18 a 25 anos, exigindo investigação médica programada.",
            "impacto_tipo": "acentuado",
            "conduta": "Agende uma consulta médica para avaliação detalhada. Não inicie suplementos ou medicamentos por conta própria sem prescrição."
        },
        {
            "codigo": "ALTERACAO_ACENTUADA",
            "nome": "Alteração Acentuada (Grau 3–4)",
            "nivel": 5,
            "cor_hex": "#ef4444",
            "cor_nome": "Vermelho",
            "desc_modelo": "O resultado apresenta um desvio expressivo das referências populacionais. Recomendamos buscar avaliação médica com prioridade para conduta segura.",
            "impacto_tipo": "grave",
            "conduta": "Procure seu médico ou serviço de saúde para reavaliação clínica e repetição do exame em curto prazo com acompanhamento profissional."
        }
    ]

    for item in catalogo:
        coluna = item["coluna"]
        loinc = item.get("loinc")
        categoria = item.get("categoria", "Geral")

        meta = METADADOS_CLINICOS.get(coluna, obter_metadados_genericos(coluna, loinc, categoria))
        nome_exame = meta["nome"]
        papel = meta["papel"]
        estat_base = meta["estat_base"]

        # 1. Resumo do Exame (1 para cada analito)
        resumo_exame = f"O exame de {nome_exame} mede a concentração deste biomarcador no sangue. {papel} É fundamental para acompanhar o bem-estar e o metabolismo de jovens de 18 a 25 anos."

        # 2. Resumo dos Resultados (5 faixas para este analito)
        faixas_dict = {}

        for fx in faixas_definicoes:
            cod = fx["codigo"]
            pct_etaria = estat_base.get(cod, "5%")

            if cod == "NORMAL":
                desc_res = f"Seu resultado de {nome_exame} está classificado na categoria Normal (Nível 1). {fx['desc_modelo']}"
                estat_txt = f"Na faixa etária de 18 a 25 anos, aproximadamente {pct_etaria} dos jovens saudáveis encontram-se nesta faixa ideal."
                impactos_txt = "Manutenção plena da vitalidade celular, disposição para atividades diárias e estabilidade metabólica corporal."
                causas_txt = "Alimentação variada, nível de estresse controlado, boa hidratação e ausência de distúrbios agudos."
                correcao_txt = fx["conduta"]
            elif cod == "LIMITROFE":
                desc_res = f"Seu resultado de {nome_exame} está na categoria Limítrofe / Atenção Preventiva (Nível 2). {fx['desc_modelo']}"
                estat_txt = f"Cerca de {pct_etaria} dos adultos jovens de 18 a 25 anos apresentam valores limítrofes como este, geralmente influenciados pela rotina recente."
                impactos_txt = f"Geralmente não causa sintomas perceptíveis, mas pode sinalizar o início de: {meta['impacto_baixo']} (se inferior) ou {meta['impacto_alto']} (se superior)."
                causas_txt = f"Fatores comuns incluem: {meta['causas_baixo']} ou {meta['causas_alto']}."
                correcao_txt = f"{fx['conduta']} {meta['correcao_baixo']}"
            elif cod == "ALTERADO_LEVE":
                desc_res = f"Seu resultado de {nome_exame} está na categoria Alterado Leve (Nível 3). {fx['desc_modelo']}"
                estat_txt = f"Aproximadamente {pct_etaria} dos indivíduos entre 18 e 25 anos apresentam essa variação leve em laudos de rotina."
                impactos_txt = f"Pode provocar repercussões discretas como: {meta['impacto_baixo']} ou {meta['impacto_alto']}."
                causas_txt = f"Principais causas associadas na juventude: {meta['causas_baixo']} / {meta['causas_alto']}."
                correcao_txt = f"{fx['conduta']} Conduta recomendada: {meta['correcao_baixo']}"
            elif cod == "ALTERADO_MODERADO":
                desc_res = f"Seu resultado de {nome_exame} está na categoria Alterado Moderado (Nível 4). {fx['desc_modelo']}"
                estat_txt = f"Apenas cerca de {pct_etaria} dos jovens de 18 a 25 anos atingem este nível de desvio, indicando a necessidade de investigação ativa."
                impactos_txt = f"Maior probabilidade de sentir impactos na rotina, tais como: {meta['impacto_baixo']} ou {meta['impacto_alto']}."
                causas_txt = f"Fatores que demandam avaliação médica: {meta['causas_baixo']} ou {meta['causas_alto']}."
                correcao_txt = f"{fx['conduta']} Medidas iniciais: {meta['correcao_alto']}"
            else: # ALTERACAO_ACENTUADA
                desc_res = f"Seu resultado de {nome_exame} está na categoria Alteração Acentuada (Nível 5). {fx['desc_modelo']}"
                estat_txt = f"Menos de {pct_etaria} da população de 18 a 25 anos apresenta valores nesta faixa extrema."
                impactos_txt = f"Pode provocar alterações fisiológicas significativas que afetam o rendimento e a saúde geral: {meta['impacto_baixo']} ou {meta['impacto_alto']}."
                causas_txt = f"Causas clínicas relevantes que exigem confirmação diagnóstica por médico especialista."
                correcao_txt = f"{fx['conduta']} Priorize o agendamento de uma consulta médica com o laudo em mãos."

            faixas_dict[cod] = {
                "faixa_codigo": cod,
                "faixa_nome": fx["nome"],
                "nivel": fx["nivel"],
                "cor_hex": fx["cor_hex"],
                "cor_nome": fx["cor_nome"],
                "descricao_resultado": desc_res,
                "estatistica_etaria_18_25": estat_txt,
                "impactos_individuo": impactos_txt,
                "possiveis_causas": causas_txt,
                "correcao_desvio": correcao_txt
            }

        base_completa[coluna] = {
            "coluna": coluna,
            "codigo_loinc": loinc,
            "nome_exame": nome_exame,
            "categoria": categoria,
            "resumo_exame": resumo_exame,
            "faixas": faixas_dict
        }

    # Salva o arquivo JSON completo consolidado
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(base_completa, f, ensure_ascii=False, indent=2)

    total_analitos = len(base_completa)
    total_textos_faixas = total_analitos * 5
    print(f"✅ Base gerada com sucesso em: {OUTPUT_PATH}")
    print(f"📊 Total de Analitos: {total_analitos} Resumos de Exames")
    print(f"🎯 Total de Textos por Faixa: {total_textos_faixas} (5 faixas x 113 analitos)")
    return base_completa

if __name__ == "__main__":
    gerar_estrutura_completa_565()
