#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSS → Foundry VTT D&D 5e Character Converter - Streamlit App v1.0
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
        .stTabs [data-baseweb="tab-list"] button {
            font-size: 1.1rem;
        }
        .success-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        .error-box {
            padding: 1.5rem;
            border-radius: 0.5rem;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
    </style>
""", unsafe_allow_html=True)


class LSSToFoundryConverterV22:
    """Конвертор персонажей из LSS в Foundry VTT D&D 5e (v2.2)"""
    
    VISION_TYPES = {
        1: {'name': 'normal', 'foundry_mode': 'basic', 'range': 0},
        2: {'name': 'darkvision', 'foundry_mode': 'darkvision', 'range': 60},
        3: {'name': 'blindsight', 'foundry_mode': 'blindsight', 'range': 0},
        4: {'name': 'truesight', 'foundry_mode': 'truesight', 'range': 500},
        5: {'name': 'tremorsense', 'foundry_mode': 'tremorsense', 'range': 0},
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
    
    def parse_lss_json(self, lss_raw):
        if 'data' in lss_raw and isinstance(lss_raw['data'], str):
            try:
                return json.loads(lss_raw['data'])
            except json.JSONDecodeError:
                return {}
        return lss_raw
    
    def create_foundry_actor(self, lss_data, character_name=None):
        """Создаёт актёра для Foundry VTT с правильными параметрами."""

        lss_character = self.parse_lss_json(lss_data)
        name_obj = lss_character.get('name', {})
        name = character_name or (name_obj.get('value') if isinstance(name_obj, dict) else str(name_obj))
        name = name.strip() or 'Новый персонаж'

        # ════════════════════════════════════════════════════════════════════════════════
        # СОЗДАЁМ АКТЁРА
        # ════════════════════════════════════════════════════════════════════════════════

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

        # ════════════════════════════════════════════════════════════════════════════════
        # КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: УСТАНОВИ ПАРАМЕТРЫ ТОКЕНА НА ПРАВИЛЬНОМ УРОВНЕ
        # ════════════════════════════════════════════════════════════════════════════════

        # Foundry VTT ищет эти параметры ИМЕННО в prototypeToken!
        actor["prototypeToken"]["displayName"] = 20
        actor["prototypeToken"]["actorLink"] = True
        actor["prototypeToken"]["lockRotation"] = True
        actor["prototypeToken"]["disposition"] = 1
        actor["prototypeToken"]["displayBars"] = 20

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
        initiative = 0
        walk_speed = self._parse_number(vitality.get('speed', {}).get('value', 30))
        level = self._parse_number(info.get('level', {}).get('value', 1) if isinstance(info.get('level'), dict) else info.get('level', 1))
        prof_bonus = (level + 7) // 4 + 1
        
        return {
            "ac": {"flat": ac_flat, "calc": "default", "formula": ""},
            "hp": {"value": current_hp, "max": max_hp, "temp": 0, "tempmax": 0},
            "init": {"bonus": initiative},
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
        """Создаёт стандартный прототип токена для персонажа."""
        return {
            "name": name,
            "displayName": 20,
            "actorLink": True,
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
            "lockRotation": True,
            "rotation": 0,
            "alpha": 1,
            "disposition": 1,
            "displayBars": 20,
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
                "animation": {
                    "type": None,
                    "speed": 5,
                    "intensity": 5,
                    "reverse": False
                },
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
            "turnMarker": {
                "mode": 1,
                "animation": None,
                "src": None,
                "disposition": False
            },
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
        ### Версия 2.2
        
        **Возможности:**
        - ✅ Импорт персонажей из LSS
        - ✅ Все характеристики (STR-CHA)
        - ✅ HP, AC, движение
        - ✅ Все 18 навыков
        - ✅ Видение в токене
        
        **Поддерживаемое видение:**
        - Normal (обычное)
        - Darkvision (тёмное зрение)
        - Blindsight (слепое видение)
        - Truesight (истинное видение)
        - Tremorsense (чувство вибраций)
        """)
        
        st.divider()
        st.markdown("**Совместимость:**")
        st.markdown("""
        - Python 3.6+
        - Foundry VTT v11-v13
        - D&D 5e v4.0+
        """)
    
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
                
                # Показываем информацию из файла
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
            
            # Получаем расу из файла
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
            else:  # Вручную
                race = st.text_input("Введите расу:", value=default_race)
            
            # Видение
            # Видение
            st.subheader("👁️ Видение")

            # Определяем видение по умолчанию в зависимости от расы
            race_vision_defaults = {
                "Дварф": ("darkvision", 60),
                "Карлик": ("darkvision", 60),
                "Эльф": ("darkvision", 60),
                "Полуэльф": ("darkvision", 60),
                "Гном": ("darkvision", 60),
                "Тифлинг": ("darkvision", 60),
                "Полуорк": ("darkvision", 60),
                "Табакси": ("darkvision", 60),
                "Аасимар": ("darkvision", 60),
                "Дроу": ("darkvision", 120),
                "Дуэргар": ("darkvision", 120),
                "Глубинный гном": ("darkvision", 120),
                "Человек": ("normal", 0),
                "Полулинг": ("normal", 0),
                "Драконорождённый": ("normal", 0),
                "Кенку": ("darkvision", 60),
            }

            # Получаем стандартное видение для выбранной расы
            default_vision_type, default_vision_range = race_vision_defaults.get(race, ("normal", 0))

            # Опциональные способности (чекбоксы)
            col_devils, col_blind = st.columns(2)
            with col_devils:
                has_devils_sight = st.checkbox(
                    "🔴 Взор дьявола (Devil's Sight)",
                    help="Позволяет видеть в магической тьме на 120 фт (например, инвокация колдуна)"
                )
            with col_blind:
                has_blind_fighting = st.checkbox(
                    "⚫ Боевой стиль Слепой бой (Blind Fighting)",
                    help="Позволяет видеть в любой тьме на 10 фт (видит невидимых и через тьму)"
                )

            # Логика определения финального видения
            final_vision_type = default_vision_type
            final_vision_range = default_vision_range

            # Если есть "Боевой стиль Слепой бой" - он имеет приоритет (10 фт, видит всё)
            if has_blind_fighting:
                final_vision_type = "blindsight"
                final_vision_range = 10
            # Если есть "Взор дьявола" - добавляем/увеличиваем тёмное зрение до 120 фт
            elif has_devils_sight:
                # Взор дьявола ВСЕГДА добавляет darkvision
                final_vision_type = "darkvision"
                # Если уже есть darkvision, увеличиваем до 120 (если меньше)
                # Если нет darkvision, добавляем 120
                final_vision_range = max(default_vision_range if default_vision_type == "darkvision" else 0, 120)

            st.write("**Видение по умолчанию (на основе расы):**")
            st.write(f"└─ Тип: **{default_vision_type}**, Дальность: **{default_vision_range if default_vision_range > 0 else 'N/A'} ft**")

            # Ручной выбор (опционально переопределить)
            with st.expander("⚙️ Переопределить видение вручную", expanded=False):
                manual_vision_choice = st.radio(
                    "Выбрать тип видения вручную:",
                    [
                        "1️⃣ Обычное (Normal)",
                        "2️⃣ Тёмное зрение (Darkvision)",
                        "3️⃣ Слепое видение (Blindsight)",
                        "4️⃣ Истинное видение (Truesight)",
                        "5️⃣ Чувство вибраций (Tremorsense)"
                    ],
                    horizontal=False,
                    key="manual_vision"
                )

                # Парсим выбор видения
                manual_vision_num = int(manual_vision_choice[0])
                vision_names = {
                    1: 'normal',
                    2: 'darkvision',
                    3: 'blindsight',
                    4: 'truesight',
                    5: 'tremorsense'
                }
                manual_vision_type = vision_names[manual_vision_num]

                # Дальность видения
                if manual_vision_type != 'normal':
                    default_ranges = {
                        'darkvision': 60,
                        'blindsight': 60,
                        'truesight': 120,
                        'tremorsense': 60
                    }
                    manual_vision_range = st.number_input(
                        f"Дальность видения (ft):",
                        min_value=0,
                        value=default_ranges.get(manual_vision_type, 60),
                        step=10,
                        key="manual_range"
                    )
                else:
                    manual_vision_range = 0

                # Флаг: используем ручной выбор (expander активен и пользователь выбрал)
                use_manual_override = st.checkbox(
                    "✓ Использовать ручной выбор видения вместо автоматического",
                    value=False,
                    key="use_manual_override"
                )

                if use_manual_override:
                    # Переопределяем финальное видение ТОЛЬКО если пользователь согласился
                    final_vision_type = manual_vision_type
                    final_vision_range = manual_vision_range
                    st.write(f"└─ **Выбрано вручную:** {manual_vision_choice}")
                else:
                    st.info("💡 Ручной выбор отключен - используется автоматическая финализация видения")

            # Отображение финального видения с учётом всех параметров
            st.divider()
            st.write("**✓ ФИНАЛЬНЫЕ ПАРАМЕТРЫ ВИДЕНИЯ:**")

            vision_display_lines = []
            vision_display_lines.append(f"  Основное видение: **{final_vision_type}**")
            if final_vision_range > 0:
                vision_display_lines.append(f"  Дальность: **{final_vision_range} ft**")

            if has_devils_sight:
                vision_display_lines.append(f"  🔴 Взор дьявола: **видит в магической тьме** (+120 фт для тёмного зрения)")

            if has_blind_fighting:
                vision_display_lines.append(f"  ⚫ Боевой стиль Слепой бой: **видит в любой тьме** (10 фт, видит невидимых)")

            for line in vision_display_lines:
                st.write(line)

            # Определяем может ли видеть в магической тьме
            can_see_magical_darkness = has_blind_fighting or (has_devils_sight and final_vision_type == "darkvision") or final_vision_type in ["truesight", "blindsight"]

            if can_see_magical_darkness:
                st.info("✅ Может видеть в **магической тьме** (например, заклинание Darkness)")
            else:
                st.warning("❌ НЕ может видеть в магической тьме (заклинание Darkness заблокирует видение)")

    st.divider()
    
    # Кнопка конвертации и результат
    st.header("🔄 Шаг 3: Конвертация")
    
    if uploaded_file is not None:
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
                converter = LSSToFoundryConverterV22()
                converter.set_race(race)
                converter.set_vision_config({
                    'type': final_vision_type,
                    'range': final_vision_range,
                    'enabled': final_vision_type != 'normal'
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
                    # Показать JSON в ekspander
                    with st.expander("📄 Показать JSON"):
                        st.json(foundry_actor)
                
                # Сохраняем в session state
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
    **LSS → Foundry VTT Converter v2.2** | Конвертер персонажей для D&D 5e
    
    📚 [Документация](https://github.com) | 🐛 [Сообщить об ошибке](https://github.com)
    """)


if __name__ == "__main__":
    main()
