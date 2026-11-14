# -*- coding: utf-8 -*-
"""Monta prototipo_leitor_exames.html somente a partir dos CSVs desta pasta.

Uso: python conhecimento_exames_csv/_gerador/montar_prototipo.py  (rodar depois de gerar_csvs.py)
"""
import csv, json, os

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.dirname(AQUI)
L = lambda n: list(csv.DictReader(open(os.path.join(D, n), encoding="utf-8")))

S, SI = [], {}
def s(t):
    if t not in SI:
        SI[t] = len(S); S.append(t)
    return SI[t]

E = {}
for c in L("catalogo_exames.csv"):
    E[c["exame_id"]] = dict(n=c["nome_exame"], c=c["categoria"], u=c["unidade"], t=c["tipo_resultado"], d=c["direcoes_relevantes"],
                           r=c["resumo_exame"], sx=c["sexo_dependente"], obs=c["observacoes"], i=[], ir=None, k=[], p=[])
for r in L("interpretacoes_exames.csv"):
    E[r["exame_id"]]["i"].append([r["nivel_id"], r["direcao"], r["status_informacao"], s(r["descricao_resultado"]), s(r["informacoes_pares_etarios"]),
                                  s(r["impactos_individuo"]), s(r["possiveis_causas"]), s(r["mitigacao"]), r["status_criterio"]])
for r in L("criterios_classificacao.csv"):
    e = E[r["exame_id"]]
    if r["tipo_criterio"] == "intervalo_referencia":
        e["ir"] = [float(r["limite_inferior"]), float(r["limite_superior"]), r["unidade"]]
    elif r["tipo_criterio"] in ("grau_evento_adverso_ctcae", "limite_decisao_clinica"):
        e["k"].append([r["tipo_criterio"], r["limite_relativo"] or " ".join(x for x in (r["operador_inferior"], r["limite_inferior"], r["operador_superior"], r["limite_superior"], r["unidade"]) if x),
                       r["condicoes_clinicas"], r["ref_id"]])
for r in L("pares_etarios.csv"):
    E[r["exame_id"]]["p"].append([r["sexo"], r["p2_5"], r["p50"], r["p97_5"], r["n_amostra"], r["unidade"], r["ciclo"], r["pct_abaixo_ref_projeto"], r["pct_acima_ref_projeto"]])
for r in L("pares_etarios_percentis.csv"):
    q = E[r["exame_id"]].setdefault("q", {}).setdefault(r["sexo"], [None] * 101)
    q[int(r["percentil"])] = float(r["valor"])

js = json.dumps({"s": S, "e": E}, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
t = open(os.path.join(AQUI, "prototipo_template.html"), encoding="utf-8").read()
open(os.path.join(D, "prototipo_leitor_exames.html"), "w", encoding="utf-8").write(t.replace("__DATA__", js))
print("ok", len(E), "exames;", sum(1 for e in E.values() if "q" in e), "com percentis")
