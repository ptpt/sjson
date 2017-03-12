import unittest
import sjson

class TestNumber(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq('0', 0)
        _eq('0.3', 0.3)
        _eq('0.30', 0.3)
        _eq('-12.3', -12.3)
        _eq('12e0', 12.0); _eq('12E0', 12.0)
        _eq('12.25E+3', 12250.0)
        _eq('12.5e-2', 0.125)
        _eq('12E-2', 0.12)
        _eq('0E0', 0.0)

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.Parser(a).number(True)
        _raise('12e')
        _raise('012')
        _raise('x')
        _raise('12.3x')

class TestLiterals(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq(' true ', True)
        _eq(' false ', False)
        _eq('   null ', None)

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.Parser(a).literal(True)
        _raise('False')
        _raise('True')
        _raise('Null')
        _raise('null 12')

class TestString(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq('hello', 'hello')
        _eq('"hello"', 'hello')
        _eq('""', '')
        _eq('"world\\n"', 'world\n')
        _eq('"\\nworld\\t"', '\nworld\t')

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.Parser(a).string(True)
        _raise('')
        _raise('.hello'); _raise('hello.')
        _raise(',hello'); _raise('hello,')
        _raise('hello:world'); _raise('hello:')
        _raise('hello[world'); _raise('hello]world')
        _raise('hello}world'); _raise('hello{world')
        _raise('hello"'); _raise('he"llo')
        _raise('hello"world"');

class TestArray(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq('[\t\n]', [])
        _eq('[1,hello,3,4]', [1,'hello',3,4])
        _eq('[[[[cool]]]]', [[[['cool']]]])
        _eq(
            '''
            [1,
            2, "hello[world", \t
            4,[5, [6, "NaN]"], []]]
            ''',
            [1, 2, 'hello[world', 4, [5, [6, "NaN]"], []]])

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.Parser(a).array(True)
        _raise('[1,2,3')
        _raise('[1,2,3, "]"')
        _raise('[1 2]')
        _raise('[,]')
        _raise('[a,,]')

class TestObject(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq('{}', {})
        _eq('1: {}', {'1': {}})
        _eq('true:false', {'true': False})
        _eq('hello.world: foo', {'hello': {'world': 'foo'}})
        _eq('"hello".world: \nfoo hello.world: 1', {'hello': {'world': 1}})
        _eq('hello."world": "foo" hello:1', {'hello': 1})
        _eq('hello.world: foo hello: " :1:" ', {'hello': " :1:"})
        _eq('"":""', {'': ''})
        _eq('"hel\\nlo":  {foo.bar: 1 bar.foo:2}',
            {'hel\nlo': {'foo': {'bar': 1}, 'bar': {'foo': 2}}})

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.Parser(a).object(True)
        _raise('')
        _raise('hello')
        _raise('hello{}')
        _raise('hello:{1,2,3}')
        _raise(':1'); _raise('h:')
        _raise('hello:world,foo:bar')
        _raise('hell".wolrd":world')
        _raise('hello world')

class TestValue(unittest.TestCase):
    def test_simple(self):
        def _eq(a, b):
            self.assertEqual(sjson.loads(a), b)
        _eq(
            '''
            [1e3,
            "foo".bar:  2      null.false:3,
            "": "hello world",
            false ,
            true,
            null
            ]
            ''',
            [1000,
             {'foo': {'bar': 2}, 'null': {'false': 3}},
             {'': 'hello world'},
             False, True, None])
        _eq(
            '''
            "foo bar".hello: [
            a: 1 b: 2
            ]
            "foo bar".world: [
            c: 2, c: 4
            ]
            ''',
            {
                'foo bar': {
                    'hello': [
                        {'a': 1, 'b': 2}
                    ],
                    'world': [
                        {'c': 2},
                        {'c': 4}
                    ]
                }
            })

    def test_failure(self):
        def _raise(a):
            with self.assertRaises(sjson.ParseError):
                sjson.loads(a)
        _raise('hello world')
