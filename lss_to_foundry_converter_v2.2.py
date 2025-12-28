#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Long Story Short (LSS) → Foundry VTT D&D 5e Character Converter v2.2
УЛУЧШЕНИЯ:
- Упрощённый ввод видения с выбором номера варианта
- Ввод расы персонажа (отображается корректно в Foundry)
- Видение в prototypeToken.sight (настройки токена)
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any


class LSSToFoundryConverterV22:
    """Конвертор персонажей из LSS в Foundry VTT D&D 5e (v2.2)"""
    
    # Маппинг видения к visionMode Foundry
    VISION_TYPES = {
        1: {'name': 'normal', 'foundry_mode': 'basic', 'range': 0},
        2: {'name': 'darkvision', 'foundry_mode': 'darkvision', 'range': 60},
        3: {'name': 'blindsight', 'foundry_mode': 'blindsight', 'range': 0},
        4: {'name': 'truesight', 'foundry_mode': 'truesight', 'range': 500},
        5: {'name': 'tremorsense', 'foundry_mode': 'tremorsense', 'range': 0},
    }
    
    # Маппинг навыков LSS → Foundry D&D 5e
    SKILLS_MAP = {
        'acrobatics': 'acr',
        'investigation': 'inv',
        'athletics': 'ath',
        'perception': 'prc',
        'survival': 'sur',
        'animalHandling': 'ani',
        'arcana': 'arc',
        'deception': 'dec',
        'history': 'his',
        'insight': 'ins',
        'intimidation': 'itm',
        'medicine': 'med',
        'nature': 'nat',
        'performance': 'prf',
        'persuasion': 'per',
        'religion': 'rel',
        'sleightOfHand': 'slt',
        'stealth': 'ste',
    }
    
    def __init__(self):
        self.vision_config = {}
        self.race = ''
    
    def set_vision_config(self, vision_data: Dict[str, Any]) -> None:
        """Устанавливает конфигурацию видения"""
        self.vision_config = vision_data
    
    def set_race(self, race: str) -> None:
        """Устанавливает расу персонажа"""
        self.race = race
    
    def parse_lss_json(self, lss_raw: Dict[str, Any]) -> Dict[str, Any]:
        """Парсит вложенный JSON структуру LSS"""
        
        if 'data' in lss_raw and isinstance(lss_raw['data'], str):
            try:
                return json.loads(lss_raw['data'])
            except json.JSONDecodeError:
                print("⚠️  Не удалось распарсить вложенный JSON")
                return {}
        
        return lss_raw
    
    def create_foundry_actor(self, lss_data: Dict[str, Any], character_name: str = None) -> Dict[str, Any]:
        """Создает актёра Foundry VTT из данных LSS"""
        
        lss_character = self.parse_lss_json(lss_data)
        
        # Получаем имя персонажа
        name_obj = lss_character.get('name', {})
        name = character_name or (name_obj.get('value') if isinstance(name_obj, dict) else str(name_obj))
        name = name.strip() or 'Новый персонаж'
        
        # Создаем актёра
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
            "_stats": {
                "systemId": "dnd5e",
                "systemVersion": "4.0.0"
            },
            "prototypeToken": self._create_prototype_token(name, lss_character)
        }
        
        return actor
    
    def _extract_abilities(self, lss_character: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Извлекает характеристики из поля 'stats'"""
        
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
                "bonuses": {
                    "check": "",
                    "save": ""
                }
            }
        
        return abilities
    
    def _extract_attributes(self, lss_character: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает HP, AC, инициативу, движение из 'vitality'"""
        
        vitality = lss_character.get('vitality', {})
        info = lss_character.get('info', {})
        
        # HP из vitality
        current_hp = self._parse_number(vitality.get('hp-current', {}).get('value', 0))
        max_hp = self._parse_number(vitality.get('hp-max', {}).get('value', current_hp))
        
        # AC из vitality
        ac_flat = self._parse_number(vitality.get('ac', {}).get('value', 10))
        
        # Инициатива
        initiative = 0
        
        # Движение из vitality
        walk_speed = self._parse_number(vitality.get('speed', {}).get('value', 30))
        
        # Бонус мастерства по уровню
        level = self._parse_number(info.get('level', {}).get('value', 1) if isinstance(info.get('level'), dict) else info.get('level', 1))
        prof_bonus = (level + 7) // 4 + 1
        
        attributes = {
            "ac": {
                "flat": ac_flat,
                "calc": "default",
                "formula": ""
            },
            "hp": {
                "value": current_hp,
                "max": max_hp,
                "temp": 0,
                "tempmax": 0
            },
            "init": {
                "bonus": initiative
            },
            "movement": {
                "walk": walk_speed,
                "burrow": 0,
                "climb": 0,
                "fly": 0,
                "swim": 0
            },
            "speed": {
                "value": f"{walk_speed} ft"
            },
            "prof": prof_bonus
        }
        
        return attributes
    
    def _extract_details(self, lss_character: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает детали из 'info' и 'subInfo'"""
        
        info = lss_character.get('info', {})
        sub_info = lss_character.get('subInfo', {})
        
        def get_value(obj, default=''):
            if isinstance(obj, dict):
                return obj.get('value', default)
            return obj if obj else default
        
        class_name = get_value(info.get('charClass'), 'Unknown')
        level = self._parse_number(get_value(info.get('level'), 1))
        # Используем введённую расу или из файла
        race = self.race or get_value(info.get('race'), '')
        background = get_value(info.get('background'), '')
        alignment = get_value(info.get('alignment'), 'Unaligned')
        experience = self._parse_number(get_value(info.get('experience'), 0))
        
        # Биография
        biography = f"Класс: {class_name}\n"
        if background:
            biography += f"Предыстория: {background}\n"
        if get_value(sub_info.get('age')):
            biography += f"Возраст: {get_value(sub_info.get('age'))}\n"
        if get_value(sub_info.get('height')):
            biography += f"Рост: {get_value(sub_info.get('height'))}\n"
        if get_value(sub_info.get('weight')):
            biography += f"Вес: {get_value(sub_info.get('weight'))}\n"
        
        details = {
            "biography": {
                "value": biography,
                "public": ""
            },
            "alignment": alignment,
            "race": race,  # ← Раса теперь отображается корректно
            "background": background,
            "level": level,
            "xp": {
                "value": experience,
                "min": 0,
                "max": 355000
            }
        }
        
        return details
    
    def _extract_traits(self, lss_character: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает черты"""
        
        return {
            "size": "med",
            "languages": {
                "value": []
            },
            "creatureType": "humanoid"
        }
    
    def _extract_currency(self, lss_character: Dict[str, Any]) -> Dict[str, int]:
        """Извлекает валюту из 'coins'"""
        
        coins = lss_character.get('coins', {})
        
        def get_value(obj, default=0):
            if isinstance(obj, dict):
                return self._parse_number(obj.get('value', default))
            return self._parse_number(obj if obj else default)
        
        currency = {
            "pp": get_value(coins.get('pp'), 0),
            "gp": get_value(coins.get('gp'), 0),
            "ep": get_value(coins.get('ep'), 0),
            "sp": get_value(coins.get('sp'), 0),
            "cp": get_value(coins.get('cp'), 0)
        }
        
        return currency
    
    def _extract_skills(self, lss_character: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Извлекает навыки из 'skills'"""
        
        skills_data = lss_character.get('skills', {})
        
        # Инициализируем все навыки
        skills = {}
        for lss_name, foundry_code in self.SKILLS_MAP.items():
            skills[foundry_code] = {
                "value": 0,
                "ability": self._get_skill_ability(foundry_code),
                "bonuses": {
                    "check": "",
                    "passive": ""
                }
            }
        
        # Парсим значения навыков
        for skill_key, skill_data in skills_data.items():
            if isinstance(skill_data, dict):
                is_prof = skill_data.get('isProf', 0)
                foundry_code = self.SKILLS_MAP.get(skill_key)
                
                if foundry_code and foundry_code in skills:
                    skills[foundry_code]['value'] = int(is_prof)
        
        return skills
    
    def _create_prototype_token(self, name: str, lss_character: Dict[str, Any]) -> Dict[str, Any]:
        """Создает настройки токена с видением"""
        
        # Базовая конфигурация токена
        prototype_token = {
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
            "bar1": {
                "attribute": "attributes.hp"
            },
            "bar2": {
                "attribute": None
            },
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
                "darkness": {
                    "min": 0,
                    "max": 1
                }
            },
            "sight": self._create_sight_config(),  # ← Видение в токене!
            "detectionModes": [],
            "occludable": {
                "radius": 0
            },
            "ring": {
                "enabled": False,
                "colors": {
                    "ring": None,
                    "background": None
                },
                "effects": 1,
                "subject": {
                    "scale": 1,
                    "texture": None
                }
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
        
        return prototype_token
    
    def _create_sight_config(self) -> Dict[str, Any]:
        """Создает конфигурацию видения для токена"""
        
        vision_type = self.vision_config.get('type', 'normal')
        vision_range = self.vision_config.get('range', 0)
        
        # Преобразуем feet в canvas units (1 ft = 1 unit в Foundry)
        # Для видения нужно указать дальность в units
        canvas_range = vision_range  # 1 ft = 1 unit
        
        # Выбираем visionMode из маппинга
        vision_mode = 'basic'
        for num, config in self.VISION_TYPES.items():
            if config['name'] == vision_type:
                vision_mode = config['foundry_mode']
                break
        
        sight = {
            "enabled": vision_type != 'normal',
            "range": canvas_range,
            "angle": 360,
            "visionMode": vision_mode,  # ← Автоматически выбранный режим!
            "color": None,
            "attenuation": 0.1,
            "brightness": 0,
            "saturation": 0,
            "contrast": 0
        }
        
        return sight
    
    def _parse_number(self, value: Any) -> int:
        """Безопасно парсит число"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                clean = ''.join(c for c in value if c.isdigit() or c == '-')
                return int(clean) if clean else 0
            return 0
        except (ValueError, TypeError):
            return 0
    
    def _get_skill_ability(self, skill_code: str) -> str:
        """Возвращает основную характеристику навыка"""
        skill_abilities = {
            'acr': 'dex', 'ani': 'wis', 'arc': 'int', 'ath': 'str',
            'dec': 'cha', 'his': 'int', 'ins': 'wis', 'itm': 'cha',
            'inv': 'int', 'med': 'wis', 'nat': 'int', 'prc': 'wis',
            'prf': 'cha', 'per': 'cha', 'rel': 'int', 'slt': 'dex',
            'ste': 'dex', 'sur': 'wis',
        }
        return skill_abilities.get(skill_code, 'str')


def get_vision_input() -> Dict[str, Any]:
    """Получает конфигурацию видения с упрощённым выбором"""
    
    print("\n" + "="*60)
    print("КОНФИГУРАЦИЯ ВИДЕНИЯ ПЕРСОНАЖА")
    print("="*60)
    
    print("\nДоступные типы видения:")
    for num, config in {
        1: {'name': 'normal', 'desc': 'обычное видение', 'default_range': 0},
        2: {'name': 'darkvision', 'desc': 'тёмное зрение (видит в темноте)', 'default_range': 60},
        3: {'name': 'blindsight', 'desc': 'слепое зрение (видит без света)', 'default_range': 60},
        4: {'name': 'truesight', 'desc': 'истинное видение (видит всё)', 'default_range': 120},
        5: {'name': 'tremorsense', 'desc': 'чувство вибраций (подземные движения)', 'default_range': 60},
    }.items():
        print(f"  {num}. {config['name']:15} - {config['desc']}")
    
    while True:
        try:
            choice = input("\nВыберите номер (1-5) [1]: ").strip() or "1"
            choice_num = int(choice)
            if 1 <= choice_num <= 5:
                break
            print("❌ Пожалуйста, выберите число от 1 до 5")
        except ValueError:
            print("❌ Ошибка ввода. Введите число от 1 до 5")
    
    # Получаем тип видения по номеру
    vision_config = {
        1: {'type': 'normal', 'range': 0, 'enabled': False},
        2: {'type': 'darkvision', 'range': 60, 'enabled': True},
        3: {'type': 'blindsight', 'range': 60, 'enabled': True},
        4: {'type': 'truesight', 'range': 120, 'enabled': True},
        5: {'type': 'tremorsense', 'range': 60, 'enabled': True},
    }
    
    selected = vision_config[choice_num]
    
    # Если это не обычное видение, спрашиваем дальность
    if selected['type'] != 'normal':
        try:
            range_input = input(f"Дальность видения {selected['type']} в футах [{selected['range']}]: ").strip()
            selected['range'] = int(range_input) if range_input else selected['range']
        except ValueError:
            print(f"⚠️  Ошибка при вводе. Используется {selected['range']} футов.")
    
    print(f"✓ Видение: {selected['type']}" + (f" ({selected['range']} ft)" if selected['range'] else ""))
    
    return selected


def get_race_input(default_race: str = '') -> str:
    """Получает расу персонажа от пользователя"""
    
    print("\n" + "="*60)
    print("РАСА ПЕРСОНАЖА")
    print("="*60)
    
    popular_races = [
        "Табакси", "Человек", "Эльф", "Полуэльф", "Полуорк",
        "Гном", "Полулинг", "Карлик", "Драконорождённый", "Кенку"
    ]
    
    if default_race:
        print(f"\nДефолтная раса из файла: {default_race}")
    
    print("\nПопулярные расы:")
    for i, race in enumerate(popular_races, 1):
        print(f"  {i}. {race}")
    
    race_input = input("\nВведите расу (или номер из списка) [Enter = из файла]: ").strip()
    
    if not race_input:
        return default_race
    
    # Если ввели число
    try:
        choice_num = int(race_input)
        if 1 <= choice_num <= len(popular_races):
            return popular_races[choice_num - 1]
    except ValueError:
        pass
    
    # Иначе используем то что ввели
    return race_input


def main():
    """Основная функция"""
    
    print("\n" + "="*70)
    print("LSS → Foundry VTT D&D 5e Character Converter v2.2 (УЛУЧШЕННАЯ)")
    print("="*70)
    
    # Получаем путь к файлу
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
    else:
        input_path_str = input("\nПуть к JSON файлу из Long Story Short: ").strip()
        input_path = Path(input_path_str)
    
    if not input_path.exists():
        print(f"❌ Ошибка: файл '{input_path}' не найден!")
        return
    
    print(f"✓ Файл найден: {input_path.name}")
    
    # Загружаем JSON
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            lss_data = json.load(f)
        print("✓ JSON файл загружен успешно")
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка при чтении JSON: {e}")
        return
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return
    
    # Получаем имя персонажа
    character_name = input("\nИмя персонажа (или Enter для автоопределения): ").strip()
    
    # Получаем расу
    lss_character = json.loads(lss_data['data']) if 'data' in lss_data else lss_data
    default_race = lss_character.get('info', {}).get('race', {}).get('value', '')
    race = get_race_input(default_race)
    
    # Получаем видение
    vision_config = get_vision_input()
    
    # Конвертируем
    print("\n⏳ Конвертация в процессе...")
    converter = LSSToFoundryConverterV22()
    converter.set_vision_config(vision_config)
    converter.set_race(race)
    
    try:
        foundry_actor = converter.create_foundry_actor(lss_data, character_name)
        print("✓ Конвертация завершена успешно!")
    except Exception as e:
        print(f"❌ Ошибка при конвертации: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Сохраняем результат
    base_name = character_name or foundry_actor['name']
    output_path = input_path.parent / f"{base_name}_foundry.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(foundry_actor, f, ensure_ascii=False, indent=2)
        print(f"✓ Сохранено: {output_path}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении: {e}")
        return
    
    # Сводка
    print("\n" + "="*70)
    print("СВОДКА КОНВЕРТАЦИИ")
    print("="*70)
    system = foundry_actor['system']
    print(f"Персонаж: {foundry_actor['name']}")
    print(f"Раса: {system['details']['race']}")
    print(f"Уровень: {system['details']['level']}")
    print(f"HP: {system['attributes']['hp']['value']}/{system['attributes']['hp']['max']}")
    print(f"AC: {system['attributes']['ac']['flat']}")
    print(f"STR: {system['abilities']['str']['value']}, DEX: {system['abilities']['dex']['value']}, CON: {system['abilities']['con']['value']}")
    print(f"INT: {system['abilities']['int']['value']}, WIS: {system['abilities']['wis']['value']}, CHA: {system['abilities']['cha']['value']}")
    
    vision_info = foundry_actor['prototypeToken']['sight']
    if vision_info['enabled']:
        print(f"Видение (в токене): {vision_config['type']} ({vision_info['range']} ft, режим: {vision_info['visionMode']})")
    else:
        print(f"Видение (в токене): обычное (без модификаций)")
    
    print(f"Файл: {output_path.name}")
    print("="*70)
    print("\n✓ Готово к импорту в Foundry VTT!")
    print("  1. Actor Directory → Create Actor")
    print("  2. Правый клик → Import Data")
    print("  3. Выберите JSON файл")
    print("  ✓ Видение уже настроено в токене!")
    print()


if __name__ == "__main__":
    main()