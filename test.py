from time import sleep

from asynchttp import AsyncHttp

asyncHttp = AsyncHttp()
for i in range(1,500):
    asyncHttp.request("get", "http://www.google.com", None, None)

print('waiting')
sleep(5)
