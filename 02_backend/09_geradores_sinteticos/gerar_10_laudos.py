# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import os
import sys
import json
from gerador_laudos import criar_laudo_pdf, OUTPUT_DIR

# -------------------------------------------------------------
# DADOS CLÍNICOS DOS 10 LAUDOS (2023 a 2026 - Paciente Janaina de Assis)
# -------------------------------------------------------------

def gerar_dados_laudos():
    laudos = []

    # ---------------------------------------------------------
    # 1. LAUDO 01: 15/03/2023 (Rotina Anual / Check-up Pós-Pandemia)
    # Faltam: CA 125, CA 19-9, Alfa Fetoproteína, IGF-1, Fibrinogênio (5 exames omitidos)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 1,
        "arquivo": "Laudo_01_JanainaAssis_15-03-2023.pdf",
        "atendimento": "8081.0112.1001",
        "cip": "6164100101",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 42,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "15/03/2023",
        "hora_coleta": "08:10 BRT",
        "data_liberacao": "17/03/2023 16:30",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Impedância / Colorimetria / Microscopia",
                "resultado": "Série Vermelha Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,75 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "13,9 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "41,5 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "87,4 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "HCM", "resultado": "29,3 pg", "referencia": "27,0 a 32,0 pg"},
                    {"nome": "CHCM", "resultado": "33,5 g/dL", "referencia": "31,0 a 35,0 g/dL"},
                    {"nome": "RDW", "resultado": "12,8 %", "referencia": "11,6 a 14,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "7.100 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Neutrófilos", "resultado": "4.970 /µL (70,0 %)", "referencia": "1.800 a 7.800 /µL"},
                    {"nome": "Linfócitos", "resultado": "1.633 /µL (23,0 %)", "referencia": "1.000 a 3.000 /µL"},
                    {"nome": "Monócitos", "resultado": "355 /µL (5,0 %)", "referencia": "200 a 1.000 /µL"},
                    {"nome": "Eosinófilos", "resultado": "110 /µL (1,5 %)", "referencia": "20 a 500 /µL"},
                    {"nome": "Basófilos", "resultado": "32 /µL (0,5 %)", "referencia": "20 a 100 /µL"},
                    {"nome": "Contagem de Plaquetas", "resultado": "285.000 /µL", "referencia": "150.000 a 450.000 /µL"},
                    {"nome": "VPM", "resultado": "9,2 fL", "referencia": "8,3 a 12,5 fL"}
                ]
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "104 mg/dL",
                "alterado": True,
                "referencia": "70 a 99 mg/dL",
                "nota": "Glicemia de jejum discretamente elevada. Recomendada confirmação conforme critérios ADA."
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria / HPLC",
                "resultado": "5,8 %",
                "alterado": True,
                "referencia": "Normal: Inferior a 5,7% | Risco aumentado (Pré-diabetes): 5,7 a 6,4%",
                "nota": "Glicose Média Estimada (GME): 120 mg/dL"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência / Cálculo",
                "resultado": "16,5 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "4,23", "alterado": True, "referencia": "Inferior a 2,70"}
                ],
                "nota": "Índice HOMA-IR indicativo de resistência insulínica."
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático CHOP-POD",
                "resultado": "205,0 mg/dL",
                "alterado": True,
                "referencia": "Com jejum: Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Fórmula de Martin",
                "resultado": "132 mg/dL",
                "alterado": True,
                "referencia": "Risco intermediário: < 100 mg/dL | Risco baixo: < 130 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "43 mg/dL",
                "referencia": "Com jejum: Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "150,0 mg/dL",
                "alterado": True,
                "referencia": "Com jejum: Inferior a 150 mg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "16,0 ng/mL",
                "alterado": True,
                "referencia": "População saudável < 60 anos: Superior a 20 ng/mL | Grupos de risco: 30 a 60 ng/mL",
                "nota": "Nível sérico de hipovitaminose D. Considerar orientação médica para suplementação."
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "42,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "72,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível (PCRus)",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,87 mg/dL",
                "alterado": True,
                "referencia": "Baixo risco: < 0,10 | Médio: 0,10-0,20 | Alto risco CV: > 0,20 mg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Colorimétrico Cinético (Jaffé)",
                "resultado": "0,73 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR (Taxa de Filtração Glomerular Estimada)", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90 mL/min/1,73m²"}
                ]
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético UV",
                "resultado": "30 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "4,5 mg/dL",
                "referencia": "2,8 a 6,7 mg/dL"
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "16 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "18 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Gama-Glutamil Transferase (GGT)",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "22 U/L",
                "referencia": "Inferior a 38 U/L"
            },
            {
                "nome": "Fosfatase Alcalina",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "65 U/L",
                "referencia": "46 a 116 U/L"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "2,30 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,10 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Potássio",
                "detalhe": "Material: Soro | Método: Eletrodo Íon Seletivo",
                "resultado": "4,2 mmol/L",
                "referencia": "3,5 a 5,1 mmol/L"
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Absorção Atômica",
                "resultado": "74,0 µg/dL",
                "referencia": "70,0 a 120,0 µg/dL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 2. LAUDO 02: 20/06/2023 (Controle Metabólico Pós-Início de Suplementação)
    # Faltam: CA 19-9, Alfa Fetoproteína, Fibrinogênio, Zinco (4 exames omitidos)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 2,
        "arquivo": "Laudo_02_JanainaAssis_20-06-2023.pdf",
        "atendimento": "8081.0118.2204",
        "cip": "6164220402",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 43,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "20/06/2023",
        "hora_coleta": "07:35 BRT",
        "data_liberacao": "21/06/2023 18:15",
        "exames": [
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "96 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,7 %",
                "referencia": "Normal: Inferior a 5,7% | Risco aumentado: 5,7 a 6,4%",
                "nota": "Glicose Média Estimada: 117 mg/dL"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,8 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "3,51", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "190,0 mg/dL",
                "referencia": "Com jejum: Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "120 mg/dL",
                "referencia": "Risco baixo: Inferior a 130 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "45 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "125,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "28,5 ng/mL",
                "referencia": "População saudável < 60 anos: Superior a 20 ng/mL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "48,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "80,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Cálcio",
                "detalhe": "Material: Soro | Método: Cresolftaleina Complexona",
                "resultado": "9,1 mg/dL",
                "referencia": "8,3 a 10,6 mg/dL"
            },
            {
                "nome": "Magnésio",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "2,2 mg/dL",
                "referencia": "1,6 a 2,6 mg/dL"
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível (PCRus)",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,55 mg/dL",
                "alterado": True,
                "referencia": "Baixo risco: < 0,10 | Alto risco CV: > 0,20 mg/dL"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,95 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,15 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Estradiol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "110,0 pg/mL",
                "referencia": "Fase Lútea: 55,8 a 214,2 pg/mL | Folicular: 19,5 a 144,2 pg/mL"
            },
            {
                "nome": "Progesterona",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "8,50 ng/mL",
                "referencia": "Fase Lútea: 3,34 a 25,56 ng/mL | Folicular: <= 1,40 ng/mL",
                "nota": "Padrão compatível com fase lútea do ciclo ovulatório."
            },
            {
                "nome": "FSH - Hormônio Folículo Estimulante",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "4,2 mUI/mL",
                "referencia": "Fase Lútea: 1,5 a 9,1 mUI/mL"
            },
            {
                "nome": "LH - Hormônio Luteinizante",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "3,8 mUI/mL",
                "referencia": "Fase Lútea: 0,5 a 16,9 mUI/mL"
            },
            {
                "nome": "Prolactina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,2 ng/mL",
                "referencia": "Não grávidas: 2,8 a 29,2 ng/mL"
            },
            {
                "nome": "Marcador Tumoral CA 125",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "15,8 U/mL",
                "referencia": "Inferior a 35,0 U/mL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 3. LAUDO 03: 25/10/2023 (Avaliação de Fadiga e Estoques Minerais)
    # Faltam: CA 125, CA 19-9, Alfa Fetoproteína, IGF-1 (4 exames omitidos)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 3,
        "arquivo": "Laudo_03_JanainaAssis_25-10-2023.pdf",
        "atendimento": "8081.0125.3340",
        "cip": "6164334003",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 43,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "25/10/2023",
        "hora_coleta": "07:50 BRT",
        "data_liberacao": "27/10/2023 11:20",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,60 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "13,5 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "40,2 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "87,4 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "HCM", "resultado": "29,3 pg", "referencia": "27,0 a 32,0 pg"},
                    {"nome": "CHCM", "resultado": "33,6 g/dL", "referencia": "31,0 a 35,0 g/dL"},
                    {"nome": "RDW", "resultado": "12,9 %", "referencia": "11,6 a 14,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "6.400 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "265.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "94 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,6 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "13,5 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "3,13", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "35,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "58,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "32,0 ng/mL",
                "referencia": "População saudável < 60 anos: Superior a 20 ng/mL"
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Absorção Atômica",
                "resultado": "75,0 µg/dL",
                "referencia": "70,0 a 120,0 µg/dL"
            },
            {
                "nome": "Cortisol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "16,2 µg/dL",
                "referencia": "Coleta entre 6:00 e 10:00h: 5,3 a 22,5 µg/dL"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "2,15 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,08 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Antiperoxidase Tireoideana - Anticorpos (Anti-TPO)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "Inferior a 6,6 U/mL",
                "referencia": "Inferior a 13,8 U/mL"
            },
            {
                "nome": "Anti-tireoglobulina, anticorpos (aTgII)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "Inferior a 1,3 UI/mL",
                "referencia": "Inferior a 4,5 UI/mL"
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "182,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "112 mg/dL",
                "referencia": "Risco baixo: Inferior a 130 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "46 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "120,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "4,2 mg/dL",
                "referencia": "2,8 a 6,7 mg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,72 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "27 mg/dL",
                "referencia": "19 a 49 mg/dL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 4. LAUDO 04: 15/01/2024 (Rotina de Início de Ano 2024)
    # Faltam: Fibrinogênio, CA 19-9, Alfa Fetoproteína (3 exames omitidos)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 4,
        "arquivo": "Laudo_04_JanainaAssis_15-01-2024.pdf",
        "atendimento": "8081.0131.4452",
        "cip": "6164445204",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 43,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "15/01/2024",
        "hora_coleta": "08:00 BRT",
        "data_liberacao": "16/01/2024 17:40",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,80 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "14,0 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "42,1 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "87,7 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "Leucócitos Totais", "resultado": "6.500 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "260.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "93 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,5 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "12,8 µUI/mL",
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "2,94", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "165,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "98 mg/dL",
                "referencia": "Risco intermediário: < 100 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "45 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "110,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "26,0 ng/mL",
                "referencia": "Superior a 20 ng/mL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "52,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "88,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,74 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "26 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Potássio",
                "detalhe": "Material: Soro | Método: Íon Seletivo",
                "resultado": "4,1 mmol/L",
                "referencia": "3,5 a 5,1 mmol/L"
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "14 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "15 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Gama-Glutamil Transferase (GGT)",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "16 U/L",
                "referencia": "Inferior a 38 U/L"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,75 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,12 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Absorção Atômica",
                "resultado": "78,0 µg/dL",
                "referencia": "70,0 a 120,0 µg/dL"
            },
            {
                "nome": "Marcador Tumoral CA 125",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,0 U/mL",
                "referencia": "Inferior a 35,0 U/mL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 5. LAUDO 05: 13/04/2024 (Data Exata Registrada no Gráfico Original!)
    # Faltam: IGF-1, Zinco, Alfa Fetoproteína (3 exames omitidos)
    # Valores retirados dos gráficos históricos do laudo modelo:
    # Ferro: 65,0 | Ferritina: 38,1 | Vit D: 18,0 | PCRus: 0,24 | Glicose: 91 | HbA1c: 5,5 | CT: 144 | LDL: 85 | HDL: 42 | TG: 78 | Ureia: 24 | Creatinina: 0,74 | Ácido Úrico: 4,4 | TGO: 12 | TGP: 12 | GGT: 17 | TSH: 1,37 | T4L: 0,97 | Estradiol: 220,6 | FSH: 6,3
    # ---------------------------------------------------------
    laudos.append({
        "numero": 5,
        "arquivo": "Laudo_05_JanainaAssis_13-04-2024.pdf",
        "atendimento": "8081.0138.5563",
        "cip": "6164556305",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 43,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "13/04/2024",
        "hora_coleta": "11:20 BRT",
        "data_liberacao": "15/04/2024 16:50",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,70 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "13,7 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "41,0 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "87,2 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "Leucócitos Totais", "resultado": "6.300 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "262.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "65,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "38,1 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "18 ng/mL",
                "alterado": True,
                "referencia": "População saudável < 60 anos: Superior a 20 ng/mL"
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível (PCRus)",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,24 mg/dL",
                "alterado": True,
                "referencia": "Baixo risco: < 0,10 | Alto risco CV: > 0,20 mg/dL"
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "91 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,5 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "144,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "85 mg/dL",
                "referencia": "Risco intermediário: < 100 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "42 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "78,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "24 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,74 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Cálcio",
                "detalhe": "Material: Soro | Método: Cresolftaleina Complexona",
                "resultado": "8,7 mg/dL",
                "referencia": "8,3 a 10,6 mg/dL"
            },
            {
                "nome": "Magnésio",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "2,1 mg/dL",
                "referencia": "1,6 a 2,6 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "4,4 mg/dL",
                "referencia": "2,8 a 6,7 mg/dL"
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "12 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "12 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Gama-Glutamil Transferase (GGT)",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "17 U/L",
                "referencia": "Inferior a 38 U/L"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,37 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "0,97 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "FSH - Hormônio Folículo Estimulante",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "6,3 mUI/mL",
                "referencia": "Fase Folicular: 2,5 a 10,2 mUI/mL | Pico Ovulatório: 3,4 a 33,4 mUI/mL"
            },
            {
                "nome": "Estradiol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "220,6 pg/mL",
                "referencia": "Ovulatória: 63,9 a 356,7 pg/mL | Folicular: 19,5 a 144,2 pg/mL",
                "nota": "Compatível com fase pré-ovulatória / pico de estrogênio."
            }
        ]
    })

    # ---------------------------------------------------------
    # 6. LAUDO 06: 11/09/2024 (Data Exata Registrada no Gráfico Original!)
    # Faltam: Homocisteína, CA 19-9, Fibrinogênio (3 exames omitidos)
    # Ferro: 104,0 | Ferritina: 61,2 | Vit D: 44,0 | Glicose: 90 | HbA1c: 5,5 | CT: 156 | LDL: 96 | HDL: 44 | TG: 74 | TSH: 1,12 | FSH: 6,2 | Estradiol: 30,0 | Testosterona Total: 20,3 | Cortisol: 14,5
    # ---------------------------------------------------------
    laudos.append({
        "numero": 6,
        "arquivo": "Laudo_06_JanainaAssis_11-09-2024.pdf",
        "atendimento": "8081.0142.6674",
        "cip": "6164667406",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 44,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "11/09/2024",
        "hora_coleta": "07:56 BRT",
        "data_liberacao": "12/09/2024 19:10",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,82 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "14,1 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "42,5 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "6.600 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "268.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "104,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "61,2 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "44 ng/mL",
                "referencia": "Superior a 20 ng/mL | Grupos de risco: 30 a 60 ng/mL"
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "90 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,5 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "156,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "96 mg/dL",
                "referencia": "Inferior a 100 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "44 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "74,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,12 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "FSH - Hormônio Folículo Estimulante",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "6,2 mUI/mL",
                "referencia": "Fase Folicular: 2,5 a 10,2 mUI/mL"
            },
            {
                "nome": "Estradiol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "30,0 pg/mL",
                "referencia": "Folicular: 19,5 a 144,2 pg/mL"
            },
            {
                "nome": "Testosterona Total",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "20,3 ng/dL",
                "referencia": "Pré Menopausa: 12,09 a 59,46 ng/dL"
            },
            {
                "nome": "Cortisol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,5 µg/dL",
                "referencia": "Coleta entre 6:00 e 10:00h: 5,3 a 22,5 µg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,75 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Absorção Atômica",
                "resultado": "81,0 µg/dL",
                "referencia": "70,0 a 120,0 µg/dL"
            },
            {
                "nome": "Marcador Tumoral CA 125",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "13,9 U/mL",
                "referencia": "Inferior a 35,0 U/mL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 7. LAUDO 07: 18/02/2025 (Check-up Geral Semestral)
    # Faltam: CA 125, CA 19-9, Alfa Fetoproteína (3 exames omitidos)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 7,
        "arquivo": "Laudo_07_JanainaAssis_18-02-2025.pdf",
        "atendimento": "8081.0145.7785",
        "cip": "6164778507",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 44,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "18/02/2025",
        "hora_coleta": "07:40 BRT",
        "data_liberacao": "19/02/2025 18:20",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,88 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "14,1 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "42,8 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "87,7 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "Leucócitos Totais", "resultado": "6.600 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "270.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "92 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,6 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "15,0 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "3,41", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "172,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "108 mg/dL",
                "referencia": "Risco intermediário: < 100 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "46 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "90,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "42,0 ng/mL",
                "referencia": "Superior a 20 ng/mL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "75,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "110,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,78 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "26 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Potássio",
                "detalhe": "Material: Soro | Método: Íon Seletivo",
                "resultado": "4,0 mmol/L",
                "referencia": "3,5 a 5,1 mmol/L"
            },
            {
                "nome": "Cálcio",
                "detalhe": "Material: Soro | Método: Cresolftaleina",
                "resultado": "8,8 mg/dL",
                "referencia": "8,3 a 10,6 mg/dL"
            },
            {
                "nome": "Magnésio",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "2,3 mg/dL",
                "referencia": "1,6 a 2,6 mg/dL"
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "13 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "14 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Fosfatase Alcalina",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "68 U/L",
                "referencia": "46 a 116 U/L"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,60 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,20 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "T3 Livre (Triiodotironina Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "3,30 pg/mL",
                "referencia": "2,30 a 4,20 pg/mL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 8. LAUDO 08: 28/07/2025 (Data Exata Registrada no Gráfico Original!)
    # Faltam: IGF-1, Alfa Fetoproteína, Homocisteína (3 exames omitidos)
    # Vit D: 40 | Ferritina: 98,4 | Glicose: 93 | HbA1c: 5,6 | CT: 186 | LDL: 124 | HDL: 47 | TG: 63 | Ácido Úrico: 6,4 (alto) | TGO: 14 | TGP: 18 | GGT: 24 | TSH: 2,03 | T4L: 1,25 | Creatinina: 0,87 | PCRus: 0,30
    # ---------------------------------------------------------
    laudos.append({
        "numero": 8,
        "arquivo": "Laudo_08_JanainaAssis_28-07-2025.pdf",
        "atendimento": "8081.0148.8896",
        "cip": "6164889608",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 45,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "28/07/2025",
        "hora_coleta": "07:36 BRT",
        "data_liberacao": "29/07/2025 17:30",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,90 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "14,2 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "43,0 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "6.700 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "272.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "40 ng/mL",
                "referencia": "Superior a 20 ng/mL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "98,4 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "93 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,6 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "16,5 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "3,79", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "186,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "124 mg/dL",
                "referencia": "Inferior a 130 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "47 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "63,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "6,4 mg/dL",
                "alterado": True,
                "referencia": "2,8 a 6,7 mg/dL",
                "nota": "Elevação em relação aos exames anteriores. Acompanhar evolução metabólica."
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "14 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático IFCC",
                "resultado": "18 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Gama-Glutamil Transferase (GGT)",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "24 U/L",
                "referencia": "Inferior a 38 U/L"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "2,03 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,25 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,87 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível (PCRus)",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,30 mg/dL",
                "alterado": True,
                "referencia": "Baixo risco: < 0,10 | Médio: 0,10-0,20 | Alto risco CV: > 0,20 mg/dL"
            },
            {
                "nome": "Marcador Tumoral CA 125",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,2 U/mL",
                "referencia": "Inferior a 35,0 U/mL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 9. LAUDO 09: 22/10/2025 (Reavaliação Pós Ajuste Nutricional)
    # Faltam: FSH, LH, Estradiol, Progesterona (4 exames omitidos - perfil hormonal feminino ausente)
    # ---------------------------------------------------------
    laudos.append({
        "numero": 9,
        "arquivo": "Laudo_09_JanainaAssis_22-10-2025.pdf",
        "atendimento": "8081.0149.9901",
        "cip": "6164990109",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 45,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "22/10/2025",
        "hora_coleta": "07:45 BRT",
        "data_liberacao": "24/10/2025 15:30",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Automatizado",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,91 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL"},
                    {"nome": "Hemoglobina", "resultado": "14,2 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "43,0 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "6.750 /µL", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Plaquetas", "resultado": "273.000 /µL", "referencia": "150.000 a 450.000 /µL"}
                ]
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "96 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,6 %",
                "referencia": "Normal: Inferior a 5,7%"
            },
            {
                "nome": "Insulina Basal com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "16,8 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "3,99", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "178,0 mg/dL",
                "referencia": "Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Martin",
                "resultado": "116 mg/dL",
                "referencia": "Inferior a 130 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: Homogêneo",
                "resultado": "44 mg/dL",
                "referencia": "Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "90,0 mg/dL",
                "referencia": "Inferior a 150 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "5,2 mg/dL",
                "referencia": "2,8 a 6,7 mg/dL",
                "nota": "Normalização dos níveis em relação ao exame anterior."
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "115,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "96,0 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "34,0 ng/mL",
                "referencia": "Superior a 20 ng/mL"
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Absorção Atômica",
                "resultado": "71,0 µg/dL",
                "referencia": "70,0 a 120,0 µg/dL"
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível (PCRus)",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,38 mg/dL",
                "alterado": True,
                "referencia": "Baixo risco: < 0,10 | Médio: 0,10-0,20 | Alto risco CV: > 0,20 mg/dL"
            },
            {
                "nome": "Fibrinogênio",
                "detalhe": "Material: Plasma | Método: Coagulométrico",
                "resultado": "390,00 mg/dL",
                "referencia": "200,00 a 400,00 mg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Jaffé",
                "resultado": "0,77 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90"}
                ]
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "25 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,40 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,24 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            }
        ]
    })

    # ---------------------------------------------------------
    # 10. LAUDO 10: 06/01/2026 (Laudo Completo Oficial do PDF Fornecido!)
    # Contém todos os exames do arquivo do usuário na íntegra.
    # ---------------------------------------------------------
    laudos.append({
        "numero": 10,
        "arquivo": "Laudo_10_JanainaAssis_06-01-2026.pdf",
        "atendimento": "8081.0150.7702",
        "cip": "6164788886",
        "paciente": "Janaina de Assis",
        "data_nascimento": "24/06/1980",
        "idade": 45,
        "sexo": "Feminino",
        "solicitante": "Dr. Gerson Righetto Junior",
        "data_coleta": "06/01/2026",
        "hora_coleta": "07:49 BRT",
        "data_liberacao": "18/01/2026 23:09",
        "exames": [
            {
                "nome": "Hemograma com Contagem de Plaquetas",
                "detalhe": "Material: Sangue Total | Método: Impedância / Colorimetria / Fluorescência / Avaliação Microscópica",
                "resultado": "Normal",
                "referencia": "",
                "subitens": [
                    {"nome": "Eritrócitos", "resultado": "4,91 10^6/µL", "referencia": "3,80 a 4,80 10^6/µL", "alterado": True},
                    {"nome": "Hemoglobina", "resultado": "14,3 g/dL", "referencia": "12,0 a 15,0 g/dL"},
                    {"nome": "Hematócrito", "resultado": "43,2 %", "referencia": "36,0 a 46,0 %"},
                    {"nome": "VCM", "resultado": "88,0 fL", "referencia": "83,0 a 101,0 fL"},
                    {"nome": "HCM", "resultado": "29,2 pg", "referencia": "27,0 a 32,0 pg"},
                    {"nome": "CHCM", "resultado": "33,1 g/dL", "referencia": "31,0 a 35,0 g/dL"},
                    {"nome": "RDW", "resultado": "13,0 %", "referencia": "11,6 a 14,0 %"},
                    {"nome": "Leucócitos Totais", "resultado": "6.790 /µL (100 %)", "referencia": "4.000 a 10.000 /µL"},
                    {"nome": "Neutrófilos", "resultado": "4.828 /µL (71,1 %)", "referencia": "1.800 a 7.800 /µL"},
                    {"nome": "Eosinófilos", "resultado": "54 /µL (0,8 %)", "referencia": "20 a 500 /µL"},
                    {"nome": "Basófilos", "resultado": "20 /µL (0,3 %)", "referencia": "20 a 100 /µL"},
                    {"nome": "Linfócitos", "resultado": "1.602 /µL (23,6 %)", "referencia": "1.000 a 3.000 /µL"},
                    {"nome": "Monócitos", "resultado": "285 /µL (4,2 %)", "referencia": "200 a 1.000 /µL"},
                    {"nome": "Contagem de Plaquetas", "resultado": "274.000 /µL", "referencia": "150.000 a 450.000 /µL"},
                    {"nome": "VPM", "resultado": "9,0 fL", "referencia": "8,3 a 12,5 fL"}
                ]
            },
            {
                "nome": "Proteína C Reativa Ultra Sensível",
                "detalhe": "Material: Soro | Método: Imunoturbidimetria",
                "resultado": "0,52 mg/dL",
                "alterado": True,
                "referencia": "Baixo Risco: < 0,10 | Médio: 0,10 - 0,20 | Alto Risco: > 0,20 mg/dL",
                "nota": "Interpretação de risco cardiovascular conforme Diretriz SBC."
            },
            {
                "nome": "Ferro Sérico",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "125,0 µg/dL",
                "referencia": "50,0 a 170,0 µg/dL"
            },
            {
                "nome": "Ferritina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "97,5 ng/mL",
                "referencia": "10,0 a 291,0 ng/mL"
            },
            {
                "nome": "Homocisteína",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "13 µmol/L",
                "referencia": "Inferior ou igual a 15 µmol/L - Normal"
            },
            {
                "nome": "Fibrinogênio",
                "detalhe": "Material: Plasma | Método: Coagulométrico",
                "resultado": "426,00 mg/dL",
                "alterado": True,
                "referencia": "200,00 a 400,00 mg/dL"
            },
            {
                "nome": "Uréia",
                "detalhe": "Material: Soro | Método: Cinético",
                "resultado": "25 mg/dL",
                "referencia": "19 a 49 mg/dL"
            },
            {
                "nome": "Creatinina",
                "detalhe": "Material: Soro | Método: Colorimétrico Cinético (Jaffé)",
                "resultado": "0,76 mg/dL",
                "referencia": "0,55 a 1,02 mg/dL",
                "subitens": [
                    {"nome": "*eGFR", "resultado": "Superior a 90 mL/min/1,73m²", "referencia": "Superior a 90 mL/min/1,73m²"}
                ],
                "nota": "Fórmula CKD-EPI Versão 2021 sem critério de raça."
            },
            {
                "nome": "Potássio",
                "detalhe": "Material: Soro | Método: Eletrodo Íon Seletivo",
                "resultado": "3,7 mmol/L",
                "referencia": "3,5 a 5,1 mmol/L"
            },
            {
                "nome": "Magnésio",
                "detalhe": "Material: Soro | Método: Colorimétrico",
                "resultado": "2,3 mg/dL",
                "referencia": "1,6 até 2,6 mg/dL"
            },
            {
                "nome": "Cálcio",
                "detalhe": "Material: Soro | Método: Cresolftaleina Complexona",
                "resultado": "8,9 mg/dL",
                "referencia": "8,3 até 10,6 mg/dL"
            },
            {
                "nome": "25-Hidroxivitamina D (Vitamina D)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "27 ng/mL",
                "referencia": "População saudável abaixo de 60 anos: Superior a 20 ng/mL"
            },
            {
                "nome": "Glicose",
                "detalhe": "Material: Soro | Método: Hexoquinase",
                "resultado": "99 mg/dL",
                "referencia": "70 a 99 mg/dL"
            },
            {
                "nome": "Hemoglobina Glicada - HbA1c",
                "detalhe": "Material: Sangue Total | Método: Imunoturbidimetria",
                "resultado": "5,7 %",
                "alterado": True,
                "referencia": "Normal: Inferior a 5,7% | Risco aumentado: 5,7 a 6,4%",
                "nota": "Glicose Média Estimada (GME): 117 mg/dL (Método: Cálculo)"
            },
            {
                "nome": "Insulina com Índice HOMA",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "17,5 µUI/mL",
                "alterado": True,
                "referencia": "2,5 a 13,1 µUI/mL",
                "subitens": [
                    {"nome": "HOMA-IR", "resultado": "4,28", "alterado": True, "referencia": "Inferior a 2,70"}
                ]
            },
            {
                "nome": "Colesterol Total",
                "detalhe": "Material: Soro | Método: Enzimático CHOP-POD",
                "resultado": "170,0 mg/dL",
                "referencia": "Com jejum: Inferior a 190 mg/dL"
            },
            {
                "nome": "LDL - Colesterol (calculado)",
                "detalhe": "Material: Soro | Método: Fórmula de Martin",
                "resultado": "111 mg/dL",
                "referencia": "Meta: Risco baixo < 130 mg/dL | Intermediário < 100 mg/dL"
            },
            {
                "nome": "HDL - Colesterol",
                "detalhe": "Material: Soro | Método: HDL - Colesterol Homogêneo",
                "resultado": "42 mg/dL",
                "referencia": "Com jejum: Superior a 40 mg/dL"
            },
            {
                "nome": "Triglicérides",
                "detalhe": "Material: Soro | Método: Enzimático CHOP-POD",
                "resultado": "83,0 mg/dL",
                "referencia": "Com jejum: Inferior a 150 mg/dL"
            },
            {
                "nome": "Ácido Úrico",
                "detalhe": "Material: Soro | Método: Colorimétrico Enzimático",
                "resultado": "4,9 mg/dL",
                "referencia": "2,8 a 6,7 mg/dL"
            },
            {
                "nome": "Transaminase oxalacética - TGO (AST)",
                "detalhe": "Material: Soro | Método: Enzimático (IFCC)",
                "resultado": "13 U/L",
                "referencia": "Inferior a 34 U/L"
            },
            {
                "nome": "Transaminase pirúvica - TGP (ALT)",
                "detalhe": "Material: Soro | Método: Enzimático (IFCC)",
                "resultado": "13 U/L",
                "referencia": "10 a 49 U/L"
            },
            {
                "nome": "Gama-Glutamil Transferase (GGT)",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "20 U/L",
                "referencia": "Inferior a 38 U/L"
            },
            {
                "nome": "Fosfatase Alcalina",
                "detalhe": "Material: Soro | Método: Enzimático",
                "resultado": "71 U/L",
                "referencia": "46 a 116 U/L"
            },
            {
                "nome": "Anti-tireoglobulina, anticorpos (aTgII)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "Inferior a 1,3 UI/mL",
                "referencia": "Inferior a 4,5 UI/mL"
            },
            {
                "nome": "Antiperoxidase Tireoideana - Anticorpos (Anti-TPO)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "Inferior a 6,6 U/mL",
                "referencia": "Inferior a 13,8 U/mL"
            },
            {
                "nome": "Hormônio Tireoestimulante Ultrassensível (TSH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,03 µUI/mL",
                "referencia": "0,40 a 4,30 µUI/mL"
            },
            {
                "nome": "T3 Livre (Triiodotironina Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "3,40 pg/mL",
                "referencia": "2,30 a 4,20 pg/mL"
            },
            {
                "nome": "Tiroxina Livre (T4 Livre)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,27 ng/dL",
                "referencia": "0,89 a 1,76 ng/dL"
            },
            {
                "nome": "Prolactina",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "16,97 ng/mL",
                "referencia": "Não grávidas: 2,8 a 29,2 ng/mL"
            },
            {
                "nome": "Estradiol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "43,7 pg/mL",
                "referencia": "Folicular: 19,5 a 144,2 | Ovulatória: 63,9 a 356,7 | Lútea: 55,8 a 214,2 pg/mL"
            },
            {
                "nome": "Progesterona",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,26 ng/mL",
                "referencia": "Fase Folicular: <= 1,40 ng/mL | Fase Lútea: 3,34 a 25,56 ng/mL"
            },
            {
                "nome": "FSH - Hormônio Folículo Estimulante",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "3,1 mUI/mL",
                "referencia": "Fase Folicular: 2,5 a 10,2 mUI/mL"
            },
            {
                "nome": "Hormônio Luteinizante (LH)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "1,7 mUI/mL",
                "referencia": "Fase Folicular: 1,9 a 12,5 mUI/mL"
            },
            {
                "nome": "SHBG (Globulina Transportadora de Hormônios Sexuais)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "25,20 nmol/L",
                "referencia": "Mulheres não grávidas: 18 a 144 nmol/L"
            },
            {
                "nome": "Cortisol",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "15,0 µg/dL",
                "referencia": "Coleta entre 6:00 e 10:00h: 5,3 a 22,5 µg/dL"
            },
            {
                "nome": "Testosterona Total",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "15,8 ng/dL",
                "referencia": "Sexo Feminino (Pré Menopausa): 12,09 a 59,46 ng/dL"
            },
            {
                "nome": "Testosterona Livre Calculada",
                "detalhe": "Material: Soro | Método: Cálculo",
                "resultado": "0,33 ng/dL",
                "referencia": "Fase folicular: 0,18 a 1,68 ng/dL"
            },
            {
                "nome": "Testosterona Biodisponível",
                "detalhe": "Material: Soro | Método: Cálculo",
                "resultado": "7,66 ng/dL",
                "referencia": "Mulheres adultas fase folicular: 4,4 a 39,0 ng/dL"
            },
            {
                "nome": "Antígeno Carcinoembriogênico (CEA)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "0,9 ng/mL",
                "referencia": "Não Fumantes: Inferior a 2,5 ng/mL"
            },
            {
                "nome": "Marcador Tumoral CA 125",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "14,6 U/mL",
                "referencia": "Inferior a 35,0 U/mL"
            },
            {
                "nome": "Marcador Tumoral CA 19-9",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "12,8 U/mL",
                "referencia": "Inferior a 37,0 U/mL"
            },
            {
                "nome": "Alfa Fetoproteína",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "Inferior a 1,3 ng/mL",
                "referencia": "Adultos: < 8,1 ng/mL"
            },
            {
                "nome": "Zinco Sanguíneo",
                "detalhe": "Material: Soro | Método: Espectrofotometria Absorção Atômica",
                "resultado": "68,79 µg/dL",
                "alterado": True,
                "referencia": "70,0 a 120,0 µg/dL (Carência: abaixo de 30)"
            },
            {
                "nome": "IGF-1 (Somatomedina C)",
                "detalhe": "Material: Soro | Método: Quimioluminescência",
                "resultado": "158,0 ng/mL",
                "referencia": "Feminino 45 a 49 anos: 53 a 215 ng/mL",
                "nota": "Data da coleta desta dosagem específica: 12/01/2026."
            }
        ]
    })

    return laudos


def main():
    laudos = gerar_dados_laudos()
    print(f"Iniciando a geração de {len(laudos)} laudos em PDF...")
    
    arquivos_gerados = []
    for l in laudos:
        caminho = os.path.join(OUTPUT_DIR, l['arquivo'])
        criar_laudo_pdf(l, caminho)
        arquivos_gerados.append(caminho)
        print(f"[OK] Gerado: {l['arquivo']} ({len(l['exames'])} exames inclusos)")
        
    # Salva também um arquivo JSON estruturado com a série histórica completa
    json_path = os.path.join(OUTPUT_DIR, "retrospectiva_3_anos_janaina.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(laudos, f, ensure_ascii=False, indent=2)
    print(f"[HISTORICO] Arquivo JSON historico consolidado salvo em: {json_path}")


if __name__ == "__main__":
    main()
