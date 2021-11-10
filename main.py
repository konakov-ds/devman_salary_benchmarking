import os
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_vacancies(
        url='https://api.hh.ru/vacancies/',
        user_agent='salary_benchmarking_app/1.2 konakov-dev@yandex.ru',
        specialization='1.221',
        area='1',
        per_page=100,
):
    amount_pages = 100
    header = {
        'User-Agent': user_agent
    }
    params = {
        'specialization': specialization,
        'area': area,
        'per_page': per_page
    }
    all_vacancies = []
    while amount_pages:
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        if amount_pages == 100:
            amount_pages = int(response.json()['pages'])
        vacancies = response.json()['items']
        all_vacancies.extend(vacancies)
        amount_pages -= 1
        params['page'] = amount_pages

    return all_vacancies


def get_hh_vacancies_for_language(lang, vacancies):
    salaries = []
    for vacancy in vacancies:
        if vacancy['snippet']['requirement']:
            if lang in vacancy['snippet']['requirement']:
                salaries.append(vacancy['salary'])
    return salaries


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
        salaries = get_hh_vacancies_for_language(lang, vacancies)
        salary_predictions = predict_rub_salaries_hh(salaries)
        salary_predictions_clean = [pred for pred in salary_predictions if pred]
        count_vacancies = len(salaries)
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


def get_sj_vacancies(
        api_key,
        url='https://api.superjob.ru/2.0/vacancies/',
        town=4,
        catalogues=48,
        count_vacancies_per_page=100,
):
    all_vacancies = []
    header = {
        'X-Api-App-Id': api_key,
        'Content-Type': 'application/json',
    }
    params = {
        'town': town,
        'catalogues': catalogues,
        'count': count_vacancies_per_page,
    }
    for page in range(10):  # Поставил 10, тк апи выдает нули на большем количестве
        params['page'] = page
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        vacancies = response.json()['objects']
        all_vacancies.append(vacancies)

    all_vacancies = [vacancy for sub in all_vacancies for vacancy in sub]

    return all_vacancies


def get_sj_vacancies_for_language(language, vacancies):
    vacancies_for_language = []
    for vacancy in vacancies:
        if vacancy['profession']:
            if language in vacancy['profession']:
                vacancies_for_language.append(vacancy)
    return vacancies_for_language


def predict_rub_salaries_sj(vacancies):
    salary_predictions = []
    for vacancy in vacancies:
        if vacancy['currency'] != 'rub':
            salary_predictions.append(None)
        elif vacancy['payment_from'] == 0 and vacancy['payment_to'] > 0:
            salary_predictions.append(vacancy['payment_to']*0.8)
        elif vacancy['payment_from'] > 0 and vacancy['payment_to'] == 0:
            salary_predictions.append(vacancy['payment_from'] * 1.2)
        elif vacancy['payment_from'] > 0 and vacancy['payment_to'] > 0:
            salary_predictions.append((vacancy['payment_from'] + vacancy['payment_to']) * 0.5)
        else:
            salary_predictions.append(None)

    return salary_predictions


def get_average_salaries_sj(vacancies, popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        vacancies_for_language = get_sj_vacancies_for_language(lang, vacancies)
        count_vacancies = len(vacancies_for_language)
        salary_predictions = predict_rub_salaries_sj(vacancies_for_language)
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


def print_salaries(salaries, title=None):
    column_names = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
    ]
    table_data = [
        [language] + list(salaries[language].values()) for language in salaries
    ]
    table_data.insert(0, column_names)
    table = AsciiTable(table_data, title=title)

    print(table.table)


if __name__ == '__main__':
    load_dotenv()
    sj_api_key = os.getenv('SJ_SECRET_KEY')

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

    sj_vacancies = get_sj_vacancies(api_key=sj_api_key)
    hh_vacancies = get_hh_vacancies()

    hh_salaries = get_average_salaries_hh(hh_vacancies, popular_program_languages)
    sj_salaries = get_average_salaries_sj(sj_vacancies, popular_program_languages)

    print_salaries(hh_salaries, 'HeadHunter Moscow')
    print_salaries(sj_salaries, 'SuperJob Moscow')
