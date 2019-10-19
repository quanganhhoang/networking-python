import config
import util
import http.client

BUFSIZE = 16

def read_all(res_stream, content_len):
    remaining = content_len
    data = bytearray()
    while (remaining > 0):
        num_read = min(remaining, BUFSIZE)
        data.extend(res_stream.read(num_read))
        remaining -= num_read

    return data

def test_eval_api_success():
    conn = http.client.HTTPConnection(config.WEB_API_SERVER, config.WEB_API_PORT)
    headers = {'Content-type': 'text/plain'}
    expression = '1+2+3'
    conn.request('POST', '/api/evalexpression', expression, headers)
    r = conn.getresponse()
    
    content_len = int(r.getheader('Content-length'))
    data = read_all(r, content_len)
    print(expression + ' = ' + data.decode())
    conn.close()

def test_eval_api_invalid():
    conn = http.client.HTTPConnection(config.WEB_API_SERVER, config.WEB_API_PORT)
    headers = {'Content-type': 'text/plain'}
    expression = '1+2+3-'
    conn.request('POST', '/api/evalexpression', expression, headers)
    r = conn.getresponse()
    content_len = int(r.getheader('Content-length'))
    data = read_all(r, content_len)
    print(expression + ' = ' + data.decode())
    conn.close()


def test_gettime_api():
    conn = http.client.HTTPConnection(config.WEB_API_SERVER, config.WEB_API_PORT)
    
    conn.request('GET', '/api/gettime')
    r = conn.getresponse()
    content_len = int(r.getheader('Content-length'))
    data = read_all(r, content_len)
    print(data.decode())
    conn.close()

def test_404():
    conn = http.client.HTTPConnection(config.WEB_API_SERVER, config.WEB_API_PORT)
    conn.request('GET', '/api/notexist')
    r = conn.getresponse()
    
    content_len = int(r.getheader('Content-length'))
    data = read_all(r, content_len)
    print(str(r.status) + ' - ' + data.decode())
    conn.close()

test_eval_api_success()
test_eval_api_invalid()
test_gettime_api()
test_404()