import asyncio
import inspect
import os
from pathlib import Path


os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DATABASE_PATH", str(Path("/tmp/office_agent_test.db")))


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: run async test functions")


def pytest_pyfunc_call(pyfuncitem):
    if not inspect.iscoroutinefunction(pyfuncitem.obj):
        return None

    kwargs = {
        name: pyfuncitem.funcargs[name]
        for name in pyfuncitem._fixtureinfo.argnames
        if name in pyfuncitem.funcargs
    }
    asyncio.run(pyfuncitem.obj(**kwargs))
    return True
