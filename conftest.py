import os
import pytest
import requests

from auxiliary_material import list_files


@pytest.fixture(scope='module')
def base_url_test_1(request):
    return request.config.getoption('--url', default='http://127.0.0.1:8001/')


@pytest.fixture(params=list_files)
def write_read_and_delete_file(base_url_test_1, request):
    """ Запись чтение и удаление файла """
    # Запись файла
    with open(f'files_for_test/{request.param}', 'rb') as fh:
        mydata = fh.read()
        requests.put(base_url_test_1, data=mydata, params=f'/{request.param}')

    # Если нет папки то создаем ее
    if not os.path.isdir('downloaded_files'):
        os.mkdir('downloaded_files')

    # Загрузка файла
    with open(f'downloaded_files/{request.param}', 'wb') as out:
        res_dwl = requests.post(base_url_test_1, params=f'/{request.param}')
        out.write(res_dwl.content)

    # Удаление загруженных файла c сервера
    requests.delete(base_url_test_1, params=f'/{request.param}')

    return request.param
