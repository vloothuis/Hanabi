from hanabi import WSGIController


class World(WSGIController):

    def index(self, environ, start_response):
        start_response('200 OK', ())
        return 'Hello World!'


class Index(WSGIController):

    def index(self, environ, start_response):
        start_response('200 OK', ())
        return 'Hello Index!'
