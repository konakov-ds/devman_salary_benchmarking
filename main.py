import itertools
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
    page_counter = float('inf')
    while page_counter:
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        response = response.json()
        if page_counter == float('inf'):
            page_counter = int(response['pages'])
            vacancies_found = response['found']
        vacancies = response['items']
        all_vacancies.extend(vacancies)
        page_counter -= 1
        params['page'] = page_counter

    return all_vacancies, vacancies_found


def get_hh_salaries_for_language(lang):
    salaries = []
    vacancies, vacancies_found = get_hh_vacancies(lang)
    for vacancy in vacancies:
        salaries.append(vacancy['salary'])
    return salaries, vacancies_found


def get_salary_prediction(
        from_stamp,
        to_stamp,
        currency_lang,
        salary
):

    if salary.get('currency') != currency_lang:
        return
    elif not salary.get(from_stamp) and not salary.get(to_stamp):
        return
    elif not salary.get(from_stamp) and salary.get(to_stamp):
        return salary.get(to_stamp) * 0.8
    elif not salary.get(to_stamp) and salary.get(from_stamp):
        return salary.get(from_stamp) * 1.2
    else:
        return (salary.get(from_stamp) + salary.get(to_stamp)) * 0.5


def predict_rub_salaries_hh(salaries):
    salary_predictions = []
    for salary in salaries:
        if salary:
            prediction = get_salary_prediction(
                from_stamp='from',
                to_stamp='to',
                currency_lang='RUR',
                salary=salary
            )
            salary_predictions.append(prediction)

    return salary_predictions


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
        salary_wrapper = {
            'vacancies_found': vacancies_found,
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
    more = True
    page = 0
    while more:
        params['page'] = page
        response = requests.get(url, headers=header, params=params)
        response.raise_for_status()
        response = response.json()
        vacancies = response['objects']
        all_vacancies.extend(vacancies)
        more = response['more']
        if not more:
            vacancies_found = response['total']
        page += 1
    return all_vacancies, vacancies_found


def predict_rub_salaries_sj(vacancies):
    salary_predictions = []
    for vacancy in vacancies:
        prediction = get_salary_prediction(
            from_stamp='payment_from',
            to_stamp='payment_to',
            currency_lang='rub',
            salary=vacancy
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
    table_data = [
        [language] + list(salary_wrapper.values()) for language, salary_wrapper in salaries.items()
    ]
    table_data.insert(0, column_names)
    table = AsciiTable(table_data, title=title)

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

    #hh_salaries = get_average_salaries_hh(popular_program_languages)
    sj_salaries = get_average_salaries_sj(sj_api_key, popular_program_languages)

    #print(get_salaries_table(hh_salaries, 'HeadHunter Moscow'))
    print(get_salaries_table(sj_salaries, 'SuperJob Moscow'))
