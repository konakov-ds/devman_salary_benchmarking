import requests

hh_api_url = 'https://api.hh.ru/vacancies/'

hh_header = {
    'User-Agent': 'salary_benchmarking_app/1.0 konakov-dev@yandex.ru'
}


dev_params = {
        'specialization': '1.221',
        'area': '1',
        'per_page': '100',
}

popular_program_languages = [
    'TypeScript',
    'Swift',
    'Scala',
    'Objective-C',
    'Shell',
    'Go',
    'C',
    'C#',
    'C++',
    'PHP',
    'Ruby',
    'Python',
    'Java',
    'JavaScript'
]


def get_hh_amount_pages(
        dev_params,
        url=hh_api_url,
        header=hh_header,


):
    response = requests.get(url, headers=header, params=dev_params)
    response.raise_for_status()
    amount_pages = int(response.json()['pages'])
    return amount_pages


def get_hh_vacancies(
        dev_params,
        url=hh_api_url,
        header=hh_header,
):
    amount_pages = get_hh_amount_pages(dev_params)
    all_vacancies = []
    for page in range(amount_pages):
        response = requests.get(hh_api_url, headers=hh_header, params=dev_params)
        response.raise_for_status()
        vacancies = response.json()['items']
        all_vacancies.append(vacancies)

    all_vacancies = [vacancy for sub in all_vacancies for vacancy in sub]
    return all_vacancies


def search_language(lang, vacancies):
    counter = 0
    for vacancy in vacancies:
        if vacancy['snippet']['requirement']:
            if lang in vacancy['snippet']['requirement']:
                counter += 1
    return counter


def get_lang_entry_in_vacancies(
        vacancies,
        languages=popular_program_languages
):
    entries = dict()
    for lang in languages:
        count = search_language(lang, vacancies)
        entries[lang] = count
    return entries


vacancies = get_hh_vacancies(dev_params)
cnt = get_lang_entry_in_vacancies(vacancies)
print(cnt)
