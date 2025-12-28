import streamlit as st
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="LSS → Foundry VTT Converter",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styles
st.markdown("""
<style>
    .header-title {
        color: #2d5f7e;
        text-align: center;
        margin-bottom: 30px;
    }
    .step-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        border-left: 4px solid #2d5f7e;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .info-box {
        background-color: #e7f3ff;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #0066cc;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("ℹ️ Информация")
    st.markdown("**Версия:** 2.2.1 (улучшенный блок видения)")
    st.markdown("**Назначение:** Конвертация персонажей из Long Story Short в Foundry VTT")
    
    st.divider()
    
    st.markdown("### ✨ Возможности")
    st.markdown("""
    - ✅ Загрузка JSON файлов
    - ✅ Выбор расы и видения
    - ✅ Учёт классовых способностей видения
    - ✅ Конвертация всех параметров
    - ✅ Скачивание готового JSON
    """)
    
    st.divider()
    
    st.markdown("### 🌐 Совместимость")
    st.markdown("""
    - Foundry VTT v11+
    - D&D 5e System v4.0+
    - Python 3.8+
    """)

# Main title
st.markdown('<h1 class="header-title">⚔️ LSS → Foundry VTT D&D 5e Converter v2.2.1</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #666;">Конвертация персонажей из Long Story Short</p>', unsafe_allow_html=True)

# STEP 1: Upload JSON file
st.markdown('<div class="step-container"><h2>📁 Шаг 1: Загрузи JSON</h2></div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Выбери JSON файл из Long Story Short",
    type=["json"],
    help="Файл должен содержать данные персонажа в формате Long Story Short"
)

character_data = None
character_info = {}

if uploaded_file:
    try:
        file_content = uploaded_file.read().decode('utf-8')
        raw_data = json.loads(file_content)
        
        # Parse character data
        if "data" in raw_data:
            character_data = raw_data["data"]
        else:
            character_data = raw_data
        
        # Extract character info for display
        character_info = {
            "Имя": character_data.get("name", {}).get("value", "Unknown"),
            "Класс": character_data.get("class", {}).get("value", "Unknown"),
            "Раса": character_data.get("race", {}).get("value", "Unknown"),
            "Уровень": character_data.get("level", {}).get("value", "Unknown"),
            "Выравнивание": character_data.get("alignment", {}).get("value", "Unknown")
        }
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("✅ JSON файл успешно загружен!")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("👤 Имя", character_info["Имя"])
        with col2:
            st.metric("🎭 Класс", character_info["Класс"])
        with col3:
            st.metric("🧝 Раса", character_info["Раса"])
        with col4:
            st.metric("⚡ Уровень", character_info["Уровень"])
        with col5:
            st.metric("⚖️ Выравнивание", character_info["Выравнивание"])
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Ошибка при чтении файла: {str(e)}")
        st.stop()

if not character_data:
    st.info("👆 Загрузите JSON файл чтобы начать")
    st.stop()

# STEP 2: Settings
st.markdown('<div class="step-container"><h2>⚙️ Шаг 2: Настройки</h2></div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

# Character name
with col1:
    character_name = st.text_input(
        "👤 Имя персонажа",
        value=character_info.get("Имя", ""),
        help="Оставьте пусто чтобы использовать из файла"
    )
    if not character_name:
        character_name = character_info.get("Имя", "Unknown")

# Character race
with col2:
    race_from_file = character_info.get("Раса", "Unknown")
    
    race_selection = st.radio(
        "🧝 Выбор расы",
        ["Из файла", "Из списка", "Вручную"],
        horizontal=True,
        help="Выберите способ определения расы"
    )
    
    popular_races = [
        "Табакси", "Человек", "Эльф", "Полуэльф", "Полуорк",
        "Гном", "Полулинг", "Карлик", "Драконорождённый", "Кенку",
        "Дроу", "Дуэргар", "Тифлинг", "Аасимар", "Гоблин"
    ]
    
    if race_selection == "Из файла":
        character_race = race_from_file
        st.caption(f"Используется из файла: **{race_from_file}**")
    elif race_selection == "Из списка":
        character_race = st.selectbox(
            "Выберите расу из списка",
            popular_races,
            index=popular_races.index(race_from_file) if race_from_file in popular_races else 0
        )
    else:  # Вручную
        character_race = st.text_input(
            "Введите расу вручную",
            value=race_from_file,
            help="Введите название расы"
        )

# STEP 3: Vision Selection (NEW IMPROVED BLOCK)
st.markdown('<div class="step-container"><h2>👁️ Шаг 3: Выбор видения</h2></div>', unsafe_allow_html=True)

st.markdown("### 🔍 Видение по умолчанию (зависит от расы)")

# Race to default vision mapping
race_vision_map = {
    "Дварф": {"type": "darkvision", "range": 60},
    "Эльф": {"type": "darkvision", "range": 60},
    "Высший эльф": {"type": "darkvision", "range": 60},
    "Лесной эльф": {"type": "darkvision", "range": 60},
    "Полуэльф": {"type": "darkvision", "range": 60},
    "Гном": {"type": "darkvision", "range": 60},
    "Скальный гном": {"type": "darkvision", "range": 60},
    "Лесной гном": {"type": "darkvision", "range": 60},
    "Тифлинг": {"type": "darkvision", "range": 60},
    "Полуорк": {"type": "darkvision", "range": 60},
    "Табакси": {"type": "darkvision", "range": 60},
    "Аасимар": {"type": "darkvision", "range": 60},
    "Кенку": {"type": "darkvision", "range": 60},
    "Гоблин": {"type": "darkvision", "range": 60},
    "Хобгоблин": {"type": "darkvision", "range": 60},
    "Кобольд": {"type": "darkvision", "range": 60},
    "Дроу": {"type": "darkvision", "range": 120},
    "Тёмный эльф": {"type": "darkvision", "range": 120},
    "Дуэргар": {"type": "darkvision", "range": 120},
    "Серый дварф": {"type": "darkvision", "range": 120},
    "Свирфнеблин": {"type": "darkvision", "range": 120},
    "Глубинный гном": {"type": "darkvision", "range": 120},
    "Человек": {"type": "normal", "range": 0},
    "Полулинг": {"type": "normal", "range": 0},
    "Драконорождённый": {"type": "normal", "range": 0},
}

# Get default vision for selected race
default_vision = race_vision_map.get(character_race, {"type": "normal", "range": 0})

st.info(f"📌 Раса '{character_race}' обычно имеет: **{default_vision['type']}** (дальность: {default_vision['range']} фт.)")

# Class abilities affecting vision
st.markdown("### 🎯 Классовые способности видения")

col1, col2, col3 = st.columns(3)

with col1:
    has_devils_sight = st.checkbox(
        "👿 Дьявольское зрение (Devil's Sight)",
        value=False,
        help="Инвокация Колдуна или Черта Адепта Метамагии. Видит в магической тьме на 120 фт."
    )

with col2:
    has_blind_fighting = st.checkbox(
        "⚡ Слепой бой (Blind Fighting)",
        value=False,
        help="Боевой стиль (Воин, Паладин, Следопыт). Слепое зрение 10 фт., видит в любой тьме"
    )

with col3:
    has_eyes_of_night = st.checkbox(
        "🌙 Глаза ночи (Eyes of Night)",
        value=False,
        help="Жрец (Сумеречный домен). Тёмное зрение 300 фт., можно давать союзникам"
    )

st.divider()

# Determine final vision based on selections
st.markdown("### 🎮 Тип и дальность видения")

# If special abilities are selected, they override base vision
final_vision_type = default_vision["type"]
final_vision_range = default_vision["range"]

if has_blind_fighting:
    final_vision_type = "blindsight"
    final_vision_range = 10
    st.success("✅ Выбрано: **Слепое зрение (Blind Fighting)** - 10 фт., видит в магической тьме")
elif has_devils_sight:
    final_vision_type = "darkvision"
    final_vision_range = 120
    st.success("✅ Выбрано: **Дьявольское зрение** - 120 фт., видит в магической тьме")
elif has_eyes_of_night:
    final_vision_type = "darkvision"
    final_vision_range = 300
    st.success("✅ Выбрано: **Глаза ночи** - 300 фт.")
else:
    st.info(f"📌 Используется видение по умолчанию: **{final_vision_type}** - {final_vision_range} фт.")

# Manual override option
st.markdown("### 🔧 Ручной выбор (переопределение)")

override_vision = st.checkbox(
    "Переопределить видение вручную",
    value=False,
    help="Отметьте если хотите выбрать видение отличное от предложенного"
)

if override_vision:
    col1, col2 = st.columns(2)
    
    with col1:
        vision_options = {
            "normal": "🔦 Обычное (Normal)",
            "darkvision": "🌙 Тёмное зрение (Darkvision)",
            "blindsight": "👻 Слепое зрение (Blindsight)",
            "truesight": "✨ Истинное зрение (Truesight)",
            "tremorsense": "📡 Чувство вибраций (Tremorsense)"
        }
        
        vision_display = st.selectbox(
            "Выберите тип видения",
            list(vision_options.keys()),
            format_func=lambda x: vision_options[x],
            index=list(vision_options.keys()).index(final_vision_type)
        )
        final_vision_type = vision_display
    
    with col2:
        if final_vision_type != "normal":
            final_vision_range = st.number_input(
                "Дальность видения (ft)",
                min_value=0,
                value=final_vision_range,
                step=5,
                help="Расстояние в футах на которое видит персонаж"
            )
        else:
            final_vision_range = 0
            st.caption("Обычное зрение: без дальности")

# Display final vision summary
st.markdown('<div class="info-box">', unsafe_allow_html=True)
st.markdown("#### 📊 Итоговое видение")
col1, col2 = st.columns(2)
with col1:
    vision_names = {
        "normal": "🔦 Обычное",
        "darkvision": "🌙 Тёмное зрение",
        "blindsight": "👻 Слепое видение",
        "truesight": "✨ Истинное зрение",
        "tremorsense": "📡 Вибрации"
    }
    st.metric("Тип видения", vision_names.get(final_vision_type, final_vision_type))
with col2:
    if final_vision_range > 0:
        st.metric("Дальность", f"{final_vision_range} фт.")
    else:
        st.metric("Дальность", "Не применимо")
st.markdown('</div>', unsafe_allow_html=True)

# STEP 4: Conversion
st.markdown('<div class="step-container"><h2>🔄 Шаг 4: Конвертация</h2></div>', unsafe_allow_html=True)

if st.button("🚀 КОНВЕРТИРОВАТЬ", use_container_width=True, type="primary"):
    try:
        # Build Foundry character
        foundry_character = {
            "name": character_name,
            "type": "character",
            "img": "icons/svg/mystery-man.svg",
            "system": {
                "abilities": {
                    "str": {"value": character_data.get("stats", {}).get("str", {}).get("score", 10)},
                    "dex": {"value": character_data.get("stats", {}).get("dex", {}).get("score", 10)},
                    "con": {"value": character_data.get("stats", {}).get("con", {}).get("score", 10)},
                    "int": {"value": character_data.get("stats", {}).get("int", {}).get("score", 10)},
                    "wis": {"value": character_data.get("stats", {}).get("wis", {}).get("score", 10)},
                    "cha": {"value": character_data.get("stats", {}).get("cha", {}).get("score", 10)}
                },
                "attributes": {
                    "hp": {
                        "value": character_data.get("vitality", {}).get("hp-current", 0),
                        "max": character_data.get("vitality", {}).get("hp-max", 0)
                    },
                    "ac": {
                        "flat": character_data.get("vitality", {}).get("ac", 10)
                    },
                    "movement": {
                        "walk": character_data.get("vitality", {}).get("speed", 30)
                    }
                },
                "details": {
                    "race": character_race,
                    "level": character_data.get("level", {}).get("value", 1),
                    "alignment": character_data.get("alignment", {}).get("value", "Unaligned")
                },
                "traits": {
                    "languages": {
                        "value": []
                    }
                }
            },
            "prototypeToken": {
                "name": character_name,
                "displayName": 0,
                "sight": {
                    "enabled": final_vision_type != "normal",
                    "range": final_vision_range if final_vision_type != "normal" else 0,
                    "visionMode": final_vision_type if final_vision_type != "normal" else "basic"
                },
                "bar1": {
                    "attribute": "attributes.hp"
                }
            }
        }
        
        # Store in session state for display and download
        st.session_state.converted_character = foundry_character
        st.session_state.character_name = character_name
        
        # Show success message
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.success("✅ Конвертация успешна!")
        
        # Display character stats
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        abilities = foundry_character["system"]["abilities"]
        with col1:
            st.metric("STR", abilities["str"]["value"])
        with col2:
            st.metric("DEX", abilities["dex"]["value"])
        with col3:
            st.metric("CON", abilities["con"]["value"])
        with col4:
            st.metric("INT", abilities["int"]["value"])
        with col5:
            st.metric("WIS", abilities["wis"]["value"])
        with col6:
            st.metric("CHA", abilities["cha"]["value"])
        
        # Display other stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            hp = foundry_character["system"]["attributes"]["hp"]
            st.metric("❤️ HP", f"{hp['value']}/{hp['max']}")
        with col2:
            st.metric("🛡️ AC", foundry_character["system"]["attributes"]["ac"]["flat"])
        with col3:
            st.metric("🏃 Скорость", f"{foundry_character['system']['attributes']['movement']['walk']} ft")
        with col4:
            vision_info = f"{vision_names.get(final_vision_type, final_vision_type)}"
            if final_vision_range > 0:
                vision_info += f" ({final_vision_range} ft)"
            st.metric("👁️ Видение", vision_info)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"❌ Ошибка при конвертации: {str(e)}")

# STEP 5: Download and Preview
if "converted_character" in st.session_state:
    st.divider()
    st.markdown('<div class="step-container"><h2>📥 Шаг 5: Скачивание и просмотр</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        json_string = json.dumps(st.session_state.converted_character, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Скачать JSON",
            data=json_string,
            file_name=f"{st.session_state.character_name}_foundry.json",
            mime="application/json",
            use_container_width=True
        )
    
    with col2:
        if st.button("📄 Показать полный JSON", use_container_width=True):
            st.session_state.show_json = not st.session_state.get("show_json", False)
    
    if st.session_state.get("show_json", False):
        with st.expander("📋 Полный JSON", expanded=True):
            st.json(st.session_state.converted_character)

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; margin-top: 30px;'>
    <p>⚔️ LSS → Foundry VTT D&D 5e Converter v2.2.1</p>
    <p style='font-size: 12px;'>Последнее обновление: 2025-12-28</p>
</div>
""", unsafe_allow_html=True)
