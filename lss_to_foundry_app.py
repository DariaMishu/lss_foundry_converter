#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
LSS → Foundry VTT D&D 5e Character Converter - Streamlit App v3.0
Веб-приложение для конвертации персонажей из Long Story Short в Foundry VTT
✨ С поддержкой портретов и токенов!
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, Any
import io
import base64
from PIL import Image

# Конфигурация страницы
st.set_page_config(
    page_title="LSS → Foundry Converter v3.0",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .streamlit-container {
        max-width: 1400px;
    }
</style>
""", unsafe_allow_html=True)


class LSSToFoundryConverterV3:
    """Конвертор персонажей из LSS в Foundry VTT D&D 5e (v3.0) - С ПОРТРЕТАМИ И ТОКЕНАМИ"""

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
        self.portrait_base64 = None
        self.token_base64 = None

    def set_vision_config(self, vision_data):
        self.vision_config = vision_data

    def set_race(self, race):
        self.race = race

    def set_portrait(self, image_bytes: bytes):
        """Конвертировать портрет в base64"""
        if image_bytes:
            self.portrait_base64 = base64.b64encode(image_bytes).decode('utf-8')

    def set_token(self, image_bytes: bytes):
        """Конвертировать токен в base64"""
        if image_bytes:
            self.token_base64 = base64.b64encode(image_bytes).decode('utf-8')

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

        # Портрет персонажа (с поддержкой загруженного изображения)
        portrait_url = "icons/svg/mystery-man.svg"
        if self.portrait_base64:
            portrait_url = f"data:image/png;base64,{self.portrait_base64}"

        actor = {
            "name": name,
            "type": "character",
            "img": portrait_url,
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

        # Явно переписываем критические параметры токена
        actor["prototypeToken"]["displayName"] = 20
        actor["prototypeToken"]["actorLink"] = True
        actor["prototypeToken"]["lockRotation"] = True
        actor["prototypeToken"]["disposition"] = 1
        actor["prototypeToken"]["displayBars"] = 20

        return actor

    def _create_prototype_token(self, name, lss_character):
        """Создаёт стандартный прототип токена для персонажа."""
        # Токен (с поддержкой загруженного изображения)
        token_texture_src = "icons/svg/mystery-man.svg"
        if self.token_base64:
            token_texture_src = f"data:image/png;base64,{self.token_base64}"

        return {
            "name": name,
            "displayName": 20,
            "actorLink": True,
            "width": 1,
            "height": 1,
            "texture": {
                "src": token_texture_src,
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


def main():
    st.title("⚔️ LSS → Foundry VTT D&D 5e Converter v3.0")
    st.markdown("**Конвертация персонажей с портретами и токенами!** 🎨✨")

    # Боковая панель
    with st.sidebar:
        st.header("ℹ️ Информация")
        st.markdown("""
        ### Версия 3.0 - НОВОЕ! 🎨

        **Возможности:**
        - ✅ Импорт персонажей из LSS
        - ✅ Все характеристики (STR-CHA)
        - ✅ HP, AC, движение
        - ✅ Все 18 навыков
        - ✅ Видение в токене
        - **🎨 НОВОЕ: Загрузка портретов**
        - **🎨 НОВОЕ: Загрузка токенов**

        **Как это работает:**
        1. Загружаешь портрет → Конвертируется в base64
        2. Загружаешь токен → Конвертируется в base64
        3. Экспортируешь JSON
        4. Импортируешь в Foundry → Всё работает!
        """)

        st.divider()
        st.markdown("**Совместимость:**")
        st.markdown("- Python 3.6+
- Foundry VTT v11-v13
- D&D 5e v4.0+")

    # Основная сетка
    col_upload, col_settings = st.columns([1, 1])

    with col_upload:
        st.header("📁 Шаг 1: Загрузка файлов")

        # JSON
        uploaded_json = st.file_uploader(
            "📋 JSON из Long Story Short",
            type=['json'],
            key="json_uploader"
        )

        # Портрет
        st.markdown("---")
        st.subheader("🖼️ Портрет персонажа (опционально)")
        uploaded_portrait = st.file_uploader(
            "Изображение портрета",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="portrait_uploader",
            help="PNG, JPG или WEBP - любой размер"
        )

        # Токен
        st.markdown("---")
        st.subheader("🎮 Токен персонажа (опционально)")
        uploaded_token = st.file_uploader(
            "Изображение токена",
            type=['png', 'jpg', 'jpeg', 'webp'],
            key="token_uploader",
            help="PNG, JPG или WEBP - рекомендуется квадратное"
        )

        # Предпросмотр портрета
        if uploaded_portrait:
            st.markdown("### Предпросмотр портрета:")
            st.image(uploaded_portrait, width=200, use_column_width=False)
            st.caption("✅ Портрет готов к импорту")

        # Предпросмотр токена
        if uploaded_token:
            st.markdown("### Предпросмотр токена:")
            st.image(uploaded_token, width=200, use_column_width=False)
            st.caption("✅ Токен готов к импорту")

    with col_settings:
        st.header("⚙️ Шаг 2: Настройки")

        if uploaded_json is not None:
            try:
                lss_data = json.load(uploaded_json)
                st.success("✅ JSON загружен!")

                lss_character = json.loads(lss_data['data']) if 'data' in lss_data else lss_data
                info = lss_character.get('info', {})

                def get_value(obj, default=''):
                    if isinstance(obj, dict):
                        return obj.get('value', default)
                    return obj if obj else default

                st.write(f"**Имя:** {lss_character.get('name', {}).get('value', 'Unknown')}")
                st.write(f"**Класс:** {get_value(info.get('charClass'), 'Unknown')}")

                # Имя персонажа
                st.subheader("👤 Имя")
                character_name = st.text_input("Переименовать (опционально):", value="")

                # Раса
                st.subheader("🧝 Раса")
                popular_races = ["Человек", "Эльф", "Полуэльф", "Полуорк", "Тифлинг",
                                 "Дворф", "Полурослик", "Гном", "Драконорождённый", "Табакси", "Кенку"]

                default_race = lss_character.get('info', {}).get('race', {})
                if isinstance(default_race, dict):
                    default_race = default_race.get('value', '')

                race_option = st.radio("Способ ввода расы:", ["Из файла", "Из списка", "Вручную"], horizontal=True)

                if race_option == "Из файла":
                    race = default_race
                    st.write(f"✓ Раса: **{race}**")
                elif race_option == "Из списка":
                    race = st.selectbox("Выберите расу:", popular_races)
                else:
                    race = st.text_input("Введите расу:", value=default_race)

                # Видение
                st.subheader("👁️ Видение")
                race_vision_defaults = {
                    "Дворф": ("darkvision", 60), "Эльф": ("darkvision", 60),
                    "Полуэльф": ("darkvision", 60), "Гном": ("darkvision", 60),
                    "Тифлинг": ("darkvision", 60), "Полуорк": ("darkvision", 60),
                    "Табакси": ("darkvision", 60), "Аасимар": ("darkvision", 60),
                    "Дроу": ("darkvision", 120), "Дуэргар": ("darkvision", 120),
                    "Глубинный гном": ("darkvision", 120), "Человек": ("normal", 0),
                    "Полурослик": ("normal", 0), "Драконорождённый": ("normal", 0),
                    "Кенку": ("darkvision", 60),
                }

                default_vision_type, default_vision_range = race_vision_defaults.get(race, ("normal", 0))

                has_devils_sight = st.checkbox("🔴 Взор дьявола (Devil's Sight)")
                has_blind_fighting = st.checkbox("⚫ Боевой стиль Слепой бой")

                final_vision_type = default_vision_type
                final_vision_range = default_vision_range

                if has_blind_fighting:
                    final_vision_type = "blindsight"
                    final_vision_range = 10
                elif has_devils_sight:
                    final_vision_type = "darkvision"
                    final_vision_range = max(default_vision_range if default_vision_type == "darkvision" else 0, 120)

                st.write(f"**Видение:** {final_vision_type} ({final_vision_range} ft)" if final_vision_range > 0 else f"**Видение:** {final_vision_type}")

            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")

    # Конвертация
    st.divider()
    st.header("🔄 Шаг 3: Конвертация")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        convert_button = st.button("🚀 КОНВЕРТИРОВАТЬ", type="primary", use_container_width=True)

    if convert_button and uploaded_json:
        try:
            converter = LSSToFoundryConverterV3()
            converter.set_race(race)
            converter.set_vision_config({
                'type': final_vision_type,
                'range': final_vision_range,
                'enabled': final_vision_type != 'normal'
            })

            # Загружаем изображения
            if uploaded_portrait:
                converter.set_portrait(uploaded_portrait.read())
            if uploaded_token:
                converter.set_token(uploaded_token.read())

            # Конвертируем
            foundry_actor = converter.create_foundry_actor(lss_data, character_name if character_name else None)

            st.success("✅ Конвертация успешна!")

            # Результаты
            result_col1, result_col2 = st.columns([1, 1])

            with result_col1:
                st.markdown("**📊 Параметры:**")
                system = foundry_actor['system']
                st.write(f"👤 **Имя:** {foundry_actor['name']}")
                st.write(f"🧝 **Раса:** {system['details']['race']}")
                st.write(f"📈 **Уровень:** {system['details']['level']}")
                st.write(f"❤️ **HP:** {system['attributes']['hp']['value']}/{system['attributes']['hp']['max']}")
                st.write(f"🛡️ **AC:** {system['attributes']['ac']['flat']}")

            with result_col2:
                st.markdown("**📋 Характеристики:**")
                st.write(f"STR: **{system['abilities']['str']['value']}**")
                st.write(f"DEX: **{system['abilities']['dex']['value']}**")
                st.write(f"CON: **{system['abilities']['con']['value']}**")
                st.write(f"INT: **{system['abilities']['int']['value']}**")
                st.write(f"WIS: **{system['abilities']['wis']['value']}**")
                st.write(f"CHA: **{system['abilities']['cha']['value']}**")

            # Визуализация если есть изображения
            if uploaded_portrait or uploaded_token:
                st.markdown("---")
                st.markdown("### 🎨 Загруженные изображения в JSON:")
                img_col1, img_col2 = st.columns(2)
                with img_col1:
                    if uploaded_portrait:
                        st.write("✅ **Портрет:** Встроен в JSON")
                with img_col2:
                    if uploaded_token:
                        st.write("✅ **Токен:** Встроен в JSON")

            # Скачивание
            st.divider()
            json_string = json.dumps(foundry_actor, ensure_ascii=False, indent=2)

            col1, col2 = st.columns([1, 1])
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

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")
            import traceback
            st.error(traceback.format_exc())

    # Футер
    st.divider()
    st.markdown("""
    ---
    **LSS → Foundry VTT Converter v3.0** | С поддержкой портретов и токенов 🎨
    """)


if __name__ == "__main__":
    main()

