import requests
from dotenv import load_dotenv
import os

load_dotenv()
sj_api_key = os.getenv('SJ_SECRET_KEY')
sj_api_id = os.getenv('SJ_ID')

hh_api_url = 'https://api.hh.ru/vacancies/'

hh_header = {
    'User-Agent': 'salary_benchmarking_app/1.1 konakov-dev@yandex.ru'
}

hh_params = {
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
        hh_params,
        url=hh_api_url,
        header=hh_header,


):
    response = requests.get(url, headers=header, params=hh_params)
    response.raise_for_status()
    amount_pages = int(response.json()['pages'])
    return amount_pages


def get_hh_vacancies(
        hh_params,
        url=hh_api_url,
        header=hh_header,
):
    amount_pages = get_hh_amount_pages(hh_params)
    all_vacancies = []
    for page in range(amount_pages):
        response = requests.get(hh_api_url, headers=hh_header, params=hh_params)
        response.raise_for_status()
        vacancies = response.json()['items']
        all_vacancies.append(vacancies)

    all_vacancies = [vacancy for sub in all_vacancies for vacancy in sub]
    return all_vacancies


def get_info_for_hh_vacancies(lang, vacancies):
    counter = 0
    salaries = []
    for vacancy in vacancies:
        if vacancy['snippet']['requirement']:
            if lang in vacancy['snippet']['requirement']:
                counter += 1
                salaries.append(vacancy['salary'])
    return counter, salaries


def get_lang_entry_in_vacancies(
        vacancies,
        languages=popular_program_languages
):
    entries = dict()
    for lang in languages:
        count, _ = get_info_for_hh_vacancies(lang, vacancies)
        entries[lang] = count
    return entries


def predict_rub_salaries_hh(salaries):
    salary_predictions = []
    for salary in salaries:
        if salary:
            if salary['currency'] != 'RUR':
                salary_predictions.append(None)
            elif not salary['from'] and salary['to']:
                salary_predictions.append(salary['to']*0.8)
            elif not salary['to'] and salary['from']:
                salary_predictions.append(salary['from'] * 1.2)
            else:
                salary_predictions.append((salary['from'] + salary['to']) * 0.5)
        else:
            salary_predictions.append(None)

    return salary_predictions


def get_average_salaries_hh(vacancies, popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        count_vacancies, salaries = get_info_for_language(lang, vacancies)
        salary_predictions = predict_rub_salaries_hh(salaries)
        salary_predictions_clean = [pred for pred in salary_predictions if pred]
        num_salaries = len(salary_predictions_clean)
        if num_salaries == 0:
            mean_salary = None
        else:
            mean_salary = int(sum(salary_predictions_clean)/num_salaries)
        salary_wrapper = {
            'vacancies_found': count_vacancies,
            'vacancies_processed': num_salaries,
            'average_salary': mean_salary
        }
        average_salaries[lang] = salary_wrapper

    return average_salaries

# vacancies = get_hh_vacancies(dev_params)
# cnt = get_lang_entry_in_vacancies(vacancies)
# avg = get_average_salaries_for_langs(vacancies, popular_program_languages)
# counter, salary = get_info_for_language(popular_program_languages[-2], vacancies)
# print(avg)
# print(counter, len(salary))
# print(salary)

sj_api_url = 'https://api.superjob.ru/2.0/vacancies/'

sj_params = {
    'town': 4,
    'catalogues': 48
}

sj_header = {
    'X-Api-App-Id': sj_api_key,
    'Content-Type': 'application/json',
}


def get_sj_vacancies(
        params=sj_params,
        url=sj_api_url,
        header=sj_header,
):

    response = requests.get(sj_api_url, headers=sj_header, params=sj_params)
    response.raise_for_status()
    vacancies = response.json()['objects']
    #professions = [vacancy['profession'] for vacancy in response['objects'] if vacancy['profession']]
    return vacancies

print(get_sj_vacancies())
#print(professions)
