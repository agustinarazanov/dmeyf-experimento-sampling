import json, sys, datetime

salida = sys.argv[1]
resultado = None
hora = datetime.datetime.now().strftime("%H:%M:%S")
for linea in sys.stdin:
    try:
        ev = json.loads(linea)
    except ValueError:
        if linea.strip():
            print(linea.rstrip(), file=sys.stderr, flush=True)
        continue
    if not isinstance(ev, dict):
        continue
    tipo = ev.get("type")
    hora = datetime.datetime.now().strftime("%H:%M:%S")
    if tipo == "assistant":
        for b in ev.get("message", {}).get("content", []) or []:
            if not isinstance(b, dict):
                continue
            if b.get("type") == "tool_use":
                entrada = b.get("input", {}) or {}
                detalle = entrada.get("command") or entrada.get("file_path") or entrada.get("pattern") or ""
                print(f"{hora}  {b.get('name', '?'):<10} {str(detalle)[:100]}", flush=True)
            elif b.get("type") == "text" and (b.get("text") or "").strip():
                print(f"{hora}  texto      {b['text'].strip().splitlines()[0][:100]}", flush=True)
    elif tipo == "result":
        resultado = ev
if resultado is None:
    resultado = {"subtype": "sin_resultado", "is_error": True, "total_cost_usd": 0, "num_turns": 0,
                 "result": "claude no emitió un evento result (flag inválido, autenticación o corte antes de empezar)"}
json.dump(resultado, open(salida, "w"), ensure_ascii=False, indent=1)
costo = round(resultado.get("total_cost_usd") or 0, 4)
print(f"{hora}  fin        {resultado.get('subtype')} · {resultado.get('num_turns')} turnos · US$ {costo}", flush=True)
if resultado.get("is_error"):
    print(f"{hora}  error      {str(resultado.get('result', ''))[:300]}", flush=True)
