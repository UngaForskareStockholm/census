#!/bin/env python3
import unittest

class TestFunctions(unittest.TestCase):
    def test_clean_whitespace(self):
        from census import clean_whitespace

        row = {
            'first_name': 'Berit  ',
            'last_name': ' Andersson Verkaz ',
            'address_postal_code': '123 45',
            'birth_date': ':1970',
        }

        expected = {
            'first_name': 'Berit',
            'last_name': 'Andersson Verkaz',
            'address_postal_code': '12345',
            'birth_date': '1970'
        }

        clean_whitespace(row)
        self.assertDictEqual(expected, row)

    def test_strip_accents(self):
        from census import strip_accents
        self.assertEqual('veor', strip_accents('véör'))

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
        self.assertEqual(None, parse_gender('annat'))
        self.assertEqual(None, parse_gender('vill ej uppge'))
        self.assertEqual(None, parse_gender('uppgift okänd'))

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
        self.assertEqual(('1950', '10', '15', None), parse_birth_date('1950.10.15'))

        # SSN
        self.assertEqual(('1995', '10', '14', '3856'), parse_birth_date('1995-10-14-3856'))

    def test_format_birth_date(self):
        from census import format_birth_date
        self.assertEqual('', format_birth_date(None))
        self.assertEqual('1995', format_birth_date(('1995', None, None, None)))
        self.assertEqual('1995-10-14', format_birth_date(('1995', '10', '14', None)))
        self.assertEqual('1995-10-14-3856', format_birth_date(('1995', '10', '14', '3856')))

    def test_fudge_gender(self):
        from census import fudge_gender
        self.assertEqual(None, fudge_gender(('1970', '01', '23', None)))
        self.assertEqual('K', fudge_gender(('1970', '01', '23', '3285')))
        self.assertEqual('M', fudge_gender(('1970', '01', '23', '0055')))

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

    def test_calculate_age(self):
        from census import calculate_age
        self.assertEqual(1, calculate_age(2016, {'birth_date': ('2015',)}))
        self.assertEqual(16, calculate_age(2016, {'birth_date': ('2000', '01', '16')}))
        self.assertEqual(16, calculate_age(2016, {'birth_date': ('2000', '06', '16')}))
        self.assertEqual(16, calculate_age(2016, {'birth_date': ('2000', '12', '31')}))
        self.assertEqual(15, calculate_age(2016, {'birth_date': ('2001', '01', '01')}))

    def test_resides_in_stockholm(self):
        from census import resides_in_stockholm
        self.assertTrue(resides_in_stockholm({'address_postal_code': '12456'}))
        self.assertFalse(resides_in_stockholm({'address_postal_code': '87812'}))

    def test_is_eligable_for_grant(self):
        from census import is_eligable_for_grant

        def row(postal_code, birth_year):
            return {'address_postal_code': postal_code, 'birth_date': (birth_year,)}

        # Just right
        self.assertTrue(is_eligable_for_grant(2016, row('14231', 2010)))
        self.assertTrue(is_eligable_for_grant(2016, row('11117', 1991)))

        # Not residing in Stockholm
        self.assertFalse(is_eligable_for_grant(2016, row('98212', 2010)))
        self.assertFalse(is_eligable_for_grant(2016, row('23111', 1991)))

        # Too old
        self.assertFalse(is_eligable_for_grant(2016, row('14231', 1990)))

        # Too young
        self.assertFalse(is_eligable_for_grant(2016, row('14231', 2011)))

    def test_filter_eligable(self):
        from census import filter_eligable

        rows = [
            {'address_postal_code': '14231', 'birth_date': (1990,)},
            {'address_postal_code': '27432', 'birth_date': (1991,)},
            {'address_postal_code': '11117', 'birth_date': (2000,)},
            {'address_postal_code': '98765', 'birth_date': (2000,)},
            {'address_postal_code': '17512', 'birth_date': (1990,)},
        ]

        expected = [
            {'address_postal_code': '11117', 'birth_date': (2000,)},
        ]

        self.assertListEqual(expected, filter_eligable(2016, rows))

    def test_gender_stats(self):
        from census import gender_stats

        rows = [
            {'gender': 'M'},
            {'gender': 'M'},
            {'gender': 'K'},
            {'gender': 'M'},
            {'gender': 'M'},
            {'gender': 'K'},
            {'gender': 'K'},
            {'gender': 'K'},
            {'gender': 'M'},
        ]

        expected = {
            'M': 5,
            'K': 4,
        }

        self.assertDictEqual(expected, gender_stats(rows))

    def test_age_stats(self):
        from census import age_stats, parse_birth_date

        rows = [
            {'birth_date': parse_birth_date('1970-06-23')},
            {'birth_date': parse_birth_date('2002-10-23')},
            {'birth_date': parse_birth_date('1987-06-23')},
            {'birth_date': parse_birth_date('1970-12-23')},
            {'birth_date': parse_birth_date('1970-09-23')},
            {'birth_date': parse_birth_date('2002-01-03')},
            {'birth_date': parse_birth_date('2010-12-23')},
            {'birth_date': parse_birth_date('2012-06-23')},
        ]

        expected = {
            '0-5': 1,
            '6-12': 1,
            '13-20': 2,
            '26+': 4
        }

        self.assertDictEqual(expected, age_stats(2016, rows))

if __name__ == '__main__':
    unittest.main()
