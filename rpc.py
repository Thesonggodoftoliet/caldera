import json

import pika
from app import get_adversary, create_operation, match_ip_and_agent, update_agents


def execute_operation(channel, method, properties, body):
    data = body
    adversary = get_adversary(data['adversaryId'])
    form = {
        "adversary": adversary,
        "name": data["operationName"],
        "id": data["operationId"],
        "jitter": "2/8",
        "auto_close": True,
        "group": "",
        "use_learning_parsers": True,
        "autonomous": 1,
        "source": {
            "rules": [
                {
                    "trait": "file.sensitive.extension",
                    "match": ".*",
                    "action": "DENY"
                },
                {
                    "trait": "file.sensitive.extension",
                    "match": "png",
                    "action": "ALLOW"
                },
                {
                    "trait": "file.sensitive.extension",
                    "match": "yml",
                    "action": "ALLOW"
                },
                {
                    "trait": "file.sensitive.extension",
                    "match": "wav",
                    "action": "ALLOW"
                }
            ],
            "id": "ed32b9c3-9593-4c33-b0db-e2007315096b",
            "name": "basic",
            "facts": [
                {
                    "value": "wav",
                    "score": 1,
                    "name": "file.sensitive.extension",
                    "collected_by": [],
                    "unique": "file.sensitive.extensionwav",
                    "limit_count": -1,
                    "technique_id": None,
                    "relationships": [],
                    "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
                    "links": [],
                    "trait": "file.sensitive.extension",
                    "origin_type": "SEEDED",
                    "created": "2023-12-06T11:51:21Z"
                },
                {
                    "value": "yml",
                    "score": 1,
                    "name": "file.sensitive.extension",
                    "collected_by": [],
                    "unique": "file.sensitive.extensionyml",
                    "limit_count": -1,
                    "technique_id": None,
                    "relationships": [],
                    "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
                    "links": [],
                    "trait": "file.sensitive.extension",
                    "origin_type": "SEEDED",
                    "created": "2023-12-06T11:51:21Z"
                },
                {
                    "value": "png",
                    "score": 1,
                    "name": "file.sensitive.extension",
                    "collected_by": [],
                    "unique": "file.sensitive.extensionpng",
                    "limit_count": -1,
                    "technique_id": None,
                    "relationships": [],
                    "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
                    "links": [],
                    "trait": "file.sensitive.extension",
                    "origin_type": "SEEDED",
                    "created": "2023-12-06T11:51:21Z"
                },
                {
                    "value": "keyloggedsite.com",
                    "score": 1,
                    "name": "server.malicious.url",
                    "collected_by": [],
                    "unique": "server.malicious.urlkeyloggedsite.com",
                    "limit_count": -1,
                    "technique_id": None,
                    "relationships": [],
                    "source": "ed32b9c3-9593-4c33-b0db-e2007315096b",
                    "links": [],
                    "trait": "server.malicious.url",
                    "origin_type": "SEEDED",
                    "created": "2023-12-06T11:51:21Z"
                }
            ],
            "plugin": "stockpile",
            "adjustments": [],
            "relationships": []
        },
        "visibility": 51,
        "planner": {
            "description": "During each phase of the operation, the atomic planner iterates through each agent and sends" +
                           " the next\navailable ability it thinks that agent can complete. This decision is based on the agent" +
                           " matching the operating\nsystem (execution platform) of the ability and the ability command having no" +
                           " unsatisfied variables.\nThe planner then waits for each agent to complete its command before" +
                           " determining the subsequent abilities.\nThe abilities are processed in the order set by each agent's" +
                           " atomic ordering.\nFor instance, if agent A has atomic ordering (A1, A2, A3) and agent B has atomic" +
                           " ordering (B1, B2, B3), then\nthe planner would send (A1, B1) in the first phase, then (A2, B2), etc.\n",
            "name": "atomic",
            "ignore_enforcement_modules": [],
            "stopping_conditions": [],
            "params": {},
            "id": "aaa7c857-37a0-4c4a-85f7-4e9f7f30e31a",
            "allow_repeatable_abilities": False,
            "plugin": "stockpile",
            "module": "plugins.stockpile.app.atomic"
        },
        "obfuscator": "plain-text",
        "objective": {
            "description": "This is a default objective that runs forever.",
            "id": "495a9828-cab1-44dd-a0ca-66e58177d8cc",
            "name": "default",
            "goals": [
                {
                    "value": "complete",
                    "target": "exhaustion",
                    "achieved": False,
                    "count": 1048576,
                    "operator": "=="
                }
            ],
            "percentage": 0
        }
    }
    res = create_operation(form)
    if data["operationId"] == res["id"]:
        res = "success"
    else:
        res = "fail"
    channel.basic_publish(exchange='', routing_key=properties.reply_to,
                          properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                          body=res)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def match_paw_ip(channel, method, properties):
    res = match_ip_and_agent()
    channel.basic_publish(exchange='', routing_key=properties.reply_to,
                          properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                          body=json.dumps(res))
    channel.basic_ack(delivery_tag=method.delivery_tag)


def assign_ip(channel, method, properties, body):
    data = body
    res = update_agents(data["group"], data["paws"])
    channel.basic_publish(exchange='', routing_key=properties.reply_to,
                          properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                          body=res)
    channel.basic_ack(delivery_tag=method.delivery_tag)
