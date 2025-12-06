import jwt
from django.contrib.auth.models import User

class MicrosoftTokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("JWT "):
            token = auth_header.split("JWT ")[1]
            try:
                decoded = jwt.decode(token, options={"verify_signature": False})
                email = (
                    decoded.get("preferred_username") or
                    decoded.get("upn") or
                    decoded.get("unique_name") or
                    decoded.get("email")
                )
                user = User.objects.filter(email=email).first()
                
                request.user = user
                request._dont_enforce_csrf_checks = True
    
            except jwt.DecodeError: 
                request.user = None
 
        return self.get_response(request)  # 👈 IMPORTANT
