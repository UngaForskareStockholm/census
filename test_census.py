#!/bin/env python3
import unittest

class TestFunctions(unittest.TestCase):
    def test_parse_gender(self):
        from census import parse_gender

        self.assertEqual('K', parse_gender('K'))
        self.assertEqual('K', parse_gender('Kvinna'))
        self.assertEqual('K', parse_gender('TJEJ'))
        self.assertEqual('K', parse_gender('female'))

        self.assertEqual('M', parse_gender('M'))
        self.assertEqual('M', parse_gender('Man'))
        self.assertEqual('M', parse_gender('Male'))
        self.assertEqual('M', parse_gender('kille'))

        self.assertEqual(None, parse_gender(''))
        self.assertEqual(None, parse_gender('?'))
        self.assertEqual(None, parse_gender('ej svar'))
        self.assertEqual(None, parse_gender('ANNAT'))

        self.assertRaisesRegex(ValueError, 'invalid gender.*', parse_gender, 'WAT')

    def test_parse_year(self):
        from census import parse_year
        self.assertEqual('1997', parse_year('1997'))
        self.assertEqual('1951', parse_year('51'))
        self.assertEqual('2050', parse_year('50'))
        self.assertEqual('1997', parse_year('97'))

    def test_parse_date(self):
        from census import parse_date
        self.assertEqual(None, parse_date(''))
        self.assertEqual(('2017', '10', '23'), parse_date('17.10.23'))
        self.assertEqual(('2017', '10', '23'), parse_date('2017.10.23'))
        self.assertEqual(('2017', '10', '23'), parse_date('2017-10-23'))
        self.assertEqual(('2017', '10', '23'), parse_date('2017/10/23'))
        self.assertEqual(('2017', '10', '23'), parse_date('2017/10/23'))
        self.assertRaises(ValueError, parse_date, '2017-07:23')

    def test_format_date(self):
        from census import format_date
        self.assertEqual('', format_date(None))
        self.assertEqual('2017-07-14', format_date(('2017', '07', '14')))

    def test_parse_birth_date(self):
        from census import parse_birth_date

        # Invalid
        self.assertRaises(ValueError, parse_birth_date, 'WAT')
        self.assertRaises(ValueError, parse_birth_date, '2015-10-TT')

        # None
        self.assertEqual(None, parse_birth_date(''))
        self.assertEqual(None, parse_birth_date('?'))
        self.assertEqual(None, parse_birth_date('0'))

        # Only year
        self.assertEqual(('1995', None, None, None), parse_birth_date('1995'))
        self.assertEqual(('1995', None, None, None), parse_birth_date('95'))
        self.assertEqual(('2015', None, None, None), parse_birth_date('15'))

        # Date
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('1995-10-14'))
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('1995/10/14'))
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('19951014'))
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('95-10-14'))
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('95/10/14'))
        self.assertEqual(('1995', '10', '14', None), parse_birth_date('951014'))
        self.assertEqual(('2015', '10', '14', None), parse_birth_date('151014'))

        # SSN
        self.assertEqual(('1995', '10', '14', '3856'), parse_birth_date('1995-10-14-3856'))

    def test_format_birth_date(self):
        from census import format_birth_date
        self.assertEqual('', format_birth_date(None))
        self.assertEqual('1995', format_birth_date(('1995', None, None, None)))
        self.assertEqual('1995-10-14', format_birth_date(('1995', '10', '14', None)))
        self.assertEqual('1995-10-14-3856', format_birth_date(('1995', '10', '14', '3856')))

    def test_parse_groups(self):
        from census import parse_groups
        self.assertEqual([], parse_groups(None))
        self.assertEqual(['A'], parse_groups('A'))
        self.assertEqual(['A', 'B', 'C'], parse_groups('A;B;C'))

    def test_format_groups(self):
        from census import format_groups
        self.assertEqual('', format_groups([]))
        self.assertEqual('A', format_groups(['A']))
        self.assertEqual('A;B;C', format_groups(['A', 'B', 'C']))

if __name__ == '__main__':
    unittest.main()
