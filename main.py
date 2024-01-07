# This is a sample Python script.
import logging
import math
import re

import requests
from neo4j import GraphDatabase
from neo4j.exceptions import DriverError, Neo4jError


# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


class App:
    def __init__(self, uri, user, password, database=None):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def create_vul(self, cve_id, cvss_v2, cvss_v3, risk_level, name, synopsis, description, solution, references,
                   plugin_id):
        query = ("MERGE (v:Vulnerability{cve_id:$cve_id, plugin_id:$plugin_id}) ON CREATE SET v.cvss_v2=$cvss_v2, "
                 "v.cvss_v3=$cvss_v3, v.risk_level=$risk_level, v.name=$name, v.synopsis=$synopsis, "
                 "v.description=$description, v.solution=$solution, v.references=$references RETURN v.cve_id")
        try:
            record = self.driver.execute_query(query, cve_id=cve_id, plugin_id=plugin_id,
                                               cvss_v2=cvss_v2, cvss_v3=cvss_v3,
                                               risk_level=risk_level, name=name, synopsis=synopsis,
                                               description=description, solution=solution, references=references,
                                               database_=self.database, result_transformer_=
                                               lambda r: r.single(strict=True))
            return {"v": record["v.cve_id"]}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise

    def create_service(self, plugin_id, name, description):
        query = ("MERGE (s:Service{plugin_id:$plugin_id}) ON CREATE SET s.name=$name, s.description=$description "
                 "RETURN s.plugin_id")
        try:
            record = self.driver.execute_query(query, plugin_id=plugin_id, name=name, description=description,
                                               database_=self.database, result_transformer_=
                                               lambda r: r.single(strict=True))
            return {"s": record["s.plugin_id"]}
        except (DriverError, Neo4jError) as exception:
            logging.error("%s raised an error: \n%s", query, exception)
            raise


if __name__ == "__main__":
    scheme = "bolt"
    host_name = "192.168.0.100"
    port = 7687
    uri = f"{scheme}://{host_name}:{port}"
    user = "neo4j"
    password = "cipc9508"
    app = App(uri, user, password, database="neo4j")
    total = 30
    begin = 1
    try:
        while begin <= total:
            print(begin)
            url = ("https://zh-cn.tenable.com/_next/data/GXZNLG_656EYaiM0enZdY/zh-CN/plugins/nessus/families/"
                   "Web%20Servers.json?page="+str(begin)+"&type=nessus&family=Web+Servers")
            data = requests.get(url).json()
            plugins = data["pageProps"]["plugins"]
            for i in plugins:
                plugin_id = i["_id"]
                print(plugin_id)
                temp_url = ("https://zh-cn.tenable.com/_next/data/GXZNLG_656EYaiM0enZdY/zh-CN"
                            "/plugins/nessus/" + str(plugin_id) + ".json?type=nessus&id=" + str(plugin_id))
                plugin_data = requests.get(temp_url).json()
                plugin = plugin_data["pageProps"]["plugin"]
                if "asset_inventory" in plugin and plugin["asset_inventory"] is True:
                    print("plugin_id")
                    service_name = re.sub('[\u4e00-\u9fa5]', '', plugin["script_name"])
                    app.create_service(plugin_id, service_name, plugin["description"])
            begin = begin + 1
    finally:
        app.close()
