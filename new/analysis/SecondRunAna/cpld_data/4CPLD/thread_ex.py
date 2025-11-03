from threading import Thread
import time
def foo(bar):
    print ('hello {0}'.format(bar))
    time.sleep(2)
    return -2

def foo2(bar):
    print ('hello {0}'.format(bar))
    time.sleep(7)
    return -4

class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None
    def run(self):
        #print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                                **self._kwargs)
    def join(self, *args):
        Thread.join(self, *args)
        return self._return

twrv = ThreadWithReturnValue(target=foo, args=('world!',))
twr2 = ThreadWithReturnValue(target=foo2, args=('world!',))

twrv.start()
twr2.start()
start_time = time.time()

while(True):
    if(not twrv.is_alive()):
        print(time.time()-start_time)
        print(twrv.join())
        twrv = ThreadWithReturnValue(target=foo, args=('world!',))
        
        twrv.start()
    if(not twr2.is_alive()):
        print(time.time()-start_time)
        print(int(twr2.join()))
        twr2 = ThreadWithReturnValue(target=foo2, args=('world!',))
        twr2.start()