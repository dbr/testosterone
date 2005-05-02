def catch_exc(func, *arg, **kw):
    try:
        func(*arg, **kw)
    except:
        return sys.exc_info()[0]
