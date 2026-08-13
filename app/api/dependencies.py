from fastapi import Header, Depends, FastAPI, HTTPException

def get_current_tenant(
        x_tenant_id: str | None = Header(default=None),
) -> str:
    if not x_tenant_id:
        raise HTTPException(
            status_code=401,
            detail="No tenant ID provided",
        )

    return x_tenant_id