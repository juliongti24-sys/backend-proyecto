"""
Dependencia de seguridad para MathBoost.
Simula validación de sesión leyendo el header X-User-ID y X-User-Role.
El frontend Express actúa como middleware de confianza que inyecta estos headers.
"""
from fastapi import Header, HTTPException, status


async def get_current_user(
    x_user_id: str = Header(..., alias="X-User-ID"),
    x_user_role: str = Header(..., alias="X-User-Role"),
) -> dict:
    """
    Extrae la identidad del usuario autenticado desde los headers de confianza.
    Retorna un dict con 'user_id' y 'role'.
    """
    if not x_user_id or not x_user_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales de sesión no proporcionadas.",
        )
    return {"user_id": x_user_id, "role": x_user_role}


def require_role(required_role: str):
    """
    Factory que devuelve una dependencia que valida que el rol del usuario
    coincida con el requerido. Si no coincide → 403 Forbidden.
    """
    async def _check_role(
        x_user_id: str = Header(..., alias="X-User-ID"),
        x_user_role: str = Header(..., alias="X-User-Role"),
    ) -> dict:
        if not x_user_id or not x_user_role:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales de sesión no proporcionadas.",
            )
        if x_user_role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {required_role}.",
            )
        return {"user_id": x_user_id, "role": x_user_role}
    return _check_role
