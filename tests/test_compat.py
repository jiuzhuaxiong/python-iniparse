# Copyright (c) 2001, 2002, 2003 Python Software Foundation
# Copyright (c) 2004 Paramjit Oberoi <param.cs.wisc.edu>
# All Rights Reserved.  See LICENSE-PSF & LICENSE for details.

import ConfigParser
import StringIO
import unittest

import cfgparse.compat

from test import test_support


class TestCaseBase(unittest.TestCase):
    def newconfig(self, defaults=None):
        if defaults is None:
            self.cf = self.config_class()
        else:
            self.cf = self.config_class(defaults)
        return self.cf

    def fromstring(self, string, defaults=None):
        cf = self.newconfig(defaults)
        sio = StringIO.StringIO(string)
        cf.readfp(sio)
        return cf

    def test_basic(self):
        cf = self.fromstring(
            "[Foo Bar]\n"
            "foo=bar\n"
            "[Spacey Bar]\n"
            "foo = bar\n"
            "[Commented Bar]\n"
            "foo: bar ; comment\n"
            "[Long Line]\n"
            "foo: this line is much, much longer than my editor\n"
            "   likes it.\n"
            "[Section\\with$weird%characters[\t]\n"
            "[Internationalized Stuff]\n"
            "foo[bg]: Bulgarian\n"
            "foo=Default\n"
            "foo[en]=English\n"
            "foo[de]=Deutsch\n"
            "[Spaces]\n"
            "key with spaces : value\n"
            "another with spaces = splat!\n"
            )
        L = cf.sections()
        L.sort()
        eq = self.assertEqual
        eq(L, [r'Commented Bar',
               r'Foo Bar',
               r'Internationalized Stuff',
               r'Long Line',
               r'Section\with$weird%characters[' '\t',
               r'Spaces',
               r'Spacey Bar',
               ])

        # The use of spaces in the section names serves as a
        # regression test for SourceForge bug #583248:
        # http://www.python.org/sf/583248
        eq(cf.get('Foo Bar', 'foo'), 'bar')
        eq(cf.get('Spacey Bar', 'foo'), 'bar')
        eq(cf.get('Commented Bar', 'foo'), 'bar')
        eq(cf.get('Spaces', 'key with spaces'), 'value')
        eq(cf.get('Spaces', 'another with spaces'), 'splat!')

        self.failIf('__name__' in cf.options("Foo Bar"),
                    '__name__ "option" should not be exposed by the API!')

        # Make sure the right things happen for remove_option();
        # added to include check for SourceForge bug #123324:
        self.failUnless(cf.remove_option('Foo Bar', 'foo'),
                        "remove_option() failed to report existance of option")
        self.failIf(cf.has_option('Foo Bar', 'foo'),
                    "remove_option() failed to remove option")
        self.failIf(cf.remove_option('Foo Bar', 'foo'),
                    "remove_option() failed to report non-existance of option"
                    " that was removed")

        self.assertRaises(ConfigParser.NoSectionError,
                          cf.remove_option, 'No Such Section', 'foo')

        eq(cf.get('Long Line', 'foo'),
           'this line is much, much longer than my editor\nlikes it.')

    def test_case_sensitivity(self):
        cf = self.newconfig()
        cf.add_section("A")
        cf.add_section("a")
        L = cf.sections()
        L.sort()
        eq = self.assertEqual
        eq(L, ["A", "a"])
        cf.set("a", "B", "value")
        eq(cf.options("a"), ["b"])
        eq(cf.get("a", "b"), "value",
           "could not locate option, expecting case-insensitive option names")
        self.failUnless(cf.has_option("a", "b"))
        cf.set("A", "A-B", "A-B value")
        for opt in ("a-b", "A-b", "a-B", "A-B"):
            self.failUnless(
                cf.has_option("A", opt),
                "has_option() returned false for option which should exist")
        eq(cf.options("A"), ["a-b"])
        eq(cf.options("a"), ["b"])
        cf.remove_option("a", "B")
        eq(cf.options("a"), [])

        # SF bug #432369:
        cf = self.fromstring(
            "[MySection]\nOption: first line\n\tsecond line\n")
        eq(cf.options("MySection"), ["option"])
        eq(cf.get("MySection", "Option"), "first line\nsecond line")

        # SF bug #561822:
        cf = self.fromstring("[section]\nnekey=nevalue\n",
                             defaults={"key":"value"})
        self.failUnless(cf.has_option("section", "Key"))


    def test_parse_errors(self):
        self.newconfig()
        self.parse_error(ConfigParser.ParsingError,
                         "[Foo]\n  extra-spaces: splat\n")
        self.parse_error(ConfigParser.ParsingError,
                         "[Foo]\n  extra-spaces= splat\n")
        self.parse_error(ConfigParser.ParsingError,
                         "[Foo]\noption-without-value\n")
        self.parse_error(ConfigParser.ParsingError,
                         "[Foo]\n:value-without-option-name\n")
        self.parse_error(ConfigParser.ParsingError,
                         "[Foo]\n=value-without-option-name\n")
        self.parse_error(ConfigParser.MissingSectionHeaderError,
                         "No Section!\n")

    def parse_error(self, exc, src):
        sio = StringIO.StringIO(src)
        self.assertRaises(exc, self.cf.readfp, sio)

    def test_query_errors(self):
        cf = self.newconfig()
        self.assertEqual(cf.sections(), [],
                         "new ConfigParser should have no defined sections")
        self.failIf(cf.has_section("Foo"),
                    "new ConfigParser should have no acknowledged sections")
        self.assertRaises(ConfigParser.NoSectionError,
                          cf.options, "Foo")
        self.assertRaises(ConfigParser.NoSectionError,
                          cf.set, "foo", "bar", "value")
        self.get_error(ConfigParser.NoSectionError, "foo", "bar")
        cf.add_section("foo")
        self.get_error(ConfigParser.NoOptionError, "foo", "bar")

    def get_error(self, exc, section, option):
        try:
            self.cf.get(section, option)
        except exc, e:
            return e
        else:
            self.fail("expected exception type %s.%s"
                      % (exc.__module__, exc.__name__))

    def test_boolean(self):
        cf = self.fromstring(
            "[BOOLTEST]\n"
            "T1=1\n"
            "T2=TRUE\n"
            "T3=True\n"
            "T4=oN\n"
            "T5=yes\n"
            "F1=0\n"
            "F2=FALSE\n"
            "F3=False\n"
            "F4=oFF\n"
            "F5=nO\n"
            "E1=2\n"
            "E2=foo\n"
            "E3=-1\n"
            "E4=0.1\n"
            "E5=FALSE AND MORE"
            )
        for x in range(1, 5):
            self.failUnless(cf.getboolean('BOOLTEST', 't%d' % x))
            self.failIf(cf.getboolean('BOOLTEST', 'f%d' % x))
            self.assertRaises(ValueError,
                              cf.getboolean, 'BOOLTEST', 'e%d' % x)

    def test_weird_errors(self):
        cf = self.newconfig()
        cf.add_section("Foo")
        self.assertRaises(ConfigParser.DuplicateSectionError,
                          cf.add_section, "Foo")

    def test_write(self):
        cf = self.fromstring(
            "[Long Line]\n"
            "foo: this line is much, much longer than my editor\n"
            "   likes it.\n"
            "[DEFAULT]\n"
            "foo: another very\n"
            " long line"
            )
        output = StringIO.StringIO()
        cf.write(output)
        self.assertEqual(
            output.getvalue(),
            "[Long Line]\n"
            "foo: this line is much, much longer than my editor\n"
            "   likes it.\n"
            "[DEFAULT]\n"
            "foo: another very\n"
            " long line"
            )

    # shared by subclasses
    def get_interpolation_config(self):
        return self.fromstring(
            "[Foo]\n"
            "bar=something %(with1)s interpolation (1 step)\n"
            "bar9=something %(with9)s lots of interpolation (9 steps)\n"
            "bar10=something %(with10)s lots of interpolation (10 steps)\n"
            "bar11=something %(with11)s lots of interpolation (11 steps)\n"
            "with11=%(with10)s\n"
            "with10=%(with9)s\n"
            "with9=%(with8)s\n"
            "with8=%(with7)s\n"
            "with7=%(with6)s\n"
            "with6=%(with5)s\n"
            "with5=%(with4)s\n"
            "with4=%(with3)s\n"
            "with3=%(with2)s\n"
            "with2=%(with1)s\n"
            "with1=with\n"
            "\n"
            "[Mutual Recursion]\n"
            "foo=%(bar)s\n"
            "bar=%(foo)s\n"
            "\n"
            "[Interpolation Error]\n"
            "name=%(reference)s\n",
            # no definition for 'reference'
            defaults={"getname": "%(__name__)s"})

    def check_items_config(self, expected):
        cf = self.fromstring(
            "[section]\n"
            "name = value\n"
            "key: |%(name)s| \n"
            "getdefault: |%(default)s|\n"
            "getname: |%(__name__)s|",
            defaults={"default": "<default>"})
        L = list(cf.items("section"))
        L.sort()
        self.assertEqual(L, expected)


class ConfigParserTestCase(TestCaseBase):
    config_class = cfgparse.compat.ConfigParser

    def test_interpolation(self):
        cf = self.get_interpolation_config()
        eq = self.assertEqual
        eq(cf.get("Foo", "getname"), "Foo")
        eq(cf.get("Foo", "bar"), "something with interpolation (1 step)")
        eq(cf.get("Foo", "bar9"),
           "something with lots of interpolation (9 steps)")
        eq(cf.get("Foo", "bar10"),
           "something with lots of interpolation (10 steps)")
        self.get_error(ConfigParser.InterpolationDepthError, "Foo", "bar11")

    def test_interpolation_missing_value(self):
        cf = self.get_interpolation_config()
        e = self.get_error(ConfigParser.InterpolationError,
                           "Interpolation Error", "name")
        self.assertEqual(e.reference, "reference")
        self.assertEqual(e.section, "Interpolation Error")
        self.assertEqual(e.option, "name")

    def test_items(self):
        self.check_items_config([('default', '<default>'),
                                 ('getdefault', '|<default>|'),
                                 ('getname', '|section|'),
                                 ('key', '|value|'),
                                 ('name', 'value')])


class RawConfigParserTestCase(TestCaseBase):
    config_class = cfgparse.compat.RawConfigParser

    def test_interpolation(self):
        cf = self.get_interpolation_config()
        eq = self.assertEqual
        eq(cf.get("Foo", "getname"), "%(__name__)s")
        eq(cf.get("Foo", "bar"),
           "something %(with1)s interpolation (1 step)")
        eq(cf.get("Foo", "bar9"),
           "something %(with9)s lots of interpolation (9 steps)")
        eq(cf.get("Foo", "bar10"),
           "something %(with10)s lots of interpolation (10 steps)")
        eq(cf.get("Foo", "bar11"),
           "something %(with11)s lots of interpolation (11 steps)")

    def test_items(self):
        self.check_items_config([('default', '<default>'),
                                 ('getdefault', '|%(default)s|'),
                                 ('getname', '|%(__name__)s|'),
                                 ('key', '|%(name)s|'),
                                 ('name', 'value')])


class SafeConfigParserTestCase(ConfigParserTestCase):
    config_class = cfgparse.compat.SafeConfigParser

    def test_safe_interpolation(self):
        # See http://www.python.org/sf/511737
        cf = self.fromstring("[section]\n"
                             "option1=xxx\n"
                             "option2=%(option1)s/xxx\n"
                             "ok=%(option1)s/%%s\n"
                             "not_ok=%(option2)s/%%s")
        self.assertEqual(cf.get("section", "ok"), "xxx/%s")
        self.assertEqual(cf.get("section", "not_ok"), "xxx/xxx/%s")


class suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
                unittest.makeSuite(RawConfigParserTestCase, 'test'),
                unittest.makeSuite(ConfigParserTestCase, 'test'),
                unittest.makeSuite(SafeConfigParserTestCase, 'test'),
        ])
