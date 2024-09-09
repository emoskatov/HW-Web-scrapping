import requests
import json
import re

from bs4 import BeautifulSoup
from fake_headers import Headers
from tqdm import tqdm

HOST = "https://spb.hh.ru"
PARAMS = {
    "area": ["1", "2"],  # Код региона по ISO 3166-1 alpha-2, для Москвы - 1, для Питера - 2
    "search_field": ["name", "company_name", "description"],
    # Поиск в названии вакансии, названии компании, описании вакансии
    "enable_snippets": "true",
    "text": "Python" + "django" + "flask",  # Поиск по ключевым словам
    "no_magic": "true",
    "ored_clusters": "true",
    "items_on_page": "20",  # Количество объявлений на странице
    "page": "0"  # Номер страницы с объявлениями
}
HOSTVACANCIES = f"{HOST}/search/vacancy"
HEADERS = Headers(browser="firefox", os="win").generate()  # Притворяемся браузером "firefox" и ОС "win"

# Настраиваем прогрессбар
progress = tqdm(desc='Обрабатано', unit='страниц(ы)', bar_format='{desc}: {n_fmt} {unit}', leave=False)

finall_list = []
i = 1
while True:  # выполняем пока не закончатся страницы

    try:

        # Получаем текст тела ответа на запрос
        response = requests.get(HOSTVACANCIES, params=PARAMS, headers=HEADERS)
        text = response.text

        # Готовим соуп
        soup = BeautifulSoup(text, features='html.parser')

        # Получаем название и ссылку объявления
        vacancies = soup.find_all("div",
                                  {"data-qa": re.compile("vacancy-serp__vacancy.vacancy-serp__vacancy_standard*")})
        for vacancie in vacancies:
            vacancie_tag_a = vacancie.find("a", {"data-qa": "serp-item__title"})

            href = vacancie_tag_a.attrs['href']

            # Получаем зарплату
            salary = vacancie.find("span", {"class": re.compile(
                'magritte-text*.*magritte-text_style-primary*.*magritte-text_typography-label-1-regular*')})
            if salary != None:
                salary_el = salary.text
            else:
                salary_el = "Зарплата не указана!"

            # Получаем работадателя
            employer = vacancie.find("span", {"data-qa": "vacancy-serp__vacancy-employer-text"}).text  # Поиск по классу

            # Получаем город
            city = vacancie.find("span", {"data-qa": "vacancy-serp__vacancy-address"}).text  # Поиск по атрибуту


            finall_dict = {
                "Вакансия": vacancie_tag_a.text,
                "Зарплата": re.sub(r"(\u202f)", " ", salary_el),
                "Работодатель": re.sub(r"(\xa0)", " ", employer),
                "Город": re.sub(r"(\xa01\xa0)", " ", city),
                "Ссылка": href
            }

            finall_list.append(finall_dict)

        # Так ка мы получаем по 20 вакансий на странице, если их меньше значит больше нет вакансий
        if len(vacancies) < 20:
            raise IndexError

        # Переключаем на следующую страницу объявлений
        i += 1
        PARAMS["page"] = i
        progress.update()


    except IndexError:
        print(f"\nПросмотрены все страницы!")
        break

print(f'Найдено {len(finall_list)} вакансий')
with open('vacancys.json', 'w', encoding='utf-8') as f:
    json.dump(finall_list, f, ensure_ascii=False, indent=5)
