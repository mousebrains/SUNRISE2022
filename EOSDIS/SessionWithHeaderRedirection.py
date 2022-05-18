#
# Keep authorization cookies through redirects
#
# May-2022, Pat Welch, pat@mousebrains.com
 
import requests

class Session(requests.Session):
    # Deal with authorization through redirects to authHost
    # This was built for dealing with eosdis authentication
    def __init__(self, username:str, codigo:str, authHost:str="urs.earthdata.nasa.gov"):
        super().__init__()
        self.auth = (username, codigo)
        self.__authHost = authHost

    def rebuild_auth(self, request, response): # Override
        headers = request.headers
        if "Authorization" not in headers: return
        requestName  = requests.utils.urlparse(request.url).hostname
        responseName = requests.utils.urlparse(response.request.url).hostname
        if (requestName != responseName) and \
                (requestName != self.__authHost) and \
                (responseName != self.__authHost):
                    del headers["Authorization"]
