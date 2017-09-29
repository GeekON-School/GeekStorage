import os
import uuid
import tornado.ioloop
import tornado.web
import json
import tornado.template

class MainHandler (tornado.web.RequestHandler):
	def get(self):
		self.render("home.html")
	def post(self):
		if 'file' in self.request.files:
			file = self.request.files['file'][0]
			file_name = file['filename']
			extension = os.path.splitext(file_name)[1]
			finalName = str(uuid.uuid4()) + str(extension)
			with open('images/' + finalName, 'wb') as f:
				f.write(file['body'])
			file_url = ' storage.geekclass.ru/' + finalName
			self.write(file_url)


settings = [
    (r'/', MainHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': 'static'}),
    (r'/images/(.*)', tornado.web.StaticFileHandler, {'path': 'images'}),
]
app = tornado.web.Application(settings)
app.listen(8888)
tornado.ioloop.IOLoop.current().start()