import urllib.request
import zipfile
import os
import lzma
from dbfread import DBF
import psycopg2
import chardet
import time
from operator import itemgetter
from multiprocessing import Process

URL_KLADR = 'https://www.gnivc.ru/html/gnivcsoft/KLADR/Base.7z'

def download_file(url, dest):
    print('Downloading file...')
    urllib.request.urlretrieve(url, dest)
    print('downloaded!')


# def unzip_file():
    # with lzma.open('Base.7z') as f:


def get_object_level(code):
    code_len = len(code)
    if code_len > 17:
        lvl = 6
    elif code_len == 17:
        lvl = 5
    elif code[8:11] != '000':
        lvl = 4
    elif code[5:8] != '000':
        lvl = 3
    elif code[2:5] != '000':
        lvl = 2
    else: lvl = 1

    return lvl


def get_type_id(list, short_title, lvl):
    #list = (id, short_title, level)
    for record in list:
        if record[1] == short_title and record[2] == lvl:
            return record[0]
    return None


#empty NAME if lvl < 6
#ищет по коду и тайтлу(для домов) есть ли в базе запись
def is_in_base(kladr_code, records_from_base, is_lvl_6):
    #0 = id, 1 = code
    # c = kladr_code[:-2]
    # if name == '':
    #     for record in records_from_base:
    #         if (c == record[1][:-2]):
    #             return True
    # else:
    #     for record in records_from_base:
    #         if (c == record[1][:-2]) and record[2]==name:
    #             return True
    # return False
    if is_lvl_6:
        c = kladr_code[:-4] + '00' + kladr_code[-2:]
    else:
        c = kladr_code[:-2] + '00'
    for record in records_from_base:
        if c == record[1]:
            return True
    return False


def is_in_base_dict(kladr_code, records_from_base, is_lvl_6):
    if is_lvl_6:
        c = kladr_code[:-4] + '00' + kladr_code[-2:]
    else:
        c = kladr_code[:-2] + '00'
    try:
        rec = records_from_base[c]
        return True
    except KeyError:
        return False


def update_kladr(cur, dbf_path, types, up_set):
    table = DBF(filename=dbf_path, encoding='cp866')

    list_lvl_1 = list(); list_lvl_2 = list(); list_lvl_3 = list(); list_lvl_4 = list()
    for record in table:
        lvl = get_object_level(record['CODE'])
        if lvl == 1:
            list_lvl_1.append(record)
        elif lvl ==2:
            list_lvl_2.append(record)
        elif lvl == 3:
            list_lvl_3.append(record)
        else:
            list_lvl_4.append(record)

    start = time.time()
    update_obects(cur, list_lvl_1, 1, types, up_set)
    end = time.time()
    print('time elapsed for lvl 1: {} secs, size of list is {} : '.format((end-start), len(list_lvl_1)))

    start = time.time()
    update_obects(cur, list_lvl_2, 2, types, up_set)
    end = time.time()
    print('time elapsed for lvl 2: {} secs, size of list is {} : '.format((end-start), len(list_lvl_2)))

    start = time.time()
    update_obects(cur, list_lvl_3, 3, types, up_set)
    end = time.time()
    print('time elapsed for lvl 3: {} secs, size of list is {} : '.format((end-start), len(list_lvl_3)))

    start = time.time()
    update_obects(cur, list_lvl_4, 4, types, up_set)
    end = time.time()
    print('time elapsed for lvl 4: {} secs, size of list is {} : '.format((end-start), len(list_lvl_4)))

def update_street(cur, dbf_path, types, up_set):
    table = DBF(filename=dbf_path, encoding='cp866', load=True)
    records = table.records
    update_obects(cur, records, 5, types, up_set)


def update_doma(cur, dbf_path, types, up_set):
    table = DBF(filename=dbf_path, encoding='cp866', load=True)
    records = table.records
    update_obects(cur, records, 6, types, up_set)


def update_obects(cur, records, lvl, kladr_types, update_set):
    sorted(records, key=lambda x: x['CODE'])
    if lvl == 6:
        cur.execute("update wt_kladr_objects SET deleted = true where char_length(kladr_code) > 17;")
        if 'ДОМ' not in update_set:
            return
    r_len = len(records)
    rec_idx = 0
    parents = list(); parents_dict = dict()
    if lvl > 4:
        cur.execute("SELECT id, kladr_code as CODE from wt_kladr_objects where kladr_code <= '{}'".format(records[-1]['CODE'][:-6]+'000099'))
        parents = cur.fetchall()
        for rec in parents:
            parents_dict[rec[1]] = rec[0]
    while rec_idx < r_len-1:
        if lvl <= 4:
            if lvl == 4:
                cur.execute("SELECT id, kladr_code as CODE from wt_kladr_objects where kladr_code <= '{}'".format(records[-1]['CODE'][:-5]+'00099'))
            elif lvl == 3:
                cur.execute("SELECT id, kladr_code as CODE from wt_kladr_objects where kladr_code <= '{}'".format(records[-1]['CODE'][:-8]+'00000099'))
            else:
                cur.execute("SELECT id, kladr_code as CODE from wt_kladr_objects where kladr_code <= '{}'".format(records[-1]['CODE'][:-11]+'00000000099'))
            parents = cur.fetchall()
            parents_dict = dict()
            for rec in parents:
                parents_dict[rec[1]] = rec[0]
        q_ins = """INSERT INTO wt_kladr_objects (id, title, kladr_code, kladr_ocatd,
         kladr_index, type_id, parent_id, deleted) VALUES """
        q_up = ''
        q_up_deleted = ''

        to = (rec_idx + 100000) if (rec_idx + 100000) < r_len else r_len-1
        cur.execute("SELECT id, kladr_code from wt_kladr_objects where kladr_code >= '{}' and kladr_code <= '{}'"
                    .format(records[rec_idx]['CODE'], records[to]['CODE']))
        same_lvl_records_from_base = cur.fetchall() #CHANGE TO DICT FOR FAST SEARCH
        same_lvl_records_from_base_dict = list_to_dict(same_lvl_records_from_base)
        if lvl == 6:
            for i in range(rec_idx, to):
                houses = records[i]['NAME'].split(',')
                for house_idx in range (0, len(houses)):
                    code = records[i]['CODE'] + (str(house_idx) if house_idx>9 else '0'+str(house_idx))
                    in_b = is_in_base_dict(code, same_lvl_records_from_base_dict, True)

                    if in_b: #если в базе есть кортеж, то обновляю его
                        q_up += """UPDATE wt_kladr_objects SET title = '{}', kladr_ocatd = '{}',
                                    kladr_index = '{}', type_id = '{}', parent_id = '{}', deleted = false
                                WHERE kladr_code = '{}'; """.format(houses[house_idx], records[i]['OCATD'],
                                                                    records[i]['INDEX'], get_type_id(kladr_types, records[i]['SOCR'], lvl),
                                                                    get_parent_id(code, lvl, parents), code)
                    else: #если кортежа в базе нет, то вставляю его
                        q_ins += " (DEFAULT, '{}', '{}', '{}', '{}', '{}', '{}', '{}'), "\
                                .format(houses[house_idx], code, records[i]['OCATD'], records[i]['INDEX'],
                                        get_type_id(kladr_types, records[i]['SOCR'], lvl),
                                        get_parent_id(code, lvl, parents), 'false')
                    print("house {} completed. ".format(code))
                print('record {} completed'.format(i))
        else:
            for i in range(rec_idx, to):
                # start = time.time()
                if records[i]['SOCR'] not in update_set:
                    continue
                status = records[i]['CODE'][-2:]
                in_b = is_in_base_dict(records[i]['CODE'], same_lvl_records_from_base_dict, False)
                # in_base_time = time.time()-start
                if (status == '99' or status == '51') and in_b:
                    q_up_deleted += "UPDATE wt_kladr_objects SET deleted = true where kladr_code = '{}'; ".format(records[i]['CODE'])
                elif status == '00':
                    if in_b: #если в базе есть кортеж, то обновляю его
                        q_up += """UPDATE wt_kladr_objects SET title = '{}', kladr_code = '{}', kladr_ocatd = '{}',
                                    kladr_index = '{}', type_id = '{}', parent_id = '{}', deleted = 'false'
                                WHERE kladr_code = '{}'; """.format(records[i]['NAME'], records[i]['CODE'],
                                                                    records[i]['OCATD'], records[i]['INDEX'], get_type_id(kladr_types, records[i]['SOCR'], lvl),
                                                                    get_parent_id(records[i]['CODE'], lvl, parents), records[i]['CODE'], records[i]['CODE'])
                    else: #если кортежа в базе нет, то вставляю его
                        q_ins += " (DEFAULT, '{}', '{}', '{}', '{}', '{}', '{}', '{}'), "\
                                .format(records[i]['NAME'], records[i]['CODE'], records[i]['OCATD'], records[i]['INDEX'],
                                        get_type_id(kladr_types, records[i]['SOCR'], lvl),
                                        get_parent_id(records[i]['CODE'], lvl, parents), 'false')
                # if_time = time.time() - start - in_base_time
                # time_e = time.time() - start
                # print('Record {} completed. in_base_time {}, get_parent time {}'.format(i, in_base_time/time_e, if_time/time_e))
        if len(q_up) > 0: cur.execute(q_up) #00, есть в базе
        if len(q_up_deleted) > 0: cur.execute(q_up_deleted) #51 или 99, есть в базе
        if q_ins[-2] == ',' :
            q_ins = q_ins[:-2] + ';'
            cur.execute(q_ins) #00, нет в базе
        rec_idx = to
        print('Block completed.')
    print('Level {} completed.'.format(lvl))


def list_to_dict(list):
    res = dict()
    for record in list:
        res[record[1]] = record
    return res


#kladr_name - конкретный дом
def get_parent_id(code, lvl, parents):
    #parent = (id, CODE)
    while lvl > 0:
        if lvl == 1:
            return 1
        elif lvl == 2:
            c = code[:2]
            for record in parents:
                if c == record[1][:2]:
                    return record[0]
        elif lvl == 3:
            c = code[:5]
            for record in parents:
                if c == record[1][:5]:
                    return record[0]
        elif lvl == 4:
            c = code[:8]
            for record in parents:
                if c == record[1][:8]:
                    return record[0]
        elif lvl == 5:
            c = code[:11]
            for record in parents:
                if c == record[1][:11]:
                    return record[0]
        else:
            c = code[:15]
            for record in parents:
                if c == record[1][:15]:
                    return record[0]
        lvl -= 1
    return None


#parents are {Key : code, Value : kladr_code)
def get_parent_id_dict(code, lvl, parents):
    while lvl > 0:
        if lvl == 6:
            try:
                return parents[code[:15]+'00']
            except KeyError:
                pass
        elif lvl == 5:
            try:
                return parents[code[:11]+'00']
            except KeyError:
                pass
        elif lvl == 4:
            try:
                return parents[code[:8]+'00000']
            except KeyError:
                pass
        elif lvl == 3:
            try:
                return parents[code[:5]+'00000000']
            except KeyError:
                pass
        elif lvl == 2:
            try:
                return parents[code[:2]+('0'*11)]
            except KeyError:
                pass
        else:
            return 1
        lvl -= 1
    return None



def update_types(cur, dbf_path):
    table = DBF(filename=dbf_path, encoding='cp866')
    q = str(("""INSERT INTO wt_kladr_types (id, short_title, title, level, kladr_code)
         VALUES """))
    for record in table:
        q += """(DEFAULT, '{}', '{}', {}, {}), """.\
            format(record['SCNAME'], record['SOCRNAME'], record['LEVEL'], record['KOD_T_ST'])
    q = q[:-2] + ' ON CONFLICT (kladr_code) DO UPDATE SET short_title=EXCLUDED.short_title,' \
                 ' title= EXCLUDED.title, level=EXCLUDED.level, kladr_code=EXCLUDED.kladr_code;'
    cur.execute(q)



def main(url, hostname, db, user, pswd, port, path, up_types_set):
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


    cur.execute('SELECT id, short_title, level from wt_kladr_types;')
    types = cur.fetchall()

    cur.execute('select id from wt_kladr_objects where id = 1')
    if len(cur.fetchall()) == 0:
        cur.execute("insert into wt_kladr_objects values (1, 'Россия', 0, 0, 0, null, null, false)")

    # print('updating wt_kladr_objects from KLADR...')
    # update_kladr(cur, arch_path_dir + '/KLADR.DBF', types, up_types_set)
    # print('update KLADR completed.')
    #
    # print('updating wt_kladr_objects from STREET...')
    # update_street(cur, arch_path_dir + '/STREET.DBF', types, up_types_set)
    # print('update STREET completed.')

    print('updating wt_kladr_objects from DOMA...')
    update_doma(cur, arch_path_dir + '/DOMA.DBF', types, up_types_set)
    print('update DOMA completed.')

    conn.commit()
    cur.close()
    conn.close()


if __name__ == '__main__':
    with open('config.txt') as f:
        lines = f.readlines()
        for i in range(0, 7):
            lines[i] = lines[i][lines[i].index(':')+1:].strip()
        url = lines[0]
        hostname = lines[1]
        port = lines[2]
        user = lines[3]
        password = lines[4]
        db_name = lines[5]
        types = lines[6].split(',')
    path = os.getcwd()

    up_set = set(types)
    start = time.time()
    main(url, hostname, db_name, user, password, port, path, up_set)
    end = time.time()
    print('time elapsed: ', (end-start))

