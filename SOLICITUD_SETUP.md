# Setup: Solicitudes de Mantenimiento

## Resumen
Se agregaron nuevas funcionalidades al módulo de mantenimiento:
- Modelo `maintenance.solicitud` para que clientes soliciten mantenimiento
- Flujo de aprobación con Director de Operaciones
- Conversión automática a órdenes de mantenimiento

## Archivos Creados/Modificados

### Modelos
- `models/maintenance_solicitud.py` - Nuevo modelo
- `models/maintenance_order.py` - Agregados campos `solicitud_id` y `created_by_user`
- `models/maintenance_order.py` - Campo `created_from_solicitud` en MaintenanceDiagnosis

### Wizard
- `wizard/maintenance_solicitud_assign_order.py` - Asignar solicitud a orden existente

### Vistas
- `views/maintenance_solicitud_views.xml` - Kanban, árbol, formulario
- `wizard/maintenance_solicitud_assign_order_views.xml` - Wizard

### Configuración
- `security/security.xml` - 4 nuevos grupos
- `security/ir.model.access.csv` - 5 nuevos permisos
- `data/ir_sequence_data.xml` - Secuencia SOL
- `__manifest__.py` - Agregados archivos

## Grupos de Acceso

| Grupo | Rol | Permisos |
|-------|-----|----------|
| `group_mtto_cliente_mantenimiento` | Cliente | Crear solicitudes, ver propias |
| `group_mtto_director_operaciones` | Director | Ver todas, aprobar, rechazar |
| `group_mtto_jefe_ventas` | Jefe Ventas | Ver asignadas, editar |
| `group_mtto_supervisor_taller` | Supervisor | Ver asignadas, editar |

## Estados
Borrador → Pendiente Aprobación → Asignada → Convertida ↘ Rechazada
## Flujo Rápido

1. **Cliente**: Menú "Solicitar Mantenimiento" → Nueva solicitud
2. **Cliente**: Click "Enviar para Aprobación"
3. **Director**: Ve en Mantenimiento → Solicitudes
4. **Director**: Aprueba y asigna a Jefe/Supervisor
5. **Staff**: Crea orden nueva O asigna a orden existente
6. **Resultado**: Solicitud convertida a orden

## Para Activar

```bash
# En Odoo, actualizar módulo
# Settings → Apps → Buscar "Global Trucks" → Click en módulo → Update
Testing
bash
# Crear usuario cliente
# Crear usuario director
# Crear usuario jefe/supervisor

# 1. Cliente solicita
# 2. Director aprueba
# Settings → Apps → Buscar "Global Trucks" → Click en módulo → Update
Testing
bash
# Crear usuario cliente
# Crear usuario director
# Crear usuario jefe/supervisor

# 1. Cliente solicita
# 2. Director aprueba
# 3. Staff convierte a orden
