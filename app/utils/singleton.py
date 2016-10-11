class Singleton(type):

    def __init__(self, *args, **kwargs):
        self.instances = {}

    def __call__(self, *args, **kw):
        if not self.instances or args not in self.instances:
            self.instances[args] = super(Singleton, self).__call__(*args, **kw)
        return self.instances[args]

    def clear(self):
        self.instances = {}
