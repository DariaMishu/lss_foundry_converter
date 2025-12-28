#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LSS → Foundry VTT D&D 5e Character Converter - Streamlit App v2.3
Веб-приложение для конвертации персонажей из Long Story Short в Foundry VTT
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, Any
import io

# Конфигурация страницы
st.set_page_config(
    page_title="LSS → Foundry Converter",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    h1 {
        color: #c41e3a;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    h2 {
        color: #333;
        border-bottom: 2px solid #c41e3a;
        padding-bottom: 0.5rem;
    }
    .stButton > button {
        width: 100%;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

class LSSToFoundryConverterV23:
    """Конвертор персонажей из LSS в Foundry VTT D&D 5e (v2.3)"""

    VISION_TYPES = {
        1: {'name': 'normal', 'foundry_mode': 'basic', 'range': 0},
        2: {'name': 'darkvision', 'foundry_mode': 'darkvision', 'range': 60},
        3: {'name': 'blindsight', 'foundry_mode': 'blindsight', 'range': 0},
        4: {'name': 'truesight', 'foundry_mode': 'truesight', 'range': 500},
        5: {'name': 'tremorsense', 'foundry_mode': 'tremorsense', 'range': 0},
    }

    # Видение по умолчанию для рас
    RACE_VISION_MAP = {
        'человек': {'type': 'normal', 'range': 0},
        'эльф': {'type': 'darkvision', 'range': 60},
        'высший эльф': {'type': 'darkvision', 'range': 60},
        'лесной эльф': {'type': 'darkvision', 'range': 60},
        'дроу': {'type': 'darkvision', 'range': 120},
        'гном': {'type': 'darkvision', 'range': 60},
        'скальный гном': {'type': 'darkvision', 'range': 60},
        'лесной гном': {'type': 'darkvision', 'range': 60},
        'глубинный гном': {'type': 'darkvision', 'range': 120},
        'карлик': {'type': 'darkvision', 'range': 60},
        'полулинг': {'type': 'normal', 'range': 0},
        'полуорк': {'type': 'darkvision', 'range': 60},
        'полуэльф': {'type': 'darkvision', 'range': 60},
        'тифлинг': {'type': 'darkvision', 'range': 60},
        'табакси': {'type': 'darkvision', 'range': 60},
        'драконорождённый': {'type': 'normal', 'range': 0},
        'кенку': {'type': 'normal', 'range': 0},
        'гоблин': {'type': 'darkvision', 'range': 60},
        'хобгоблин': {'type': 'darkvision', 'range': 60},
        'кобольд': {'type': 'darkvision', 'range': 60},
        'юань-ти': {'type': 'darkvision', 'range': 60},
        'аасимар': {'type': 'darkvision', 'range': 60},
    }

    SKILLS_MAP = {
        'acrobatics': 'acr', 'investigation': 'inv', 'athletics': 'ath',
        'perception': 'prc', 'survival': 'sur', 'animalHandling': 'ani',
        'arcana': 'arc', 'deception': 'dec', 'history': 'his',
        'insight': 'ins', 'intimidation': 'itm', 'medicine': 'med',
        'nature': 'nat', 'performance': 'prf', 'persuasion': 'per',
        'religion': 'rel', 'sleightOfHand': 'slt', 'stealth': 'ste',
    }

    def __init__(self):
        self.vision_config = {}
        self.race = ''

    def set_vision_config(self, vision_data):
        self.vision_config = vision_data

    def set_race(self, race):
        self.race = race

    def get_default_vision_for_race(self, race):
        """Получить видение по умолчанию для расы"""
        race_lower = race.lower().strip()

        # Точный поиск
        if race_lower in self.RACE_VISION_MAP:
            return self.RACE_VISION_MAP[race_lower]

        # Поиск по частичному совпадению
        for race_key, vision_config in self.RACE_VISION_MAP.items():
            if race_key in race_lower or race_lower in race_key:
                return vision_config

        # По умолчанию для неизвестных рас
        return {'type': 'normal', 'range': 0}

    def parse_lss_json(self, lss_raw):
        if 'data' in lss_raw and isinstance(lss_raw['data'], str):
            try:
                return json.loads(lss_raw['data'])
            except json.JSONDecodeError:
                return {}
        return lss_raw

    def create_foundry_actor(self, lss_data, character_name=None):
        lss_character = self.parse_lss_json(lss_data)
        name_obj = lss_character.get('name', {})
        name = character_name or (name_obj.get('value') if isinstance(name_obj, dict) else str(name_obj))
        name = name.strip() or 'Новый персонаж'

        actor = {
            "name": name,
            "type": "character",
            "img": "icons/svg/mystery-man.svg",
            "system": {
                "abilities": self._extract_abilities(lss_character),
                "attributes": self._extract_attributes(lss_character),
                "details": self._extract_details(lss_character),
                "traits": self._extract_traits(lss_character),
                "currency": self._extract_currency(lss_character),
                "skills": self._extract_skills(lss_character),
            },
            "items": [],
            "effects": [],
            "flags": {},
            "folder": None,
            "sort": 0,
            "ownership": {"default": 0},
            "_stats": {"systemId": "dnd5e", "systemVersion": "4.0.0"},
            "prototypeToken": self._create_prototype_token(name, lss_character)
        }
        return actor

    def _extract_abilities(self, lss_character):
        stats_data = lss_character.get('stats', {})
        abilities = {}
        for ability_key in ['str', 'dex', 'con', 'int', 'wis', 'cha']:
            if ability_key in stats_data:
                stat_obj = stats_data[ability_key]
                value = self._parse_number(stat_obj.get('score', 10))
            else:
                value = 10
            abilities[ability_key] = {
                "value": value,
                "proficient": 0,
                "bonuses": {"check": "", "save": ""}
            }
        return abilities

    def _extract_attributes(self, lss_character):
        vitality = lss_character.get('vitality', {})
        info = lss_character.get('info', {})
        current_hp = self._parse_number(vitality.get('hp-current', {}).get('value', 0))
        max_hp = self._parse_number(vitality.get('hp-max', {}).get('value', current_hp))
        ac_flat = self._parse_number(vitality.get('ac', {}).get('value', 10))
        walk_speed = self._parse_number(vitality.get('speed', {}).get('value', 30))
        level = self._parse_number(info.get('level', {}).get('value', 1) if isinstance(info.get('level'), dict) else info.get('level', 1))
        prof_bonus = (level + 7) // 4 + 1

        return {
            "ac": {"flat": ac_flat, "calc": "default", "formula": ""},
            "hp": {"value": current_hp, "max": max_hp, "temp": 0, "tempmax": 0},
            "init": {"bonus": 0},
            "movement": {"walk": walk_speed, "burrow": 0, "climb": 0, "fly": 0, "swim": 0},
            "speed": {"value": f"{walk_speed} ft"},
            "prof": prof_bonus
        }

    def _extract_details(self, lss_character):
        info = lss_character.get('info', {})
        sub_info = lss_character.get('subInfo', {})

        def get_value(obj, default=''):
            if isinstance(obj, dict):
                return obj.get('value', default)
            return obj if obj else default

        class_name = get_value(info.get('charClass'), 'Unknown')
        level = self._parse_number(get_value(info.get('level'), 1))
        race = self.race or get_value(info.get('race'), '')
        background = get_value(info.get('background'), '')
        alignment = get_value(info.get('alignment'), 'Unaligned')
        experience = self._parse_number(get_value(info.get('experience'), 0))

        biography = f"Класс: {class_name}\n"
        if background:
            biography += f"Предыстория: {background}\n"
        if get_value(sub_info.get('age')):
            biography += f"Возраст: {get_value(sub_info.get('age'))}\n"
        if get_value(sub_info.get('height')):
            biography += f"Рост: {get_value(sub_info.get('height'))}\n"
        if get_value(sub_info.get('weight')):
            biography += f"Вес: {get_value(sub_info.get('weight'))}\n"

        return {
            "biography": {"value": biography, "public": ""},
            "alignment": alignment,
            "race": race,
            "background": background,
            "level": level,
            "xp": {"value": experience, "min": 0, "max": 355000}
        }

    def _extract_traits(self, lss_character):
        return {"size": "med", "languages": {"value": []}, "creatureType": "humanoid"}

    def _extract_currency(self, lss_character):
        coins = lss_character.get('coins', {})

        def get_value(obj, default=0):
            if isinstance(obj, dict):
                return self._parse_number(obj.get('value', default))
            return self._parse_number(obj if obj else default)

        return {
            "pp": get_value(coins.get('pp'), 0),
            "gp": get_value(coins.get('gp'), 0),
            "ep": get_value(coins.get('ep'), 0),
            "sp": get_value(coins.get('sp'), 0),
            "cp": get_value(coins.get('cp'), 0)
        }

    def _extract_skills(self, lss_character):
        skills_data = lss_character.get('skills', {})
        skills = {}
        for lss_name, foundry_code in self.SKILLS_MAP.items():
            skills[foundry_code] = {"value": 0, "ability": self._get_skill_ability(foundry_code), "bonuses": {"check": "", "passive": ""}}

        for skill_key, skill_data in skills_data.items():
            if isinstance(skill_data, dict):
                is_prof = skill_data.get('isProf', 0)
                foundry_code = self.SKILLS_MAP.get(skill_key)
                if foundry_code and foundry_code in skills:
                    skills[foundry_code]['value'] = int(is_prof)

        return skills

    def _create_prototype_token(self, name, lss_character):
        return {
            "name": name,
            "displayName": 0,
            "actorLink": False,
            "width": 1,
            "height": 1,
            "texture": {
                "src": "icons/svg/mystery-man.svg",
                "anchorX": 0.5,
                "anchorY": 0.5,
                "offsetX": 0,
                "offsetY": 0,
                "fit": "contain",
                "scaleX": 1,
                "scaleY": 1,
                "rotation": 0,
                "tint": "#ffffff",
                "alphaThreshold": 0.75
            },
            "lockRotation": False,
            "rotation": 0,
            "alpha": 1,
            "disposition": -1,
            "displayBars": 0,
            "bar1": {"attribute": "attributes.hp"},
            "bar2": {"attribute": None},
            "light": {
                "negative": False,
                "priority": 0,
                "alpha": 0.5,
                "angle": 360,
                "bright": 0,
                "color": None,
                "coloration": 1,
                "dim": 0,
                "attenuation": 0.5,
                "luminosity": 0.5,
                "saturation": 0,
                "contrast": 0,
                "shadows": 0,
                "animation": {"type": None, "speed": 5, "intensity": 5, "reverse": False},
                "darkness": {"min": 0, "max": 1}
            },
            "sight": self._create_sight_config(),
            "detectionModes": [],
            "occludable": {"radius": 0},
            "ring": {
                "enabled": False,
                "colors": {"ring": None, "background": None},
                "effects": 1,
                "subject": {"scale": 1, "texture": None}
            },
            "turnMarker": {"mode": 1, "animation": None, "src": None, "disposition": False},
            "movementAction": None,
            "flags": {},
            "randomImg": False,
            "appendNumber": False,
            "prependAdjective": False
        }

    def _create_sight_config(self):
        vision_type = self.vision_config.get('type', 'normal')
        vision_range = self.vision_config.get('range', 0)
        canvas_range = vision_range
        vision_mode = 'basic'
        for num, config in self.VISION_TYPES.items():
            if config['name'] == vision_type:
                vision_mode = config['foundry_mode']
                break

        return {
            "enabled": vision_type != 'normal',
            "range": canvas_range,
            "angle": 360,
            "visionMode": vision_mode,
            "color": None,
            "attenuation": 0.1,
            "brightness": 0,
            "saturation": 0,
            "contrast": 0
        }

    def _parse_number(self, value):
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                clean = ''.join(c for c in value if c.isdigit() or c == '-')
                return int(clean) if clean else 0
            return 0
        except (ValueError, TypeError):
            return 0

    def _get_skill_ability(self, skill_code):
        skill_abilities = {
            'acr': 'dex', 'ani': 'wis', 'arc': 'int', 'ath': 'str',
            'dec': 'cha', 'his': 'int', 'ins': 'wis', 'itm': 'cha',
            'inv': 'int', 'med': 'wis', 'nat': 'int', 'prc': 'wis',
            'prf': 'cha', 'per': 'cha', 'rel': 'int', 'slt': 'dex',
            'ste': 'dex', 'sur': 'wis',
        }
        return skill_abilities.get(skill_code, 'str')


# ============================================================================
# STREAMLIT ИНТЕРФЕЙС
# ============================================================================

def main():
    # Заголовок
    st.title("⚔️ LSS → Foundry VTT D&D 5e Converter")
    st.markdown("**Конвертация персонажей из Long Story Short в Foundry VTT**")

    # Боковая панель с информацией
    with st.sidebar:
        st.header("ℹ️ Информация")
        st.markdown("""
### Версия 2.3

**Возможности:**
- ✅ Импорт персонажей из LSS
- ✅ Все характеристики (STR-CHA)
- ✅ HP, AC, движение
- ✅ Все 18 навыков
- ✅ Видение в токене
- ✅ Видение по умолчанию для рас
- ✅ Дьявольское зрение
- ✅ Слепой бой

**Поддерживаемое видение:**
- Normal (обычное)
- Darkvision (тёмное зрение)
- Blindsight (слепое видение)
- Truesight (истинное видение)
- Tremorsense (чувство вибраций)

**Совместимость:**
- Python 3.8+
- Foundry VTT v11-v13
- D&D 5e v4.0+
        """
        )

    # Основной контент
    col1, col2 = st.columns([1, 1])

    with col1:
        st.header("📁 Шаг 1: Загрузи JSON")
        uploaded_file = st.file_uploader(
            "Выбери JSON файл из Long Story Short",
            type=['json'],
            help="Файл должен содержать данные персонажа из LSS"
        )

        if uploaded_file is not None:
            try:
                lss_data = json.load(uploaded_file)
                st.success("✅ JSON файл загружен успешно!")

                st.markdown("### 📋 Информация о персонаже:")
                lss_character = json.loads(lss_data['data']) if 'data' in lss_data else lss_data
                info = lss_character.get('info', {})

                def get_value(obj, default=''):
                    if isinstance(obj, dict):
                        return obj.get('value', default)
                    return obj if obj else default

                st.write(f"**Имя из файла:** {lss_character.get('name', {}).get('value', 'Unknown')}")
                st.write(f"**Класс:** {get_value(info.get('charClass'), 'Unknown')}")
                st.write(f"**Раса (из файла):** {get_value(info.get('race'), 'Unknown')}")
                st.write(f"**Уровень:** {get_value(info.get('level'), 1)}")
                st.write(f"**Выравнивание:** {get_value(info.get('alignment'), 'Unaligned')}")

            except json.JSONDecodeError:
                st.error("❌ Ошибка: неверный формат JSON файла")
                uploaded_file = None
            except Exception as e:
                st.error(f"❌ Ошибка при чтении файла: {str(e)}")
                uploaded_file = None

    with col2:
        st.header("⚙️ Шаг 2: Настройки")

        if uploaded_file is not None:
            # Имя персонажа
            st.subheader("👤 Имя персонажа")
            character_name = st.text_input(
                "Имя (если пусто, используется из файла):",
                value=""
            )

            # Раса
            st.subheader("🧝 Раса")
            popular_races = [
                "Табакси", "Человек", "Эльф", "Полуэльф", "Полуорк",
                "Гном", "Полулинг", "Карлик", "Драконорождённый", "Кенку"
            ]

            default_race = lss_character.get('info', {}).get('race', {})
            if isinstance(default_race, dict):
                default_race = default_race.get('value', '')

            race_option = st.radio(
                "Выберите способ ввода расы:",
                ["Из файла", "Из списка", "Вручную"],
                horizontal=True
            )

            race = ""
            if race_option == "Из файла":
                race = default_race
                st.write(f"✓ Раса: **{race}**")
            elif race_option == "Из списка":
                race = st.selectbox("Выберите расу:", popular_races)
                st.write(f"✓ Раса: **{race}**")
            else:
                race = st.text_input("Введите расу:", value=default_race)

            # ===== НОВЫЙ БЛОК ВИДЕНИЯ (v2.3) =====
            st.subheader("👁️ Видение")

            # Инициализация session state для видения
            if 'vision_state' not in st.session_state:
                st.session_state.vision_state = {
                    'devil_sight': False,
                    'blind_fighting': False
                }

            # Получаем видение по умолчанию для расы
            converter_temp = LSSToFoundryConverterV23()
            default_vision = converter_temp.get_default_vision_for_race(race)

            # Возможности от способностей
            vision_col1, vision_col2 = st.columns([1, 1])

            with vision_col1:
                st.markdown("**Способности:**")
                devil_sight = st.checkbox(
                    "👿 Дьявольское зрение",
                    value=st.session_state.vision_state.get('devil_sight', False),
                    help="Инвокация колдуна - видит тёмное зрение 120 фт в магической тьме"
                )
                st.session_state.vision_state['devil_sight'] = devil_sight

            with vision_col2:
                st.markdown("**Боевые стили:**")
                blind_fighting = st.checkbox(
                    "🎯 Слепой бой (Blind Fighting)",
                    value=st.session_state.vision_state.get('blind_fighting', False),
                    help="Видит слепым зрением 10 фт в любой тьме и сквозь невидимость"
                )
                st.session_state.vision_state['blind_fighting'] = blind_fighting

            st.divider()

            # Определяем видение
            if devil_sight:
                vision_type = 'darkvision'
                vision_range = 120
                note = "👿 Дьявольское зрение - видит в магической тьме"
            elif blind_fighting:
                vision_type = 'blindsight'
                vision_range = 10
                note = "🎯 Слепой бой - видит в любой тьме"
            else:
                vision_type = default_vision['type']
                vision_range = default_vision['range']
                race_display = race if race else "неизвестной расе"
                note = f"🧝 По умолчанию для {race_display}: {vision_type.capitalize()} ({vision_range} ft)"

            # Показываем рекомендуемое видение
            if not devil_sight and not blind_fighting:
                st.info(f"📌 {note}")
            else:
                st.success(f"✅ {note}")

            st.divider()

            # Ручной выбор видения (свертываемый блок)
            with st.expander("⚙️ Ручная настройка видения"):
                st.markdown("**Если хотите переопределить автоматическое видение:**")

                manual_vision_choice = st.radio(
                    "Выберите тип видения:",
                    options=[
                        "1️⃣ Обычное (Normal)",
                        "2️⃣ Тёмное зрение (Darkvision)",
                        "3️⃣ Слепое видение (Blindsight)",
                        "4️⃣ Истинное видение (Truesight)",
                        "5️⃣ Чувство вибраций (Tremorsense)"
                    ],
                    horizontal=False,
                    label_visibility="collapsed"
                )

                # Парсим выбор видения
                manual_vision_num = int(manual_vision_choice[0])
                manual_vision_names = {
                    1: 'normal',
                    2: 'darkvision',
                    3: 'blindsight',
                    4: 'truesight',
                    5: 'tremorsense'
                }

                manual_vision_type = manual_vision_names[manual_vision_num]

                # Дальность видения
                if manual_vision_type != 'normal':
                    manual_default_ranges = {
                        'darkvision': 60,
                        'blindsight': 60,
                        'truesight': 120,
                        'tremorsense': 60
                    }
                    manual_vision_range = st.number_input(
                        f"Дальность видения (ft):",
                        min_value=0,
                        value=manual_default_ranges.get(manual_vision_type, 60),
                        step=10
                    )
                else:
                    manual_vision_range = 0

                # Применяем ручной выбор
                use_manual = st.checkbox(
                    "✏️ Использовать ручную настройку",
                    value=False,
                    help="Отключите, чтобы вернуться к автоматическому выбору"
                )

                if use_manual:
                    vision_type = manual_vision_type
                    vision_range = manual_vision_range
                    st.success(f"✅ Видение переопределено: {manual_vision_choice} ({vision_range} ft)")

            # ===== КОНЕЦ БЛОКА ВИДЕНИЯ =====

            st.divider()

            # Кнопка конвертации и результат
            st.header("🔄 Шаг 3: Конвертация")

            col1, col2, col3 = st.columns([1, 1, 1])

            with col2:
                convert_button = st.button(
                    "🚀 КОНВЕРТИРОВАТЬ",
                    type="primary",
                    use_container_width=True
                )

            if convert_button:
                try:
                    # Создаём конвертер
                    converter = LSSToFoundryConverterV23()
                    converter.set_race(race)
                    converter.set_vision_config({
                        'type': vision_type,
                        'range': vision_range,
                        'enabled': vision_type != 'normal'
                    })

                    # Конвертируем
                    foundry_actor = converter.create_foundry_actor(lss_data, character_name if character_name else None)

                    # Показываем результат
                    st.markdown("### ✅ Конвертация успешна!")

                    result_col1, result_col2 = st.columns([1, 1])

                    with result_col1:
                        st.markdown("**📊 Параметры персонажа:**")
                        system = foundry_actor['system']
                        st.write(f"👤 **Имя:** {foundry_actor['name']}")
                        st.write(f"🧝 **Раса:** {system['details']['race']}")
                        st.write(f"📈 **Уровень:** {system['details']['level']}")
                        st.write(f"❤️ **HP:** {system['attributes']['hp']['value']}/{system['attributes']['hp']['max']}")
                        st.write(f"🛡️ **AC:** {system['attributes']['ac']['flat']}")
                        st.write(f"🏃 **Скорость:** {system['attributes']['speed']['value']}")

                    with result_col2:
                        st.markdown("**📋 Характеристики:**")
                        abilities_text = f"""
STR: **{system['abilities']['str']['value']}**
DEX: **{system['abilities']['dex']['value']}**
CON: **{system['abilities']['con']['value']}**
INT: **{system['abilities']['int']['value']}**
WIS: **{system['abilities']['wis']['value']}**
CHA: **{system['abilities']['cha']['value']}**
                        """
                        st.markdown(abilities_text)

                    st.divider()

                    st.markdown("**👁️ Видение в токене:**")
                    sight = foundry_actor['prototypeToken']['sight']
                    st.write(f"Включено: **{sight['enabled']}**")
                    st.write(f"Тип: **{sight['visionMode']}**")
                    st.write(f"Дальность: **{sight['range']}** ft")

                    st.divider()

                    # Кнопки скачивания
                    json_string = json.dumps(foundry_actor, ensure_ascii=False, indent=2)

                    col1, col2, col3 = st.columns([1, 1, 1])

                    with col1:
                        st.download_button(
                            label="📥 Скачать JSON",
                            data=json_string,
                            file_name=f"{foundry_actor['name']}_foundry.json",
                            mime="application/json",
                            use_container_width=True
                        )

                    with col2:
                        with st.expander("📄 Показать JSON"):
                            st.json(foundry_actor)

                    st.session_state.last_result = foundry_actor
                    st.session_state.conversion_success = True

                except Exception as e:
                    st.error(f"❌ Ошибка при конвертации: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

        else:
            st.info("👆 Загрузите JSON файл из Long Story Short, чтобы начать")

    # Футер
    st.divider()
    st.markdown("""
---
**LSS → Foundry VTT Converter v2.3** | Конвертер персонажей для D&D 5e
📚 [Документация](https://github.com) | 🐛 [Сообщить об ошибке](https://github.com)
    """)


if __name__ == "__main__":
    main()
