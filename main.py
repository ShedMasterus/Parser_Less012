# Lesson 012
# Работа с REST API
# Работа с api сайта hh.ru

# Задача:
# Программа запрашивает Страну и Профессию
# Далее по Стране выбираются города
# Далее для каждого города выбираются вакансии по указанной профессии
# Для выбранных вакансий формируется вилка заработной платы
# 20-ка городов с самыми высокими значениями заработной платы записывается в выходной файл
#
# Выходной файл имеет структуру:
# Страна: ХХХХХХХ
# Профессия: ХХХХХХХХХХХХХ
# +--------+------------+------------+-----------+
# | № п/п  |   Город    |  Мин З/П   | Макс З/П  |
# +--------+------------+------------+-----------+
# |   1    |            |            |           |
# |   2    |            |            |           |
# |  ...   |            |            |           |
# |   20   |            |            |           |
# +========+============+============+===========+

import requests
import pprint

DOMAIN = "https://api.hh.ru/"

url_vac = f'{DOMAIN}vacancies'

areas = []                   # Список городов указанной страны
city_vacances = []           # Список вакансий по городу



# Функция печатает одну вакансию (для примера)
def get_one_vacancie(vacance):
    params = {
        'text': vacance,
        'page': 1
    }

    result = requests.get(url_vac, params=params).json()
    items = result['items']
    first = items[0]
    pprint.pprint(first)



# Создадим список городов страны по коду country
def get_citys(country):
    url_areas = 'https://api.hh.ru/areas/'
    result = requests.get(url_areas).json()
    for k in result:
        if k['name'] == country:
            for i in range(len(k['areas'])):
                if len(k['areas'][i]['areas']) != 0:                        # Если у зоны есть внутренние зоны
                    for j in range(len(k['areas'][i]['areas'])):
                        areas.append([k['id'],
                                      k['name'],
                                      k['areas'][i]['areas'][j]['id'],
                                      k['areas'][i]['areas'][j]['name']])
                else:                                                        # Если у зоны нет внутренних зон
                 areas.append([k['id'],
                               k['name'],
                               k['areas'][i]['id'],
                               k['areas'][i]['name']])

    #pprint.pprint(areas)
    return areas

# Функция проверяет есть ли город в списке
def city_exists(city_name, areas):
    res = False
    for c in areas:
        if c[3] == city_name:
            res = True
            break
    return res

# На основании полученных данных обновляем итоговый список
def update_itog(itog, city_name, zp_min, zp_max):
    apd = True
    for i in itog:
        if i[0] == city_name:
            apd = False
            # Сравним зарплаты и поправим если надо
            if zp_min > 0:
                if i[1] == 0 or i[1] > zp_min:
                    i[1] = zp_min

            if i[2] < zp_max:
                i[2] = zp_max
            break
        # else:
        #     if len(itog) > 19:
        #         apd = False

    if apd:
        # Добавим новый город в список
        row = [city_name, zp_min, zp_max]
        itog.append(row)

# Ключ сортировки списка
def custom_key(city):
    return city[2]


# Отсортируем список по максимальным значениям зарплаты и возвращает его первые 20 элементов
def sort_list(src_list=[]):
    dst_list = []

    src_list.sort(key=custom_key)

    # Перед вывборкой перевернем список
    src_list.reverse()

    cnt = 0
    for item in src_list:
        dst_list.append(item)
        cnt += 1
        if cnt == 20:
            break

    return dst_list


# Запрос на выборку указанной профессии в городах из списка
def Zapros(vacance, country, areas):

    itog = []

    # Выберем все возможные вакансии
    params = {
                'text': vacance,
                'page': 1,
                'per_page': 100
            }

    result = requests.get(url_vac, params=params).json()
    print('Найдено: ', result['found'])
    items = result['items']

    cnt = 1
    # Теперь пройдем по каждому пункту и выберем в отдельный список Город, мин зп, макс зп
    for i in items:
        city_vacances.clear()
        # Начинаем анализировать вакансию
        city_name = i['area']['name']

        # Если город есть в списке городов
        if city_exists(city_name, areas):
            try:
                zp_min = i['salary']['from']
            except:
                zp_min = 0
            else:
                if zp_min == None:
                    zp_min = 0

            try:
                zp_max = i['salary']['to']
            except:
                zp_max = zp_min
            else:
                if zp_max == None:
                    zp_max = zp_min

            # В список будем отбирать только те записи в которых присутствует число зарплаты больше 0
            if zp_min > 0 or zp_max > 0:
                # Обновим итоговый список
                update_itog(itog, city_name, zp_min, zp_max)

            cnt += 1



    # Отсортируем список по росту макс ЗП и вернем 20 первых
    itog_itog = sort_list(itog)
    #print(itog_itog)
    return itog_itog


# Генерируем файл отчета
def generate_file_report(itog_list,country, prof):
    sstr = prof + '.txt'
    report_file = open(sstr, "w+")

    sstr = 'СТРАНА: ' + country + '\n'
    report_file.write(sstr)
    sstr = 'ПРОФЕССИЯ: ' + prof + '\n'
    report_file.write(sstr)
    # Заголовок таблицы

    sstr = "+--------+-------------------------------------+----------------+----------------+\n"
    report_file.write(sstr)
    sstr = "| № п/п  |               Город                 |     Мин З/П    |    Макс З/П    |\n"
    report_file.write(sstr)
    sstr = "+--------+-------------------------------------+----------------+----------------+\n"
    report_file.write(sstr)

    # Формируем строку для вывода
    cnt = 1
    for row in itog_list:
        # часть строки под номер
        la = 6 - len(str(cnt))
        sstr = '|  ' + str(cnt) + ' ' * la

        # часть строки с названием города
        a = len(row[0])
        la = 35 - a
        sstr2 = '  ' + row[0] + ' '*la

        sstr = sstr + '|' + sstr2

        #  Часть строки с мин зп
        la = 14 - len(str(row[1]))
        sstr2 = '  ' + str(row[1]) + ' ' * la

        sstr = sstr + '|' + sstr2

        #  Часть строки с макс зп
        la = 14 - len(str(row[2]))
        sstr2 = '  ' + str(row[2]) + ' ' * la

        sstr = sstr + '|' + sstr2

        sstr = sstr + '|\n'
        report_file.write(sstr)
        cnt += 1

    sstr = "+--------+-------------------------------------+----------------+----------------+\n"
    report_file.write(sstr)

    report_file.close()




    # # Для каждого города
    # for k in areas:
    #     city_vacances.clear()
    #
    #     city = k[3]
    #     id_city = k[2]
    #
    #     # Сформируем запрос к hh  город + Профессия + за время (а то что-то не очень ищет) !!!!
    #     params = {
    #             'text': vacance,
    #             'area': id_city,     # Город по которому выбирать
    #             'page': 1,
    #             'per_page': 100      # Кол-во вакансий на 1 странице
    #         }
    #
    #     result = requests.get(url_vac, params=params).json()
    #     if result['found'] > 0:
    #         #print('Нашел!!!')
    #         items = v['items']
    #         item = items[0]
    #         alt_url = item['alternate_url']
    #         city_vacances.append(alt_url)
    #         # for i in items:
    #         #     city_vacances.append(i)
    #
    #     if len(city_vacances) > 0:
    #         print('Город:',  city)
    #         pprint.pprint(city_vacances)
    #


    # first = "заглушка"
    # params = {
    #     'text': vacance,
    #     'area': 'NAME:{},
    #     'page': 1
    # }
    #
    # result = requests.get(url_vac, params = params).json()
    # items = result['items']
    # first = items[0]
    #return first


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # ------------------------------------------------------------------
    # Временный код для отладки
    #ans = 'Картограф'
    #country = 'Россия'
    # get_one_vacancie(ans)  # Выведем одну вакансию для просмотра полей
    #------------------------------------------------------------------


    # Создадим список городов России
    country = input('По какой стране сделать выборку ?: ')
    areas = get_citys(country)
    print('Выбрано', len(areas), 'городов страны', country)

    ans = input('По какой специальности сделать выборку ?: ')
    itog_list = Zapros(ans, country, areas)

    # Сформируем файл отчета
    generate_file_report(itog_list, country, ans)