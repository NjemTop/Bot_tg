import os
import subprocess
import json
from pathlib import Path
from urllib.parse import quote
from YandexDocsMove import create_nextcloud_folder, upload_to_nextcloud

# Указываем путь к файлу с данными
CONFIG_FILE = "Main.config"
# Открываем файл и загружаем данные
with open(CONFIG_FILE, 'r', encoding='utf-8-sig') as file:
    data = json.load(file)

# Получаем учётные данные из конфиг-файла
USERNAME = data["FILE_SHARE"]["USERNAME"]
PASSWORD = data["FILE_SHARE"]["PASSWORD"]
DOMAIN = data["FILE_SHARE"]["DOMAIN"]

# Получаем данные для доступа к NextCloud из конфиг-файла
NEXTCLOUD_URL = data["NEXT_CLOUD"]["URL"]
NEXTCLOUD_USERNAME = data["NEXT_CLOUD"]["USER"]
NEXTCLOUD_PASSWORD = data["NEXT_CLOUD"]["PASSWORD"]

# Задаем параметры файловой шары
share_path = r"//corp.boardmaps.com/data/Releases/[Server]"
mount_point = "/mnt/windows_share"

# Монтируем файловую шару
mount_cmd = f"sudo mount -t cifs {share_path} {mount_point} -o username={USERNAME},password={PASSWORD},domain={DOMAIN}"
mount_result = subprocess.run(mount_cmd, shell=True, stderr=subprocess.PIPE, text=True, check=False, timeout=30)

if mount_result.returncode != 0:
    print(f"Не удалось смонтировать файловую шару. Код возврата: {mount_result.returncode}. Ошибка: {mount_result.stderr}")
else:
    print("Файловая шара успешно смонтирована.")

def move_distr_file(version):
    """Функция мув дистр на NextCloud"""
    # Создаем папку с названием версии на NextCloud
    create_nextcloud_folder(f"1. Актуальный релиз/Дистрибутив/{version}", NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

    # Путь к папке с дистрибутивом на файловой шаре
    distributive_folder = f"/mnt/windows_share/{version}/Release/Mainstream"

    # Ищем файл с расширением .exe в папке с дистрибутивами
    executable_file = None
    try:
        for file in os.listdir(distributive_folder):
            if file.endswith(".exe"):
                executable_file = file
                break
    except FileNotFoundError:
        print(f"Не удалось найти папку {distributive_folder}. Проверьте доступность файловой шары.")
    except OSError as error:
        print(f"Произошла ошибка при чтении папки {distributive_folder}: {error}")
    except Exception as error:
        print(f"Произошла ошибка при поиске файла дистрибутива с расширением .exe: {error}")

    if executable_file is not None:
        # Формируем пути к файлу на файловой шаре и на NextCloud
        local_file_path = os.path.join(distributive_folder, executable_file)
        remote_file_path = f"/1. Актуальный релиз/Дистрибутив/{version}/{executable_file}"
        remote_file_path = quote(remote_file_path, safe="/")  # Кодируем URL-путь

        # Загружаем файл на NextCloud
        upload_to_nextcloud(local_file_path, remote_file_path, NEXTCLOUD_URL, NEXTCLOUD_USERNAME, NEXTCLOUD_PASSWORD)

    else:
        print("Не удалось найти файл дистрибутива с расширением .exe")

# Версия, которую нужно скопировать
version = "2.61"

move_distr_file(version)

# Уберём монтирование диска
unmount_cmd = f"sudo umount {mount_point}"
unmount_result = subprocess.run(unmount_cmd, shell=True, stderr=subprocess.PIPE, text=True, check=False, timeout=30)

if unmount_result.returncode != 0:
    print(f"Не удалось размонтировать файловую шару. Код возврата: {unmount_result.returncode}. Ошибка: {unmount_result.stderr}")
else:
    print("Файловая шара успешно размонтирована.")
