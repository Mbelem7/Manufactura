
# Sistema ERP/MES - Manufactura de Champú Artesanal

## Descripción del proyecto

Sistema ERP/MES desarrollado para gestionar los procesos administrativos y productivos relacionados con la elaboración de champú artesanal de café y romero.

El sistema integra las operaciones de compras, inventario, producción y ventas, permitiendo registrar y consultar la información de cada proceso desde una misma plataforma.

Además, incorpora funcionalidades de ejecución de manufactura (MES) para dar seguimiento a las órdenes de producción, registrar las cantidades producidas y mantener actualizado el inventario de materias primas y productos terminados.

Este proyecto fue desarrollado como parte de la asignatura **Sistema de Manufactura** de la carrera de Ingeniería de Sistemas de la Universidad Nacional de Ingeniería (UNI).

## Tecnologías utilizadas

| Tecnología | Descripción |
|---|---|
| Python | Lenguaje de programación del backend |
| Flask 3.1.3 | Framework de desarrollo web |
| PostgreSQL | Sistema de gestión de base de datos |
| Supabase | Alojamiento de la base de datos |
| SQLAlchemy 2.1.3 | Gestión y consultas a la base de datos |
| Flask-SQLAlchemy 3.1.1 | Integración entre Flask y SQLAlchemy |
| Psycopg 3.3.6 | Conexión con PostgreSQL |
| Jinja2 3.1.6 | Motor de plantillas HTML |
| Bootstrap 5 | Diseño de la interfaz web |
| HTML, CSS y JavaScript | Estructura, estilos e interactividad |
| Vercel | Despliegue de la aplicación |

## Funcionalidades del sistema

### 1. Gestión de usuarios
- Inicio de sesión.
- Administración de usuarios.
- Asignación de roles y permisos.
- Control de acceso mediante sesiones.

### 2. Compras
- Registro y administración de proveedores.
- Creación de órdenes de compra.
- Registro de recepción de materiales.
- Actualización del inventario mediante las recepciones.

### 3. Inventario
- Administración del catálogo de productos.
- Registro y gestión de almacenes.
- Control de existencias.
- Consulta de inventario por producto, almacén y lote.
- Seguimiento de materias primas y productos terminados.

### 4. Producción
- Registro de listas de materiales (BOM).
- Administración de centros de trabajo.
- Creación de órdenes de producción.
- Registro de operaciones y rutas de fabricación.
- Consulta de materiales requeridos para la producción.

### 5. Ejecución de manufactura (MES)
- Inicio y finalización de ejecuciones de producción.
- Registro de fechas y horas de ejecución.
- Registro de cantidades aceptadas y rechazadas.
- Actualización automática del inventario al finalizar la producción.
- Seguimiento de las órdenes de producción.

### 6. Ventas
- Administración de clientes.
- Creación de órdenes de venta.
- Registro de despachos.
- Descuento de productos del inventario al realizar despachos.

### 7. Dashboard
Panel de control que presenta información e indicadores relacionados con las operaciones del sistema:

- Rendimiento de producción.
- Porcentaje de órdenes de compra recibidas.
- Porcentaje de órdenes de venta despachadas.

## Estructura del proyecto

El proyecto está organizado en carpetas destinadas al backend, los recursos estáticos y las plantillas de la interfaz web.

```text
Manufactura/
├── Documentos/
│   └── Tareas/
├── models/
├── modulos/
├── routes/
├── static/
│   ├── css/
│   └── js/
├── templates/
│   ├── auth/
│   ├── components/
│   ├── compras/
│   │   ├── ordenes/
│   │   ├── proveedores/
│   │   └── recepciones/
│   ├── configuracion/
│   │   └── usuarios/
│   ├── dashboard/
│   ├── inventario/
│   │   ├── almacenes/
│   │   ├── existencias/
│   │   ├── lotes/
│   │   └── productos/
│   ├── layouts/
│   ├── produccion/
│   │   ├── bom/
│   │   ├── centros_trabajo/
│   │   ├── ejecuciones/
│   │   ├── ordenes/
│   │   └── rutas/
│   └── ventas/
│       ├── clientes/
│       ├── despachos/
│       └── ordenes/
├── app.py
└── requirements.txt
```

Las carpetas `models`, `modulos` y `routes` forman parte de la organización del backend. La carpeta `static` contiene recursos CSS y JavaScript, mientras que `templates` agrupa las plantillas HTML utilizadas en los distintos módulos del sistema.

## Instalación y ejecución local

### Requisitos previos

Para ejecutar el proyecto localmente se necesita:

- Python instalado.
- Git instalado.
- Acceso a la configuración privada requerida por la aplicación.
- Conexión a la base de datos correspondiente.

### 1. Clonar el repositorio

Clonar la rama `Backend`:

```bash
git clone -b Backend https://github.com/Mbelem7/Manufactura.git
```

Ingresar al directorio del proyecto:

```bash
cd Manufactura
```

### 2. Crear un entorno virtual

En Windows:

```bash
py -m venv .venv
```

Activar el entorno virtual:

```bash
.venv\Scripts\activate
```

### 3. Instalar las dependencias

Ejecutar:

```bash
pip install -r requirements.txt
```

Este comando instala las librerías necesarias utilizando las versiones definidas en el archivo `requirements.txt`.

### 4. Configuración de acceso

Para ejecutar el sistema localmente es necesario contar con la configuración de acceso correspondiente a los servicios utilizados por la aplicación.

Por motivos de seguridad, las credenciales y configuraciones privadas no se incluyen en este repositorio. Deben obtenerse mediante los responsables del proyecto.

### 5. Iniciar el servidor

Ejecutar el siguiente comando desde la carpeta principal:

```bash
py -m flask --app app run --debug
```

Este comando inicia la aplicación Flask en modo de desarrollo.

Por defecto, Flask utiliza la siguiente dirección local:

```text
http://127.0.0.1:5000
```

## Acceso al sistema desplegado

El sistema se encuentra desplegado en Vercel y puede consultarse desde la siguiente dirección:

**[Acceder al sistema ERP/MES](https://manufactura-orcin.vercel.app)**

Repositorio del proyecto:

**[GitHub - Manufactura](https://github.com/Mbelem7/Manufactura)**

**Rama correspondiente a la entrega:** `Backend`

## Caso de estudio

El sistema fue desarrollado tomando como referencia la fabricación de champú artesanal de café y romero en presentaciones de 260 ml.

El proceso contempla la elaboración de lotes de 50 botellas, utilizando una lista de materiales (BOM) que incluye materias primas y componentes de envasado.

Se consideran dos almacenes principales:

- **ALM-MP-001:** almacén de materias primas y envases.
- **ALM-PT-001:** almacén de productos terminados.

El proceso productivo comprende las siguientes operaciones:

1. Preparación y dosificación.
2. Elaboración de la mezcla.
3. Refrigeración y reposo.
4. Control de calidad.
5. Envasado y cierre.
6. Etiquetado e identificación.
7. Registro y almacenamiento.
8. Limpieza y acondicionamiento.

Estas operaciones permiten representar la secuencia de fabricación y registrar su ejecución dentro del sistema.

## Flujo general de funcionamiento

El sistema permite realizar un proceso integrado desde el abastecimiento de materiales hasta la venta del producto terminado.

1. **Compra de materiales:** se registra una orden de compra con las materias primas necesarias.

2. **Recepción:** se confirma la recepción de los materiales y se actualizan sus existencias en inventario.

3. **Orden de producción:** se selecciona el producto, la lista de materiales y la cantidad que se desea fabricar.

4. **Operaciones de fabricación:** se registran las operaciones correspondientes a la orden de producción.

5. **Ejecución MES:** se inicia y finaliza la ejecución, registrando las cantidades aceptadas y rechazadas.

6. **Actualización del inventario:** se descuentan los materiales consumidos y se registran las unidades terminadas.

7. **Orden de venta:** se registra la venta de los productos disponibles.

8. **Despacho:** se realiza la salida de los productos y se actualizan las existencias.

Este flujo permite mantener la relación entre las compras, la producción, el inventario y las ventas.

## Estado actual del proyecto

### Funcionalidades implementadas

- Gestión de usuarios y acceso al sistema.
- Administración de productos, almacenes, proveedores y clientes.
- Gestión de órdenes de compra y recepciones.
- Control de inventario por producto, almacén y lote.
- Gestión de listas de materiales y órdenes de producción.
- Registro de operaciones de fabricación.
- Ejecución de producción MES.
- Gestión de órdenes de venta y despachos.
- Dashboard con indicadores operativos.

### Funcionalidades pendientes

- Implementación de reportes.
- Registro de no conformidades de control de calidad y su disposición.
- Bloqueo del envasado cuando un lote no haya sido aprobado.

## Equipo de desarrollo

Proyecto desarrollado por estudiantes de Ingeniería de Sistemas de la Universidad Nacional de Ingeniería (UNI).

| Integrante | Rol |
|---|---|
| María Belén Guevara Ochoa | Líder de proyecto y documentación |
| Joel Oveth Arroliga Acevedo | Analista de procesos |
| Daviana Paola Lourdes Vela Miranda | Configurador ERP/MES |
| Juan Agustín Vega Chávez | Configurador ERP/MES |
| Eynar Eduardo Espinoza Miranda | Responsable de integración |
| Alberto José Salgado Castillo | Responsable de integración |

## Información académica

**Universidad:** Universidad Nacional de Ingeniería (UNI)

**Carrera:** Ingeniería de Sistemas

**Asignatura:** Sistema de Manufactura

**Grupo:** 5T1-SIS

**Entregable:** Implementación e integración

**Año:** 2026
