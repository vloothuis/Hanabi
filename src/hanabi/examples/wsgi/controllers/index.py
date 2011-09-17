from hanabi import WSGIController


class Index(WSGIController):

    def index(self, environ, start_response):
        start_response('200 OK', ())
        return 'Index Index!'
