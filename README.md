# 🎲 AI Dungeon Master - RPG Adventure Generator

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangChain](https://img.shields.io/badge/LangChain-Powered-green.svg)](https://langchain.com)

Un generador de aventuras RPG potenciado por Inteligencia Artificial que crea misiones, enemigos, narrativa, diálogos y mapas ASCII de forma procedural.

![AI Dungeon Master Demo](https://via.placeholder.com/800x400/1a1a2e/ffffff?text=AI+Dungeon+Master+Demo)

## 🌟 Características

- **🗡️ Generación de Misiones**: Quests completas con objetivos, recompensas y giros argumentales
- **👹 Creación de Enemigos**: Monstruos únicos con estadísticas, habilidades y lore
- **📖 Narrativa Atmosférica**: Descripciones inmersivas de escenas y ambientes
- **💬 Diálogos de NPCs**: Conversaciones dinámicas con personalidad
- **🗺️ Mapas ASCII**: Mazmorras y mundos generados proceduralmente
- **⚔️ Encuentros Completos**: Combina todos los elementos para crear encuentros listos para jugar

## 🛠️ Tecnologías

- **Python 3.9+**
- **LangChain** - Framework para aplicaciones LLM
- **Ollama** - LLMs locales (llama3.2, mistral, etc.)
- **OpenAI API** - GPT-3.5/GPT-4 (opcional)
- **Rich** - Terminal formatting
- **Pydantic** - Data validation

## 📦 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/cesar530/ai-dungeon-master.git
cd ai-dungeon-master
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. (Opcional) Configurar Ollama

Para usar LLMs locales, instala [Ollama](https://ollama.ai/):

```bash
# Instalar Ollama y descargar un modelo
ollama pull llama3.2
```

### 5. (Opcional) Configurar OpenAI

Crea un archivo `.env` con tu API key:

```bash
OPENAI_API_KEY=tu_api_key_aqui
```

## 🚀 Uso Rápido

### Modo Interactivo (Jupyter Notebook)

```bash
jupyter notebook nb_principal.ipynb
```

### Modo Script

```python
from ai_dungeon_master import AIDungeonMaster

# Inicializar (usa 'fallback' si no tienes LLM configurado)
dm = AIDungeonMaster(provider="fallback")

# Generar una misión
mission = dm.generate_mission(
    theme="dark fantasy",
    player_level=5,
    difficulty="medium"
)

# Generar un enemigo
enemy = dm.generate_enemy(
    difficulty="hard",
    environment="dungeon"
)

# Generar un mapa de mazmorra
dungeon = dm.generate_dungeon_map(
    width=40,
    height=20,
    num_rooms=5
)

# Generar narrativa
narrative = dm.generate_narrative(
    scene_type="exploration",
    mood="mysterious"
)
```

### Demo desde terminal

```bash
python ai_dungeon_master.py
```

## 📁 Estructura del Proyecto
```
12_AI_Dungeon_Master/
├── ai_dungeon_master.py  # Clase principal y lógica del generador
├── utils.py              # Funciones de utilidad y templates
├── nb_principal.ipynb    # Notebook interactivo con demos
├── requirements.txt      # Dependencias del proyecto
├── .gitignore           # Archivos ignorados por git
├── README.md            # Este archivo
└── .env                 # Variables de entorno (crear manualmente)
```

## 🎮 Ejemplos

### Generar un Encuentro Completo

```python
dm = AIDungeonMaster(provider="ollama", model="llama3.2")

encounter = dm.create_encounter(
    difficulty="hard",
    num_enemies=3,
    theme="undead"
)
```

### Mapa ASCII Ejemplo

```
########################################
#......................................#
#..@..#####....#######################.#
#.....#   #....#                     #.#
#.....# E #....# C                   #.#
#.....#   #....#                     #.#
#.....#####....#######################.#
#......................................#
#..........#####.......................#
#..........#   #.....###################
#..........# E #.....#                >#
#..........#   #.....###################
#..........#####.......................#
########################################

Leyenda:
@ = Jugador    E = Enemigo    C = Cofre
# = Muro       . = Suelo      > = Escaleras
```

### Guardar y Cargar Campañas

```python
# Guardar todo el contenido generado
dm.save_campaign("mi_campana.json")

# Cargar una campaña existente
dm.load_campaign("mi_campana.json")
```

## 🔧 Configuración

### Proveedores LLM Disponibles

| Provider | Descripción | Requisitos |
| -------- | ----------- | ---------- |
| `ollama` | LLM local con Ollama | Ollama instalado + modelo |
| `openai` | OpenAI API | API key en `.env` |
| `fallback` | Generación sin LLM | Ninguno |

### Parámetros de Configuración

```python
dm = AIDungeonMaster(
    provider="ollama",      # Proveedor LLM
    model="llama3.2",       # Modelo a usar
    base_url="http://localhost:11434"  # URL de Ollama
)
```

## 📊 Características Técnicas

- **Generación Procedural**: Algoritmos para crear mapas únicos
- **Sistema de Plantillas**: Prompts optimizados para cada tipo de contenido
- **Escalado de Dificultad**: Estadísticas de enemigos ajustadas al nivel
- **Fallback Inteligente**: Funciona sin LLM con contenido pre-generado
- **Rich Output**: Visualización colorida en terminal

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.
```
MIT License

Copyright (c) 2026 César Adrián Delgado Díaz

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👤 Autor

- 👤 Autor : **César Adrián Delgado Díaz**
- 💼 LinkedIn: [linkedin.com/in/cesar-delgado-diaz](linkedin.com/in/cesar-delgado-diaz)
- 🐙 GitHub: [github.com/cesar530](https://github.com/cesar530)

---

🎲 *"Roll for initiative!"* 🎲
