from datetime import datetime, timedelta
import paramiko
import sys
import time
import pymongo
import pdb
client = pymongo.MongoClient("mongodb://thedash:dash1234@10.106.22.171:27017/estore?replicaSet=rs0")
db = client["estore"]


pdb.set_trace()
today_data = db.dtvchannelautomations.find()

for rec in today_data:
    acl_no = rec.get("acl_no")
    result = rec.get("result")
    switch_mgt_ip = rec.get("switch_ip")
    try:
    if "stb_details" in rec:
        for sub in rec["stb_details"]:
            if "multicast_ip" in sub:
                multicast_ip = sub.get("multicast_ip")
                    db.dtvehospitalityacls.update(
                        {'acl_no': acl_no, 
                         'acl_output_ip':multicast_ip,
                          'switch_mgt_ip':switch_mgt_ip
                         },
                        {
                            '$set': {
                                'result': result,
                            }
                        }
                    )