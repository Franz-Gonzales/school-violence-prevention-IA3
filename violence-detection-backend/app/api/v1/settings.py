"""
Endpoints de configuración del sistema
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from app.core.dependencies import DependenciasComunes, requiere_admin
from app.models.system_config import ConfiguracionSistema, TipoDato, Categoria  # Importar los Enum
from app.utils.logger import obtener_logger

logger = obtener_logger(__name__)
router = APIRouter(prefix="/settings", tags=["configuración"])


@router.get("/")
async def obtener_configuraciones(
    categoria: Optional[Categoria] = None,  # Usar Enum
    deps: DependenciasComunes = Depends()
):
    """Obtiene las configuraciones del sistema"""
    query = select(ConfiguracionSistema)
    
    if categoria:
        query = query.where(ConfiguracionSistema.categoria == categoria)  # Comparar con Enum
    
    # Filtrar configuraciones sensibles para usuarios normales
    if deps.usuario_actual.get("rol") != "admin":
        query = query.where(ConfiguracionSistema.es_sensible == False)
    
    resultado = await deps.db.execute(query)
    configuraciones = resultado.scalars().all()
    
    # Convertir a diccionario para facilitar uso
    config_dict = {}
    for config in configuraciones:
        config_dict[config.clave] = {
            "valor": config.valor,
            "tipo": config.tipo_dato.value,  # Convertir Enum a cadena
            "descripcion": config.descripcion,
            "modificable": config.modificable_por_usuario
        }
    
    return config_dict


@router.get("/{clave}")
async def obtener_configuracion(
    clave: str,
    deps: DependenciasComunes = Depends()
):
    """Obtiene una configuración específica"""
    query = select(ConfiguracionSistema).where(
        ConfiguracionSistema.clave == clave
    )
    
    resultado = await deps.db.execute(query)
    config = resultado.scalars().first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    # Verificar permisos para configuraciones sensibles
    if config.es_sensible and deps.usuario_actual.get("rol") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para ver esta configuración"
        )
    
    return {
        "clave": config.clave,
        "valor": config.valor,
        "tipo": config.tipo_dato.value,  # Convertir Enum a cadena
        "descripcion": config.descripcion
    }


@router.put("/{clave}")
async def actualizar_configuracion(
    clave: str,
    valor: str,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Actualiza una configuración del sistema"""
    # Buscar configuración
    query = select(ConfiguracionSistema).where(
        ConfiguracionSistema.clave == clave
    )
    
    resultado = await deps.db.execute(query)
    config = resultado.scalars().first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    # Verificar si es modificable
    if not config.modificable_por_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Esta configuración no es modificable"
        )
    
    # Validar tipo de dato
    try:
        if config.tipo_dato == TipoDato.INTEGER:  # Usar Enum
            int(valor)
        elif config.tipo_dato == TipoDato.FLOAT:  # Usar Enum
            float(valor)
        elif config.tipo_dato == TipoDato.BOOLEAN:  # Usar Enum
            if valor.lower() not in ["true", "false"]:
                raise ValueError("Valor booleano inválido")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Valor inválido para tipo {config.tipo_dato.value}"  # Convertir Enum a cadena
        )
    
    # Actualizar
    config.valor = valor
    config.ultima_modificacion_por = int(deps.usuario_actual["id"])
    
    await deps.db.commit()
    await deps.db.refresh(config)
    
    logger.info(f"Configuración {clave} actualizada por usuario {deps.usuario_actual['id']}")
    print(f"Configuración {clave} actualizada por usuario {deps.usuario_actual['id']}")
    
    return {
        "mensaje": "Configuración actualizada",
        "configuracion": {
            "clave": config.clave,
            "valor": config.valor
        }
    }


@router.post("/reset/{clave}")
async def resetear_configuracion(
    clave: str,
    deps: DependenciasComunes = Depends(),
    _admin = Depends(requiere_admin())
):
    """Resetea una configuración a su valor por defecto"""
    query = select(ConfiguracionSistema).where(
        ConfiguracionSistema.clave == clave
    )
    
    resultado = await deps.db.execute(query)
    config = resultado.scalars().first()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuración no encontrada"
        )
    
    if not config.valor_por_defecto:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta configuración no tiene valor por defecto"
        )
    
    # Resetear
    config.valor = config.valor_por_defecto
    config.ultima_modificacion_por = int(deps.usuario_actual["id"])
    
    await deps.db.commit()
    
    return {
        "mensaje": "Configuración reseteada",
        "valor_actual": config.valor
    }


@router.get("/categorias/listar")
async def listar_categorias(
    deps: DependenciasComunes = Depends()
):
    """Lista las categorías de configuración disponibles"""
    query = select(ConfiguracionSistema.categoria).distinct()
    resultado = await deps.db.execute(query)
    categorias = [cat.value for (cat,) in resultado if cat]  # Convertir Enum a cadena
    
    return {"categorias": categorias}