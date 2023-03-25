import requests
import json
from config import info_moex,performance
import re
# from time import sleep

result_json = []

class APIException(Exception):
    pass

class MOEX:
    @staticmethod
    def get_price(amount,base,quote,info=False):

        try:
            base_key = performance[base.lower()]
        except KeyError:
            raise APIException(f"Валюта {base} не найдена!")

        try:
            quote_key = performance[quote.lower()]
        except KeyError:
            raise APIException(f"Валюта {quote} не найдена!")

        if base_key == quote_key:
            raise APIException(f'Невозможно перевести одинаковые валюты {base}!')

        try:
            amount = float(amount.replace(",", "."))
        except ValueError:
            raise APIException(f'Не удалось обработать количество {amount}!')

        url = ("https://iss.moex.com/iss/engines/currency/markets/selt/securities.jsonp?"
                   "lang=ru&iss.meta=off&iss.json=extended&callback=angular.callbacks._gk")
        data = requests.get(url)
        text = data.text[22:len(data.text) - 1:]
        text = re.sub(r"\n", "", text)
        json_string = json.loads(text)
        new_json(json_string)
        if info:
            message = convector(base_key, quote_key, amount, info)
        else:
            price = convector(base_key, quote_key, amount)
            if price == 0 or price is None:
                message = f"В настоящее время по Вашему запросу нет данных. Повторите, пожалуйста, свой запрос позже"
            else:
                price = round(price, 2)  # convector(base_key,quote_key,amount,False)
                message = f"Стоимость {amount} {base_key} в {quote_key} будет {price}"
        return message


def info(stock_market="moex"):
    result = ""
    if stock_market == "moex":
        for cur, about in info_moex.items():
            result += cur + " - " + about + "\n"
    # Информация по стоимости ресурсов
    # if stock_market == "resurs":
    #     for cur, about in info_resurs.items():
    #         result += cur + " - " + about + "\n"
    return result

# В самом запросе не нашел как отфильтровать по нужным критериям поэтому:
# Обрезаем json_string и оставляя только нужные значения
def new_json(json_str):

    securitie = {}
    securities = []
    marketdata = {}
    marketdatas = []

    for sc in json_str[1]['securities']:  # Рыночные инструменты после закрытия торговой сессии
        if sc['BOARDID'] == "CETS" and "СВОП" not in str(sc["SECNAME"]): #  Основной режим торгов - "CETS" ; SECID - Индификатор инструмента
            securitie={"SECID":sc["SECID"],"SHORTNAME":sc["SHORTNAME"],
                       "SETTLEDATE":sc["SETTLEDATE"],"BOARDID":sc["BOARDID"],
                       "FACEVALUE":sc["FACEVALUE"],"FACEUNIT":sc["FACEUNIT"],
                       "CURRENCYID":sc["CURRENCYID"],"PREVPRICE":sc["PREVPRICE"],
                       "SECNAME": sc["SECNAME"]  }
            securities.append(securitie)

    for md in json_str[1]['marketdata']:  # Информация по торговым сессиям
        if md['BOARDID'] == "CETS": #  Основной режим торгов - "CETS" ; SECID - Индификатор инструмента
            marketdata = {"SECID": md["SECID"], "UPDATETIME": md["UPDATETIME"],
                          "LAST": md["LAST"], "TRADINGSTATUS": md["TRADINGSTATUS"]
                          }
            marketdatas.append(marketdata)

    #  Объединяем словари
    for sc_l in securities:
        for md_l in marketdatas:
            if sc_l['SECID']==md_l['SECID']:
                sc_l.update(md_l)
                result_json.append(sc_l)

    # Из 1138 строк останется только 84! Вот с ними и будем работать дальше
    return result_json


# Список валютных пар
def valutnie_pari(value):
    valutnie_pari = set()
    for vl in value:
        valutnie_pari.add((str(vl['FACEUNIT']), str(vl['CURRENCYID'])))
    return valutnie_pari


def convector(numerator="USD", denominator="RUB", ammount=0, info=False):
    info_resultes=""
    price_rezult = float
    val_par = valutnie_pari(result_json)
    for nj in result_json:

        # Сначала проверяем торгующиеся сейчас валюты в комбинации А В
        if (f'{numerator}', f'{denominator}') in val_par:

            if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['LAST']) != "None" \
                             and nj['TRADINGSTATUS'] == "T":
                if info:
                     info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
                               f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
                               f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
                               f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
                               f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} - marketdata\n"
                     if len(info_resultes)>35:
                         return str(info_resultes)
                else:
                     price_rezult = (float(nj['LAST']) * ammount) / int(nj['FACEVALUE'])
                     if price_rezult > 0:
                         return price_rezult
            # Если не нашли, то проверяем прошедшие торги в комбинации А В
            if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['PREVPRICE']) != "None" \
                             and "_TOM" in str(nj['SHORTNAME'][-4:]):
                if info:
                    info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
                               f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
                               f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
                               f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
                               f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} - securities\n"
                    if len(info_resultes)>35:
                        return str(info_resultes)
                else:
                    price_rezult = (float(nj['PREVPRICE']) * ammount) / int(nj['FACEVALUE'])
                    if price_rezult is not None or price_rezult > 0:
                        return price_rezult
                    else:
                        return 0
        #  Если не нашли комбинацию валют, то меняем комбинацию на В А
        elif (f'{denominator}', f'{numerator}') in val_par:

            # Снова проверяем торгующиеся сейчас валюты в комбинации В А
            if nj['FACEUNIT'] == denominator and str(nj['CURRENCYID']) == numerator and str(nj['LAST']) != "None" \
                             and nj['TRADINGSTATUS'] == "T":
                if info:
                     info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
                               f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
                               f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
                               f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
                               f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} - marketdata\n"
                     if len(info_resultes)>35:
                         return str(info_resultes)
                else:
                     price_rezult = (float(nj['LAST']) * ammount) / int(nj['FACEVALUE'])
                     if price_rezult > 0:
                         return price_rezult

            # Если не нашли в режиме текущих торгов, то проверяем прошедшие торги в комбинации В А
            if nj['FACEUNIT'] == denominator and str(nj['CURRENCYID']) == numerator and str(nj['PREVPRICE']) != "None" \
                             and "_TOM" in str(nj['SHORTNAME'][-4:]):
                if info:
                    info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
                               f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
                               f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
                               f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
                               f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} - securities\n"
                    if len(info_resultes)>35:
                        return str(info_resultes)
                else:
                    price_rezult = (ammount / (float(nj['PREVPRICE']) / int(nj['FACEVALUE'])))
                    if price_rezult is not None or price_rezult > 0:
                        return price_rezult
                    else:
                        return 0
        else:
            try:
                if info:
                    krosskurs_n = convector(numerator, "RUB", ammount,info)
                    krosskurs_d = convector(denominator, "RUB", 1,info)
                    info_resultes = str(krosskurs_n) + str(krosskurs_d)
                    return info_resultes
                else:
                    krosskurs_n = convector(numerator, "RUB", ammount)
                    krosskurs_d = convector(denominator, "RUB", 1)
                    if krosskurs_n == 0 or krosskurs_d == 0 or krosskurs_n is None or krosskurs_d is None:
                        return 0
                    else:
                        resultes = float(krosskurs_n / krosskurs_d)
            except ZeroDivisionError as e:
                raise APIException(f'Не делиться на ноль float (krosskurs_n / krosskurs_d)!{e}')
            except ValueError as e:
                raise APIException(f'Ошибка обработки: {e}')
            except TypeError as e:
                raise APIException(f'Ошибка обработки: {e}')
            else:
                return float(resultes)



            # if (f'{numerator}', 'RUB') in val_par:
            #     print("Есть совпадение3: ", numerator, 'RUB')
        # elif (f'{denominator}', 'RUB') in val_par:
        #     print("Есть совпадение4: ", denominator, 'RUB')






       #
       # # V3
       #
       #  if nj['CURRENCYID'] == numerator and str(nj['FACEUNIT']) == denominator and str(nj['LAST']) != "None" \
       #          and nj['TRADINGSTATUS'] == "T":
       #      if info:
       #          info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
       #                    f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
       #                    f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
       #                    f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
       #                    f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} \n"
       #          if len(info_resultes)>20:
       #              return info_resultes
       #      else:
       #          price_rezult = (float(nj['LAST']) * ammount) / int(nj['FACEVALUE'])
       #          if price_rezult > 0:
       #              return price_rezult
       #
       #  # Затем проверяем торгующиеся сейчас валюты в комбинации В А
       #  if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['LAST']) != "None" \
       #          and nj['TRADINGSTATUS'] == "T":
       #      if info:
       #          info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
       #                    f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
       #                    f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
       #                    f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
       #                    f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} \n"
       #          if len(info_resultes)>20:
       #              return info_resultes
       #      else:
       #          price_rezult = (float(nj['LAST']) * ammount) / int(nj['FACEVALUE'])
       #          if price_rezult > 0:
       #              return price_rezult
       #  # Если не нашли, то проверяем прошедшие торги в комбинации А В
       #  if nj['CURRENCYID'] == numerator and str(nj['FACEUNIT']) == denominator and str(nj['PREVPRICE']) != "None" \
       #          and "_TOM" in str(nj['SHORTNAME'][-4:]):
       #      if info:
       #          info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
       #                    f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
       #                    f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
       #                    f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
       #                    f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} \n"
       #          if len(info_resultes)>20:
       #              return info_resultes
       #      else:
       #          price_rezult = (float(nj['PREVPRICE']) * ammount) / int(nj['FACEVALUE'])
       #          if price_rezult > 0:
       #              return price_rezult
       #
       #  # Если не нашли, то проверяем прошедшие торги в комбинации В А
       #  if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['PREVPRICE']) != "None" \
       #          and "_TOM" in str(nj['SHORTNAME'][-4:]):
       #      if info:
       #          info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
       #                           f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
       #                           f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
       #                           f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
       #                           f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} \n"
       #          if len(info_resultes) > 20:
       #              return info_resultes
       #      else:
       #          price_rezult = (float(nj['PREVPRICE']) * ammount) / int(nj['FACEVALUE'])
       #          if price_rezult > 0:
       #              return price_rezult


    #     if nj['CURRENCYID']==numerator and str(nj['FACEUNIT'])==denominator and str(nj['LAST']) != "None" \
    #             and nj['TRADINGSTATUS'] == "T" :
    #         if info:
    #             info_resultes += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
    #                       f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])}" \
    #                       f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
    #                       f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
    #                       f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} \n"
    #         else:
    #             price_rezult += str((float(nj['LAST']) * ammount) / int(nj['FACEVALUE']))+"G"
    #
    #     if (str(nj['FACEUNIT'])==numerator and str(nj['CURRENCYID'])==denominator) and \
    #             str(nj['LAST']) != "None":     #  and "_TOM" in str(nj['SHORTNAME'][-4:])
    #         if info:
    #             info_resultes += f"2Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
    #                       f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} - {str(nj['PREVPRICE'])} " \
    #                       f"{str(nj['CURRENCYID'])} - {str(nj['FACEVALUE'])}" \
    #                       f" - {str(nj['TRADINGSTATUS'])} - {str(nj['SETTLEDATE'])}" \
    #                       f" - {str(nj['SECID'])}</b> - {str(nj['SHORTNAME'])} + {str(nj['SHORTNAME'][-4:])}\n"
    #         else:
    #             price_rezult += str((float(nj['PREVPRICE'])*ammount)/int(nj['FACEVALUE']))+"G"
    #
    # resultes = price_rezult
    # print(price_rezult)
    # if info:
    #     return info_resultes
    # else:
    #     try:
    #         if (f'{numerator}', 'RUB') in all_cur_z and (f'{denominator}', 'RUB') in all_cur_d:
    #             krosskurs_n = convector(numerator, "RUB", ammount)
    #             krosskurs_d = convector(denominator, "RUB", 1)
    #             resultes = float(krosskurs_n / krosskurs_d)
    #         elif (f'{numerator}', 'RUB') in all_cur_z and (f'{denominator}', 'RUB') in all_cur_z:
    #             krosskurs_n = convector(numerator, "RUB", ammount)
    #             krosskurs_d = convector("RUB",denominator , 1)
    #             resultes = float(krosskurs_d) / float(krosskurs_n)
    #         elif (f'{numerator}', 'USD') in all_cur_z and (f'{denominator}', 'USD') in all_cur_z:
    #             krosskurs_n = convector(denominator, "USD", ammount)
    #             krosskurs_d = convector(numerator, "USD", 1)
    #             resultes = float(krosskurs_n / krosskurs_d)
    #
    #     except ZeroDivisionError as e:
    #         raise APIException(f'Не делиться на ноль float (krosskurs_n / krosskurs_d)!{e}')
    #     except ValueError as e:
    #         raise APIException(f'Ошибка обработки: {e}')
    #     except TypeError as e:
    #         raise APIException(f'Ошибка обработки: {e}')
    #     else:
    #         return float(resultes)


        #  Если истина, то это валюты конвертируется через другие валюты (кросс-курсы)
        # if (f'{numerator}',f'{denominator}') not in all_cur_z and (f'{numerator}',f'{denominator}') not in all_cur_d:
        #     print(f'({numerator},{denominator}) in all_cur_z')
        #     if (f'{denominator}', f'{numerator}') not in all_cur_z and (f'{denominator}', f'{numerator}') not in all_cur_d:
        #         print(f'({denominator},{numerator}) in all_cur_z')
        #         if (f'{numerator}', 'RUB') in all_cur_z and (f'{denominator}', 'RUB') in all_cur_d:
        #             krosskurs_n = convector(numerator, "RUB", ammount)
        #             krosskurs_d = convector(denominator, "RUB", 1)
        #             return float(krosskurs_n / krosskurs_d)
        #         elif(f'{numerator}', 'RUB') in all_cur_z and (f'{denominator}', 'RUB') in all_cur_z:
        #
        #
        #             if all_cur_z.isdisjoint((numerator,"RUB")) and all_cur_d.isdisjoint((numerator, "RUB")):
        #                 #  Через rub
        #
        #                 print("Совпадение: ", numerator," RUB", all_cur_z.issubset(f"('{numerator}','RUB')"))
        #                 if (f'{denominator}','RUB') in all_cur_d and (f'{denominator}','RUB') in all_cur_z:
        #                     print("Совпадение: ", denominator, " RUB -", (f'{denominator}','RUB') in all_cur_z)
        #                     # krosskurs_n = convector(numerator, "RUB", ammount)
        #                     # krosskurs_d = convector(denominator, "RUB", 1)
        #                     return 0 #  float(krosskurs_n/krosskurs_d)
        #
        #                 try:
        #                     krosskurs_n = convector(numerator, "RUB", ammount)
        #                     krosskurs_d = convector(denominator, "RUB", 1)
        #                     return float(krosskurs_n / krosskurs_d)
        #                 except ZeroDivisionError:
        #                     raise APIException(f'Не делиться на ноль float (krosskurs_n / krosskurs_d)!')
        #
        #                 else:
        #                     krosskurs_n = convector(numerator, "RUB", ammount)
        #                     krosskurs_d = convector(denominator, "RUB", 1)
        #                     return float(krosskurs_n / krosskurs_d)
        #                     print("Не совпадение: ", denominator, " RUB")
        #
        #
        #                 print("Не совпадение: ", numerator, " RUB")
        #
        #                 print("Не совпадение: ", numerator, " RUB")
        # else:
        #
        #     print("Нет вообще ни каких данных: ")
        #     # print(all_cur_z.isdisjoint((numerator,denominator)))
        #     # print(all_cur_d.isdisjoint((numerator, denominator)))
        #     # print(all_cur_z.isdisjoint((denominator, numerator)))
        #     # print(all_cur_d.isdisjoint((denominator, numerator)))
        # return 0
        #
        #
        # if resultes>0:
        #     if resultes == ['']:
        #         krosskurs = float(float(convector("RUB", denominator, ammount)) * float(
        #             convector(numerator, "RUB", 1)))  # Проверить!!!
        #         return krosskurs
        #     else:
        #         return float((resultes[0]))

# print(convector("USD",denominator,ammount), convector(numerator,"USD",ammount))



# print(len(new_json()),new_json())

# print(convector("EUR","CNY", ammount=100))
# print(convector("EUR","CNY", ammount=100))
# for nj in result_json:
#     all_cur_z.add(str(nj['FACEUNIT']))
#     all_cur_d.add(str(nj['CURRENCYID']))
#     if nj['TRADINGSTATUS'] == "T":  # Состояние торгов по инструменту: T - торговая сессия
#         if nj['LAST'] is not None and "_TOD" in nj['SHORTNAME'][-4:]:
#                 result += f"Курс <b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}</b>" \
#                       f" в {nj['UPDATETIME']}: <b>{str(nj['LAST'])} " \
#                       f"{str(nj['CURRENCYID'])}  - {str(nj['SECID'])}</b>\n"
#     else:
#         if nj['PREVPRICE'] is not None and "_TOM" in nj['SHORTNAME'][-4:]:
#             result += f"Курс на конец вчерашнего дня " \
#                       f"<b>{str(nj['FACEUNIT'])}/{str(nj['CURRENCYID'])}: {str(nj['PREVPRICE'])} " \
#                       f"{str(nj['CURRENCYID'])} - {str(nj['SECID'])}</b>\n"
#     print("len(all_cur_z): ", len(all_cur_z), "all_cur_z: ", all_cur_z)
#     print("len(all_cur_d): ", len(all_cur_d), "all_cur_d: ", all_cur_d)
#     print("all_cur_d.symmetric_difference(all_cur_z): ", all_cur_d.symmetric_difference(all_cur_z),
#           "len(all_cur_d.symmetric_difference(all_cur_z)): ", len(all_cur_d.symmetric_difference(all_cur_z)))
#     print("all_cur_z.symmetric_difference(all_cur_d): ", all_cur_z.symmetric_difference(all_cur_d),
#           "len(all_cur_d.symmetric_difference(all_cur_z)): ", len(all_cur_z.symmetric_difference(all_cur_d)))
#     print("all_cur_d.isdisjoint(all_cur_z): ", all_cur_d.isdisjoint(all_cur_z))
#     print("all_cur_z.isdisjoint(all_cur_d): ", all_cur_z.isdisjoint(all_cur_d))



# print(result)
# MOEX.get_price(100, "EUR", "CNY")

        #
        # #  Основной режим торгов - "CETS" ; SECID - Индификатор инструмента
        # if (sc['BOARDID'] =="CETS" and md['BOARDID'] =="CETS") and (sc['SECID'] == md['SECID'])  :
        #     if md['TRADINGSTATUS'] == "T":  # Состояние торгов по инструменту: T - торговая сессия
        #         if md['LAST'] is not None:
        #             result += f"Курс <b>{str(sc['FACEUNIT'])}/{str(sc['CURRENCYID'])}</b>" \
        #                       f" в {md['UPDATETIME']}: <b>{str(md['LAST'])} " \
        #                       f"{str(sc['CURRENCYID'])}  - {str(md['SECID'])}</b>\n"
        #     else:
        #         if sc['PREVWAPRICE'] is not None:
        #             result += f"Курс на конец вчерашнего дня " \
        #                       f"<b>{str(sc['FACEUNIT'])}/{str(sc['CURRENCYID'])}: {str(sc['PREVWAPRICE'])} " \
        #                       f"{str(sc['CURRENCYID'])} - {str(sc['SECID'])}</b>\n"
        #

            # # print(sm['BOARDID'])
            # # if md['LAST'] is None:
            #     if sc['PREVWAPRICE'] is None :
            #         result += ""
            #     else:
            #         result += f"Курс на конец вчерашнего дня " \
            #                   f"<b>{str(sc['FACEUNIT'])}/{str(sc['CURRENCYID'])}: {str(sc['PREVWAPRICE'])} " \
            #                   f"{str(sc['CURRENCYID'])} - {str(sc['SECID'])}</b>\n"
            #
            #     # print(
            #     # f"Курс валюты на конец вчерашнего дня {ss['SECNAME'].split(' - ')[1]}: {ss['PREVWAPRICE']}
            #     # {ss['CURRENCYID']}")
            # else:
            #     result += f"Курс <b>{str(sc['FACEUNIT'])}/{str(sc['CURRENCYID'])}</b>" \
            #               f" в {md['UPDATETIME']}: <b>{str(md['LAST'])} " \
            #               f"{str(sc['CURRENCYID'])}  - {str(md['SECID'])}</b>\n"
            #     # print( f"Курс валюты {ss['SECNAME'].split(' - ')[1]} в {sm['UPDATETIME']}: {sm['LAST']} {
            #     # ss['CURRENCYID']}")
# print(result)


#
# #
# def request_currency(currency_numerator, currency_denominator, cross_course=True):
#     result = ''
#     dictionary_currency = {}
#     try:
#         if type(currency_numerator) is not list and type(currency_denominator) is not list:
#             raise SendErrors(f'!!! request_currency({currency_numerator, currency_denominator})',
#                          'Переданы аргументы не list типа')
#     except SendErrors as e:
#         print(e.args[0])
#         print(e.args[1])
#
#     else:
#         dict_cur_secid_usd = {'CNY': 'USDCNY_TOM', 'EUR': 'EURUSD_TOM', 'TRY': 'USDTRY_TOM',
#                               'ZAR': 'USDZAR_TOM', 'KZT': 'USDKZT_TOM', 'USD': 'EURUSD_TOM'}
#         # dict_cur_secid_eur = {'USD': 'EURUSD_TOM'}
#         dict_cur_secid_rub = {'USD': 'USD000UTSTOM', 'EUR': 'EUR_RUB__TOM', 'CNY': 'CNYRUB_TOM', 'HKD': 'HKDRUB_TOD',
#                               'BYN': 'BYNRUB_TOM', 'TRY': 'TRYRUB_TOM', 'KZT': 'KZTRUB_TOM', 'ZAR': 'ZARRUB_TOM',
#                               'AMD': 'AMDRUB_TOM', 'UZS': 'UZSRUB_TOM'}
#         dict_met_secid_rub = {'GLD': 'GLDRUB_TOM', 'SLV': 'SLVRUB_TOM'}
#         if 'RUB' in currency_denominator:
#             if cross_course:
#                 dictionary_currency = dict_cur_secid_rub.copy()
#             else:
#                 dictionary_currency = dict_met_secid_rub.copy()
#         if 'USD' in currency_denominator:
#             dictionary_currency = dict_cur_secid_usd.copy()
#         # if 'EUR' in currency_denominator:
#         #     dictionary_currency = dict_cur_secid_eur.copy()
#
#         quert = ""
#         for cnum in currency_numerator:
#             secid = "CETS:"
#             try:
#                 if cnum in dictionary_currency.keys():
#                     quert += secid + dictionary_currency[cnum] + ","
#             except SendErrors as e:
#                 raise SendErrors(f'for {cnum} in {currency_numerator}',
#                                  f'В словаре нет ключа с именем - {cnum}')
#                 print(e.args[0])
#                 print(e.args[1])
#
#         querty = "securities=" + quert
#
#         url = ("https://iss.moex.com/iss/engines/currency/markets/selt/securities.jsonp?"
#                "iss.only=securities,marketdata&"
#                f"{querty[:-1]}&"  # f"securities=CETS:{cets}&"  # USD000UTSTOM,CETS:EUR_RUB__TOM,CETS:CNYRUB_TOM
#                "lang=ru&iss.meta=off&iss.json=extended&callback=angular.callbacks._gk")
#         data = requests.get(url)
#         # Обрежем лишнее (вызов функции и переводы строк)
#         text = data.text[22:len(data.text) - 1:]
#         text = re.sub(r'\n', "", text)
#         json_string = json.loads(text)
#         for ss in json_string[1]['securities']:
#             # print( f"Курс валюты на конец вчерашнего дня {ss['SECNAME'].split(' - ')[1]}: {ss['PREVWAPRICE']} {ss[
#             # 'CURRENCYID']}")
#             for sm in json_string[1]['marketdata']:
#                 if ss['SECID'] == sm['SECID']:
#                     if sm['LAST'] is None:
#                         if ss['PREVWAPRICE'] is None:
#                             result += ""
#                         else:
#                             result += f"Курс на конец вчерашнего дня " \
#                                       f"<b>{ str(ss['SECNAME'].split(' - ')[1])}</b> : <b>{str(ss['PREVWAPRICE'])} " \
#                                       f"{str(ss['CURRENCYID'])}</b>\n"
#
#                         # print(
#                         # f"Курс валюты на конец вчерашнего дня {ss['SECNAME'].split(' - ')[1]}: {ss['PREVWAPRICE']}
#                         # {ss['CURRENCYID']}")
#                     else:
#                         result += f"Курс <b>{ str(ss['SECNAME'].split(' - ')[1])}</b>"\
#                                   f" в {sm['UPDATETIME']}: <b>{str(sm['LAST'])} " \
#                                   f"{str(ss['CURRENCYID'])} </b>\n"
#                         # print( f"Курс валюты {ss['SECNAME'].split(' - ')[1]} в {sm['UPDATETIME']}: {sm['LAST']} {
#                         # ss['CURRENCYID']}")
#     return result