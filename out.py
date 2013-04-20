import sys

_stdout = sys.stdout

def set_output(my_name='Main', *writers):
    f = open('logs/%s.log' % my_name.lower(), 'a')
    my_writers = [_stdout, f]
    my_writers += writers
    sys.stdout = Output(*my_writers, name=my_name)

class Output:
    def __init__(self, *writers, **kwargs) :
        self.writers = writers
        self.name = kwargs.get('name', 'Main')
        self.line_written = False

    def write(self, text) :
        orig_written = self.line_written
        for w in self.writers :
            if text == '\n':
                try:
                    w.write(text)
                except:
                    w.write('<encoding error>')
                try:
                    w.flush()
                except:
                    pass
                self.line_written = False
            elif orig_written:
                try:
                    w.write(text)
                except:
                    w.write('<encoding error>')
            else:
                try:
                    w.write("[%s] %s" % (self.name, text))
                except:
                    w.write('<encoding error>')
                self.line_written = True

    def __del__(self):
        for w in self.writers:
            try:
                w.close()
            except:
                pass

if __name__ == '__main__':
    set_output()
    print 'testing'
