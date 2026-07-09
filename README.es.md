# Organismo

**Deja de pagarle a tu LLM por recalcular lo mismo dos veces.**

[![Licencia: Apache 2.0](https://img.shields.io/badge/Licencia-Apache%202.0-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.9+-black?style=flat-square)
![MCP](https://img.shields.io/badge/MCP-compatible-black?style=flat-square)
![Estado](https://img.shields.io/badge/estado-temprano-orange?style=flat-square)

[English](README.md) · [Español](README.es.md)

## Qué es esto

Una capa de caché semántico para sistemas de IA multi-agente. Antes de generar una respuesta, tu sistema revisa si ya contestó algo casi idéntico — y si es así, sirve esa respuesta gratis en vez de pagar por generar de nuevo.

Tres resultados posibles por cada consulta:

- **reflejo** (similitud ≥ 0.90) — sirve la respuesta guardada directo. Cero tokens.
- **déjà vu** (similitud ≥ 0.78) — inyecta las respuestas más parecidas como contexto, y genera.
- **miss** — genera normal, y guarda el resultado para la próxima vez.

Cada generación hace la siguiente más barata. Más uso → más ecos → mejor tasa de aciertos → menor costo marginal. Es la curva contraria a como escala el costo en la mayoría de productos de IA.

## Arranque rápido

```bash
pip install psycopg2-binary
git clone https://github.com/turbillon50/organismo && cd organismo
```

```python
from organismo.cache import Organismo
from organismo.pg_store import PgVectorStore
from organismo.middleware import with_organismo

store = Organismo(
    PgVectorStore(dsn="postgres://...", embed_fn=tu_funcion_de_embeddings, dims=768)
)
handler = with_organismo(store, tu_funcion_de_generacion)

respuesta = handler({"messages": [{"role": "user", "content": "¿Qué es X?"}]})
```

O sáltate la infraestructura por completo y conéctalo como servidor MCP hospedado, vivo en 30 segundos:

```json
{
  "mcpServers": {
    "organismo": {
      "url": "https://mcp.mindcontextia.one/mcp/tu-slug/sse",
      "headers": { "Authorization": "Bearer tu-api-key" }
    }
  }
}
```

Consigue una llave gratis en [mindcontextia.one](https://mindcontextia.one).

## Por qué existe

Lo construí después de quemar $200 USD diarios en tokens de inferencia construyendo un producto desde cero — sobre todo repreguntándole a mis propios agentes las mismas cosas sobre mi propio código, una y otra vez, porque los LLMs no tienen memoria entre llamadas. La corrección fue vergonzosamente simple: vectoriza la pregunta, no el par pregunta-respuesta junto. Vectorizar ambos diluye la similitud — una pregunta idéntica nunca da 1.0 contra un bloque que también trae la respuesta. Vectoriza la llave, guarda el valor. Con eso corregido: las consultas idénticas dan similitud **1.0**, las parafraseadas caen cerca de **0.87**, las que no tienen relación se quedan cerca de **0.52** — separación limpia, medida en producción, no en una lámina de benchmark.

## Cómo se compara

| | Organismo | Mem0 | Supermemory | MemClaw |
|---|---|---|---|---|
| Mecanismo | Caché semántico de respuesta | Extracción de hechos + perfil | Extracción de hechos + búsqueda híbrida | Memoria compartida gobernada + grafo de conocimiento |
| MCP nativo | ✅ | Parcial | ✅ | ✅ |
| Self-host | ✅ Apache 2.0 | ✅ Apache 2.0 | ❌ | ✅ Apache 2.0 |
| Detección de contradicciones | 🔧 en camino | ❌ | ❌ | ✅ |
| Aprendizaje por resultado | 🔧 en camino | ❌ | ❌ | ✅ |
| Documentación en español primero | ✅ | ❌ | ❌ | ❌ |

Mem0 y Supermemory extraen hechos estructurados de conversaciones y arman perfiles que evolucionan — un mecanismo relacionado pero distinto. MemClaw es el par arquitectónico más cercano: memoria compartida gobernada para flotas de agentes, hoy más madura en gobernanza. Vamos hacia allá (ver [CONTRIBUTING.md](CONTRIBUTING.md)), empezando por la pieza más barata de resolver bien primero: no regeneres lo que ya sabes.

## Implementación de referencia

- [`organismo/cache.py`](organismo/cache.py) — el motor de decisión central
- [`organismo/pg_store.py`](organismo/pg_store.py) — backend de Postgres + pgvector
- [`organismo/middleware.py`](organismo/middleware.py) — envuelve cualquier endpoint compatible con OpenAI
- [`examples/quickstart.py`](examples/quickstart.py) — ejemplo completo funcionando

## Licencia

Apache 2.0 — ver [LICENSE](LICENSE). Úsalo, clónalo, véndelo, solo conserva el aviso.

---

*Construido por [V·Momentum](https://mindcontextia.one). Extraído de un sistema en producción con tráfico real.*
