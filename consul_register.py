import os
import uuid
from contextlib import asynccontextmanager
from typing import Optional, List

from consul import Consul, Check
from fastapi import FastAPI
from llama_cpp.server.settings import ModelSettings
from pydantic import Field
from pydantic_settings import BaseSettings


class ConsulSettings(BaseSettings):
    """Consul settings."""

    is_register: bool = Field(default=False, description="is register")
    consul_host: str = Field(default="localhost", description="Consul address")
    consul_port: int = Field(default=8500, description="Consul port")
    bind_service_host: str = Field(default="localhost", description="Bind service address")
    bind_service_port: int = Field(default=8000, description="Bind service port")


_all_service_id = []
_consul: Optional[Consul] = None
_consul_settings: Optional[ConsulSettings] = None
_model_settings: Optional[List[ModelSettings]] = None


def init_consul():
    global _consul_settings, _consul

    config_file = os.environ.get("CONSUL_CONFIG_FILE", "configs/config_consul.json")
    with open(config_file, "rb") as f:
        _consul_settings = ConsulSettings.model_validate_json(f.read())
        if _consul_settings.is_register:
            _consul = Consul(host=_consul_settings.consul_host, port=_consul_settings.consul_port)


def get_consul_settings():
    return _consul_settings


def set_model_settings(model_settings: List[ModelSettings]):
    for model in model_settings:
        assert (
                model.model_alias is not None
        ), "The model_alias attribute must be included in the model configuration file."

    global _model_settings
    _model_settings = model_settings


def register_services():
    for model in _model_settings:
        service_name = model.model_alias.lower()
        service_id = f"{service_name}-{uuid.uuid4()}"

        route_name = service_name.replace(".", "_")
        fabio_tag = f"urlprefix-/{route_name} strip=/{route_name}"
        tags = ["embeddings" if model.embedding else "chat", fabio_tag]
        health_url = f"http://{_consul_settings.bind_service_host}:{_consul_settings.bind_service_port}/health"

        result = _consul.agent.service.register(
            name=service_name,
            service_id=service_id,
            address=_consul_settings.bind_service_host,
            port=_consul_settings.bind_service_port,
            tags=tags,
            check=Check.http(health_url, interval="10s"),
        )
        print(
            f"register service {'success' if result else 'failed'}. service_name:{service_name}, service_id:{service_id}")
        if result:
            _all_service_id.append(service_id)


def deregister_services():
    for service_id in _all_service_id:
        result = _consul.agent.service.deregister(service_id=service_id)
        print(f"deregister service {'success' if result else 'failed'}. service_id:{service_id}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    if _consul_settings.is_register:
        register_services()

    yield

    if _consul_settings.is_register:
        deregister_services()
