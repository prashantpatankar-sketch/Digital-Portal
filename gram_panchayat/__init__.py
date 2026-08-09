import pymysql

pymysql.install_as_MySQLdb()

# Python 3.14 compatibility patch for Django Template Context copy
try:
    import copy
    from django.template.context import Context

    def _context_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    Context.__copy__ = _context_copy
except Exception:
    pass

