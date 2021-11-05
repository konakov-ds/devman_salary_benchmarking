import requests

hh_api_url = 'https://api.hh.ru/vacancies/'

hh_header = {
    'User-Agent': 'salary_benchmarking_app/1.0 konakov-dev@yandex.ru'
}
params = {
    'specialization': '1.221',
    'area': '1',
    'period': '300',
    'per_page': '100',
}

response = requests.get(hh_api_url, headers=hh_header, params=params)
response.raise_for_status()
amount_vacancies = response.json()['found']
print(amount_vacancies)
