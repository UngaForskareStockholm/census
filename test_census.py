import pytest
from census import clean_whitespace, strip_accents
from census import parse_gender, fudge_gender, format_gender
from census import parse_year, parse_date, format_date
from census import parse_birth_date, format_birth_date
from census import normalize_postal_code
from census import parse_groups, format_groups
from census import calculate_age
from census import resides_in_stockholm
from census import is_eligable_for_grant
from census import filter_eligable
from census import gender_stats
from census import age_stats

def test_clean_whitespace():

    row = {
        'first_name': 'Berit  ',
        'last_name': ' Andersson Verkaz ',
        'birth_date': ':1970',
    }

    expected = {
        'first_name': 'Berit',
        'last_name': 'Andersson Verkaz',
        'birth_date': '1970'
    }

    clean_whitespace(row)
    assert row == expected

def test_strip_accents():
    assert strip_accents('véör') == 'veor'

def test_parse_gender():
    assert parse_gender('K') == 'K'
    assert parse_gender('Kvinna') == 'K'
    assert parse_gender('TJEJ') == 'K'
    assert parse_gender('female') == 'K'

    assert parse_gender('M') == 'M'
    assert parse_gender('Man') == 'M'
    assert parse_gender('Male') == 'M'
    assert parse_gender('kille') == 'M'

    assert parse_gender('annat') == 'A'
    assert parse_gender('vill ej uppge') == 'A'

    assert parse_gender('') is None
    assert parse_gender('?') is None
    assert parse_gender('ej svar') is None
    assert parse_gender('uppgift okänd') is None

    with pytest.raises(ValueError, match='invalid gender.*'):
        parse_gender('WAT')

def test_format_gender():
    assert format_gender('K') == 'Kvinna'
    assert format_gender('M') == 'Man'
    assert format_gender('A') == 'Annat'

def test_parse_year():
    assert parse_year('1997') == '1997'
    assert parse_year('51') == '1951'
    assert parse_year('50') == '2050'
    assert parse_year('97') == '1997'

def test_parse_date():
    assert parse_date('') is None
    assert parse_date('17.10.23') == ('2017', '10', '23')
    assert parse_date('2017.10.23') == ('2017', '10', '23')
    assert parse_date('2017-10-23') == ('2017', '10', '23')
    assert parse_date('2017/10/23') == ('2017', '10', '23')
    assert parse_date('2017 10 23') == ('2017', '10', '23')

    # No day
    assert parse_date('2017-10') == ('2017', '10', None)

    with pytest.raises(ValueError):
        parse_date('2017-07:23')

def test_format_date():
    assert format_date(None) == ''
    assert format_date(('2017', '07', '14')) == '2017-07-14'
    assert format_date(('2017', '07', None)) == '2017-07'

def test_parse_birth_date():
    # Invalid
    with pytest.raises(ValueError):
        parse_birth_date('WAT')
    with pytest.raises(ValueError):
        parse_birth_date('2015-10-TT')
    with pytest.raises(ValueError):
        parse_birth_date('2017-07:23')

    # None
    assert parse_birth_date('') is None
    assert parse_birth_date('?') is None
    assert parse_birth_date('0') is None

    # Only year
    assert parse_birth_date('1995') == ('1995', None, None, None)
    assert parse_birth_date('95') == ('1995', None, None, None)
    assert parse_birth_date('15') == ('2015', None, None, None)

    # Date
    assert parse_birth_date('1950.10.15') == ('1950', '10', '15', None)
    assert parse_birth_date('1995-10-14') == ('1995', '10', '14', None)
    assert parse_birth_date('1995/10/14') == ('1995', '10', '14', None)
    assert parse_birth_date('1995 10 14') == ('1995', '10', '14', None)
    assert parse_birth_date('19951014') == ('1995', '10', '14', None)
    assert parse_birth_date('95-10-14') == ('1995', '10', '14', None)
    assert parse_birth_date('95/10/14') == ('1995', '10', '14', None)
    assert parse_birth_date('95 10 14') == ('1995', '10', '14', None)
    assert parse_birth_date('951014') == ('1995', '10', '14', None)
    assert parse_birth_date('151014') == ('2015', '10', '14', None)

    # Zeros
    assert parse_birth_date('199510140000') == ('1995', '10', '14', None)
    assert parse_birth_date('199510000000') == ('1995', '10', None, None)
    assert parse_birth_date('199500000000') == ('1995', None, None, None)

    # SSN
    assert parse_birth_date('1995-10-14-3856') == ('1995', '10', '14', '3856')
    assert parse_birth_date('199510143856') == ('1995', '10', '14', '3856')

def test_format_birth_date():
    assert format_birth_date(None) == ''
    assert format_birth_date(('1995', None, None, None)) == '1995'
    assert format_birth_date(('1995', '10', '14', None)) == '1995-10-14'
    assert format_birth_date(('1995', '10', '14', '3856')) == '1995-10-14-3856'

def test_fudge_gender():
    assert fudge_gender(('1970', '01', '23', None)) is None
    assert fudge_gender(('1970', '01', '23', '3285')) == 'K'
    assert fudge_gender(('1970', '01', '23', '0055')) == 'M'

def test_normalize_postal_code():
    assert normalize_postal_code('123 45') == '12345'
    assert normalize_postal_code('12345') == '12345'

    # Unnecessary place name
    assert normalize_postal_code('123 45 Stockholm') == '12345'
    assert normalize_postal_code('12345Stockholm') == '12345'

    # None
    assert normalize_postal_code('') is None
    assert normalize_postal_code('-') is None
    assert normalize_postal_code('Saknas') is None
    assert normalize_postal_code('Vetej') is None
    assert normalize_postal_code('Skyddadadress') is None

    # Invalid
    with pytest.raises(ValueError):
        normalize_postal_code('123')
    with pytest.raises(ValueError):
        normalize_postal_code('Stockholm')

def test_parse_groups():
    assert parse_groups(None) == []
    assert parse_groups('A') == ['A']
    assert parse_groups('A;B;C') == ['A', 'B', 'C']

def test_format_groups():
    assert format_groups([]) == ''
    assert format_groups(['A']) == 'A'
    assert format_groups(['A', 'B', 'C']) == 'A;B;C'

def test_calculate_age():
    assert calculate_age(2016, {'birth_date': ('2015',)}) == 1
    assert calculate_age(2016, {'birth_date': ('2000', '01', '16')}) == 16
    assert calculate_age(2016, {'birth_date': ('2000', '06', '16')}) == 16
    assert calculate_age(2016, {'birth_date': ('2000', '12', '31')}) == 16
    assert calculate_age(2016, {'birth_date': ('2001', '01', '01')}) == 15

def test_resides_in_stockholm():
    assert resides_in_stockholm({'address_postal_code': '12456'})
    assert not resides_in_stockholm({'address_postal_code': '87812'})

def test_is_eligable_for_grant():
    def row(postal_code, birth_year):
        return {'address_postal_code': postal_code, 'birth_date': (birth_year,)}

    # Just right
    assert is_eligable_for_grant(2016, row('14231', 2010))
    assert is_eligable_for_grant(2016, row('11117', 1991))

    # Not residing in Stockholm
    assert not is_eligable_for_grant(2016, row('98212', 2010))
    assert not is_eligable_for_grant(2016, row('23111', 1991))

    # Too old
    assert not is_eligable_for_grant(2016, row('14231', 1990))

    # Too young
    assert not is_eligable_for_grant(2016, row('14231', 2011))

def test_filter_eligable():
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

    assert filter_eligable(2016, rows) == expected

def test_gender_stats():
    rows = [
        {'gender': 'M'},
        {'gender': 'M'},
        {'gender': 'K'},
        {'gender': 'A'},
        {'gender': 'M'},
        {'gender': 'M'},
        {'gender': 'K'},
        {'gender': 'A'},
        {'gender': 'K'},
        {'gender': 'K'},
        {'gender': 'M'},
    ]

    expected = {
        'M': 5,
        'K': 4,
        'A': 2,
    }

    assert gender_stats(rows) == expected

def test_age_stats():
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

    assert age_stats(2016, rows) == expected
