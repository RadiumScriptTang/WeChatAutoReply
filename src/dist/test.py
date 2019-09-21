import os
import re
import time
import itchat
from itchat.content import *
from requests import post
from json import dumps
from random import randint

# 说明：可以撤回的有文本文字、语音、视频、图片、位置、名片、分享、附件
# {msg_id:(msg_from,msg_to,msg_time,msg_time_rec,msg_type,msg_content,msg_share_url)}
msg_dict = {}
# 呼叫转移队列
messageTransferFriends = None
# 机器人回复队列
robotReplyFriendsList = []
# 文件存储临时目录
rev_tmp_dir = "/msg/"
if not os.path.exists(rev_tmp_dir): os.mkdir(rev_tmp_dir)

# 表情有一个问题 | 接受信息和接受note的msg_id不一致 巧合解决方案
face_bug = None

firstReplyMessage = "这是自动回复，我现在出去上课了\n" \
                    "如果有紧急情况找我\n" \
                    "可以通过以下方式联系我\n" \
                    "1.QQ 1760768391\n" \
                    "2.回复\"转接\"，为您转接我的秘书\n" \
                    "继续发送消息将为您转接机器人"


# 将接收到的消息存放在字典中，当接收到新消息时对字典中超时的消息进行清理 | 不接受不具有撤回功能的信息
# [TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO, FRIENDS, NOTE]、

@itchat.msg_register([TEXT, PICTURE, MAP, CARD, SHARING, RECORDING, ATTACHMENT, VIDEO])
def handler_receive_msg(msg, isGroupChat=False):
    global robotReplyFriendsList
    global messageTransferFriends
    global face_bug
    agent = itchat.search_friends(name="耿土奇")[0]["UserName"]
    # 获取的是本地时间戳并格式化本地时间戳 e: 2017-04-21 21:30:08
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    # 消息ID
    msg_id = msg['MsgId']
    # 消息时间
    msg_time = msg['CreateTime']
    # 消息发送人昵称 | 这里也可以使用RemarkName备注　但是自己或者没有备注的人为None
    if (itchat.search_friends(userName=msg['FromUserName']))["RemarkName"]:
        msg_from = (itchat.search_friends(userName=msg['FromUserName']))["RemarkName"]
    else:
        msg_from = (itchat.search_friends(userName=msg['FromUserName']))["NickName"]
    # 消息内容
    msg_content = None
    # 分享的链接
    msg_share_url = None
    if msg['Type'] == 'Text' \
            or msg['Type'] == 'Friends':
        msg_content = msg['Text']
        # 好友选择转接
        if msg["Text"] == "转接":
            # 成功转接
            if messageTransferFriends is None:
                messageTransferFriends = msg["FromUserName"]
                itchat.send("已为您转接",msg["FromUserName"])
            else:
                itchat.send("以占线，转接失败",msg["FromUserName"])
        elif msg["Text"] == "结束" :
            if messageTransferFriends == msg["FromUserName"]:
                messageTransferFriends = None
            if messageTransferFriends in robotReplyFriendsList:
                robotReplyFriendsList.remove(msg["FromUserName"])
        elif messageTransferFriends == msg["FromUserName"]:
            itchat.send("这是来自我的好友" + msg["User"]["RemarkName"] + "的消息\n" + msg["Text"],agent) # 需要代理人的id

        elif msg["FromUserName"] == agent: #需要代理人id
            itchat.send("我的秘书回复了您：\n" + msg["Text"] + "\n完成后请及时回复\"结束\"",messageTransferFriends)

        elif msg["FromUserName"] in robotReplyFriendsList:
            reply_data = {
                "reqType": 0,
                "perception": {
                    "inputText": {
                        "text": msg_content
                    }
                },
                "userInfo": {
                    "userId": "151896",
                    "apiKey": "0faecbb220634ae39aef98fd238612fc"
                }
            }
            r = post("http://openapi.tuling123.com/openapi/api/v2", dumps(reply_data))
            reply = "以下为自动回复\n" \
                    + r.json()["results"][0]['values']['text'] \
                    + "\n结束机器人聊天请回复\"结束\""
            itchat.send(reply, msg['FromUserName'])
        else:
            itchat.send(firstReplyMessage,msg["FromUserName"])
            robotReplyFriendsList.append(msg["FromUserName"])
            print(msg["FromUserName"],msg["User"]["RemarkName"])

    if msg['Type'] == 'Recording' \
            or msg['Type'] == 'Attachment' \
            or msg['Type'] == 'Video' \
            or msg['Type'] == 'Picture':
        msg_content = r"" + msg['FileName']
        # 保存文件
        msg['Text'](rev_tmp_dir + msg['FileName'])
    elif msg['Type'] == 'Card':
        msg_content = msg['RecommendInfo']['NickName'] + r" 的名片"
    elif msg['Type'] == 'Map':
        x, y, location = re.search(
            "<location x=\"(.*?)\" y=\"(.*?)\".*label=\"(.*?)\".*", msg['OriContent']).group(1, 2, 3)
        if location is None:
            msg_content = r"纬度->" + x.__str__() + " 经度->" + y.__str__()
        else:
            msg_content = r"" + location
    elif msg['Type'] == 'Sharing':
        msg_content = msg['Text']
        msg_share_url = msg['Url']
    face_bug = msg_content
    # 更新字典
    msg_dict.update(
        {
            msg_id: {
                "msg_from": msg_from, "msg_time": msg_time,
                "msg_time_rec": msg_time_rec, "msg_username":msg["FromUserName"],
                "msg_type": msg["Type"],
                "msg_content": msg_content, "msg_share_url": msg_share_url
            }
        }
    )


# 收到note通知类消息，判断是不是撤回并进行相应操作
@itchat.msg_register([NOTE])
def send_msg_helper(msg):
    global face_bug
    if re.search(r"\<\!\[CDATA\[.*撤回了一条消息\]\]\>", msg['Content']) is not None:
        # 获取消息的id
        old_msg_id = re.search("\<msgid\>(.*?)\<\/msgid\>", msg['Content']).group(1)
        old_msg = msg_dict.get(old_msg_id, {})
        if len(old_msg_id) < 11:
            itchat.send_file(rev_tmp_dir + face_bug, toUserName='filehelper')
            os.remove(rev_tmp_dir + face_bug)
        else:
            msg_body = old_msg.get('msg_from') + " 撤回了 " + old_msg.get("msg_type") + " 消息" + "\n" \
                       + old_msg.get('msg_time_rec') + "\n" \
                       + r"" + old_msg.get('msg_content')
            # 如果是分享存在链接
            if old_msg['msg_type'] == "Sharing": msg_body += "\n链接➣ " + old_msg.get('msg_share_url')
            msg_body_laugh = '你' + " 撤回了消息" + "\n" \
                       + r"" + old_msg.get('msg_content') + "\n" + "别以为我没发现哦"
            # 将撤回消息发送到文件助手
            itchat.send(msg_body_laugh, old_msg.get('msg_username'))
            print(msg_body)
            # 有文件的话也要将文件发送回去
            if old_msg["msg_type"] == "Picture" \
                    or old_msg["msg_type"] == "Recording" \
                    or old_msg["msg_type"] == "Video" \
                    or old_msg["msg_type"] == "Attachment":
                file = '@fil@%s' % (rev_tmp_dir + old_msg['msg_content'])
                itchat.send(msg=file, toUserName='filehelper')
                os.remove(rev_tmp_dir + old_msg['msg_content'])
            # 删除字典旧消息
            msg_dict.pop(old_msg_id)


if __name__ == '__main__':
    itchat.auto_login(hotReload=True, enableCmdQR=False)
    itchat.run()




