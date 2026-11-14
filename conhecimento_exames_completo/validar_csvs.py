# -*- coding: utf-8 -*-
"""Validação dos CSVs gerados (somente leitura)."""
import csv, json, os, re, collections
D = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.dirname(D)
def ler(n):
    with open(os.path.join(D, n), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))
T = {n: ler(n) for n in ["catalogo_exames.csv","interpretacoes_exames.csv","criterios_classificacao.csv","pares_etarios.csv","mapeamento_niveis.csv","referencias.csv","pendencias.csv"]}
res = []
def ok(c, m): res.append(("OK " if c else "FALHA ") + m)
pk = {"catalogo_exames.csv":"exame_id","interpretacoes_exames.csv":"interp_id","criterios_classificacao.csv":"criterio_id","pares_etarios.csv":"par_id","mapeamento_niveis.csv":"mapeamento_id","referencias.csv":"ref_id","pendencias.csv":"pendencia_id"}
for n, k in pk.items():
    v = [r[k] for r in T[n]]
    ok(len(v) == len(set(v)) and all(v), f"{n}: {len(v)} linhas, chave {k} única e não vazia")
    cab = open(os.path.join(D, n), encoding="utf-8").readline()
    ok(cab.count('"') % 2 == 0 and not cab.startswith("﻿"), f"{n}: cabeçalho único, UTF-8 sem BOM")
ex = {r["exame_id"] for r in T["catalogo_exames.csv"]}
refs = {r["ref_id"] for r in T["referencias.csv"]}
pars = {r["par_id"] for r in T["pares_etarios.csv"]}
kb = json.load(open(os.path.join(R,"02_backend/03_semantica_ontologias/base_conhecimento_exames_565.json"), encoding="utf-8"))
ok(ex == set(kb), f"catálogo cobre os {len(kb)} exames da base 565")
ok(all(r["codigo_loinc"] == kb[r["exame_id"]]["codigo_loinc"] and r["nome_exame"] == kb[r["exame_id"]]["nome_exame"] for r in T["catalogo_exames.csv"]), "LOINC e nomes preservados da base 565")
for n in ["interpretacoes_exames.csv","criterios_classificacao.csv","pares_etarios.csv"]:
    ok(all(r["exame_id"] in ex for r in T[n]), f"{n}: todo exame_id existe no catálogo")
for n, c in [("interpretacoes_exames.csv","ref_id_texto"),("criterios_classificacao.csv","ref_id"),("pares_etarios.csv","ref_id"),("catalogo_exames.csv","ref_id_resumo")]:
    ok(all((not r[c]) or r[c] in refs for r in T[n]), f"{n}: {c} existe em referencias.csv")
ok(all(all(p in pars for p in r["par_ids"].split(";") if p) for r in T["interpretacoes_exames.csv"]), "interpretacoes.par_ids existem em pares_etarios.csv")
I = T["interpretacoes_exames.csv"]
cov = collections.Counter((r["exame_id"], r["nivel_id"]) for r in I if r["nivel_id"])
falta = [(e, n) for e in ex for n in "12345" if cov[(e, n)] == 0]
ok(not falta, f"todos os exames têm linha para os 5 níveis (faltando: {len(falta)})")
ok(len({(r['exame_id'], r['nivel_id'], r['direcao']) for r in I}) == len(I), "sem duplicidade exame+nível+direção")
st = collections.Counter(r["status_informacao"] for r in I)
res.append("INFO status_informacao: " + dict(st).__repr__())
res.append("INFO linhas por nível: " + dict(collections.Counter(r["nivel_id"] or "fora_escala" for r in I)).__repr__())
proib = ["parabéns","excelente","hábitos ruins","perfeitamente equilibrad","totalmente seguro","basta melhorar","a maioria das pessoas"]
txt = " ".join(" ".join(r.values()) for n in T for r in T[n] if n != "referencias.csv").lower()
ok(not any(p in txt for p in proib), "nenhuma expressão proibida nos textos")
ok(not re.search(r"\b(86|8|4|1,5|0,5)% d", txt), "percentuais da base antiga (86%, 8%, 4%, 1,5%, 0,5%) não copiados")
ok(all(r["status_informacao"] != "conteudo_disponivel" or r["descricao_resultado"] for r in I), "linhas com conteúdo têm descrição")
ok(all(r["status_informacao"] in ("nao_aplicavel","evidencia_insuficiente") or r["mitigacao"] for r in I), "linhas aplicáveis com texto têm mitigação")
# altos e baixos não compartilham causas
pares_dir = collections.defaultdict(dict)
for r in I:
    if r["direcao"] in ("abaixo","acima") and r["possiveis_causas"]:
        pares_dir[(r["exame_id"], r["nivel_id"])][r["direcao"]] = r["possiveis_causas"]
ok(all(v.get("abaixo") != v.get("acima") for v in pares_dir.values() if len(v) == 2), "causas de valores baixos e altos são textos distintos")
P = T["pares_etarios.csv"]
ok(all((r["p50"] == "") == (r["status_informacao"] == "evidencia_insuficiente") for r in P), "pares sem amostra suficiente ficam vazios (sem zero)")
ok(all(r["n_amostra"].isdigit() for r in P), "n_amostra numérico")
CR = T["criterios_classificacao.csv"]
def num(s):
    try: float(s); return True
    except ValueError: return False
ok(all((not r[c]) or num(r[c]) for r in CR for c in ("limite_inferior","limite_superior")), "limites numéricos com ponto decimal")
# lacunas/sobreposições da regra do projeto por exame
g = collections.defaultdict(list)
for r in CR:
    if r["tipo_criterio"] == "regra_algoritmica_projeto":
        g[r["exame_id"]].append(r)
prob = 0
for e, rs in g.items():
    iv = sorted([(float(r["limite_inferior"]) if r["limite_inferior"] else -1e18, r["operador_inferior"], float(r["limite_superior"]) if r["limite_superior"] else 1e18, r["operador_superior"]) for r in rs])
    for (a1, o1, b1, p1), (a2, o2, b2, p2) in zip(iv, iv[1:]):
        if abs(b1 - a2) > 1e-6 or (p1 in ("<=",) and o2 == ">=") or (p1 == "<" and o2 == ">"):
            prob += 1
ok(prob == 0, f"regras do projeto sem lacuna nem sobreposição em {len(g)} exames (problemas: {prob})")
for l in res: print(l)
