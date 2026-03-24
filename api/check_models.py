import litellm

models = list(litellm.model_cost.keys())

# Группируем по провайдерам
providers = {}
for m in models:
    if "/" in m:
        provider = m.split("/")[0]
    elif m.startswith(("gpt", "o1", "o3", "chatgpt")):
        provider = "openai"
    elif m.startswith("claude"):
        provider = "anthropic"
    else:
        provider = "other"
    providers.setdefault(provider, []).append(m)

print("Providers with model counts:")
for p, ms in sorted(providers.items(), key=lambda x: -len(x[1]))[:15]:
    print(f"  {p}: {len(ms)} models")

print()
print("OpenAI models (first 15):")
openai = [m for m in models if m.startswith(("gpt", "o1-", "o3-"))]
for m in sorted(set(openai))[:15]:
    print(f"  {m}")
