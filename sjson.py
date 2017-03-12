__all__ = ['ParseError' 'Parser', 'loads']
__author__ = 'Tao Peng'

import functools
import json
import re

_FLAGS = re.VERBOSE | re.MULTILINE
_c = functools.partial(re.compile, flags=_FLAGS)
_RE_WHITESPACE = _c(r'[ \t\n\r]*')
_ws = lambda p: _RE_WHITESPACE.pattern + p + _RE_WHITESPACE.pattern
_wc = lambda p: _c(_ws(p))
_ewc = lambda p: _wc(re.escape(p))

_RE_BEGIN_ARRAY, _RE_END_ARRAY = _ewc('['), _ewc(']')
_RE_BEGIN_OBJECT, _RE_END_OBJECT = _ewc('{'), _ewc('}')

_RE_PATH_SEP = _ewc(':')
_RE_SEGMENT_SEP = _c(re.escape('.'))
_RE_VALUE_SEP = _ewc(',')

_RE_LITERALS = _wc(r'(true|false|null)')
_RE_NUMBER = _wc(r'''
(-?                              # [minus]
(?:0|[1-9][0-9]*)                # int
(?:\.[0-9]+)?                    # [frac]
(?:[eE][-+]?[0-9]+)?)            # [exp]
''')
_RE_SEGMENT = _c(r'([^",.:\[\]\{\} \t\n\r]+)')
_RE_QUOTED_SEGMENT = _c(r'("(?:[^"\\]|\\.)*")')
_RE_EOF = _c(r'\Z')

class ParseError(Exception):
    pass

class ParseResult(list):
    pass

_IgnoredResult = object()

def _merge_members(members):
    root = {}
    for path, value in members:
        obj = root
        for i, segment in enumerate(path):
            if i == len(path) - 1:
                obj[segment] = value
            else:
                new_obj = obj.setdefault(segment, {})
                if not isinstance(new_obj, dict):
                    new_obj = obj[segment] = {}
                obj = new_obj
    return root

def _agg(acc, res):
    if res is _IgnoredResult:
        return acc
    if isinstance(res, ParseResult):
        acc += res
    else:
        acc.append(res)
    return acc

class Parser(object):
    def __init__(self, s):
        self._s = s
        self._at = 0

    def _seq(self, *parsers):
        at = self._at
        try:
            res = functools.reduce(_agg, (p() for p in parsers), ParseResult())
        except ParseError as err:
            self._at = at
            raise err
        assert isinstance(res, ParseResult)
        return res

    def _rec(self, *parsers):
        res = ParseResult()
        while True:
            at = self._at
            try:
                res += self._seq(*parsers)
            except ParseError:
                self._at = at
                break
        assert isinstance(res, ParseResult)
        return res

    def _opt(self, *parsers):
        try:
            return self._seq(*parsers)
        except ParseError:
            return ParseResult()

    def _alt(self, *parsers):
        last_err = None
        for parser in parsers:
            try:
                ret = parser()
                if ret is not _IgnoredResult:
                    return ret
            except ParseError as err:
                last_err = err
        if last_err:
            raise last_err
        raise RuntimeError('require at least one parser without result ignored')

    def _expect(self, regex, message=None):
        if message is None:
            message = 'expect {0}'.format(regex.pattern)
        match = regex.match(self._s, self._at)
        if not match:
            raise ParseError(message)
        self._at = match.end()
        return match

    def expect(self, regex):
        self._expect(regex)
        return _IgnoredResult

    def literal(self, top=False):
        """literal = true | false | null"""
        if top:
            return self._top(self.literal)
        match = self._expect(_RE_LITERALS, 'expect true | false | null')
        literal = match.group(1)
        if literal == 'true':
            return True
        elif literal == 'false':
            return False
        else:
            assert literal == 'null'
            return None

    def number(self, top=False):
        """number = [ minus ] int [ frac ] [ exp ]"""
        if top:
            return self._top(self.number)
        match = self._expect(_RE_NUMBER, 'expect number')
        return json.loads(match.group(1))

    def _quoted_segment(self):
        """
        quoted_segment = quotation_mark *quoted_char quotation_mark
        quoted_char = char / (escape char)
        """
        match = self._expect(_RE_QUOTED_SEGMENT, 'expect quoted segment')
        return json.loads(match.group(1))

    def _unquoted_segment(self):
        """unquoted_segment = *unquoted_char"""
        return self._expect(_RE_SEGMENT, 'expect unquoted segment').group(1)

    def _segment(self):
        """segment = quoted_segment | unquoted_segment"""
        return self._alt(self._quoted_segment, self._unquoted_segment)

    def string(self, top=False):
        """string = [ws] (quoted_segment | unquoted_segment) [ws]"""
        if top:
            return self._top(self.string)
        return self._seq(
            lambda: self.expect(_RE_WHITESPACE),
            lambda: self._alt(self._quoted_segment, self._unquoted_segment),
            lambda: self.expect(_RE_WHITESPACE))[0]

    def path(self):
        """path = string *(segment_separator string)"""
        return tuple(self._seq(
            self._segment,
            lambda: self._rec(lambda: self.expect(_RE_SEGMENT_SEP), self._segment)))

    def member(self):
        """member = path path_separator value"""
        return tuple(self._seq(
            lambda: self.expect(_RE_WHITESPACE),
            self.path,
            lambda: self.expect(_RE_PATH_SEP),
            self.value))

    def object(self, top=False):
        """object = [begin_object] *member [end_object]"""
        if top:
            return self._top(self.array)
        p1 = lambda: self._seq(
            lambda: self.expect(_RE_BEGIN_OBJECT),
            lambda: self._rec(self.member),
            lambda: self.expect(_RE_END_OBJECT))
        p2 = lambda: self._seq(self.member, lambda: self._rec(self.member))
        return _merge_members(self._alt(p1, p2))

    def array(self, top=False):
        """array = begin_array [value *(value_separator value)] end_array"""
        if top:
            return self._top(self.array)
        return list(self._seq(
            lambda: self.expect(_RE_BEGIN_ARRAY),
            lambda: self._opt(
                self.value,
                lambda: self._rec(lambda: self.expect(_RE_VALUE_SEP), self.value)),
            lambda: self.expect(_RE_END_ARRAY)))

    def value(self, top=False):
        """value = object | array | literal | number | string"""
        if top:
            return self._top(self.value)
        return self._alt(self.object, self.literal, self.number, self.array, self.string)

    def _top(self, parser):
        """top_parser = parser eof"""
        self._at = 0
        return self._seq(parser, lambda: self.expect(_RE_WHITESPACE), lambda: self.expect(_RE_EOF))[0]

def loads(s):
    return Parser(s).value(True)

if __name__ == '__main__':
    import sys
    argv = sys.argv[1:]
    s = ' '.join(argv) if argv else sys.stdin.read()
    print(json.dumps(loads(s)))
