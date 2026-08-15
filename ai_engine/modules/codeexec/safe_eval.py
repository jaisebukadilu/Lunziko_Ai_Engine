"""Safe Evaluator (Niveau 0) — interprète un sous-ensemble d'expressions Python via l'AST.

Réellement sûr : pas d'import, pas d'appel hors liste blanche, pas d'accès attributs dunder,
pas d'I/O ni de boucles. Utile pour l'arithmétique et les transformations de données pures.
"""

from __future__ import annotations

import ast
import operator as op

_BINOPS = {
    ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv, ast.Mod: op.mod, ast.Pow: op.pow,
    ast.BitAnd: op.and_, ast.BitOr: op.or_, ast.BitXor: op.xor,
}
_UNARYOPS = {ast.UAdd: op.pos, ast.USub: op.neg, ast.Not: op.not_}
_CMPOPS = {
    ast.Eq: op.eq, ast.NotEq: op.ne, ast.Lt: op.lt, ast.LtE: op.le,
    ast.Gt: op.gt, ast.GtE: op.ge, ast.In: lambda a, b: a in b, ast.NotIn: lambda a, b: a not in b,
}
# fonctions pures autorisées
_FUNCS = {
    "len": len, "min": min, "max": max, "sum": sum, "abs": abs, "round": round,
    "sorted": sorted, "range": lambda *a: list(range(*a)), "int": int, "float": float,
    "str": str, "bool": bool, "list": list, "dict": dict, "tuple": tuple, "set": set,
    "any": any, "all": all,
}


class SafeEvalError(ValueError):
    pass


def _eval(node, names: dict):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval(node.left, names), _eval(node.right, names))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval(node.operand, names))
    if isinstance(node, ast.BoolOp):
        vals = [_eval(v, names) for v in node.values]
        return all(vals) if isinstance(node.op, ast.And) else any(vals)
    if isinstance(node, ast.Compare):
        left = _eval(node.left, names)
        for opnode, comp in zip(node.ops, node.comparators):
            right = _eval(comp, names)
            if type(opnode) not in _CMPOPS or not _CMPOPS[type(opnode)](left, right):
                return False
            left = right
        return True
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        vals = [_eval(e, names) for e in node.elts]
        return {ast.List: list, ast.Tuple: tuple, ast.Set: set}[type(node)](vals)
    if isinstance(node, ast.Dict):
        return {_eval(k, names): _eval(v, names) for k, v in zip(node.keys, node.values)}
    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        raise SafeEvalError(f"nom non autorisé: {node.id}")
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FUNCS:
            raise SafeEvalError("appel de fonction non autorisé")
        args = [_eval(a, names) for a in node.args]
        return _FUNCS[node.func.id](*args)
    if isinstance(node, ast.Subscript):
        return _eval(node.value, names)[_eval(node.slice, names)]
    if isinstance(node, ast.IfExp):
        return _eval(node.body, names) if _eval(node.test, names) else _eval(node.orelse, names)
    raise SafeEvalError(f"expression non autorisée: {type(node).__name__}")


def safe_eval(expression: str, variables: dict | None = None) -> object:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise SafeEvalError(f"syntaxe invalide: {e}")
    return _eval(tree.body, variables or {})
