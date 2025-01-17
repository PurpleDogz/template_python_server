from typing import Callable
from fastapi import Request, Response
import uuid
from user_agents import parse
from urllib.parse import parse_qs
from datetime import datetime
from fastapi.routing import APIRoute


from . import taskrunner, custom_logging, config

LOGGING_ID = "LoggingRoute"
LOGGER = custom_logging.getLogger(LOGGING_ID)

# Filter out all these routes, they are not needed
FILTER_LIST = ["/healthz", "/session_validate"]

###################################

_data_capture = None


def set_data_capture(func):
    global _data_capture
    _data_capture = func


def get_data_capture():
    global _data_capture
    return _data_capture


##################################

_queue = None


def set_queue(q):
    global _queue
    _queue = q


def get_queue():
    global _queue
    return _queue


_session_cookie = None


def set_session_cookie(c):
    global _session_cookie
    _session_cookie = c


def get_session_cookie():
    global _session_cookie
    return _session_cookie


class LoggingRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            # if capture_func is None:
            #     return await original_route_handler(request)

            try:
                dt = taskrunner.DurationTimer()
                response = await original_route_handler(request)
                duration = dt.duration()
                header = dict(request.headers)

                capture_func = get_data_capture()

                if capture_func is not None:
                    uuid_str = None

                    if "uuid" in header.keys():
                        uuid_str = header["uuid"]
                    else:
                        uuid_str = str(uuid.uuid4())

                    user_agent = parse("")
                    if "user-agent" in header.keys():
                        user_agent = parse(header["user-agent"])

                    browser = user_agent.browser.version
                    if len(browser) >= 2:
                        browser_major, browser_minor = browser[0], browser[1]
                    else:
                        browser_major, browser_minor = 0, 0

                    user_os = user_agent.os.version
                    if len(user_os) >= 2:
                        os_major, os_minor = user_os[0], user_os[1]
                    else:
                        os_major, os_minor = 0, 0

                    source = request.client.host
                    if "x-real-ip" in header.keys():
                        source = header["x-real-ip"]

                    # # Request json
                    # body = await request.body()
                    # if len(body)!=0:
                    #     body = json.loads(body)
                    # else:
                    #     body = ""

                    session_cookie = None
                    if (
                        get_session_cookie()
                        and get_session_cookie() in request.cookies.keys()
                    ):
                        session_cookie = request.cookies[get_session_cookie()]

                    args = parse_qs(str(request.query_params))

                    # Handle URL access and remove it from the query
                    if session_cookie is None and "access" in args.keys():
                        session_cookie = args["access"]
                        del args["access"]

                    # Fall back to header
                    if session_cookie is None:
                        if "Authorization" in request.headers.keys():
                            auth = request.headers["Authorization"]
                            if auth:
                                session_cookie = auth.replace("Bearer ", "")

                    size = (
                        header["content-length"]
                        if "content-length" in header.keys()
                        else ""
                    )

                    request_json = {
                        "type": "request",
                        "uuid": uuid_str,
                        "method": request.method,
                        "source": source,
                        "auth_key": session_cookie,
                        "user_agent": {
                            "family": user_agent.browser.family,
                            "major": browser_major,
                            "minor": browser_minor,
                            "patch": user_agent.browser.version_string,
                            "device": {
                                "family": user_agent.device.family,
                                "brand": user_agent.device.brand,
                                "model": user_agent.device.model,
                                "major": "0",
                                "minor": "0",
                                "patch": "0",
                            },
                            "os": {
                                "family": user_agent.os.family,
                                "major": os_major,
                                "minor": os_minor,
                                "patch": user_agent.os.version_string,
                            },
                        },
                        "endpoint": request.url.path,
                        "query": args,
                        "status_code": response.status_code,
                        # "body":body,
                        "size": size,
                        "duration": duration,
                        "time": datetime.utcnow().isoformat(
                            sep=" ", timespec="milliseconds"
                        ),
                    }
                    capture_func(request_json)

                if config.get().ENABLE_PERF_LOGGING_UX == config.TRUE:
                    skip = False
                    # Skip positive status code only
                    if response.status_code == 200:
                        for f in FILTER_LIST:
                            if request.url.path in f:
                                skip = True
                                break
                    if not skip:
                        size = (
                            header["content-length"]
                            if "content-length" in header.keys()
                            else ""
                        )
                        size_desc = (
                            ", Size: {} bytes".format(size) if len(size) > 0 else ""
                        )
                        LOGGER.info(
                            "API Call: {} {} = {} [Duration {} ms{}]".format(
                                request.method,
                                request.url.path,
                                response.status_code,
                                duration,
                                size_desc,
                            )
                        )

                return response
            except Exception as exc:
                LOGGER.info(
                    "API Logger Error [{}, {}] : {}".format(
                        request.method, request.url.path, str(exc)
                    )
                )
                return await original_route_handler(request)

        return custom_route_handler
