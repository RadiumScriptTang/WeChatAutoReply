# WeChatAutoReply
-------------------------------------------------------
### source code
source code is in the folder src.
The code is terrible, so I suggest not try to read it. It is because the code actually needs rebuilding but I didn't as I was lasy.

### executable release program
radiumWeChatAutoReply is for linux and the other with ending ".exe" is for windows.

start them as following:
```
#windows
radiumWeChatAutoReply reply.txt [TransferToFriendRemarkName]
#linux
./radiumWeChatAutoReply reply.txt [TransferToFriendRemarkName]
```
The parameter reply.txt defines a file that includes a default text to reply your friends when you are busy, and it's better to get the file and the executable program in the same folder.
The parameter TransferToFriendRemarkName is optional. If it is missing, then the program will only reply your friends with text prepared. Else the program will transfer your friends' message to the person you selected here(with its remark name) after your friends message "转接".

Be careful that once your friend recalls a message, the program will laugh at the friend by sending him or her the recalled message, which sometimes could be dangerous.
