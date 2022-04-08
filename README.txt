Установка
1.1| sudo apt update && sudo apt upgrade
1.2| sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update && sudo apt install python3.10 && sudo apt install python3.10-venv -y
1.3| curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3.10 -

2.зайти в нужную папку c помощью: cd /home/
2.1 git clone https://github.com/taimaskhanov11/BotExchange.git
2.2 cd BotExchange
2.3 Заполнить данные в файле конфига config.yml
2.3 poetry install --no-dev
2.4 poetry update --no-dev
2.5 poetry run python botexchange/main.py

Установка переводов
pybabel extract .\botexchange\ -o .\botexchange\apps\bot\locales\botexchange.pot
pybabel init -i .\botexchange\apps\bot\locales\botexchange.pot -d .\botexchange\apps\bot\locales\ -D botexchange -l ru
pybabel init -i .\botexchange\apps\bot\locales\botexchange.pot -d .\botexchange\apps\bot\locales\ -D botexchange -l en
# Собрать переводы
pybabel compile -d .\botexchange\apps\bot\locales\ -D botexchange


Обновляем переводы
1. Вытаскиваем тексты из файлов, Добавляем текст в переведенные версии
# Обновить переводы
pybabel extract .\botexchange\apps\ -o .\botexchange\apps\bot\locales\botexchange.pot
pybabel update -d .\botexchange\apps\bot\locales -D botexchange -i .\botexchange\apps\bot\locales\botexchange.pot
# После перевода
pybabel compile -d .\botexchange\apps\bot\locales\ -D botexchange