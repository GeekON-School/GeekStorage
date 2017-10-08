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
			file_path_small = os.path.join(os.path.dirname(os.path.realpath(__file__)),
							     'images')
			file_path = os.path.join (file_path_small,finalName)
			with open(file_path, 'wb') as f:
				f.write(file['body'])
			direct_url = 'https://storage.geekclass.ru/images/' + finalName
			markdown_url = '![](https://storage.geekclass.ru/images/'+ finalName + ')'
			html_url =  '<img src="https://storage.geekclass.ru/images/"'+finalName+'/>'
			data ={"direct":direct_url, "markdown": markdown_url, "html" : html_url}
			self.write(json.dumps(data))


settings = [
    (r'/', MainHandler),
    (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(os.path.realpath(__file__)),'static')}),
    (r'/images/(.*)', tornado.web.StaticFileHandler, {'path': os.path.join(os.path.dirname(os.path.realpath(__file__)),'images')}),
]
app = tornado.web.Application(settings)
app.listen(8083)
tornado.ioloop.IOLoop.current().start()