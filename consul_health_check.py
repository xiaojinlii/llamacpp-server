from datetime import datetime

from fastapi import APIRouter, FastAPI
from starlette.responses import JSONResponse

from consul_register import get_consul_settings

router = APIRouter()


def register_consul_health_check_router(app: FastAPI):
    consul_settings = get_consul_settings()
    if consul_settings.is_register:
        app.include_router(router)


def is_time_in_range(start_time, end_time):
    """
    判断当前时间是否在start_time和end_time之间。
    start_time和end_time格式应为"HH:MM"字符串。
    """
    now = datetime.now()  # 获取当前时间
    current_time = now.time()  # 只保留时间部分

    # 将字符串格式的开始时间和结束时间转换为time对象
    start = datetime.strptime(start_time, "%H:%M").time()
    end = datetime.strptime(end_time, "%H:%M").time()

    # 判断当前时间是否在开始时间和结束时间之间
    if start <= current_time <= end:
        return True
    else:
        return False


@router.get("/health")
async def health_check():
    try:
        # in_time = is_time_in_range("11:33", "11:35")
        # return JSONResponse({"status": "OK"}, status_code=400 if in_time else 200)
        return JSONResponse({"status": "OK"},  200)
    except Exception as e:
        return JSONResponse({"status": "FAILED", "msg": str(e)}, status_code=503)
