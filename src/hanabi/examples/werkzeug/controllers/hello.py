from hanabi import Controller


class World(Controller):

    def index(self, request):
        return 'Hello World!'

class Index(Controller):

    def index(self, request):
        return 'Hello Index!'
