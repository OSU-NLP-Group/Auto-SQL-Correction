CLAUSE_KEYWORDS = ('select', 'from', 'where', 'group', 'having', 'order', 'limit', 'intersect', 'union', 'except')
JOIN_KEYWORDS = ('join', 'on', 'as')

WHERE_OPS = ('not', 'between', '=', '>', '<', '>=', '<=', '!=', 'in', 'like', 'is', 'exists')
AGG_OPS = ('max', 'min', 'count', 'sum', 'avg')
AGG_OPS_PY = {'func.max': 'max', 'func.min': 'min', 'func.count': 'count', 'func.sum': 'sum', 'func.avg': 'avg'}
UNIT_OPS = ('-', '+', "*", '/')
ORDER_OPS = ('desc', 'asc')

class ASTNode:
    def __init__(self):
        Exception("Not Implemented")

    def parse_sql(self):
        Exception("Not Implemented")

    def parse_python(self):
        Exception("Not Implemented")

    def print_sql(self):
        Exception("Not Implemented")

    def print_python(self):
        Exception("Not Implemented")