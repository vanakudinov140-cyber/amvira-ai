import pandas as pd
from dadata import Dadata
import time

# --- НАСТРОЙКИ ---
TOKEN = "ff136bacfa4b0dbd548771ffc437361f9a0b0b19"
SECRET = "dfc96156f17debb0279f0aae0706ef11cebc79cb"
INPUT_FILE = "без данных.xlsx"   
COLUMN_NAME = "ИНН"        
OUTPUT_FILE = "result.xlsx" 

def get_phones(inn):
    if pd.isna(inn) or inn == "":
        return "Нет ИНН"
    
    try:
        # Превращаем ИНН из 7.7E+11 в нормальную строку '7712345678'
        inn_str = str(int(float(inn))) 
        
        # ПРАВИЛЬНЫЙ МЕТОД: find_by_id ("party" - для организаций)
        response = dadata.find_by_id("party", inn_str)
        
        if response and len(response) > 0:
            # Данные лежат в первом элементе списка
            data = response[0].get('data', {})
            phones = data.get('phones')
            
            if phones:
                # Извлекаем номера телефонов. Они могут быть списком строк или словарей.
                phone_list = []
                for p in phones:
                    if isinstance(p, dict):
                        phone_list.append(p.get('value'))
                    else:
                        phone_list.append(str(p))
                
                return ", ".join(filter(None, phone_list))
            return "Телефон не найден"
        return "Организация не найдена"
    
    except Exception as e:
        return f"Ошибка: {str(e)}"

# --- ОСНОВНОЙ ПРОЦЕСС ---
with Dadata(TOKEN, SECRET) as dadata:
    # 1. Читаем Excel
    try:
        df = pd.read_excel(INPUT_FILE)
    except Exception as e:
        print(f"Не удалось открыть файл: {e}")
        exit()

    print(f"Начинаю обработку {len(df)} строк...")

    # 2. Проходим по строкам
    # Используем lambda так, чтобы возвращался только результат функции get_phones
    df['Найденные телефоны'] = df[COLUMN_NAME].apply(lambda x: (get_phones(x), time.sleep(0.1))[0])

    # 3. Сохраняем в новый файл
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Готово! Результат сохранен в файл: {OUTPUT_FILE}")
