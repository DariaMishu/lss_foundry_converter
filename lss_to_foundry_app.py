#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LSS → Foundry VTT D&D 5e Character Converter - Streamlit App v2.3
Веб-приложение для конвертации персонажей из Long Story Short в Foundry VTT
Обновлено: Переработан блок видения с поддержкой расовых умолчаний и класс-способностей
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
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.1rem;
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
    RACE_DEFAULT_VISION = {
        'Табакси': {'mode': 'darkvision', 'range': 60},
        'Человек': {'mode': 'basic', 'range': 0},
        'Эльф': {'mode': 'darkvision', 'range': 60},
        'Полуэльф': {'mode': 'darkvision', 'range': 60},
        'Дварф': {'mode': 'darkvision', 'range': 60},
        'Гном': {'mode': 'darkvision', 'range': 60},
        'Полулинг': {'mode': 'basic', 'range': 0},
        'Карлик': {'mode': 'darkvision', 'range': 60},
        'Полуорк': {'mode': 'darkvision', 'range': 60},
        'Драконорождённый': {'mode': 'basic', 'range': 0},
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
            skills[foundry_code] = {
                "value": 0,
                "ability": self._get_skill_ability(foundry_code),
                "bonuses": {"check": "", "passive": ""}
            }

        for skill_key, skill_data in skills_data.items():
            if isinstance(skill_data, dict):
                is_prof = skill_data.get('isProf', 0)
                foundry_code = self.SKILLS_MAP.get(skill_key)
                if foundry_code and foundry_code in skills:
                    skills[foundry_code]['value'] = int(is_prof)

        return skills

    def _create_prototype_token(self, name, lss_character):
        sight_config = self._build_sight_config()
        
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
            },
            "sight": sight_config,
            "detectionModes": []
        }

    def _build_sight_config(self):
        """Собирает конфигурацию видения для токена"""
        vision_mode = self.vision_config.get('foundry_mode', 'basic')
        vision_range = self.vision_config.get('range', 0)
        
        return {
            "enabled": True,
            "range": vision_range,
            "visionMode": vision_mode,
            "color": None
        }

    @staticmethod
    def _parse_number(value):
        try:
            return int(value) if isinstance(value, (int, float)) else int(str(value).split('.')[0])
        except (ValueError, AttributeError):
            return 0

    @staticmethod
    def _get_skill_ability(skill_code):
        ability_map = {
            'acr': 'dex', 'ani': 'wis', 'arc': 'int', 'ath': 'str',
            'dec': 'cha', 'his': 'int', 'ins': 'wis', 'itm': 'cha',
            'inv': 'int', 'med': 'wis', 'nat': 'int', 'prc': 'wis',
            'prf': 'cha', 'per': 'cha', 'rel': 'int', 'slt': 'dex',
            'ste': 'dex', 'sur': 'wis'
        }
        return ability_map.get(skill_code, 'str')


def render_vision_section():
    """Переработанный блок выбора видения с расовыми умолчаниями и класс-способностями"""
    
    st.header("👁️ Шаг 3: Видение и восприятие")
    
    # Инициализация session state
    if 'vision_race' not in st.session_state:
        st.session_state.vision_race = st.session_state.get('selected_race', 'Табакси')
    
    if 'has_devil_sight' not in st.session_state:
        st.session_state.has_devil_sight = False
    
    if 'has_blind_fighting' not in st.session_state:
        st.session_state.has_blind_fighting = False
    
    if 'manual_vision_type' not in st.session_state:
        st.session_state.manual_vision_type = None
    
    if 'manual_vision_range' not in st.session_state:
        st.session_state.manual_vision_range = None
    
    # РАЗДЕЛ 1: Выбор видения по расе
    st.subheader("1️⃣ Видение по умолчанию (раса)")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        selected_race = st.session_state.get('selected_race', 'Табакси')
        default_vision = LSSToFoundryConverterV23.RACE_DEFAULT_VISION.get(
            selected_race, 
            {'mode': 'basic', 'range': 0}
        )
        
        vision_mode = default_vision['mode']
        vision_range = default_vision['range']
        
        mode_display = {
            'basic': 'Обычное',
            'darkvision': 'Тёмное зрение',
            'blindsight': 'Слепое зрение',
            'truesight': 'Истинное зрение',
            'tremorsense': 'Чувство вибрации'
        }
        
        display_text = f"{selected_race}"
        if vision_range > 0:
            display_text += f" ({vision_range} фт. {mode_display.get(vision_mode, vision_mode)})"
        else:
            display_text += f" ({mode_display.get(vision_mode, vision_mode)})"
        
        st.info(f"📌 {display_text}")
    
    # РАЗДЕЛ 2: Класс-способности
    st.subheader("2️⃣ Класс-способности")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.has_devil_sight = st.checkbox(
            "🔴 Дьявольское зрение (Devil's Sight)",
            value=st.session_state.has_devil_sight,
            help="Колдун: видит в магической тьме на 120 фт."
        )
    
    with col2:
        st.session_state.has_blind_fighting = st.checkbox(
            "⚫ Слепой бой (Blind Fighting)",
            value=st.session_state.has_blind_fighting,
            help="Боевой стиль: слепое зрение на 10 фт."
        )
    
    # РАЗДЕЛ 3: Вычисление итогового видения
    st.subheader("3️⃣ Итоговое видение")
    
    # Вычисляем максимум из всех видений
    final_config = calculate_final_vision(
        race=selected_race,
        has_devil_sight=st.session_state.has_devil_sight,
        has_blind_fighting=st.session_state.has_blind_fighting
    )
    
    # Отображение
    final_mode = final_config['mode']
    final_range = final_config['range']
    can_see_magic_dark = final_config.get('can_see_magic_darkness', False)
    
    mode_display_full = {
        'basic': '🟡 Обычное',
        'darkvision': '⬛ Тёмное зрение',
        'blindsight': '👁️ Слепое зрение',
        'truesight': '✨ Истинное зрение',
        'tremorsense': '〰️ Чувство вибрации'
    }
    
    final_text = f"{mode_display_full.get(final_mode, final_mode)}"
    if final_range > 0:
        final_text += f" ({final_range} фт.)"
    
    if can_see_magic_dark:
        final_text += " | ✅ Видит в магической тьме"
    
    st.success(f"📊 {final_text}")
    
    # РАЗДЕЛ 4: Ручное переопределение
    st.subheader("4️⃣ Переопределение (опционально)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        manual_override = st.checkbox(
            "Переопределить видение вручную",
            value=st.session_state.manual_vision_type is not None,
            help="Выберите другой тип видения"
        )
    
    if manual_override:
        with col2:
            override_type = st.selectbox(
                "Выберите тип видения:",
                options=[
                    (1, "1 - Обычное"),
                    (2, "2 - Тёмное зрение"),
                    (3, "3 - Слепое зрение"),
                    (4, "4 - Истинное зрение"),
                    (5, "5 - Чувство вибрации")
                ],
                format_func=lambda x: x[1],
                key="override_vision_select"
            )
            st.session_state.manual_vision_type = override_type[0]
        
        with col1:
            st.session_state.manual_vision_range = st.number_input(
                "Дальность (в футах):",
                min_value=0,
                max_value=1000,
                step=10,
                value=st.session_state.manual_vision_range or 60,
                key="override_vision_range"
            )
        
        # Использование переопределения
        final_config = {
            'foundry_mode': LSSToFoundryConverterV23.VISION_TYPES[st.session_state.manual_vision_type]['foundry_mode'],
            'range': st.session_state.manual_vision_range,
            'name': LSSToFoundryConverterV23.VISION_TYPES[st.session_state.manual_vision_type]['name']
        }
    else:
        st.session_state.manual_vision_type = None
        st.session_state.manual_vision_range = None
    
    return final_config


def calculate_final_vision(race: str, has_devil_sight: bool, has_blind_fighting: bool) -> Dict[str, Any]:
    """
    Вычисляет итоговое видение с учетом расы и класс-способностей.
    Берется максимум из всех видений.
    """
    
    # Базовое видение по расе
    base_vision = LSSToFoundryConverterV23.RACE_DEFAULT_VISION.get(
        race, 
        {'mode': 'basic', 'range': 0}
    )
    
    final_mode = base_vision['mode']
    final_range = base_vision['range']
    can_see_magic_darkness = False
    
    # Добавляем дьявольское зрение
    if has_devil_sight:
        if final_mode == 'basic' or final_range < 120:
            final_mode = 'darkvision'
            final_range = max(final_range, 120)
        can_see_magic_darkness = True
    
    # Добавляем слепое зрение (берем максимум, но слепое зрение видит в любой тьме)
    if has_blind_fighting:
        if final_mode == 'basic':
            final_mode = 'blindsight'
            final_range = 10
        elif final_mode in ['darkvision', 'blindsight']:
            if final_range < 10:  # Слепое зрение хуже видит дальше, но видит в магической тьме
                final_mode = 'blindsight'
                final_range = 10
        can_see_magic_darkness = True
    
    return {
        'foundry_mode': {
            'basic': 'basic',
            'darkvision': 'darkvision',
            'blindsight': 'blindsight',
            'truesight': 'truesight',
            'tremorsense': 'tremorsense'
        }[final_mode],
        'mode': final_mode,
        'range': final_range,
        'can_see_magic_darkness': can_see_magic_darkness
    }


def main():
    """Главная функция приложения"""
    
    st.title("⚔️ LSS → Foundry VTT D&D 5e Converter v2.3")
    st.markdown("*Конвертируйте персонажей из Long Story Short в Foundry VTT*")
    
    # Боковая панель
    with st.sidebar:
        st.header("📚 Справка")
        st.markdown("""
        **Версия:** 2.3 (Переработано видение)
        
        **Функции:**
        - ✅ Загрузка JSON персонажей
        - ✅ Выбор расы с предложениями
        - ✅ Видение по расам + класс-способности
        - ✅ Скачивание готового JSON
        
        **Видение:**
        - Автоматический выбор по расе
        - Дьявольское зрение (120 фт, видит в магической тьме)
        - Слепой бой (10 фт, видит в любой тьме)
        - Ручное переопределение
        """)
    
    # ШАГИ КОНВЕРТАЦИИ
    st.markdown("---")
    
    # ШАГ 1: Загрузка файла
    st.header("📁 Шаг 1: Загрузи JSON файл")
    
    uploaded_file = st.file_uploader(
        "Выбери JSON файл из Long Story Short...",
        type=["json"],
        help="Файл должен быть из приложения Long Story Short"
    )
    
    if uploaded_file is None:
        st.info("👈 Загрузи JSON файл для начала")
        return
    
    try:
        lss_data = json.load(uploaded_file)
        st.success("✅ Файл загружен успешно!")
    except json.JSONDecodeError:
        st.error("❌ Ошибка: неверный JSON формат")
        return
    
    # Показываем информацию о персонаже
    converter = LSSToFoundryConverterV23()
    parsed = converter.parse_lss_json(lss_data)
    name_obj = parsed.get('name', {})
    current_name = name_obj.get('value') if isinstance(name_obj, dict) else str(name_obj)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**Персонаж:** {current_name}")
    
    # ШАГ 2: Выбор расы
    st.markdown("---")
    st.header("🧝 Шаг 2: Выбор расы")
    
    race_options = [
        "Табакси", "Человек", "Эльф", "Полуэльф", "Дварф",
        "Гном", "Полулинг", "Карлик", "Полуорк", "Драконорождённый"
    ]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        race_choice = st.radio(
            "Выбор расы:",
            options=["Из файла"] + race_options,
            index=1,
            horizontal=False
        )
    
    with col2:
        if race_choice != "Из файла":
            custom_race = st.text_input(
                "Или введи свою расу:",
                value=race_choice,
                key="custom_race_input"
            )
            selected_race = custom_race if custom_race != race_choice else race_choice
        else:
            selected_race = current_name.split('(')[1].rstrip(')') if '(' in current_name else parsed.get('info', {}).get('race', {}).get('value', 'Табакси')
            st.write(f"📌 {selected_race}")
    
    st.session_state.selected_race = selected_race
    
    # ШАГ 3: Видение
    st.markdown("---")
    final_vision_config = render_vision_section()
    
    # ШАГ 4: Конвертация и скачивание
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🚀 КОНВЕРТИРОВАТЬ", use_container_width=True, type="primary"):
            converter.set_race(selected_race)
            converter.set_vision_config(final_vision_config)
            
            try:
                foundry_actor = converter.create_foundry_actor(lss_data, current_name)
                st.session_state.converted_data = foundry_actor
                st.session_state.converted_name = current_name
                st.success("✅ Персонаж успешно конвертирован!")
            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")
    
    # Показываем результат если есть
    if 'converted_data' in st.session_state:
        st.markdown("---")
        st.header("📊 Результат")
        
        converted = st.session_state.converted_data
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Персонаж", converted['name'])
        with col2:
            hp = converted['system']['attributes']['hp']
            st.metric("HP", f"{hp['value']}/{hp['max']}")
        with col3:
            st.metric("AC", converted['system']['attributes']['ac']['flat'])
        
        # Скачивание
        json_str = json.dumps(converted, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        
        st.download_button(
            label="📥 Скачать JSON",
            data=json_bytes,
            file_name=f"{st.session_state.converted_name}_foundry.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Просмотр JSON
        with st.expander("📄 Просмотреть полный JSON"):
            st.json(converted)


if __name__ == "__main__":
    main()
