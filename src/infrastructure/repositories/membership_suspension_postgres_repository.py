import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any
from result import Result, Ok, Err
from sqlmodel import select

from domain.repositories.membership_suspension_repository import MembershipSuspensionRepository
from infrastructure.database.session_manager import SQLSessionManager
from infrastructure.models.iam_models import (
    MembershipSuspension,
    UserMembership,
    ApplicationMembership,
    User,
)

logger = logging.getLogger(__name__)

# table_name polimórfico -- únicas dos tablas que este interruptor apaga.
USER_MEMBERSHIPS = "user_memberships"
APPLICATION_MEMBERSHIPS = "application_memberships"


class MembershipSuspensionPostgresRepository(MembershipSuspensionRepository):
    def __init__(self, sql_session: SQLSessionManager):
        self.sql_session = sql_session

    def suspend(self, user_id: str) -> Result[Dict[str, Any], str]:
        """iam.user.suspend_membership.in — apaga TODAS las afiliaciones y
        accesos activos de un usuario de un jalón, guardando snapshot para
        poder restaurar exactamente ese estado después.

        No toca turing.users.is_active (mecanismo distinto y ya existente).
        Si ya hay una suspensión vigente, es un error explícito -- no se
        "apila" ni se re-snapshotea sobre un apagón ya en curso.
        """
        try:
            uid = uuid.UUID(user_id)

            user = self.sql_session.session.exec(
                select(User).where(User.id == uid)
            ).first()
            if not user:
                return Err("USER_NOT_FOUND")

            already_active = self.sql_session.session.exec(
                select(MembershipSuspension).where(
                    MembershipSuspension.user_id == uid,
                    MembershipSuspension.is_active_suspension == True,  # noqa: E712
                )
            ).first()
            if already_active:
                return Err("MEMBERSHIP_ALREADY_SUSPENDED")

            active_memberships = self.sql_session.session.exec(
                select(UserMembership).where(
                    UserMembership.user_id == uid,
                    UserMembership.is_active == True,  # noqa: E712
                )
            ).all()
            active_accesses = self.sql_session.session.exec(
                select(ApplicationMembership).where(
                    ApplicationMembership.user_id == uid,
                    ApplicationMembership.is_active == True,  # noqa: E712
                )
            ).all()

            # No-op válido (Ok, no Err): si el usuario ya no tenía nada
            # activo, "suspender" no es una operación fallida -- simplemente
            # no hay nada que apagar. El snapshot queda vacío a propósito
            # (no se crea ninguna fila en membership_suspensions), así que
            # membership_suspension_status.in seguirá reportando
            # suspended=false y restore_membership.in devolverá
            # NO_ACTIVE_SUSPENSION si se invoca -- comportamiento correcto,
            # no había nada que restaurar.
            snapshot_rows = []
            for row in active_memberships:
                snapshot_rows.append(MembershipSuspension(
                    user_id=uid, table_name=USER_MEMBERSHIPS, row_id=row.id,
                ))
                row.is_active = False
                self.sql_session.session.add(row)
            for row in active_accesses:
                snapshot_rows.append(MembershipSuspension(
                    user_id=uid, table_name=APPLICATION_MEMBERSHIPS, row_id=row.id,
                ))
                row.is_active = False
                self.sql_session.session.add(row)

            for snap in snapshot_rows:
                self.sql_session.session.add(snap)

            self.sql_session.session.flush()
            return Ok({
                "user_id": str(uid),
                "suspended_user_memberships": len(active_memberships),
                "suspended_application_memberships": len(active_accesses),
            })
        except Exception as e:
            logger.error(f"MembershipSuspensionPostgresRepository.suspend error: {e}")
            return Err(str(e))

    def restore(self, user_id: str) -> Result[Dict[str, Any], str]:
        """iam.user.restore_membership.in — reactiva EXACTAMENTE las filas
        capturadas en el snapshot vigente (nunca "todas las filas del
        usuario") y cierra esa suspensión.
        """
        try:
            uid = uuid.UUID(user_id)

            snapshot = self.sql_session.session.exec(
                select(MembershipSuspension).where(
                    MembershipSuspension.user_id == uid,
                    MembershipSuspension.is_active_suspension == True,  # noqa: E712
                )
            ).all()
            if not snapshot:
                return Err("NO_ACTIVE_SUSPENSION")

            restored_memberships = 0
            restored_accesses = 0
            now = datetime.now(timezone.utc)

            for snap in snapshot:
                if snap.table_name == USER_MEMBERSHIPS:
                    row = self.sql_session.session.exec(
                        select(UserMembership).where(UserMembership.id == snap.row_id)
                    ).first()
                    if row:
                        row.is_active = True
                        self.sql_session.session.add(row)
                        restored_memberships += 1
                elif snap.table_name == APPLICATION_MEMBERSHIPS:
                    row = self.sql_session.session.exec(
                        select(ApplicationMembership).where(ApplicationMembership.id == snap.row_id)
                    ).first()
                    if row:
                        row.is_active = True
                        self.sql_session.session.add(row)
                        restored_accesses += 1
                else:
                    logger.error(
                        f"MembershipSuspensionPostgresRepository.restore: "
                        f"table_name desconocido '{snap.table_name}' en snapshot {snap.id}, se ignora"
                    )
                    continue

                snap.is_active_suspension = False
                snap.restored_at = now
                self.sql_session.session.add(snap)

            self.sql_session.session.flush()
            return Ok({
                "user_id": str(uid),
                "restored_user_memberships": restored_memberships,
                "restored_application_memberships": restored_accesses,
            })
        except Exception as e:
            logger.error(f"MembershipSuspensionPostgresRepository.restore error: {e}")
            return Err(str(e))

    def status(self, user_id: str) -> Result[Dict[str, Any], str]:
        try:
            uid = uuid.UUID(user_id)
            active = self.sql_session.session.exec(
                select(MembershipSuspension).where(
                    MembershipSuspension.user_id == uid,
                    MembershipSuspension.is_active_suspension == True,  # noqa: E712
                )
            ).first()
            return Ok({"suspended": active is not None})
        except Exception as e:
            logger.error(f"MembershipSuspensionPostgresRepository.status error: {e}")
            return Err(str(e))
