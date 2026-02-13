import json
import os

# Эта функция будет отвечать только за сохранение
def save_settings(bot):
    with open("settings.json", "w", encoding="utf-8") as f:
        # Превращаем ID серверов в строки для JSON
        serializable_settings = {str(k): v for k, v in bot.guild_settings.items()}
        json.dump(serializable_settings, f, ensure_ascii=False, indent=4)
        print("[System] Настройки успешно сохранены в файл.")
