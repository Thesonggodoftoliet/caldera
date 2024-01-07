import datetime

import mysql.connector

from app import get_abilities


if __name__ == '__main__':
    data = get_abilities()
    conn = mysql.connector.connect(host="192.168.0.100", port="3306",
                                   user="root", password="ubuntu", database="attackplus")
    cursor = conn.cursor()
    i = 1
    for ability in data:
        print(ability)
        sql = ("INSERT INTO `att_testcase_caldera`(`id`,`create_time`,`update_time`,`testcase_name`,`tactic`,"
               "`technique_name`,`technique_id`,`testcase_des`,`ability_id`,`supported_platforms`,`platform`)"
               "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)")
        values = (i,datetime.datetime.now(),datetime.datetime.now(),ability["name"],ability["tactic"],
                  ability["technique_name"],ability["technique_id"],ability["description"],ability["ability_id"],
                  "","caldera")
        cursor.execute(sql, values)
        i=i+1
    conn.commit()
    cursor.close()
    conn.close()