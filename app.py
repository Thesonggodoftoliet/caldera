import json
import logging
import threading
import time
from RpcClient import RpcClient
import pika
import polling
from flask import request
import requests
from flask import Flask
import nacos
import rpc

SERVER_ADDRESSES = "http://192.168.0.108:8848"
CALDERA_URI = "http://192.168.0.108:8888/api/v2"
CALDERA_HEADER = {"KEY": "AOTZ5bQA8hSU3D-InikFzKMKAN_Z2UyfUf9HY_sQJyQ"}
MQ_HOST = "192.168.0.108"
MQ_PORT = 5672
MQ_USER = "cipc"
MQ_PASSWORD = "cipc9508"

app = Flask(__name__)


def test_task(channel, method, properties, body):
    time.sleep(3)
    body = body.decode('utf-8') + "已处理"
    channel.basic_publish(exchange='', routing_key=properties.reply_to,
                          properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                          body=body)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def mq_rpc_handler():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=MQ_HOST, port=MQ_PORT,
                                  credentials=pika.PlainCredentials(username=MQ_USER, password=MQ_PASSWORD))
    )
    channel = connection.channel()
    channel.basic_consume(queue='direct.request', on_message_callback=on_message)
    channel.start_consuming()


def on_message(channel, method, properties, body):
    request_data = json.loads(body)
    if request_data['method'] == 'executeOperation':
        threading.Thread(target=rpc.execute_operation, args=(channel, method, properties, request_data['data'])).start()
    elif request_data['method'] == 'match':
        threading.Thread(target=rpc.match_paw_ip, args=(channel, method, properties)).start()
    elif request_data['method'] == 'assign':
        threading.Thread(target=rpc.assign_ip, args=(channel, method, properties, request_data['data'])).start()
    else:
        test_task(channel, method, properties, request_data['data'])


def health_stat():
    url = CALDERA_URI + "/health"
    res = requests.get(url=url, headers=CALDERA_HEADER, verify=False)
    return res.status_code == 200


def service_register():
    client = nacos.NacosClient(SERVER_ADDRESSES)
    client.add_naming_instance("caldera", "192.168.1.109", "8085")


def service_beat():
    client = nacos.NacosClient(SERVER_ADDRESSES)
    while True:
        if health_stat():
            client.send_heartbeat("caldera", "192.168.1.109", "8085")
        time.sleep(5)


@app.route('/caldera/abilities', methods=['GET'])
def get_abilities():
    url = CALDERA_URI + "/abilities"
    res = requests.get(url=url, headers=CALDERA_HEADER)
    return res.json()


def match_ip_and_agent():
    url = CALDERA_URI + "/agents"
    res = requests.get(url=url, headers=CALDERA_HEADER)
    my_map = {}
    for item in res.json():
        info = {"paw": item["paw"], "host_name": item["host"]}
        key = str(item["group"])
        my_map[key] = info
    return my_map


@app.route('/caldera/agents', methods=['GET'])
def get_agents():
    url = CALDERA_URI + "/agents"
    res = requests.get(url=url, headers=CALDERA_HEADER)
    return res.json()


def update_agents(group, paws):
    try:
        for paw in paws:
            url = CALDERA_URI + "/agents/" + paw
            res = requests.patch(url, headers=CALDERA_HEADER, json={"group": group})
            print(res.json())
    except Exception as e:
        print(e)
        return "Fail"
    return "Success"


@app.route('/caldera/agents/<paw>', methods=['GET'])
def get_agent_by_paw(paw):
    url = CALDERA_URI + "/agents/" + paw
    res = requests.get(url=url, headers=CALDERA_HEADER)
    return res.json()


@app.route('/caldera/agents/<paw>', methods=['PATCH'])
def update_agent(paw):
    url = CALDERA_URI + "/agents/" + paw
    data = request.get_json()
    res = requests.patch(url=url, headers=CALDERA_HEADER, json=data['data'])
    return res.json()


@app.route('/caldera/deploy_commands')
def get_deploy_commands():
    url = CALDERA_URI + "/agents/deploy_commands"
    res = requests.get(url=url, headers=CALDERA_HEADER)
    return res.json()


@app.route('/caldera/adversaries', methods=['GET'])
def get_adversaries():
    url = CALDERA_URI + "/adversaries"
    res = requests.get(url, headers=CALDERA_HEADER)
    return res.json()


@app.route('/caldera/adversaries/<adversary_id>', methods=['GET'])
def get_adversary(adversary_id):
    url = CALDERA_URI + "/adversaries/" + adversary_id
    res = requests.get(url, headers=CALDERA_HEADER)
    return res.json()


@app.route('/caldera/adversaries/<adversary_id>', methods=['PUT'])
def update_adversary(adversary_id):
    url = CALDERA_URI + "/adversaries/" + adversary_id
    data = request.get_json()
    res = requests.get(url, headers=CALDERA_HEADER, json=data)
    return res.json()


@app.route('/caldera/operations', methods=['POST'])
def create_operation():
    url = CALDERA_URI + "/operations"
    data = request.get_json()
    print(data)
    res = requests.post(url, headers=CALDERA_HEADER, json=data)
    print(res.json())

    # 启动轮询
    try:
        print(res.json()['id'])
    except KeyError:
        print("出错")
    else:
        query_thread = threading.Thread(target=query_caldera_state, args=(res.json()['id'],))
        query_thread.start()
    return res.json()


def create_operation(data):
    url = CALDERA_URI + "/operations"
    res = requests.post(url, headers=CALDERA_HEADER, json=data)
    print(res.json())

    # 启动轮询
    try:
        print(res.json()['id'])
    except KeyError:
        print("出错")
    else:
        query_thread = threading.Thread(target=query_caldera_state, args=(res.json()['id'],))
        query_thread.start()
    return res.json()


@app.route('/caldera/plugins', methods=['GET'])
def get_plugins():
    url = CALDERA_URI + "/plugins"
    res = requests.get(url, headers=CALDERA_HEADER)
    return res.json()


def is_finish(response):
    obj = json.loads(response.text)
    if obj['state'] == 'finished':
        return True
    else:
        return False


@app.route('/caldera/query/<operation_id>', methods=['GET'])
def query_caldera_state(operation_id=''):
    url = CALDERA_URI + "/operations/" + operation_id
    data = polling.poll(lambda: requests.get(url=url, headers=CALDERA_HEADER, verify=False),
                        check_success=is_finish, step=300, log=logging, poll_forever=True)
    obj = json.loads(data.text)
    messages = []
    for chain in obj["chain"]:
        timeline = {"operation_id": operation_id, "paw": chain["paw"], "time": chain["decide"],
                    "filed": chain["ability"]["name"], "action": "攻击开始",
                    "ability_id": chain["ability"]["ability_id"]}
        publish_caldera(json.dumps(timeline))
        timeline["time"] = chain["collect"]
        timeline["filed"] = "攻击数据"
        timeline["action"] = "收集"
        publish_caldera(json.dumps(timeline))
        timeline["time"] = chain["finish"]
        timeline["filed"] = chain["ability"]["name"]
        timeline["action"] = "攻击结束"
        publish_caldera(json.dumps(timeline))
        message = {"start_time": chain["decide"], "end_time": chain["finish"], "command": chain["command"],
                   "technique_name": chain["ability"]["technique_name"], "case_des": chain["ability"]["description"],
                   "technique_id": chain["ability"]["technique_id"], "tactic": chain["ability"]["tactic"],
                   "status": chain["status"], "operation_id": operation_id, "testcase_name": chain["ability"]["name"],
                   "case_id": chain["id"], "paw": chain["paw"], "ability_id": chain["ability"]["ability_id"]}
        messages.append(message)
    rpclient = RpcClient()
    msg = {"method": "updateFromCaldera", "params": messages}
    response = rpclient.call(json.dumps(msg))
    print("[返回的数据]" + response)
    return response
    # 处理返回值


def publish_caldera(message=''):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=MQ_HOST, port=MQ_PORT,
                                  credentials=pika.PlainCredentials(username=MQ_USER, password=MQ_PASSWORD))
    )
    channel = connection.channel()
    channel.basic_publish(exchange='caldera', routing_key='timeline', body=message)


if __name__ == '__main__':
    if health_stat():
        service_register()
        threading.Thread(target=mq_rpc_handler).start()
        threading.Timer(5, service_beat).start()
        app.run(host='0.0.0.0', port=8085, debug=True)
