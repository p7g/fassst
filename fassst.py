import ast
import dis
import functools
import inspect
import textwrap
import types
import typing


class InlineFor(ast.NodeTransformer):
    def __init__(self, code, filename):
        self.code = code
        self.filename = filename
        super()

    def visit_For(self, node):
        def is_pure(node):
            # TODO
            return True

        if not is_pure(node.iter):
            return node

        iter_code = ast.get_source_segment(self.code, node.iter)
        target_code = ast.get_source_segment(self.code, node.target)
        new_code = ""
        for x in eval(iter_code):
            new_code += f"{target_code} = {repr(x)}\n"
            for l in node.body:
                new_code += ast.get_source_segment(self.code, l) + "\n"
        new_ast = ast.parse(new_code, filename=self.filename)
        return new_ast.body


def fast(fn):
    code = fn.__code__
    # bcode = dis.dis(code)
    src = textwrap.dedent(inspect.getsource(fn))
    tree = ast.parse(src)

    # Before
    # print(ast.dump(tree, indent=2))

    new_tree = InlineFor(src, code.co_filename).visit(tree)

    # After
    # print(ast.dump(new_tree.body[0], indent=2))
    new_code = compile(new_tree, filename=code.co_filename, mode="exec")
    new_fn_code = new_code.co_consts[0]

    # Return a new function to leave the original unaltered.
    args = [
        new_fn_code.co_argcount,
        new_fn_code.co_nlocals,
        new_fn_code.co_stacksize,
        new_fn_code.co_flags,
        new_fn_code.co_code,
        new_fn_code.co_consts,
        new_fn_code.co_names,
        new_fn_code.co_varnames,
        new_fn_code.co_filename,
        new_fn_code.co_name,
        new_fn_code.co_firstlineno,
        new_fn_code.co_lnotab,
        new_fn_code.co_freevars,
        new_fn_code.co_cellvars,
    ]
    try:
        args.insert(1, new_fn_code.co_kwonlyargcount)  # Py3
        args.insert(1, new_fn_code.co_posonlyargcount)  # Py38+
    except AttributeError:
        pass

    return functools.update_wrapper(
        types.FunctionType(
            types.CodeType(*args),
            fn.__globals__,
            fn.__name__,
            fn.__defaults__,
            fn.__closure__,
        ),
        fn,
    )