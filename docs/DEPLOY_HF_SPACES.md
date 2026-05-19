# Deploy en Hugging Face Spaces (mirror de Streamlit Cloud)

Hugging Face Spaces es alternativa estable a Streamlit Cloud free:

| | Streamlit Cloud free | HF Spaces free |
|---|---|---|
| Sleep mode | <6h sin tráfico (cambió silenciosamente 2026) | 48h sin tráfico |
| Wake-up | Manual o Playwright keepalive (impredecible) | Auto, <5s al primer hit |
| RAM | 1 GB | **16 GB** |
| CPU | shared | shared (similar) |
| Errores "Oh no" intermitentes | Frecuentes | Ninguno reportado |
| Deploy | `git push origin main` | `git push hf main` |

URL final: `https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring`

## Setup paso a paso (~10 min total)

### Paso 1 — Crear cuenta gratis en HF

1. Andá a https://huggingface.co/join
2. Email + password + username (anotá tu username, lo necesitas en paso 3)
3. Confirmá email
4. Login

### Paso 2 — Crear el Space

1. https://huggingface.co/new-space
2. Llená:
   - **Owner**: tu username
   - **Space name**: `goes-volcanic-monitoring` (o el que prefieras)
   - **License**: `mit`
   - **Select the Space SDK**: click **`Docker`** (HF removio el SDK
     Streamlit de la UI en mayo-2026 — usamos Docker con Dockerfile
     custom que ya esta en el repo).
   - **Choose a Docker template**: click **`Blank`** (la opcion mas a
     la izquierda, sin template).
   - **Space hardware**: `CPU Basic · FREE` (default).
   - **Public** (no Private para que sea accesible sin login).
3. Click **Create Space**.

Te lleva a `https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring`. Va a mostrar un repo vacío con un README placeholder. Lo vamos a reemplazar.

### Paso 3 — Generar Access Token

HF requiere autenticación para `git push`. Generamos un token:

1. https://huggingface.co/settings/tokens
2. Click **New token**.
3. Nombre: `goes-push`
4. Type: **Write** (no Read).
5. Click **Generate token**.
6. **COPIÁ EL TOKEN** (no se vuelve a mostrar). Empezará con `hf_...`.

### Paso 4 — Agregar HF como remote git + push

Desde el terminal en la carpeta del repo:

```bash
cd C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/Goes

# Agregar HF como remote (reemplazá <USERNAME> con tu username de HF)
git remote add hf https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring

# Push con autenticación (te va a pedir username y password)
# Username: tu username HF
# Password: el TOKEN que generaste en Paso 3 (NO tu password de HF)
git push hf main
```

Si HF ya creó algún commit (README placeholder), capaz necesitás force push:
```bash
git push hf main --force
```

### Paso 5 — Esperar el build

1. Volvé al Space en `https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring`.
2. Vas a ver un log de build en vivo:
   - `Installing requirements...` (~2-3 min)
   - `Starting streamlit...`
   - `App is running` (3-5 min total)
3. Si falla, mostrá el log y diagnosticamos.

### Paso 6 — Verificar

1. Refrescá la página del Space.
2. Vas a ver el dashboard cargando.
3. Sidebar debería tener el badge `🔖 build-2026-05-19-defensive-geo-load`.
4. Probá: Modo Guardia → Mosaico → botones funcionando.

## Workflow post-deploy

### Cambios nuevos al código

```bash
# Push a AMBOS deploys
git push origin main      # Streamlit Cloud
git push hf main          # HF Spaces
```

O para que `git push` empuje a los dos automaticamente:

```bash
# Configurar push múltiple (una sola vez)
git remote set-url --add --push origin https://github.com/MendozaVolcanic/goes-volcanic-monitoring.git
git remote set-url --add --push origin https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring
# Ahora `git push origin main` pushea a los dos
```

### Si Streamlit Cloud sigue dando problemas

Compartí con SERNAGEOMIN la URL de HF Spaces como **primaria**:
```
https://huggingface.co/spaces/<USERNAME>/goes-volcanic-monitoring
```

Streamlit Cloud (`goesvolcanic.streamlit.app`) queda como respaldo.

## Troubleshooting

### Build falla con `ModuleNotFoundError`
- Verificá que el módulo esté en `requirements.txt`.
- HF usa pip estándar (no uv como Streamlit Cloud), versiones se resuelven igual.

### Build OK pero app crashea
- Click **Logs** en el panel del Space para ver el traceback completo.
- Probable: alguna feature funciona en Streamlit Cloud pero no en HF (raro pero posible).

### `git push hf main` falla con `403 Forbidden`
- El token caducó o no tiene permiso Write. Regenerá en https://huggingface.co/settings/tokens.

### Quiero borrar el Space
- Settings del Space → Delete this space. Confirmá escribiendo el nombre.
- El repo en GitHub queda intacto.

## Costo

$0. HF Spaces free es para siempre, sin tarjeta. Si en algún momento querés más recursos (GPU, RAM extra), tienen tier paid pero no lo necesitamos.
