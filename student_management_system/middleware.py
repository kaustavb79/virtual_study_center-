from django.utils.deprecation import MiddlewareMixin


class CustomMiddleware(MiddlewareMixin):

    def process_request(self, request):

        # set API URL here
        SCHEME = request.scheme
        HOST = request.get_host()
        API_URL = SCHEME + '://' + HOST
        request.api_url = API_URL