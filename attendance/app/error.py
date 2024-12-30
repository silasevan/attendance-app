from flask import render_template

def render_error_page(error_code, message=None):
    if error_code == 403:
        message = message or "You do not have permission to access this page."
    elif error_code == 404:
        message = message or "The page you are looking for does not exist."
    elif error_code == 500:
        message = message or "An internal server error occurred."
    
    return render_template(f"error/{error_code}.html", message=message), error_code
