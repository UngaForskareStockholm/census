#!/bin/env python3
# coding=utf-8
import os
import re
import sys
import csv
from collections import defaultdict
from copy import copy

REPORTING_YEAR = '2019'

FIELDS = [
    'first_name',
    'last_name',
    'birth_date',  # Can be SSN, birth date or birth year
    'gender',
    'address_co',
    'address_street',
    'address_postal_code',
    'email',
    'phone',
    'confirmed_membership_at',
    'groups',
    'removal_cause'] # Only used when writing

def clean_whitespace(row):
    for key, value in row.items():
        if value is not None:
            row[key] = value.strip()
    if row['birth_date'].startswith(':'): # THS Kemisektionen special...
        row['birth_date'] = row['birth_date'][1:]

def strip_accents(text):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def parse_gender(text):
    text = text.upper()
    if text in ['K', 'F', 'FEMALE', 'KVINNA', 'TJEJ']:
        return 'K'
    if text in ['M', 'MAN', 'MALE', 'KILLE']:
        return 'M'
    if text in ['', '?', 'EJ SVAR', 'ANNAT', 'UPPGIFT OKÄND', 'VILL EJ UPPGE']:
        return None
    raise ValueError('invalid gender: ' + text)

def parse_year(text):
    if len(text) == 2:
        if int(text) > 50:
            return '19' + text
        return '20' + text
    return text

def format_date(parts):
    if parts is None:
        return ''
    if parts[2] is None:
        return '{0}-{1}'.format(parts[0], parts[1])
    return '{0}-{1}-{2}'.format(parts[0], parts[1], parts[2])

def parse_date(text):
    if not text:
        return None

    match = re.match(r'^(\d{2,4})[ ./-]?(\d{2})(?:[ ./-]?(\d{2}))?$', text)
    if match:
        parts = match.groups()
        year = parse_year(parts[0])
        return (year, parts[1], parts[2])

    raise ValueError('invalid confirmation date: ' + text)

def format_birth_date(parts):
    if parts is None:
        return ''

    if parts[3] is not None:
        return '{0}-{1}-{2}-{3}'.format(parts[0], parts[1], parts[2], parts[3])
    if parts[1] is not None:
        return '{0}-{1}-{2}'.format(parts[0], parts[1], parts[2])
    return parts[0]

def parse_birth_date(text):
    if text in ['', '?', '0']:
        return None

    match = re.match(r'^(\d{2,4})(?:[ ./-]?(\d{2})[ ./-]?(\d{2})(?:[ ./-]?(\d{4}))?)?$', text)
    if match:
        parts = match.groups()
        year = parse_year(parts[0])
        return (year, parts[1], parts[2], parts[3])
    raise ValueError('invalid birth date: ' + text)

def fudge_gender(birth_date):
    if birth_date[3] is not None:
        return 'K' if int(birth_date[3][2]) % 2 == 0 else 'M'
    return None

def normalize_postal_code(text):
    text = text.lower().replace(' ', '')
    if text in ['', '-', 'saknas', 'vetej']:
        return None
    if text.startswith('skyddad'):
        return None

    match = re.match(r'^(\d{5})', text)
    if match:
        return match.groups()[0]
    raise ValueError('invalid postal code: ' + text)

def parse_groups(text):
    if text is not None:
        return text.split(';')
    return []

def format_groups(groups):
    return ';'.join(groups)

def resides_in_stockholm(row):
    return row['address_postal_code'].startswith('1')

def calculate_age(reporting_year, row):
    result = int(reporting_year) - int(row['birth_date'][0])
    assert result >= 0
    return result

def is_eligable_for_grant(reporting_year, row):
    return 6 <= calculate_age(reporting_year, row) <= 25 and resides_in_stockholm(row)

def filter_stockholm(rows):
    return [row for row in rows if resides_in_stockholm(row)]

def filter_eligable(reporting_year, rows):
    return [row for row in rows if is_eligable_for_grant(reporting_year, row)]

def load(infile, group=None):
    result = []
    for row in csv.DictReader(infile, FIELDS):
        clean_whitespace(row)
        row['gender'] = parse_gender(row['gender'])
        row['birth_date'] = parse_birth_date(row['birth_date'])
        row['address_postal_code'] = normalize_postal_code(row['address_postal_code'])
        row['confirmed_membership_at'] = parse_date(row['confirmed_membership_at'])
        row['groups'] = parse_groups(row['groups'])
        if not row['groups'] and group is not None:
            row['groups'].append(group)
        if row['gender'] is None and row['birth_date'] is not None:
            row['gender'] = fudge_gender(row['birth_date'])
        result.append(row)
    return result

def save(rows, outfile):
    writer = csv.DictWriter(outfile, FIELDS)
    for row in rows:
        copied = copy(row)
        copied['birth_date'] = format_birth_date(copied['birth_date'])
        copied['confirmed_membership_at'] = format_date(copied['confirmed_membership_at'])
        copied['groups'] = format_groups(copied['groups'])
        writer.writerow(copied)

def remove_invalid(rows):
    kept = []
    invalid = []

    def remove(row, why):
        row['removal_cause'] = why
        invalid.append(row)

    for row in rows:
        if row['confirmed_membership_at'] is None:
            remove(row, 'confirmed_membership_at not given')
        elif row['confirmed_membership_at'][0] != REPORTING_YEAR:
            remove(row, 'confirmed_membership_at is not ' + REPORTING_YEAR)
        elif row['birth_date'] is None:
            remove(row, 'birth_date not given')
        elif row['gender'] is None:
            remove(row, 'gender not given')
        elif row['address_postal_code'] is None:
            remove(row, 'address_postal_code not given')
        elif row['email'] == '' and row['phone'] == '':
            remove(row, 'neither email nor phone given')
        else:
            kept.append(row)

    return (kept, invalid)

def maybe_duplicates(rows):
    def make_key(row):
        return strip_accents(row['first_name']).casefold() + \
            ':' + strip_accents(row['last_name']).casefold()

    rows_by_key = defaultdict(list)
    for row in rows:
        rows_by_key[make_key(row)].append(row)

    maybe = []
    for member in rows_by_key.values():
        if len(member) > 1:
            maybe.extend(member)

    return maybe

def remove_duplicates(rows):
    def make_key(row):
        date = row['birth_date']
        return strip_accents(row['first_name']).casefold() + \
            ':' + strip_accents(row['last_name']).casefold() + \
            ':' + str(date[0]) + str(date[1]) + str(date[2]) + \
            ':' + str(row['address_postal_code'])

    rows_by_key = defaultdict(list)
    for row in rows:
        rows_by_key[make_key(row)].append(row)

    unique = []
    duplicates = []
    for member in rows_by_key.values():
        groups = []
        for single in member:
            for group in single['groups']:
                if group not in groups:
                    groups.append(group)

        first = copy(member[0])
        first['groups'] = groups
        unique.append(first)

        if len(member) > 1:
            duplicates.extend(member)

    return (unique, duplicates)

def print_removal_cause_stats(rows):
    counts = defaultdict(int)
    for row in rows:
        counts[row['removal_cause']] += 1
    for (key, value) in counts.items():
        print('{}: {}'.format(key, value))

def gender_stats(rows):
    genders = defaultdict(int)

    for row in rows:
        genders[row['gender']] += 1

    return genders

def age_stats(reporting_year, rows):
    ages = defaultdict(int)

    for row in rows:
        age = calculate_age(reporting_year, row)
        if 0 <= age <= 5:
            ages['0-5'] += 1
        elif 6 <= age <= 12:
            ages['6-12'] += 1
        elif 13 <= age <= 20:
            ages['13-20'] += 1
        elif 21 <= age <= 25:
            ages['21-25'] += 1
        else:
            ages['26+'] += 1

    return ages

def statistics_file(path):
    def format_count(count):
        return '{:>4}'.format(count)

    def format_statistic(count, total):
        return '{:>4} {:>7.2%}'.format(count, count / total)

    loaded = load(open(path))
    stockholm = filter_stockholm(loaded)
    print()
    print('# Länstillhörighet')
    print('Totalt:                  ' + format_count(len(loaded)))
    print('Stockholm:               ' + format_statistic(len(stockholm), len(loaded)))
    print('Ej Stockholm:            ' + format_statistic(len(loaded) - len(stockholm), len(loaded)))
    print()
    print()
    print('# Ålder- och könsfördelning av medlemmar bosatta i Stockholms Län')

    print()
    print('## Könsfördelning alla åldrar')
    genders_all = gender_stats(stockholm)
    print('Totalt antal medlemmar:  ' + format_count(len(stockholm)))
    print('Totalt andel kvinnor:    ' + format_statistic(genders_all['K'], len(stockholm)))
    print('Totalt andel män:        ' + format_statistic(genders_all['M'], len(stockholm)))

    print()
    print('## Könsfördelning 6-25 år')
    eligable = list(filter(lambda row: is_eligable_for_grant(REPORTING_YEAR, row), stockholm))
    genders_eligable = gender_stats(eligable)
    print('Total antal   6-25 år:   ' + format_count(len(eligable)))
    print('Andel flickor 6-25 år:   ' + format_statistic(genders_eligable['K'], len(eligable)))
    print('Andel pojkar  6-25 år:   ' + format_statistic(genders_eligable['M'], len(eligable)))

    print()
    print('## Åldersfördelning')
    ages_all = age_stats(REPORTING_YEAR, stockholm)
    print(' 0-5 år:                 ' + format_statistic(ages_all['0-5'], len(stockholm)))
    print(' 6-12 år:                ' + format_statistic(ages_all['6-12'], len(stockholm)))
    print('13-20 år:                ' + format_statistic(ages_all['13-20'], len(stockholm)))
    print('21-25 år:                ' + format_statistic(ages_all['21-25'], len(stockholm)))
    print('26 år och äldre:         ' + format_statistic(ages_all['26+'], len(stockholm)))

def eligable_file(path):
    group = os.path.splitext(os.path.basename(path))[0]
    loaded = load(open(path), group)
    eligable = filter_eligable(REPORTING_YEAR, loaded)
    print('{:<40} {:>4}'.format(group, len(eligable)))

def normalize_file(path):
    loaded = load(open(path), os.path.splitext(os.path.basename(path))[0])
    kept, invalid = remove_invalid(loaded)

    print('Totalt:             {:<4}'.format(len(loaded)))
    print('Ogiltiga:           {:<4}'.format(len(invalid)))
    print('Giltiga:            {:<4}'.format(len(kept)))
    print('Bidragsberättigade: {:<4}'.format(len(filter_eligable(REPORTING_YEAR, kept))))
    print()
    print('Ogiltighetsanledningar:')
    print_removal_cause_stats(invalid)

    save(kept, open(path + '.ok', 'w'))
    if invalid:
        save(invalid, open(path + '.invalid', 'w'))

def process_all(files, function):
    for path in files:
        print('Processing "{}"...'.format(os.path.basename(path)))
        function(path)

def merge_files(files):
    everything = []
    for path in files:
        print('Loading "{}"...'.format(os.path.basename(path)))
        loaded = load(open(path))
        everything.extend(loaded)

    unique, duplicates = remove_duplicates(everything)
    maybe = maybe_duplicates(everything)

    print()
    print('Merged:')
    print('= All ' + str(len(everything)))
    print('= Unique ' + str(len(unique)))
    print('= Duplicates ' + str(len(everything) - len(unique)))

    def sort_key(row):
        return strip_accents(row['first_name']).casefold() + \
            ':' + strip_accents(row['last_name']).casefold() + \
            ':' + strip_accents(row['address_street']).casefold()

    save(sorted(unique, key=sort_key), open('all.csv', 'w'))
    save(duplicates, open('dups.csv', 'w'))
    save(maybe, open('maybedups.csv', 'w'))

def main(args):
    if len(args) < 3 or args[1] not in ['normalize', 'merge', 'eligable', 'stats']:
        print('Usage: {} normalize|merge|eligable|stats file [file ...]'.format(args[0]))
        return 1

    mode = args[1]
    files = args[2:]

    if mode == 'normalize':
        process_all(files, normalize_file)
    elif mode == 'stats':
        process_all(files, statistics_file)
    elif mode == 'eligable':
        process_all(files, eligable_file)
    elif mode == 'merge':
        merge_files(files)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
