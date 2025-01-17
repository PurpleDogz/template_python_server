from fastapi.responses import JSONResponse

ERROR_NONE = 200

ERROR_INTERNAL = 500
ERROR_AUTH = 401
ERROR_FORBIDDEN = 403
ERROR_NOT_FOUND = 404
ERROR_INVALID_PARAMETERS = 400

ERRORS = {
    ERROR_INTERNAL: "Internal Failure",
    ERROR_AUTH: "Authentication Failure",
    ERROR_FORBIDDEN: "Forbidden",
    ERROR_NOT_FOUND: "Not Found",
    ERROR_INVALID_PARAMETERS: "Invalid Parameters",
}

RESULT_FAIL = "fail"
RESULT_SUCCESS = "success"


def get_error_json(error, extra=None):
    ret = {"result": RESULT_FAIL, "errorid": error, "message": ERRORS[error]}
    if extra:
        ret = ret | extra

    return JSONResponse(status_code=error, content=ret)


def get_success_json(extra=None):
    ret = {"result": RESULT_SUCCESS}

    if extra:
        ret = ret | extra

    return JSONResponse(status_code=ERROR_NONE, content=ret)
