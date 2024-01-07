import datetime
import mysql.connector
from app import get_adversaries

if __name__ == '__main__':
    data = get_adversaries()
    conn = mysql.connector.connect(host="192.168.0.100", port="3306",
                                   user="root", password="ubuntu", database="attackplus")
    cursor = conn.cursor()
    i = 1
    j = 1
    for adversary in data:
        print(adversary)
        adversary_sql = ("INSERT INTO `att_campaign`(`id`,`create_time`,`update_time`,`campaign_name`,"
                         "`campaign_description`,`adversary_id`) VALUES (%s,%s,%s,%s,%s,%s)")
        adversary_values = (
            i, datetime.datetime.now(), datetime.datetime.now(), adversary['name'], adversary['description'],
            adversary['adversary_id'])
        atomics = adversary['atomic_ordering']
        k = 1
        for atomic in atomics:
            sql = "SELECT id FROM `att_testcase_caldera` WHERE `ability_id`=%s"
            value = (atomic,)
            cursor.execute(sql, value)
            result = cursor.fetchone()
            sql = ("INSERT INTO `att_testcase_campaign` (`id`,`campaign_id`,`testcase_id`,`platform`,`priority`) "
                   "VALUES (%s,%s,%s,%s,%s)")
            values = (j, i, result[0], 'caldera', k)
            print(str(j) + " : " + str(i) + " : " + str(k))
            j = j + 1
            k = k + 1
            cursor.execute(sql, values)
        cursor.execute(adversary_sql, adversary_values)
        i = i + 1
    conn.commit()
    cursor.close()
    conn.close()
