class PyTestException(Exception):
    pass

class utils:
    """convenience methods for use in pytests
    """

    def catch_exc(func, *arg, **kw):
        try:
            func(*arg, **kw)
        except:
            return sys.exc_info()[0]
    catch_exc = staticmethod(catch_exc)
