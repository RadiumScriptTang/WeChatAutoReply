# f = "aaa"
import sys

def fx():
    print(f)

if  __name__ == "__main__":
    f = 123
    fx()
    print(sys.argv)
    f = open("reply.txt","r",encoding="UTF-8")
    s = ''.join(f)
    print(s)