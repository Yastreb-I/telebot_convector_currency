import requests
import json
import re

from config import info_moex, performance


class APIException(Exception):
    pass


class Moex:
    @staticmethod
    def get_price(amount, base, quote, info=False):

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
            value = float(f"{amount}".replace(",", "."))
        except ValueError:
            raise APIException(f'Не удалось обработать количество {amount}!')

        if info:
            message = convector(base_key, quote_key, value, info)
        else:
            price = convector(base_key, quote_key, value)
            if price == 0 or price is None:
                message = f"В настоящее время по Вашему запросу нет данных. Повторите, пожалуйста, свой запрос позже"
            else:
                price = round(price, 2)  # convector(base_key,quote_key,amount,False)
                message = f"Стоимость <b>{'{:,}'.format(value).replace(',', ' ')} {base_key}</b> в " \
                          f"<b>{quote_key}</b> будет <b>{'{:,}'.format(price).replace(',', ' ')}</b>"
        return message

    @staticmethod
    def info(stock_market="moex"):
        result = ""
        if stock_market == "moex":
            for cur, about in info_moex.items():
                result += "<b>" + cur + "</b> - " + about + "\n"
        # Информация по стоимости ресурсов
        # if stock_market == "resurs":
        #     for cur, about in info_resurs.items():
        #         result += cur + " - " + about + "\n"
        return result

    @staticmethod
    def exchange_rates():
        list_cur = ""
        pars = parser()
        result_json = new_json(pars)
        val_par = currency_pairs(result_json)
        for prev, curr in val_par:
            lc = convector(prev, curr, 1, True)
            if lc is not None:
                list_cur += str(lc) + "\n"
        return list_cur


def parser():
    url = ("https://iss.moex.com/iss/engines/currency/markets/selt/securities.jsonp?"
           "lang=ru&iss.meta=off&iss.json=extended&callback=angular.callbacks._gk")
    data = requests.get(url)
    text = data.text[22:len(data.text) - 1:]
    text = re.sub(r"\n", "", text)
    json_string = json.loads(text)
    return json_string


# В самом запросе не нашел как отфильтровать по нужным критериям поэтому:
# Обрезаем json_string и оставляя только нужные значения
def new_json(json_str):
    # securitie = {}
    securities = []
    # marketdata = {}
    marketdatas = []
    result_json = []
    for sc in json_str[1]['securities']:  # Рыночные инструменты после закрытия торговой сессии
        # Основной режим торгов - "CETS" ; SECID - Индификатор инструмента
        if sc['BOARDID'] == "CETS" and "СВОП" not in str(sc["SECNAME"]):
            securitie = {"SECID": sc["SECID"], "SHORTNAME": sc["SHORTNAME"],
                         "SETTLEDATE": sc["SETTLEDATE"], "FACEVALUE": sc["FACEVALUE"],
                         "FACEUNIT": sc["FACEUNIT"], "PREVPRICE": sc["PREVPRICE"],
                         "CURRENCYID": sc["CURRENCYID"],
                         }
            securities.append(securitie)

    for md in json_str[1]['marketdata']:  # Информация по торговым сессиям
        if md['BOARDID'] == "CETS":  # Основной режим торгов - "CETS" ; SECID - Индификатор инструмента
            marketdata = {"SECID": md["SECID"], "UPDATETIME": md["UPDATETIME"],
                          "LAST": md["LAST"], "TRADINGSTATUS": md["TRADINGSTATUS"]
                          }
            marketdatas.append(marketdata)

    #  Объединяем словари
    for sc_l in securities:
        for md_l in marketdatas:
            if sc_l['SECID'] == md_l['SECID']:
                sc_l.update(md_l)
                result_json.append(sc_l)
    # Из 1138 строк останется только 84! Вот с ними и будем работать дальше
    return result_json


# Список валютных пар
def currency_pairs(value):
    valutnie_pari = set()
    for vl in value:
        valutnie_pari.add((str(vl['FACEUNIT']), str(vl['CURRENCYID'])))
    return valutnie_pari


def convector(numerator="USD", denominator="RUB", amount=0.0, info=False):
    info_results = ""
    # price_results = float
    run = parser()
    result_json = new_json(run)

    val_par = currency_pairs(result_json)
    for nj in result_json:

        # Сначала проверяем торгующиеся сейчас валюты в комбинации А В
        if (f'{numerator}', f'{denominator}') in val_par:
            if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['LAST']) != "None" \
                    and nj['TRADINGSTATUS'] == "T":
                if info:
                    info_results += f"Курс за <i>{'{:,}'.format(nj['FACEVALUE']).replace(',', ' ')}</i> " \
                                    f"<b>{str(nj['FACEUNIT'])}</b> - <b>{str(nj['LAST'])} {str(nj['CURRENCYID'])}</b>"

                    if len(info_results) > 30:
                        return str(info_results)
                else:
                    price_results = (float(nj['LAST']) * amount) / int(nj['FACEVALUE'])
                    if price_results > 0:
                        return price_results
            # Если не нашли, то проверяем прошедшие торги в комбинации А В
            if nj['FACEUNIT'] == numerator and str(nj['CURRENCYID']) == denominator and str(nj['PREVPRICE']) != "None" \
                    and "_TOM" in str(nj['SHORTNAME'][-4:]):
                if info:
                    info_results += f"Курс за <i>{'{:,}'.format(nj['FACEVALUE']).replace(',', ' ')}</i> <b>" \
                                    f"{str(nj['FACEUNIT'])}</b> - <b>{str(nj['PREVPRICE'])} {str(nj['CURRENCYID'])}</b>"
                    if len(info_results) > 30:
                        return str(info_results)
                else:
                    price_results = (float(nj['PREVPRICE']) * amount) / int(nj['FACEVALUE'])
                    if price_results is not None:
                        return price_results
                    else:
                        return 0
        #  Если не нашли комбинацию валют, то меняем комбинацию на В А
        elif (f'{denominator}', f'{numerator}') in val_par:

            # Снова проверяем торгующиеся сейчас валюты в комбинации В А
            if nj['FACEUNIT'] == denominator and str(nj['CURRENCYID']) == numerator and str(nj['LAST']) != "None" \
                    and nj['TRADINGSTATUS'] == "T":
                if info:
                    info_results += f"Курс за <i>{'{:,}'.format(nj['FACEVALUE']).replace(',', ' ')}</i> <b>" \
                                    f"{str(nj['FACEUNIT'])}</b> - <b>{str(nj['LAST'])} {str(nj['CURRENCYID'])}</b>"
                    if len(info_results) > 30:
                        return str(info_results)
                else:
                    price_results = (float(nj['LAST']) * amount) / int(nj['FACEVALUE'])
                    if price_results > 0:
                        return price_results

            # Если не нашли в режиме текущих торгов, то проверяем прошедшие торги в комбинации В А
            if nj['FACEUNIT'] == denominator and str(nj['CURRENCYID']) == numerator and str(nj['PREVPRICE']) != "None" \
                    and "_TOM" in str(nj['SHORTNAME'][-4:]):
                if info:
                    info_results += f"Курс за <i>{'{:,}'.format(nj['FACEVALUE']).replace(',', ' ')}</i> <b>" \
                                    f"{str(nj['FACEUNIT'])}</b> - <b>{str(nj['PREVPRICE'])} {str(nj['CURRENCYID'])}</b>"
                    if len(info_results) > 30:
                        return str(info_results)
                else:
                    price_results = (amount / (float(nj['PREVPRICE']) / int(nj['FACEVALUE'])))
                    if price_results is not None:
                        return price_results
                    else:
                        return 0
        else:
            #  Если на рынке нет прямой конвертации валютной пары, то через кросс-курс рубля
            try:
                if info:
                    krosskurs_n = convector(numerator, "RUB", amount, info)
                    krosskurs_d = convector(denominator, "RUB", 1, info)
                    info_results = str(krosskurs_n) + str(krosskurs_d)
                    return info_results
                else:
                    krosskurs_n = convector(numerator, "RUB", amount)
                    krosskurs_d = convector(denominator, "RUB", 1)
                    if krosskurs_n == 0 or krosskurs_d == 0 or krosskurs_n is None or krosskurs_d is None:
                        return 0
                    else:
                        price_results = float(krosskurs_n / krosskurs_d)
            except ZeroDivisionError as e:
                raise APIException(f'Не делиться на ноль float (krosskurs_n / krosskurs_d)!{e}')
            except ValueError as e:
                raise APIException(f'Ошибка обработки: {e}')
            except TypeError as e:
                raise APIException(f'Ошибка обработки: {e}')
            else:
                return float(price_results)
