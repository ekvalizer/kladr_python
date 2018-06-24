import urllib.request
import zipfile
import os
from dbfread import DBF
import psycopg2
import chardet
import time
from operator import itemgetter

URL_KLADR = 'https://www.gnivc.ru/html/gnivcsoft/KLADR/Base.7z'

def download_file(url, dest):
    print('Downloading file...')
    urllib.request.urlretrieve(url, dest)
    print('downloaded!')


def unzip_file(path_to_zip_file, directory_to_extract_to):
    zip_ref = zipfile.ZipFile(path_to_zip_file, 'r')
    zip_ref.extractall(directory_to_extract_to)
    zip_ref.close()



def q_types(s_title, title, level, kladr_code):
    return str(("""INSERT INTO wt_kladr_types (id, short_title, title, level, kladr_code)
         VALUES (DEFAULT, '{}', '{}', {}, {}) 
         ON CONFLICT (kladr_code) 
         DO UPDATE SET 
         short_title=EXCLUDED.short_title, title=EXCLUDED.title, kladr_code=EXCLUDED.kladr_code; """
        .format(s_title, title, level, kladr_code)))


def q_objects(title, short_title, code, ocatd, index, parent_id, deleted, obj_level):
    return ("""
        INSERT INTO wt_kladr_objects (id, title, kladr_code, kladr_ocatd, kladr_index, type_id, parent_id, deleted)
         SELECT nextval('wt_kladr_objects_id_seq'), '{}', '{}', '{}', '{}', id, '{}', '{}'
            from wt_kladr_types as types
            where short_title = '{}' and level = '{}';
             """.format(title, code, ocatd, index, parent_id, deleted, short_title, obj_level))


def get_kladr_level(code):
    if code[-5:-2] != '000':
        lvl = 4
    elif code[5:8] != '000':
        lvl = 3
    elif code[2:5] != '000':
        lvl = 2
    else: lvl = 1

    return lvl


def update_kladr(conn, cur, dbf_path):
    table = DBF(filename=dbf_path, encoding='cp866')
    #records = table.records
    #sorted(records, key=lambda x: x['CODE'])
    # for record in table:
    #     cur.execute(q_objects(record['NAME'], record['SOCR'], record['CODE'], record['OCATD'], record['INDEX'],
    #                           '1', 'false', get_kladr_level(record['CODE'])))
    for record in table:
        cur.execute("""UPDATE wt_kladr_objects
            SET parent_id = '{}'
            where kladr_code = '{}';
            """.format(get_parent_id(cur, record['CODE']), record['CODE']))




def get_parent_id(cur, code):
    digits_num = 11
    lvl = get_kladr_level(code)
    if lvl == 4:
        r = 8
    elif lvl == 3:
        r = 5
    elif lvl == 2:
        r = 2
    else: return 1

    p_code = code[:r] + '0'*(digits_num-r) + '__'
    q = """SELECT id from wt_kladr_objects
    WHERE kladr_code LIKE '{}';
    """
    cur.execute(q.format(p_code))
    id = cur.fetchone()
    if id is None:
        if lvl == 4:
            r = 5
        elif lvl == 3:
            r = 2
        p_code = code[:r] + '0'*(digits_num-r) + '__'
        cur.execute(q.format(p_code))
        id = cur.fetchone()
        if id is None:
            p_code = code[:2] + '0'*(digits_num-2) + '__'
            cur.execute(q.format(p_code))
            id = cur.fetchone()
    return id[0]


def update_types(cur, dbf_path):
    table = DBF(filename=dbf_path, encoding='cp866')
    for record in table:
        cur.execute(q_types(record['SCNAME'], record['SOCRNAME'], record['LEVEL'], record['KOD_T_ST']))


def main(url, hostname, db, user, pswd, port, path):
    arch_path = path + '/Base.7z'
    # download_file(url, arch_path)
    # arch_path_dir = arch_path[:arch_path.rindex(os.sep)]
    arch_path_dir = path + '/Base'

    # os.system( '7za e %s -o%s' % (arch_path, arch_path_dir))
    conn = psycopg2.connect(host=hostname,dbname=db, user=user, password=pswd, port=port)
    cur = conn.cursor()

    print('updating wt_kladr_types from SOCRBASE...')
    update_types(cur, arch_path_dir + '/SOCRBASE.DBF')
    print('update wt_kladr_types completed.')

    print('updating wt_kladr_types from KLADR...')
    update_kladr(conn, cur, arch_path_dir + '/KLADR.DBF')
    print('update KLADR completed.')
    #
    # print('updating wt_kladr_types from STREET...')
    # update_objects_table(cur, arch_path_dir + '/STREET.DBF')
    # print('update STREET completed.')
    #
    # print('updating wt_kladr_types from DOMA...')
    # update_objects_table(cur, arch_path_dir + '/DOMA.DBF')
    # print('update DOMA completed.')

    conn.commit()
    cur.close()
    conn.close()

def menu():
    print("Enter archive URL[%s]: " % URL_KLADR)
    url = str(input())
    if not url: url = URL_KLADR

    print("Enter hostname[localhost]:")
    hostname = str(input())
    if not hostname: hostname = 'localhost'

    print("Enter port[5432]: ")
    port = str(input())
    if not port: port = '5432'

    print("Enter db user login[postgres]: ")
    user = str(input())
    if not user: user = 'postgres'

    print("Enter db user password[postgres]: ")
    password = str(input())
    if not password: password = 'postgres'

    print('Enter db name[kladr]: ')
    db_name = str(input())
    if not db_name: db_name = 'kladr'

    #which types should i import into database??
    cwd = os.getcwd()
    print("Enter directory path to store and unpack archive[%s]: " % cwd)
    path = str(input())
    if not path: path = str(cwd)

    start = time.time()
    main(url, hostname, db_name, user, password, port, path)
    end = time.time()
    print('time elapsed: ', end-start)

#arr = open('/Users/olegsergeev/PycharmProjects/Kladr/test_files/Base/KLADR.DBF', "rb").read()
#print(chardet.detect(arr))

#main('localhost', 'kladr', 'postgres', 'postgres', '5432')
menu()

