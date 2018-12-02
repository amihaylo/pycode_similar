import sys
import ast
import difflib
import operator
import argparse
import itertools
import collections
import json
import itertools

def get_file(value):
    return open(value, 'rb')

def save_json_file(json_data):
    with open(args.o, 'w') as outfile:
        json.dump(json_data, outfile, indent=4)

def check_line_limit(value):
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid line limit" % value)
    return ivalue

def check_percentage_limit(value):
    ivalue = float(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("%s is an invalid percentage limit" % value)
    return ivalue


class FuncNodeCollector(ast.NodeTransformer):
    """
    Clean node attributes, delete the attributes that are not helpful for recognition repetition.
    Then collect all function nodes.
    """

    def __init__(self):
        super(FuncNodeCollector, self).__init__()
        self._curr_class_names = []
        self._func_nodes = []
        self._last_node_lineno = -1
        self._node_count = 0

    @staticmethod
    def _mark_docstring_sub_nodes(node):
        """
        Inspired by ast.get_docstring, mark all docstring sub nodes.

        Case1:
        regular docstring of function/class/module

        Case2:
        def foo(self):
            '''pure string expression'''
            for x in self.contents:
                '''pure string expression'''
                print x
            if self.abc:
                '''pure string expression'''
                pass

        Case3:
        def foo(self):
            if self.abc:
                print('ok')
            else:
                '''pure string expression'''
                pass

        :param node: every ast node
        :return:
        """

        def _mark_docstring_nodes(body):
            if body and isinstance(body, collections.Sequence):
                for n in body:
                    if isinstance(n, ast.Expr) and isinstance(n.value, ast.Str):
                        n.is_docstring = True

        node_body = getattr(node, 'body', None)
        _mark_docstring_nodes(node_body)
        node_orelse = getattr(node, 'orelse', None)
        _mark_docstring_nodes(node_orelse)

    @staticmethod
    def _is_docstring(node):
        return getattr(node, 'is_docstring', False)

    def generic_visit(self, node):
        self._node_count = self._node_count + 1
        self._last_node_lineno = max(getattr(node, 'lineno', -1), self._last_node_lineno)
        self._mark_docstring_sub_nodes(node)
        return super(FuncNodeCollector, self).generic_visit(node)

    def visit_Str(self, node):
        del node.s
        self.generic_visit(node)
        return node

    def visit_Expr(self, node):
        if not self._is_docstring(node):
            self.generic_visit(node)
            if hasattr(node, 'value'):
                return node

    def visit_arg(self, node):
        """
        remove arg name & annotation for python3
        :param node: ast.arg
        :return:
        """
        del node.arg
        del node.annotation
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        del node.id
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Attribute(self, node):
        del node.attr
        del node.ctx
        self.generic_visit(node)
        return node

    def visit_Call(self, node):
        func = getattr(node, 'func', None)
        if func and isinstance(func, ast.Name) and func.id == 'print':
            return  # remove print call and its sub nodes for python3
        return node

    def visit_ClassDef(self, node):
        self._curr_class_names.append(node.name)
        self.generic_visit(node)
        self._curr_class_names.pop()
        return node

    def visit_FunctionDef(self, node):
        node.name = '.'.join(itertools.chain(self._curr_class_names, [node.name]))
        self._func_nodes.append(node)
        count = self._node_count
        self.generic_visit(node)
        node.endlineno = self._last_node_lineno
        node.nsubnodes = self._node_count - count
        return node

    def visit_Compare(self, node):

        def _simple_nomalize(*ops_type_names):
            if node.ops and len(node.ops) == 1 and type(node.ops[0]).__name__ in ops_type_names:
                if node.left and node.comparators and len(node.comparators) == 1:
                    left, right = node.left, node.comparators[0]
                    if type(left).__name__ > type(right).__name__:
                        left, right = right, left
                        node.left = left
                        node.comparators = [right]
                        return True
            return False

        if _simple_nomalize('Eq'):
            pass

        if _simple_nomalize('Gt', 'Lt'):
            node.ops = [{ast.Lt: ast.Gt, ast.Gt: ast.Lt}[type(node.ops[0])]()]

        if _simple_nomalize('GtE', 'LtE'):
            node.ops = [{ast.LtE: ast.GtE, ast.GtE: ast.LtE}[type(node.ops[0])]()]

        self.generic_visit(node)
        return node

    def visit_Print(self, node):
        # remove print expr for python2
        pass

    def clear(self):
        self._func_nodes = []

    def get_function_nodes(self):
        return self._func_nodes


class FuncInfo(object):
    """
    Part of the astor library for Python AST manipulation.

    License: 3-clause BSD

    Copyright 2012 (c) Patrick Maupin
    Copyright 2013 (c) Berker Peksag

    """

    class NonExistent(object):
        pass

    def __init__(self, func_node, code_lines):
        assert isinstance(func_node, ast.FunctionDef)
        self._func_node = func_node
        self._code_lines = code_lines
        self._func_name = func_node.__dict__.pop('name', '')
        self._func_code = None
        self._func_code_lines = None
        self._func_ast = None
        self._func_ast_lines = None

    def __str__(self):
        return '<' + type(self).__name__ + ': ' + self.func_name + '>'

    @property
    def func_name(self):
        return self._func_name

    @property
    def func_node(self):
        return self._func_node

    @property
    def func_code(self):
        if self._func_code is None:
            self._func_code = ''.join(self.func_code_lines)
        return self._func_code

    @property
    def func_code_lines(self):
        if self._func_code_lines is None:
            self._func_code_lines = self._retrieve_func_code_lines(self._func_node, self._code_lines)
        return self._func_code_lines

    @property
    def func_ast(self):
        if self._func_ast is None:
            self._func_ast = self._dump(self._func_node)
        return self._func_ast

    @property
    def func_ast_lines(self):
        if self._func_ast_lines is None:
            self._func_ast_lines = self.func_ast.splitlines(True)
        return self._func_ast_lines

    @staticmethod
    def _retrieve_func_code_lines(func_node, code_lines):
        if not isinstance(func_node, ast.FunctionDef):
            return []
        if not isinstance(code_lines, collections.Sequence) or isinstance(code_lines, basestring):
            return []
        if getattr(func_node, 'endlineno', -1) < getattr(func_node, 'lineno', 0):
            return []
        lines = code_lines[func_node.lineno - 1: func_node.endlineno]
        if lines:
            padding = lines[0][:-len(lines[0].lstrip())]
            stripped_lines = []
            for l in lines:
                if l.startswith(padding):
                    stripped_lines.append(l[len(padding):])
                else:
                    stripped_lines = []
                    break
            if stripped_lines:
                return stripped_lines
        return lines

    @staticmethod
    def _iter_node(node, name='', missing=NonExistent):
        """Iterates over an object:

           - If the object has a _fields attribute,
             it gets attributes in the order of this
             and returns name, value pairs.

           - Otherwise, if the object is a list instance,
             it returns name, value pairs for each item
             in the list, where the name is passed into
             this function (defaults to blank).

        """
        fields = getattr(node, '_fields', None)
        if fields is not None:
            for name in fields:
                value = getattr(node, name, missing)
                if value is not missing:
                    yield value, name
        elif isinstance(node, list):
            for value in node:
                yield value, name

    @staticmethod
    def _dump(node, name=None, initial_indent='', indentation='    ',
              maxline=120, maxmerged=80, special=ast.AST):
        """Dumps an AST or similar structure:

           - Pretty-prints with indentation
           - Doesn't print line/column/ctx info

        """

        def _inner_dump(node, name=None, indent=''):
            level = indent + indentation
            name = name and name + '=' or ''
            values = list(FuncInfo._iter_node(node))
            if isinstance(node, list):
                prefix, suffix = '%s[' % name, ']'
            elif values:
                prefix, suffix = '%s%s(' % (name, type(node).__name__), ')'
            elif isinstance(node, special):
                prefix, suffix = name + type(node).__name__, ''
            else:
                return '%s%s' % (name, repr(node))
            node = [_inner_dump(a, b, level) for a, b in values if b != 'ctx']
            oneline = '%s%s%s' % (prefix, ', '.join(node), suffix)
            if len(oneline) + len(indent) < maxline:
                return '%s' % oneline
            if node and len(prefix) + len(node[0]) < maxmerged:
                prefix = '%s%s,' % (prefix, node.pop(0))
            node = (',\n%s' % level).join(node).lstrip()
            return '%s\n%s%s%s' % (prefix, level, node, suffix)

        return _inner_dump(node, name, initial_indent)


class ArgParser(argparse.ArgumentParser):
    """
    A simple ArgumentParser to print help when got error.
    """

    def error(self, message):
        self.print_help()
        from gettext import gettext as _

        self.exit(2, _('\n%s: error: %s\n') % (self.prog, message))


class FuncDiffInfo(object):
    """
    An object stores the result of candidate python code compared to referenced python code.
    """

    info_ref = None
    info_candidate = None
    plagiarism_count = 0
    total_count = 0

    @property
    def plagiarism_percent(self):
        return 0 if self.total_count == 0 else (self.plagiarism_count / float(self.total_count))

    def __str__(self):
        if isinstance(self.info_ref, FuncInfo) and isinstance(self.info_candidate, FuncInfo):
            return '{:<4.2}: ref {}, candidate {}'.format(self.plagiarism_percent,
                                                          self.info_ref.func_name + '<' + str(
                                                              self.info_ref.func_node.lineno) + ':' + str(
                                                              self.info_ref.func_node.col_offset) + '>',
                                                          self.info_candidate.func_name + '<' + str(
                                                              self.info_candidate.func_node.lineno) + ':' + str(
                                                              self.info_candidate.func_node.col_offset) + '>')
        return '{:<4.2}: ref {}, candidate {}'.format(0, None, None)


class UnifiedDiff(object):
    """
    Line diff algorithm to formatted AST string lines, naive but efficiency, result is good enough.
    """

    @staticmethod
    def diff(a, b):
        """
        Simpler and faster implementation of difflib.unified_diff.
        """
        assert a is not None
        assert b is not None
        a = a.func_ast_lines
        b = b.func_ast_lines

        def _gen():
            for group in difflib.SequenceMatcher(None, a, b).get_grouped_opcodes(0):
                for tag, i1, i2, j1, j2 in group:
                    if tag == 'equal':
                        for line in a[i1:i2]:
                            yield ''
                        continue
                    if tag in ('replace', 'delete'):
                        for line in a[i1:i2]:
                            yield '-'
                    if tag in ('replace', 'insert'):
                        for line in b[j1:j2]:
                            yield '+'

        return collections.Counter(_gen())['-']

    @staticmethod
    def total(a, b):
        assert a is not None  # b may be None
        return len(a.func_ast_lines)


class TreeDiff(object):
    """
    Tree edit distance algorithm to AST, very slow and the result is not good for small functions.
    """

    @staticmethod
    def diff(a, b):
        assert a is not None
        assert b is not None

        def _str_dist(i, j):
            return 0 if i == j else 1

        def _get_label(n):
            return type(n).__name__

        def _get_children(n):
            if not hasattr(n, 'children'):
                n.children = list(ast.iter_child_nodes(n))
            return n.children

        import zss
        res = zss.distance(a.func_node, b.func_node, _get_children,
                           lambda node: 0,  # insert cost
                           lambda node: _str_dist(_get_label(node), ''),  # remove cost
                           lambda _a, _b: _str_dist(_get_label(_a), _get_label(_b)), )  # update cost
        return res

    @staticmethod
    def total(a, b):
        #  The count of AST nodes in referenced function
        assert a is not None  # b may be None
        return a.func_node.nsubnodes


class NoFuncException(Exception):
    def __init__(self, source):
        super(NoFuncException, self).__init__('Can not find any functions from code, index = {}'.format(source))
        self.source = source


class ArgParser(argparse.ArgumentParser):
    """
    A simple ArgumentParser to print help when got error.
    """

    def error(self, message):
        self.print_help()
        from gettext import gettext as _

        self.exit(2, _('\n%s: error: %s\n') % (self.prog, message))

def compare_files(file1, file2, diff_method=UnifiedDiff):
    #returns:
    #         False if it is a syntax Error
    #         The object if both files are parsable
    
    debug_msg = "Processing {} & {}".format(file1, file2) + "..."
    filename_list = [file1, file2]
    func_info_list = list()
    for filename in filename_list:
        with open(filename) as file:
            code_str = file.read()
            try:
                root_node = ast.parse(code_str)
            except SyntaxError as ex:
                if args.d: print(debug_msg + "Syntax Error [{}]".format(filename))
                return False
            collector = FuncNodeCollector()
            collector.visit(root_node)
            code_utf8_lines = code_str.splitlines(True)
            func_info = [FuncInfo(n, code_utf8_lines) for n in collector.get_function_nodes()]
            func_info_list.append(func_info)

    #Compare the files
    func_ast_diff_list = []
    func_info_ref = func_info_list[0]
    func_info_candidate = func_info_list[1]
    for fi1 in func_info_ref:
        min_diff_value = int((1 << 31) - 1)
        min_diff_func_info = None
        for fi2 in func_info_candidate:
            dv = diff_method.diff(fi1, fi2)
            if dv < min_diff_value:
                min_diff_value = dv
                min_diff_func_info = fi2
            if dv == 0:  # entire function structure is plagiarized by candidate
                break

        func_diff_info = FuncDiffInfo()
        func_diff_info.info_ref = fi1
        func_diff_info.info_candidate = min_diff_func_info
        func_diff_info.total_count = diff_method.total(fi1, min_diff_func_info)
        func_diff_info.plagiarism_count = func_diff_info.total_count - min_diff_value if min_diff_func_info else 0
        func_ast_diff_list.append(func_diff_info)
    func_ast_diff_list.sort(key=operator.attrgetter('plagiarism_percent'), reverse=True)
            
    #Successfully proessed both files
    if args.d: print(debug_msg + "Success!")
    return func_ast_diff_list
    # return [{"SUCESS":"True"}]

def jsonify(file1, file2, raw_result):
    curr_result = {}
    curr_result["ref"] = file1
    curr_result["candidate"] = file2
    curr_result["plagiarism_count"] = sum(func_diff_info.plagiarism_count for func_diff_info in raw_result)
    curr_result["total_count"] = sum(func_diff_info.total_count for func_diff_info in raw_result)
    curr_result["percent_plagiarized"] = curr_result["plagiarism_count"] / curr_result["total_count"]
    curr_result["AST_lower_bound"] = args.l
    curr_result["PLAG_lower_bound"] = args.p
    curr_result["diff_list"] = list()

    for func_diff_info in raw_result:
        if len(func_diff_info.info_ref.func_ast_lines) >= args.l and func_diff_info.plagiarism_percent >= args.p:
            curr_func = {}
            curr_func["percent_plagiarized"] = func_diff_info.plagiarism_percent
            curr_func["ref_func"] = {
                "name": func_diff_info.info_ref.func_name,
                "line": func_diff_info.info_ref.func_node.lineno,
                "col":func_diff_info.info_ref.func_node.col_offset

            }
            curr_func["candidate_func"] = {
                "name": func_diff_info.info_candidate.func_name,
                "line": func_diff_info.info_candidate.func_node.lineno,
                "col":func_diff_info.info_candidate.func_node.col_offset

            }
            curr_result["diff_list"].append(str(func_diff_info))
            # curr_result["diff_list"].append(curr_func) # Uncomment to have everything in nice json format        
    return curr_result


def run_batch(filename_list):
    results = {
        "configuration": {
            "files": filename_list,
            "PLAG_lower_bound": args.c,
            "func_PLAG_lower_bound": args.p,
            "func_AST_lower_bound": args.l
        },
        "detected": list()
    }

    combinations = itertools.combinations(filename_list, 2)
    for files_tuple in combinations:
        #Create combinations of all the files
        file1 = files_tuple[0]
        file2 = files_tuple[1]
        # all_results.append(compare_files(file1, file2))
        raw_result = compare_files(file1, file2)
        if raw_result:
            json_result = jsonify(file1, file2, raw_result)
            if json_result["percent_plagiarized"] >= args.c:        
                results["detected"].append(json_result)        

    return results
    

if __name__ == "__main__":
    print("---------PYCODE SIMILAR---------")
    parser = ArgParser(description='Checks for similarity in code')
    parser.add_argument('files', nargs='+', help='The input files')
    parser.add_argument('-c', type=check_percentage_limit, default=0.5, help='The total plagiarism cutoff percent (default: 0.5)')
    parser.add_argument('-l', type=check_line_limit, default=4, help='if AST line of the function >= value then output detail (default: 4)')
    parser.add_argument('-p', type=check_percentage_limit, default=0.5, help='if plagiarism percentage of the function >= value then output detail (default: 0.5)')
    parser.add_argument('-o', type=str, default="./results.out", help='File where results will be output (default: ./results.out)')
    parser.add_argument('-d', action='store_true', help='Turn debug mode on')
    args = parser.parse_args()

    #Ensure that 2 or more files are supplied
    if len(args.files) < 2:
        parser.error("Must supply 2 or more files")

    #Run the batch
    results = run_batch(args.files)
    #Save the results to the outfile
    save_json_file(results)

    print("DONE!")