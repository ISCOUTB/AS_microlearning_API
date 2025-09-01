# arc42 – Plataforma Universitaria de Micro-learning

**Versión:** Actualizada  
**Alcance:** Secciones completadas hasta la Solución Arquitectónica y extensión sobre persistencia/escalabilidad.  
**Nota:** Se ha tomado el contenido existente y se ha insertado en la plantilla. Se han eliminado las secciones de la plantilla que no se han trabajado todavía.

---

# Introducción y Metas

## Propósito
Documentar la arquitectura de la "Plataforma Universitaria de Micro-learning", una aplicación tipo feed (similar a TikTok/Instagram), orientada a entregar micro-contenidos (videos cortos, imágenes, tarjetas) asociados a las materias que cursan los estudiantes. El foco de esta versión está en la funcionalidad backend, la recolección de métricas básicas (vistas y likes) y la entrega de APIs para consumo por parte del cliente y del equipo docente.

## Metas / Objetivos
- Soportar subida, almacenamiento y catalogación de micro-contenidos (metadatos: título, descripción, etiquetas, duración).
- Permitir consumo tipo scroll por parte de usuarios, con reproducción eficiente y registro únicamente de métricas básicas: número de vistas y número de likes.
- Identificar videos mediante un ID único cifrado para mayor seguridad.
- Exponer APIs para el cliente (web/móvil) y para consultas de métricas por parte del personal autorizado.

## Partes interesadas (Stakeholders)
- **Usuarios (generales):** consumen y reaccionan ante los micro-contenidos.  
- **Docentes:** interesados en métricas y en subir contenido (stakeholders).  
- **Equipo de desarrollo:** implementa y mantiene la plataforma.  
- **Área de TI / Operaciones:** responsables de despliegue y operación.

---

# Restricciones de la Arquitectura

## Técnicas
- No almacenar rutas de vídeo en la arquitectura de metadatos: los videos se identifican por un ID único que será cifrado cuando sea necesario y las URL de acceso a medios serán firmadas temporalmente por el servicio de entrega en el momento de la reproducción.
- Solo métricas mínimas por ahora: número de vistas y número de likes. No se registran detalles de reproducción (porcentaje visto, pausas, etc.) en esta fase.
- Separación metadatos ↔ contenido multimedia: blobs en almacenamiento de objetos (cloud buckets/CDN), metadatos en base de datos.

## Organizativas
- Por ahora, los usuarios se consideran de tipo general; no hay distinción funcional entre estudiante, profesor o superusuario en el modelo de usuarios.

## Legales / Privacidad
- Cumplimiento de políticas de protección de datos de la universidad: consentimiento para recolección de métricas, retención y eliminación según normativa.

## No funcionales
- Escalabilidad para atender feed infinito y picos de reproducciones.
- Seguridad: cifrado de IDs sensibles, URLs firmadas para acceso a medios y cifrado en tránsito/reposo.

---

# Alcance y Contexto del Sistema

## Visión general
El sistema interactúa con los siguientes actores y servicios externos:
- Usuarios (clientes web/móvil) que consumen el feed.
- Docentes/docentes como interesados en métricas y en subir contenido (stakeholders).
- Servicios de la universidad (SSO, catálogos académicos) si se requieren integraciones.
- Servicios de nube: almacenamiento de objetos, CDN, servicios de mensajería/eventos y caches (Redis).

## Entradas externas principales
- Subida de metadatos y archivos multimedia desde una interfaz de subida (profesor o personal autorizado).
- Solicitudes del feed y peticiones de reproducción desde clientes.

## Salidas externas principales
- Entrega de contenido (streaming controlado mediante CDN y URLs firmadas).
- Endpoints de métricas para consulta y exportación.

## Relaciones y límites del sistema
- Los blobs (archivos multimedia) permanecen en almacenamiento de objetos y son entregados vía CDN; la aplicación no expone rutas estáticas de archivos, sino IDs y firmas temporales.
- Eventos de interacción se limitan a "vista" y "like" y serán gestionados en memoria para rendimiento antes de su persistencia.

---

# Estrategia de solución

La solución prioriza una experiencia tipo feed con latencias bajas para interacciones sencillas (vistas y likes), seguridad en la entrega de medios y una arquitectura preparada para escalar. A continuación se detallan los elementos implementados y las decisiones tomadas hasta la fecha.

---

# Vista de Bloques / Componentes principales

- **Backend (Service API):** Endpoints para el feed, reproducción, subida de contenido y registro de interacciones (vista, like). Autenticación mínima (usuarios generales).
- **Servicio de Almacenamiento / Media:** Buckets en la nube para videos; no se persisten rutas públicas. Acceso mediante URL firmada generada al solicitar reproducción; los videos son referenciados internamente por un ID cifrado.
- **Caché y contadores en memoria (Redis):** Registro en memoria de incrementos de vistas y likes para latencias muy bajas.
- **Almacén transaccional (PostgreSQL o MongoDB):** Persistencia de metadatos (usuarios, videos, estado histórico).
- **Procesamiento y sincronización por lotes:** Jobs que sincronizan los contadores de Redis con la base de datos persistente en intervalos regulares.
- **Panel de métricas / BI:** Consulta de métricas básicas (vistas, likes) a partir de la base de datos persistente y pre-aggregados.
- **Servicios auxiliares:** CDN para entrega, monitoreo y backups.

---

# Flujos principales (resumidos)

- **Subida de video (simplificado):** Interfaz de subida → validación de metadatos → almacenamiento de archivo en bucket (ID asignado) → persistencia de metadatos en DB (ID cifrado almacenado).
- **Reproducción / scroll infinito:** Cliente solicita items del feed → Backend devuelve lista paginada o basada en cursores (sin exponer rutas) → cliente solicita reproducción de un item → Backend genera URL firmada desde CDN/Storage usando el ID cifrado → reproducción en cliente.
- **Registro de interacción (vistas/likes):** Cliente envía evento (vista o like) → API incrementa contador en Redis (operación O(1)) → los contadores se sincronizan periódicamente a la DB persistente por un job por lotes.

---

# Decisiones arquitectónicas importantes

- Eliminación de "ruta de vídeo": para evitar exposición de paths, se usa ID único cifrado como identificador de recursos.
- Métricas limitadas: por simplicidad y privacidad, registrar sólo vistas y likes en esta fase.
- Usuarios generales: el modelo de seguridad no discrimina entre tipos de usuario; cualquier acceso especial se gestionará externamente o en futuras iteraciones.
- Uso de Redis para métricas en tiempo real y sincronización por lotes a DB para durabilidad.

---

# Solución Arquitectónica (Extensión sobre persistencia y escalabilidad)

La plataforma seguirá un modelo híbrido para balancear consistencia, velocidad y escalabilidad:

## 1. Manejo de Interacciones Rápidas (likes y vistas)
- Redis actuará como base en memoria para registrar incrementos de likes y vistas en tiempo real, asegurando latencias muy bajas y evitando sobrecarga de escritura en la base de datos principal.
- Los contadores en Redis serán sincronizados periódicamente (por lotes) con la base de datos persistente para garantizar durabilidad y evitar pérdida de información ante reinicios. Se recomienda diseñar ventanas y checkpoints (por ejemplo, sincronización cada N segundos o por número de eventos) y usar operaciones atómicas en Redis (INCR) para consistencia eventual.

## 2. Persistencia de Datos Principales
- **PostgreSQL:** opción recomendada para manejar usuarios, videos y relaciones estructuradas que requieren integridad referencial (FKs, transacciones).
- **Alternativa – MongoDB:** considerar MongoDB si se espera que los metadatos de videos o interacciones evolucionen hacia estructuras semi-estructuradas.

## 3. Estrategia de Escalabilidad y Feed Infinito
- Paginación basada en cursores o índices eficientes: el feed infinito debe implementarse con paginación basada en cursores (cursor pagination) o mediante índices en PostgreSQL para evitar sobresaltos de rendimiento en OFFSET grandes. En MongoDB, usar paginación por `_id` o cursores nativos.
- Redis como caché y fuente de estado en vivo: mantener contadores en Redis para consultas rápidas (p. ej. número de likes mostrado en el feed), y usar TTLs para entradas cacheadas que puedan ser recargadas desde la DB.
- Preparado para escalar horizontalmente: servicios stateless (API) en contenedores orquestados, almacenamiento gestionado y particionado con read replicas si es necesario.

**Resumen técnico:**  
Redis → métricas en tiempo real (likes, vistas).  
PostgreSQL / MongoDB → persistencia y consultas históricas.

---

# Notas finales y próximos pasos

1. Incorporar en el documento los diagramas C4 (nivel 1 y 2) que reflejen la arquitectura con Redis, Storage/CDN, DB persistente y jobs de sincronización.  
2. Preparar un esquema de datos mínimo: Usuario (id, metadata), Video (id cifrado, título, etiquetas, tamaño, duración, metadatos), Contadores (video_id, likes_total, views_total).  
3. Definir contratos API simplificados: endpoints para obtener feed (cursor/paginación), obtener meta de un video, solicitar URL firmada, y endpoints para reportar "vista" y "like".  
4. Diseñar y parametrizar la política de sincronización Redis→DB (ventana, tolerancia de pérdida, confirmaciones).  
5. Documentar políticas de retención y consentimiento conforme a la normativa universitaria.

---
