import requests
import hashlib
from pprint import pprint
class sonnenbatterie:
    def __init__(self,username,password,ipaddress):
        self.username=username
        self.password=password
        self.ipaddress=ipaddress
        self.baseurl='http://'+self.ipaddress+'/api/'
        self._login()


    def _login(self):
        password_sha512 = hashlib.sha512(self.password.encode('utf-8')).hexdigest()
        req_challenge=requests.get(self.baseurl+'challenge')
        req_challenge.raise_for_status()
        challenge=req_challenge.json()
        response=hashlib.pbkdf2_hmac('sha512',password_sha512.encode('utf-8'),challenge.encode('utf-8'),7500,64).hex()
        
        #print(password_sha512)
        #print(challenge)
        #print(response)
        getsession=requests.post(self.baseurl+'session',{"user":self.username,"challenge":challenge,"response":response})
        getsession.raise_for_status()
        #print(getsession.text)
        token=getsession.json()['authentication_token']
        #print(token)
        self.token=token
    
    def _get(self,what,isretry=False):
        response=requests.get(self.baseurl+what,
            headers={'Auth-Token': self.token},
        )
        if not isretry and response.status_code==401:
            self._login()
            return self._get(self,what,True)
        if response.status_code != 200:
            response.raise_for_status()

        return response.json()

    def get_powermeter(self):
        return self._get("powermeter")
        
    def get_batterysystem(self):
        return self._get("battery_system")
        
    def get_inverter(self):
        return self._get("inverter")
    
    def get_systemdata(self):
        return self._get("system_data")

    def get_status(self):
        return self._get("v1/status")

        
        

        
    
        
