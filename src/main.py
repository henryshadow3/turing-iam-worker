import logging
import grpc
import sys
import os
import json
from concurrent import futures
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.getcwd(), "src"))

from protos import worker_service_pb2
from protos import worker_service_pb2_grpc
from protos import event_service_pb2
from protos import event_service_pb2_grpc

from config.settings import Settings
from infrastructure.di.container import DependencyContainer
from application.business import business_logic

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - iam-worker - %(filename)s:%(lineno)d - %(message)s",
)
logger = logging.getLogger(__name__)


class IAMWorkerService(worker_service_pb2_grpc.GenericWorkerServicer):
    def __init__(self, settings: Settings, container: DependencyContainer):
        self.settings = settings
        self.container = container

    def HandleAction(self, request, context):
        event = request.event
        logger.info(f"Received event: {event}")

        try:
            payload_dict = self._deserialize(event, request.payload)
            context_dict = self._deserialize("context", request.context)
            context_dict["event"] = event

            result = business_logic(payload_dict, context_dict, self.container)

            if result.get("error"):
                return worker_service_pb2.ActionResponse(
                    success=False,
                    message=f"Error: {result['error']}",
                )

            if result.get("domain_events") and len(result["domain_events"]) > 0:
                out_event = result["domain_events"][0]
            else:
                out_event = event.replace(".in", ".out") if event.endswith(".in") else f"{event}.out"

            response_bytes = self._serialize(out_event, result["response"])

            return worker_service_pb2.ActionResponse(
                success=True,
                message="OK",
                data=response_bytes,
            )

        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.error(f"Unhandled error in HandleAction: {e}")
            return worker_service_pb2.ActionResponse(success=False, message=str(e))

    def _get_gateway_channel(self):
        if self.settings.enable_tls:
            try:
                ca   = open(self.settings.tls_ca_cert_path,     "rb").read()
                cert = open(self.settings.tls_client_cert_path, "rb").read()
                key  = open(self.settings.tls_client_key_path,  "rb").read()
                creds = grpc.ssl_channel_credentials(
                    root_certificates=ca, private_key=key, certificate_chain=cert
                )
                return grpc.secure_channel(self.settings.gateway_address, creds)
            except Exception as e:
                logger.warning(f"TLS setup failed, falling back to insecure: {e}")
        return grpc.insecure_channel(self.settings.gateway_address)

    def _deserialize(self, event: str, data_bytes: bytes) -> dict:
        if not data_bytes:
            return {}
        with self._get_gateway_channel() as channel:
            stub = event_service_pb2_grpc.EventServiceStub(channel)
            response = stub.DeserializeEvent(
                event_service_pb2.DeserializeRequest(event=event, data=data_bytes)
            )
            return json.loads(response.json_data)

    def _serialize(self, event: str, data_dict: dict) -> bytes:
        with self._get_gateway_channel() as channel:
            stub = event_service_pb2_grpc.EventServiceStub(channel)
            response = stub.ProcessEvent(
                event_service_pb2.EventRequest(event=event, data=json.dumps(data_dict))
            )
            return response.response


def serve():
    settings  = Settings.from_env()
    container = DependencyContainer(settings)

    port   = os.getenv("GRPC_PORT", "50053")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    worker_service_pb2_grpc.add_GenericWorkerServicer_to_server(
        IAMWorkerService(settings, container), server
    )
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info(f"IAM Worker started on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("Shutting down IAM Worker")
        container.close()


if __name__ == "__main__":
    serve()
