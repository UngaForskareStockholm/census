#!/bin/env python3
# coding=utf-8
import sys, os, re
import csv
from datetime import date
from collections import defaultdict
from copy import copy

reporting_year = '2016'
debug = False

fields = [
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
    row['address_postal_code'] = row['address_postal_code'].replace(' ', '')
    if row['birth_date'].startswith(':'): # THS Kemisektionen special...
        row['birth_date'] = row['birth_date'][1:]

def strip_accents(text):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')

def parse_gender(text):
    text = text.upper()
    if text in ['K', 'F', 'FEMALE', 'KVINNA', 'TJEJ']:
        return 'K'
    elif text in ['M', 'MAN', 'MALE', 'KILLE']:
        return 'M'
    elif text in ['', '?', 'EJ SVAR', 'ANNAT']:
        return None
    else:
        raise Exception('invalid gender: ' + text)

def parse_year(text):
    if len(text) == 2:
        if int(text) > 50:
            return '19' + text
        else:
            return '20' + text
    return text

def format_date(parts):
    if parts is None:
        return ''

    return '{0}-{1}-{2}'.format(parts[0], parts[1], parts[2])

def parse_date(text):
    if len(text) == 0: return None
    match = re.match(r'^(\d{2,4})[\./-]?(\d{2})[\./-]?(\d{2})$', text)
    if match:
        parts = match.groups()
        year = parse_year(parts[0])
        return (year, parts[1], parts[2])
    raise Exception('invalid confirmation date: ' + text)

def format_birth_date(parts):
    if parts is None:
        return ''

    if parts[3] is not None:
        return '{0}-{1}-{2}-{3}'.format(parts[0], parts[1], parts[2], parts[3])
    elif parts[1] is not None:
        return '{0}-{1}-{2}'.format(parts[0], parts[1], parts[2])
    else:
        return parts[0]

def parse_birth_date(text):
    if len(text) == 0 or text in ['?', '0']: return None
    match = re.match(r'^(\d{2,4})(?:[/-]?(\d{2})[/-]?(\d{2})(?:[/-]?(\d{4}))?)?$', text)
    if match:
        parts = match.groups()
        year = parse_year(parts[0])
        return (year, parts[1], parts[2], parts[3])
    raise Exception('invalid birth date: ' + text)

def fudge_gender(birth_date):
    if birth_date[3] is not None:
        return 'K' if int(birth_date[3][2]) % 2 == 0 else 'M'
    return None

def parse_groups(text):
    if text is not None:
        return text.split(';')
    else:
        return []

def format_groups(groups):
    return ';'.join(groups)

def load(infile, group=None):
    result = []
    for row in csv.DictReader(infile, fields):
        if debug: print(row)
        clean_whitespace(row)
        row['gender'] = parse_gender(row['gender'])
        row['birth_date'] = parse_birth_date(row['birth_date'])
        row['confirmed_membership_at'] = parse_date(row['confirmed_membership_at'])
        row['groups'] = parse_groups(row['groups'])
        if len(row['groups']) == 0 and group is not None:
            row['groups'].append(group)
        if row['gender'] is None and row['birth_date'] is not None:
            row['gender'] = fudge_gender(row['birth_date'])
        result.append(row)
    return result

def save(rows, outfile):
    writer = csv.DictWriter(outfile, fields)
    for row in rows:
        copied = copy(row)
        copied['birth_date'] = format_birth_date(copied['birth_date'])
        copied['confirmed_membership_at'] = format_date(copied['confirmed_membership_at'])
        copied['groups'] = format_groups(copied['groups'])
        
        #if 'removal_cause' in copied:
        #    copied['removal_cause'] = ', '.join(copied['removal_cause'])

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
        elif row['confirmed_membership_at'][0] != reporting_year:
            remove(row, 'confirmed_membership_at is not ' + reporting_year)
        elif row['birth_date'] is None:
            remove(row, 'birth_date not given')
        elif row['gender'] is None:
            remove(row, 'gender not given')
        elif row['address_postal_code'] in ['', '-', 'Saknas', 'Vetej', None]:
            remove(row, 'address_postal_code not given')
        elif row['email'] == '' and row['phone'] == '':
            remove(row, 'neither email nor phone given')
        else:
            kept.append(row)

    return (kept, invalid)

def remove_not_stockholm(rows):
    kept = []
    removed = []

    def remove(row, why):
        row['removal_cause'] = why
        removed.append(row)

    for row in rows:
        if not row['address_postal_code'].startswith('1'): 
            remove(row, 'address_postal_code not in stockholm')
        else:
            kept.append(row) 
    
    return (kept, removed)

def maybe_duplicates(rows):
    def make_key(row):
        return strip_accents(row['first_name']).casefold() + ':' + strip_accents(row['last_name']).casefold()

    by = {}
    for row in rows:
        key = make_key(row)
        if key not in by: by[key] = []
        by[key].append(row)

    maybe = []
    for member in by.values():
        if len(member) > 1:
            maybe.extend(member)
    
    return maybe
    

def remove_duplicates(rows):
    def make_key(row):
        bd = row['birth_date']
        return strip_accents(row['first_name']).casefold() + \
            ':' + strip_accents(row['last_name']).casefold() + \
            ':' + str(bd[0]) + str(bd[1]) + str(bd[2]) + \
            ':' + str(row['address_postal_code'])

    by = {}
    for row in rows:
        key = make_key(row)
        if key not in by: by[key] = []
        by[key].append(row)

    unique = []
    duplicates = []
    for member in by.values():
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

def calculate_age(row):
    result = int(reporting_year) - int(row['birth_date'][0])
    assert result >= 0
    return result

def is_eligable_for_grant(row):
    return 6 <= calculate_age(row) <= 25

def print_removal_cause_stats(rows):
    counts = defaultdict(lambda: 0)
    for row in rows:
        counts[row['removal_cause']] += 1
    for (k, v) in counts.items():
        print('  ' + k + ': ' + str(v))

def gender_stats(rows):
    genders = defaultdict(lambda: 0)

    for row in rows:
        genders[row['gender']] += 1
    
    return genders

def age_stats(rows):
    ages = defaultdict(lambda: 0)
    
    for row in rows:
        age = calculate_age(row)
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
    stockholm, unstockholm = remove_not_stockholm(loaded)
    print()
    print('# Länstillhörighet')
    print('Totalt:                  ' + format_count(len(loaded)))
    print('Stockholm:               ' + format_statistic(len(stockholm), len(loaded)))
    print('Ej Stockholm:            ' + format_statistic(len(unstockholm), len(loaded)))
    print()
    print()
    print('# Ålder- och könsfördelning av medlemmar bosatta i Stockholms Län')
    all = stockholm

    print()
    print('## Könsfördelning alla åldrar')
    genders_all = gender_stats(all)
    print('Totalt antal medlemmar:  ' + format_count(len(all)))
    print('Totalt andel kvinnor:    ' + format_statistic(genders_all['K'], len(all)))
    print('Totalt andel män:        ' + format_statistic(genders_all['M'], len(all)))

    print()
    print('## Könsfördelning 6-25 år')
    eligable = list(filter(is_eligable_for_grant, all))
    genders_eligable = gender_stats(eligable)
    print('Total antal   6-25 år:   ' + format_count(len(eligable)))
    print('Andel flickor 6-25 år:   ' + format_statistic(genders_eligable['K'], len(eligable)))
    print('Andel pojkar  6-25 år:   ' + format_statistic(genders_eligable['M'], len(eligable)))

    print()
    print('## Åldersfördelning')
    ages_all = age_stats(all)
    print(' 0-5 år:                 ' + format_statistic(ages_all['0-5'], len(all)))
    print(' 6-12 år:                ' + format_statistic(ages_all['6-12'], len(all)))
    print('13-20 år:                ' + format_statistic(ages_all['13-20'], len(all)))
    print('21-25 år:                ' + format_statistic(ages_all['21-25'], len(all)))
    print('26 år och äldre:         ' + format_statistic(ages_all['26+'], len(all)))

def eligable_file(path):
    group = os.path.splitext(os.path.basename(path))[0]
    loaded = load(open(path), group)

    stockholm, unstockholm = remove_not_stockholm(loaded)
    eligable = list(filter(is_eligable_for_grant, stockholm))
    print('{:<40} {:>4}'.format(group, len(eligable)))

def normalize_file(path):
    loaded = load(open(path), os.path.splitext(os.path.basename(path))[0])
    kept, invalid = remove_invalid(loaded)

    print('= Kept ' + str(len(kept)))
    print('= Invalid ' + str(len(invalid)))
    print_removal_cause_stats(invalid)

    save(kept, open(path + '.ok', 'w'))
    if len(invalid) > 0:
        save(invalid, open(path + '.invalid', 'w'))

def process_all(files, fn):
    for path in files:
        print('Processing "{}"...'.format(os.path.basename(path)))
        fn(path)

def merge_files(files):
    all = []
    for path in files:
        print('Loading "{}"...'.format(os.path.basename(path)))
        loaded = load(open(path))
        all.extend(loaded)
    
    unique, duplicates = remove_duplicates(all)
    maybe = maybe_duplicates(all)

    print()
    print('Merged:')
    print('= All ' + str(len(all)))
    print('= Unique ' + str(len(unique)))
    print('= Duplicates ' + str(len(all) - len(unique)))
    
    def sort_key(row):
        return strip_accents(row['first_name']).casefold() + \
            ':' + strip_accents(row['last_name']).casefold() + \
            ':' + strip_accents(row['address_street']).casefold()

    save(sorted(unique, key=sort_key), open('all.csv', 'w'))
    save(duplicates, open('dups.csv', 'w'))
    save(maybe, open('maybedups.csv', 'w'))

if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ['normalize', 'merge', 'eligable', 'stats']:
        print('Usage: {} normalize|merge|eligable|stats file [file ...]'.format(sys.argv[0]))
        sys.exit(1)

    mode = sys.argv[1]
    files = sys.argv[2:]

    if mode == 'normalize':
        process_all(files, normalize_file)
    elif mode == 'stats':
        process_all(files, statistics_file)
    elif mode == 'eligable':
        process_all(files, eligable_file)
    elif mode == 'merge':
        merge_files(files)
