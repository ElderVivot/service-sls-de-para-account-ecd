try:
    import unzip_requirements
except ImportError:
    pass

try:
    import unicodedata
    import re
    import datetime
    from typing import Any, List
except Exception as e:
    print("Error importing libraries", e)


def removeCharSpecials(text: str):
    nfkd = unicodedata.normalize('NFKD', text).encode(
        'ASCII', 'ignore').decode('ASCII')
    textFormated = u"".join([c for c in nfkd if not unicodedata.combining(c)])
    return re.sub('[^a-zA-Z0-9.!+:><=[)|?$(/*,\-_ \\\]', '', textFormated)


def treatDecimalField(value, numberOfDecimalPlaces=2, decimalSeparator=','):
    if type(value) == float:
        return value
    try:
        value = str(value)
        value = re.sub('[^0-9.,-]', '', value)
        if decimalSeparator == '.' and value.find(',') >= 0 and value.find('.') >= 0:
            value = value.replace(',', '')
        elif value.find(',') >= 0 and value.find('.') >= 0:
            value = value.replace('.', '')

        if value.find(',') >= 0:
            value = value.replace(',', '.')

        if value.find('.') < 0:
            value = int(value)

        return float(value)
    except Exception:
        return float(0)


def treatDateField(valorCampo, formatoData=1):
    """
    :param valorCampo: Informar o campo string que será transformado para DATA
    :param formatoData: 1 = 'DD/MM/YYYY' ; 2 = 'YYYY-MM-DD' ; 3 = 'YYYY/MM/DD' ; 4 = 'DDMMYYYY'
    :return: retorna como uma data. Caso não seja uma data válida irá retornar None
    """
    if type(valorCampo) == 'datetime.date':
        return valorCampo

    valorCampo = str(valorCampo).strip()

    lengthField = 10  # tamanho padrão da data são 10 caracteres, só muda se não tiver os separados de dia, mês e ano

    if formatoData == 1:
        formatoDataStr = "%d/%m/%Y"
    elif formatoData == 2:
        formatoDataStr = "%Y-%m-%d"
    elif formatoData == 3:
        formatoDataStr = "%Y/%m/%d"
    elif formatoData == 4:
        formatoDataStr = "%d%m%Y"
        lengthField = 8
    elif formatoData == 5:
        formatoDataStr = "%d/%m/%Y"
        valorCampo = valorCampo[0:6] + '20' + valorCampo[6:]

    try:
        return datetime.datetime.strptime(valorCampo[:lengthField], formatoDataStr).strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


def returnDataInDictOrArray(data: Any, arrayStructureDataReturn: List[Any], valueDefault='') -> Any:
    """
    :data: vector, matrix ou dict with data -> example: {"name": "Obama", "adress": {"zipCode": "1234567"}}
    :arrayStructureDataReturn: array in order with position of vector/matriz or name property of dict to \
    return -> example: ['adress', 'zipCode'] -> return is '1234567'
    """
    try:
        dataAccumulated = ''
        for i in range(len(arrayStructureDataReturn)):
            if i == 0:
                dataAccumulated = data[arrayStructureDataReturn[i]]
            else:
                dataAccumulated = dataAccumulated[arrayStructureDataReturn[i]]
        return dataAccumulated
    except Exception:
        return valueDefault
