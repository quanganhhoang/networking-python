import http.server
import socket
import struct
import time
import queue
import pymemcache

import config
import util

EVAL_API = '/api/evalexpression'
TIME_API = '/api/gettime'
STATUS_API = '/status.html'

LAST_MIN = 'last_min'
LAST_HOUR = 'last_hour'
LAST_24HR = 'last_24HR'
LIFETIME = 'lifetime'

NUM_SECONDS_24HR = 60 * 60 * 24

times = [0] * NUM_SECONDS_24HR # holds timestamps indexed by time % NUM_SECONDS_24HR
eval_stats = [0] * NUM_SECONDS_24HR
time_stats = [0] * NUM_SECONDS_24HR

last_ten_expression = []

# LIFE_TIME_COUNT = [0] * 2 # holds lifetime count for eval_api and time_api

BUFSIZE = 16
start_time = int(time.time())

routes = [EVAL_API, TIME_API, STATUS_API]

class Handler(http.server.BaseHTTPRequestHandler):
	def do_GET(self):
		self.respond()

	def do_POST(self):
		self.respond()
	
	# read post content given content-length
	def read_post_content(self, content_len):
		remaining = content_len
		post_body = bytearray()
		while (remaining > 0):
			read = min(BUFSIZE, remaining)
			post_body.extend(self.rfile.read(read))
			remaining -= read
		
		return post_body

	# communicate with eval-server
	def process_expression(self, post_body):
		encoded_expression = struct.pack('!h', 1) # only sends 1 expression per req
		encoded_expression += struct.pack('!h' + str(len(post_body)) + 's', len(post_body), post_body)

		server_name = config.EXPRESSION_EVAL_SERVER
		server_port = config.EXPRESSION_EVAL_PORT

		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.connect((server_name, server_port))
		print('Asking eval-server...')
		s.sendall(encoded_expression)

		num_answers = util.recv_all(s, 2)
		res_len = util.recv_all(s, 2)
		response = util.recv_all(s, int.from_bytes(res_len, 'big'))
		s.close()

		return response
	
	# get current stat for /status.html
	def get_stat(self, cur_time, api):
		data = {LAST_MIN: 0,
				LAST_HOUR: 0,
				LAST_24HR: 0, 
				LIFETIME: int(cache.get('lifetime_count_eval')) if api == EVAL_API else int(cache.get('lifetime_count_time'))}
		
		# eval_stats = cache.get('eval_stats')
		# time_stats = cache.get('time_stats')

		for i in range(NUM_SECONDS_24HR):
			diff = cur_time - times[i]

			if diff < 60:
				data[LAST_MIN] += eval_stats[i] if api == EVAL_API else time_stats[i]
			if diff < 60 * 60:
				data[LAST_HOUR] += eval_stats[i] if api == EVAL_API else time_stats[i]
			if diff < NUM_SECONDS_24HR:
				data[LAST_24HR] += eval_stats[i] if api == EVAL_API else time_stats[i]
			
		return data

	# update status count per http request
	def update_status(self, url, req_timestamp):
		# print('Updating status...\r\n')
		if (url == EVAL_API):
			cache.incr('lifetime_count_eval', 1)
			# LIFE_TIME_COUNT[0] += 1
		elif (url == TIME_API):
			cache.incr('lifetime_count_time', 1)
			# LIFE_TIME_COUNT[1] += 1

		index = (req_timestamp - start_time) % NUM_SECONDS_24HR
		
		# times = cache.get('times')
		if (times[index] != req_timestamp):
			times[index] = req_timestamp
			if (url == EVAL_API): 
				eval_stats[index] = 1
				# cache.get('eval_stats')[index] = 1
			elif (url == TIME_API):
				time_stats[index] = 1
				# cache.get('time_stats')[index] = 1
		else:
			if (url == EVAL_API):
				eval_stats[index] += 1
				# cache.get('eval_stats')[index] += 1
			elif (url == TIME_API):
				time_stats[index] += 1
				# cache.get('time_stats')[index] += 1

	def handle_http(self):
		status = 200
		content_type = "text/plain"
		response = bytearray()
		req_timestamp = int(time.time()) # take a timestamp

		# print(self.path)
		if self.path in routes:
			if (self.path == EVAL_API):
				# pass req content to eval-server
				content_len = int(self.headers.get('Content-length'))
				# print(content_len)
				post_body = self.read_post_content(content_len)
				# print('post_body: ' + post_body.decode())
				self.update_status(EVAL_API, req_timestamp)
				
				# last_ten_expression = cache.get('last_ten_expressions')
				last_ten_expression.append(post_body.decode())
				if (len(last_ten_expression) > 10):
					last_ten_expression.pop(0)
				cache.set('last_ten_expression', last_ten_expression)

				if (util.validate_expression(post_body.decode())):
					response = self.process_expression(post_body)
				else:
					response = b'Invalid expression'
					status = 400
			elif (self.path == TIME_API):
				self.update_status(TIME_API, req_timestamp)
				response = util.now().encode()
			elif (self.path == STATUS_API):
				content_type = "text/html"

				eval_expression_stats = self.get_stat(req_timestamp, EVAL_API)
				get_time_stats = self.get_stat(req_timestamp, TIME_API)

				response = util.populate_html(eval_expression_stats, get_time_stats, last_ten_expression).encode()
		else:
			status = 404
			response = b'404 Not Found' 

		self.send_response(status)
		self.send_header('Content-type', content_type)
		self.send_header('Content-length', len(response))
		self.end_headers()

		return response

	def respond(self):
		content = self.handle_http()
		self.wfile.write(content)

def init_cache():
	cache = pymemcache.client.base.Client((config.CACHE_SERVER, config.CACHE_PORT))
	# start_time = int(time.time())
	# cache.set('start_time', 10)
	# cache.set('times', [0] * NUM_SECONDS_24HR) # holds timestamps indexed by time % NUM_SECONDS_24HR
	# cache.set('eval_stats', [0] * NUM_SECONDS_24HR)
	# cache.set('time_stats', [0] * NUM_SECONDS_24HR)
	cache.set('last_ten_expression', [])
	cache.set('lifetime_count_eval', 0)
	cache.set('lifetime_count_time', 0)

	return cache

s = http.server.ThreadingHTTPServer((config.WEB_API_SERVER, config.WEB_API_PORT), Handler)
print('Server started at {0}:{1}. Waiting for connection...'.format(config.WEB_API_SERVER, config.WEB_API_PORT))
cache = init_cache()

s.serve_forever()
