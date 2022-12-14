import os
import pytest
import cerberus
import requests
import zlib

from time import sleep
from auxiliary_material import list_files


def test_api_status(base_url_test_1):
    """ Проверка статуса, кодировки, хедера"""
    res = requests.get(base_url_test_1)
    assert res.status_code == 200
    assert res.encoding == 'utf-8'
    assert res.headers['content-type'] == 'application/json'


def test_api_validate_json(base_url_test_1):
    """ Проверка сообщения json"""
    res = requests.get(base_url_test_1)
    schema = {
        'description': {'type': 'string'},
        'data': {'type': 'list', 'schema': {'type': 'string'}},
        'last_command': {'type': 'string'},
        'change_time': {'type': 'string'}
    }
    v = cerberus.Validator()
    assert v.validate(eval(res.json()), schema)


def test_api_content_name(base_url_test_1):
    """ Проверка сервера на запись 9 файлов и корректности их имен """
    list_files = ['cat.jpeg', 'func.docx', 'server.png', 'include.rar', 'keywords.txt',
                  'text_1.txt', 'Yandex.html', 'CoolTermMac.zip', 'text_2.doc']

    # Запись файлов
    for name_file in list_files:
        with open(f'files_for_test/{name_file}', 'rb') as fh:
            mydata = fh.read()
            requests.put(base_url_test_1, data=mydata, params=f'/{name_file}')
    res_rec = eval(requests.get(base_url_test_1).json())

    # Удаление загруженных файлов с сервера
    for name_file in list_files:
        requests.delete(base_url_test_1, params=f'/{name_file}')
    res_del = eval(requests.get(base_url_test_1).json())

    if ('data' not in res_rec) or ('data' not in res_del):
        assert False

    assert set(res_rec.get('data')) == set(list_files) and len(res_del.get('data')) == 0


@pytest.mark.parametrize('file_name', list_files)
def test_api_content_status_response_codes(base_url_test_1, file_name):
    """ Проверка статуса команды записи и удаления файла"""
    # Запись файла
    with open(f'files_for_test/server.png', 'rb') as fh:
        mydata = fh.read()
        res_rec = requests.put(base_url_test_1, data=mydata, params=f'/{file_name}')

    # Удаление файла с сервера
    res_del = requests.delete(base_url_test_1, params=f'/{file_name}')

    assert res_rec.status_code == 201 and res_del.status_code == 301


@pytest.mark.parametrize('file_name', list_files)
def test_api_content_status_last_command_json(base_url_test_1, file_name):
    """ Проверка статуса последней команды"""
    # Запись файла
    with open(f'files_for_test/{file_name}', 'rb') as fh:
        mydata = fh.read()
        requests.put(base_url_test_1, data=mydata, params=f'/{file_name}')
    res_rec = eval(requests.get(base_url_test_1).json())

    # Если нет папки то создаем ее
    if not os.path.isdir('downloaded_files'):
        os.mkdir('downloaded_files')

    # Загрузка файла
    with open(f'downloaded_files/server.png', 'wb') as out:
        res_dwl = requests.post(base_url_test_1, params=f'/{file_name}')
        out.write(res_dwl.content)
    res_rec_dwl = eval(requests.get(base_url_test_1).json())

    # Удаление файла с сервера
    requests.delete(base_url_test_1, params=f'/{file_name}')
    res_del = eval(requests.get(base_url_test_1).json())

    assert res_rec.get('last_command') == 'PUT' and res_rec_dwl.get('last_command') == 'POST' \
           and res_del.get('last_command') == 'DELETE'


@pytest.mark.parametrize('file_name', list_files)
def test_api_content_status_change_time_json(base_url_test_1, file_name):
    """ Проверка статуса записи времени команды запроса """
    # Запись файла
    with open(f'files_for_test/{file_name}', 'rb') as fh:
        mydata = fh.read()
        requests.put(base_url_test_1, data=mydata, params=f'/{file_name}')
    res_rec = eval(requests.get(base_url_test_1).json())

    sleep(2)

    # Удаление файла с сервера
    requests.delete(base_url_test_1, params=f'/{file_name}')
    res_del = eval(requests.get(base_url_test_1).json())

    assert int(str(res_rec.get('change_time'))[17:-7]) != int(str(res_del.get('change_time'))[17:-7])


def test_api_content_download(base_url_test_1):
    """ Проверка на скачивание файлов (проверка на количество)"""
    list_files = ['cat.jpeg', 'func.docx', 'server.png', 'include.rar', 'keywords.txt',
                  'text_1.txt', 'Yandex.html', 'CoolTermMac.zip', 'text_2.doc']

    # Запись файлов
    for name_file in list_files:
        with open(f'files_for_test/{name_file}', 'rb') as fh:
            mydata = fh.read()
            res_rec = requests.put(base_url_test_1, data=mydata, params=f'/{name_file}')

    # Если нет папки то создаем ее
    if not os.path.isdir('downloaded_files'):
        os.mkdir('downloaded_files')

    # Загрузка файлов
    for name_file in list_files:
        with open(f'downloaded_files/{name_file}', 'wb') as out:
            res_dwl = requests.post(base_url_test_1, params=f'/{name_file}')
            out.write(res_dwl.content)

    # Удаление загруженных файлов c сервера
    for name_file in list_files:
        res_del = requests.delete(base_url_test_1, params=f'/{name_file}')

    assert res_rec.status_code == 201 and res_dwl.status_code == 202 and res_del.status_code == 301


def test_api_content_filename_comparison(write_read_and_delete_file):
    """ Сравнение имен файлов"""
    assert os.path.exists(f'downloaded_files/{write_read_and_delete_file}')
    assert write_read_and_delete_file in os.listdir('files_for_test')


def test_api_content_files_size_comparison(write_read_and_delete_file):
    """ Сравнение размера """
    
    file_1_size = os.stat(f'downloaded_files/{write_read_and_delete_file}').st_size
    file_2_size = os.stat(f'files_for_test/{write_read_and_delete_file}').st_size

    assert file_1_size == file_2_size


def test_api_content_files_CRC(write_read_and_delete_file):
    """ Сравнение CRC """
    buffersize = 65536
    dict_crc = {'files_for_test': 0, 'downloaded_files': 0}
    for name_dir in dict_crc.keys():
        with open(f'{name_dir}/{write_read_and_delete_file}', 'rb') as afile:
            buffr = afile.read(buffersize)
            while len(buffr) > 0:
                crcvalue = zlib.crc32(buffr)
                buffr = afile.read(buffersize)
        dict_crc[name_dir] = format(crcvalue & 0xFFFFFFFF, '08x')

    assert len(set(dict_crc.values())) == 1


def test_api_content_multiple_entry_status(base_url_test_1):
    """ Проверка статуса многократной записью одного файла на сервер"""
    # Проверяем наличие файлов на сервере и удаляем их
    res = eval(requests.get(base_url_test_1).json()).get('data')
    if len(res) > 0:
        [requests.delete(base_url_test_1, params=f'/{name_file}') for name_file in res]

    statuscode = []
    for _ in range(3):
        # Запись файла
        with open(f'files_for_test/cat.jpeg', 'rb') as fh:
            mydata = fh.read()
            statuscode.append(requests.put(base_url_test_1, data=mydata, params=f'/cat.jpeg').status_code)

    # Проверяем наличие файлов на сервере и удаляем их
    res = eval(requests.get(base_url_test_1).json()).get('data')
    if len(res) > 0:
        [requests.delete(base_url_test_1, params=f'/{name_file}') for name_file in res]

    assert statuscode == [201, 409, 409]


def test_api_content_multiple_deletion_status(base_url_test_1):
    """ Проверка статуса многократного удаления одного файла с сервера"""
    # Запись файла
    with open(f'files_for_test/cat.jpeg', 'rb') as fh:
        mydata = fh.read()
        requests.put(base_url_test_1, data=mydata, params=f'/cat.jpeg')

    # Удаляем файл многократно
    statuscode = [requests.delete(base_url_test_1, params=f'/cat.jpeg').status_code for _ in range(3)]

    assert statuscode == [301, 302, 302]
