from functools import wraps
import time

def retry(ExceptionToCheck=Exception, tries=2, delay=1, backoff=1, logger=None):
    '''Retry calling the decorated function using an exponential backoff.'''
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            '''
            # also can change the value of tries and delay by kwargs in your method
            @retry()
            def div(a, b, **kwargs):
                a / b
            print div(1, 0, tries=5)
            '''
            mtries = tries if not kwargs.has_key('tries') else kwargs.get('tries')
            mdelay = delay if not kwargs.has_key('delay') else kwargs.get('delay')
            mbackoff = backoff if not kwargs.has_key('backoff') else kwargs.get('backoff')
            log = logger if not kwargs.has_key('logger') else kwargs.get('logger')
            
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "Failed to execute %s: %s, Retrying in %d seconds..." % (f.__name__, str(e), mdelay)
                    if log:
                        log.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= mbackoff
            if try_one_last_time:
                try:
                    return f(*args, **kwargs)
                except Exception, e:
                    msg = "Failed to execute %s: %s" % (f.__name__, str(e))
                    if log:
                        log.warning(msg)
                    else:
                        print msg
            return
        return f_retry  # true decorator
    return deco_retry

def synchronized(lock):
    """
    Decorator to synchronize several methods with a given lock
    """
    def wrapper(f):
        @wraps(f)
        def sync(*args, **kwargs):
            with lock:
                return f(*args, **kwargs)
        return sync
    return wrapper  

@retry()
def div(a, b, **kwargs):
    a / b
    
# print div(1, 0, tries=5)
