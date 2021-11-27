import os
import requests
from itertools import count
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_vacancies(
        search_text,
        url='https://api.hh.ru/vacancies/',
        user_agent='salary_benchmarking_app/1.3 konakov-dev@yandex.ru',
        area='1',
        per_page=100,
):

    header = {
        'User-Agent': user_agent
    }
    all_vacancies = []
    params = {
        'area': area,
        'per_page': per_page,
        'text': search_text.lower()
    }
    for page_number in count(1):
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        response_extraction = response.json()
        all_vacancies.extend(response_extraction['items'])
        params['page'] = page_number
        if page_number > int(response_extraction['pages']) - 1:
            vacancies_found = response_extraction['found']
            return all_vacancies, vacancies_found


def get_hh_salaries_for_language(lang):
    salaries = []
    vacancies, vacancies_found = get_hh_vacancies(lang)
    for vacancy in vacancies:
        salaries.append(vacancy['salary'])
    return salaries, vacancies_found


def get_salary_prediction(
        salary_from,
        salary_to,
):
    if not salary_from and not salary_to:
        return
    elif not salary_from and salary_to:
        return salary_to * 0.8
    elif not salary_to and salary_from:
        return salary_from * 1.2
    else:
        return (salary_from + salary_to) * 0.5


def predict_rub_salaries_hh(salaries):
    salary_predictions = []
    for salary in salaries:
        if salary and salary.get('currency') == 'RUR':
            prediction = get_salary_prediction(
                salary['from'],
                salary['to']
            )
            salary_predictions.append(prediction)

    return [pred for pred in salary_predictions if pred]


def get_average_salaries_hh(popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        salaries, vacancies_found = get_hh_salaries_for_language(lang)
        salary_predictions = predict_rub_salaries_hh(salaries)
        num_salaries = len(salary_predictions)
        if not num_salaries:
            mean_salary = None
        else:
            mean_salary = int(sum(salary_predictions)/num_salaries)
        average_salaries[lang] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': num_salaries,
            'average_salary': mean_salary
        }

    return average_salaries


def get_sj_vacancies(
        api_key,
        search_text,
        url='https://api.superjob.ru/2.0/vacancies/',
        town=4,
        count_vacancies_per_page=100,
):
    all_vacancies = []
    header = {
        'X-Api-App-Id': api_key,
        'Content-Type': 'application/json',
    }
    params = {
        'town': town,
        'keyword': search_text,
        'count': count_vacancies_per_page,
    }

    for page_number in count(0):
        params['page'] = page_number
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        response_extraction = response.json()
        all_vacancies.extend(response_extraction['objects'])
        if not response_extraction['more']:
            vacancies_found = response_extraction['total']
            return all_vacancies, vacancies_found


def predict_rub_salaries_sj(vacancies):
    salary_predictions = []
    for vacancy in vacancies:
        if vacancy.get('currency') == 'rub':
            prediction = get_salary_prediction(
                vacancy['payment_from'],
                vacancy['payment_to'],
            )
            salary_predictions.append(prediction)

    return salary_predictions


def get_average_salaries_sj(api_key, popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        vacancies_for_language, vacancies_found = get_sj_vacancies(api_key, lang)
        salary_predictions = predict_rub_salaries_sj(vacancies_for_language)
        salary_predictions_clean = [pred for pred in salary_predictions if pred]
        num_salaries = len(salary_predictions_clean)
        if not num_salaries:
            mean_salary = None
        else:
            mean_salary = int(sum(salary_predictions_clean)/num_salaries)
        salary_wrapper = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': num_salaries,
            'average_salary': mean_salary
        }
        average_salaries[lang] = salary_wrapper

    return average_salaries


def get_salaries_table(salaries, title=None):
    column_names = [
        'Язык программирования',
        'Вакансий найдено',
        'Вакансий обработано',
        'Средняя зарплата'
    ]
    table = [
        [language] + list(salary_wrapper.values()) for language, salary_wrapper in salaries.items()
    ]
    table.insert(0, column_names)
    table = AsciiTable(table, title=title)

    return table.table


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

    hh_salaries = get_average_salaries_hh(popular_program_languages)
    sj_salaries = get_average_salaries_sj(sj_api_key, popular_program_languages)

    print(get_salaries_table(hh_salaries, 'HeadHunter Moscow'))
    print(get_salaries_table(sj_salaries, 'SuperJob Moscow'))
