import requests

hh_api_url = 'https://api.hh.ru/vacancies/'

hh_header = {
    'User-Agent': 'salary_benchmarking_app/1.0 konakov-dev@yandex.ru'
}
params = {
    'specialization': '1.221'
}

response = requests.get(hh_api_url, headers=hh_header, params=params)
response.raise_for_status()
print(response.json())
