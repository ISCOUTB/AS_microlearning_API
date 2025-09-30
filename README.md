# AS_microlearning_API
# 📚 Plataforma Universitaria de Micro-learning

Versión: Actualizada
Basado en: arc42 – Documentación arquitectónica

## 🚀 Introducción

Este proyecto implementa el backend de una plataforma universitaria de micro-learning.
El sistema permite la subida y consumo de micro-contenidos (videos cortos, imágenes, tarjetas), con un feed infinito estilo TikTok/Instagram y recolección de métricas básicas:

• ✅ Vistas

• ✅ Likes

La versión actual está centrada en el backend, las APIs y la arquitectura de persistencia/escalabilidad.

### 🎯 Objetivos principales

• Subida, almacenamiento y catalogación de micro-contenidos.

• Consumo tipo scroll con reproducción eficiente.

• Registro mínimo de métricas: vistas y likes.

• Identificación de videos por ID único cifrado.

• APIs abiertas para cliente web/móvil y panel de métricas para docentes.

### 👥 Stakeholders

∙ Usuarios: consumen y reaccionan a micro-contenidos.

• Docentes: suben material y consultan métricas.

• Equipo de desarrollo: mantiene la plataforma.

• Área TI/Operaciones: despliegue y monitoreo.

### 🏗️ Arquitectura

La solución está diseñada para ser segura, escalable y con baja latencia.

#### Componentes principales

• Backend API: feed, reproducción, subida y métricas.

• Storage/CDN: blobs multimedia con URLs firmadas temporalmente.

• Redis: contadores en memoria (likes, vistas) → sincronización a BD.

• DB persistente (PostgreSQL/MongoDB): metadatos, usuarios, métricas históricas.

• Jobs de sincronización: trasladan contadores de Redis a DB.

• Panel de métricas/BI: consultas y reportes.

#### Flujos básicos

• Subida: validación → bucket de storage → DB con ID cifrado.

• Reproducción: API → lista paginada → URL firmada para CDN.

• Métricas: API → contador Redis → sync por lotes a DB.

### 🔐 Decisiones clave

• No se exponen rutas de archivos → solo IDs cifrados y URLs firmadas.

• Se registran solo likes y vistas (sin métricas avanzadas).

• Todos los usuarios actuales son generales (sin roles diferenciados aún).

• Redis se usa como fuente en tiempo real y DB como histórico persistente.

# ⚙️ Métodos de ejecución
### 1. Clonar el repositorio
`git clone https://github.com/ISCOUTB/AS_microlearning_API.git`
`cd AS_microlearning_API`
### 2. Variables de entorno

Crea un archivo `.env` con al menos:

```env
DATABASE_URL=...
REDIS_URL=...
STORAGE_BUCKET=...
JWT_SECRET=...

npm run start:dev

