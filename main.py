import os
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def get_hh_vacancies(
        search_text,
        url='https://api.hh.ru/vacancies/',
        user_agent='salary_benchmarking_app/1.2 konakov-dev@yandex.ru',
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
    amount_pages = 100
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


def get_hh_salaries_for_language(lang):
    salaries = []
    vacancies = get_hh_vacancies(search_text=lang)
    for vacancy in vacancies:
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


def get_average_salaries_hh(popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        salaries = get_hh_salaries_for_language(lang)
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
    for page in range(10):  # Поставил 10, тк апи выдает нули на большем количестве
        params['page'] = page
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        vacancies = response.json()['objects']
        all_vacancies.extend(vacancies)

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


def get_average_salaries_sj(api_key, popular_program_languages):
    average_salaries = dict()
    for lang in popular_program_languages:
        vacancies_for_language = get_sj_vacancies(api_key, lang)
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

    #hh_salaries = get_average_salaries_hh(popular_program_languages)
    sj_salaries = get_average_salaries_sj(sj_api_key, popular_program_languages)

    #print_salaries(hh_salaries, 'HeadHunter Moscow')
    print_salaries(sj_salaries, 'SuperJob Moscow')
