import sys

with open('Etapa Exames de Sangue/test_script.js', encoding='utf-8') as f:
    code = f.read()

# Tokenizer básico que ignora strings e regex
pos = 0
n = len(code)
line = 1
col = 1
stack = [] # armazena (tipo, line, col, snippet)

in_backtick = False

while pos < n:
    ch = code[pos]
    
    # Gerenciamento de linhas
    if ch == '\n':
        line += 1
        col = 1
        pos += 1
        continue
        
    # Comentários //
    if ch == '/' and pos + 1 < n and code[pos+1] == '/':
        pos += 2
        while pos < n and code[pos] != '\n':
            pos += 1
        continue
        
    # Comentários /* */
    if ch == '/' and pos + 1 < n and code[pos+1] == '*':
        pos += 2
        while pos + 1 < n and not (code[pos] == '*' and code[pos+1] == '/'):
            if code[pos] == '\n':
                line += 1
                col = 1
            pos += 1
        pos += 2
        continue

    # Strings simples '
    if ch == "'":
        pos += 1
        while pos < n and code[pos] != "'":
            if code[pos] == '\\':
                pos += 1
            elif code[pos] == '\n':
                line += 1
            pos += 1
        pos += 1
        continue

    # Strings duplas "
    if ch == '"':
        pos += 1
        while pos < n and code[pos] != '"':
            if code[pos] == '\\':
                pos += 1
            elif code[pos] == '\n':
                line += 1
            pos += 1
        pos += 1
        continue

    # Template strings `
    if ch == '`':
        pos += 1
        while pos < n and code[pos] != '`':
            if code[pos] == '\\':
                pos += 1
            elif code[pos] == '$' and pos + 1 < n and code[pos+1] == '{':
                # Expressão ${...} dentro de template literal
                stack.append(('${', line, col, code[pos:pos+15]))
                pos += 2
                # Agora estamos dentro do código JS de novo até achar o correspondente '}'
                break
            elif code[pos] == '\n':
                line += 1
            pos += 1
        else:
            if pos < n and code[pos] == '`':
                pos += 1
        continue

    if ch == '{':
        stack.append(('{', line, col, code[pos:pos+20].replace('\n', ' ')))
    elif ch == '}':
        if not stack:
            print(f"ERRO: Chave fechada extra '}}' na LINHA {line}, COLUNA {col} -> Contexto: {code[max(0, pos-40):pos+40].replace('\n', ' ')}")
        else:
            topo = stack.pop()
            # print(f"Fechou {topo[0]} da linha {topo[1]} na linha {line}")
            
    pos += 1
    col += 1

print(f"Varredura finalizada. Restaram {len(stack)} blocos abertos na pilha.")
for item in stack[:10]:
    print(f"Aberto não fechado: {item[0]} na linha {item[1]}: {item[3]}")
