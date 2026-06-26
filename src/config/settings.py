import os
from dataclasses import dataclass


@dataclass
class Settings:
    postgres_host: str
    postgres_port: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    gateway_address: str
    enable_tls: bool
    tls_ca_cert_path: str
    tls_client_cert_path: str
    tls_client_key_path: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            postgres_host=os.getenv("POSTGRES_HOST", "localhost"),
            postgres_port=os.getenv("POSTGRES_PORT", "5432"),
            postgres_db=os.getenv("POSTGRES_DB", "brilliant_sql"),
            postgres_user=os.getenv("POSTGRES_USER", "turing_admin"),
            postgres_password=os.getenv("POSTGRES_PASSWORD", ""),
            gateway_address=os.getenv("GATEWAY_ADDRESS", "localhost:50051"),
            enable_tls=os.getenv("ENABLE_TLS", "false").lower() == "true",
            tls_ca_cert_path=os.getenv("TLS_CA_CERT_PATH", ""),
            tls_client_cert_path=os.getenv("TLS_CLIENT_CERT_PATH", ""),
            tls_client_key_path=os.getenv("TLS_CLIENT_KEY_PATH", ""),
        )
