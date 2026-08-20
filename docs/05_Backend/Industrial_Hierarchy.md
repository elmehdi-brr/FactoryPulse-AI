
# Industrial Hierarchy

## Purpose

FactoryPulse AI is designed as a broad industrial intelligence platform rather than only a machine-monitoring application.

The Industrial Hierarchy provides the organizational structure required to represent real industrial environments such as factories, plants, logistics facilities, utility sites, and multi-site organizations.

This hierarchy will become the structural foundation for future FactoryPulse modules including:

- Production monitoring
- Predictive maintenance
- Energy management
- Quality control
- Inventory and spare parts
- Work orders
- Industrial analytics
- Downtime tracking
- KPI and OEE monitoring
- Multi-site management
- AI-driven industrial insights

---

## Initial Hierarchy

The first FactoryPulse industrial hierarchy is:

Organization / Company

↓

Site / Factory

↓

Area / Department

↓

Production Line

↓

Machine

↓

Sensor

The hierarchy does not assume that every machine belongs to a production line.

Some industrial assets may belong directly to an Area.

For example:

Organization: FactoryPulse Demo Industries

└── Site: Tangier Factory

    ├── Area: Production Hall

    │   ├── Production Line 1

    │   │   ├── Machine: Motor 01

    │   │   └── Machine: Packaging Machine 01

    │   └── Production Line 2

    │       └── Machine: Conveyor 02

    └── Area: Utilities

        ├── Machine: Air Compressor 01

        ├── Machine: Cooling Pump 01

        └── Machine: HVAC Unit 01

This design prevents FactoryPulse from forcing every industrial asset into a production-line model.

---

## Core Entities

### Organization

Represents the company or industrial organization using FactoryPulse.

An Organization may contain multiple industrial sites.

Examples:

- Manufacturing company
- Port operator
- Logistics company
- Energy company
- Industrial group

Relationship:

Organization

↓

Multiple Sites

---

### Site

Represents a physical industrial location.

Examples:

- Factory
- Plant
- Warehouse
- Terminal
- Distribution center
- Energy facility

Each Site belongs to one Organization.

A Site may contain multiple Areas.

Relationship:

Organization

↓

Site

↓

Areas

---

### Area

Represents a logical or physical section inside a Site.

Examples:

- Production Hall
- Assembly Area
- Packaging Department
- Utilities
- Maintenance Workshop
- Quality Laboratory
- Warehouse Area

Each Area belongs to one Site.

An Area may contain:

- Production Lines
- Machines
- Future industrial resources

---

### Production Line

Represents a production or operational line within an Area.

Examples:

- Assembly Line 1
- Packaging Line 2
- Filling Line A
- Conveyor Line

Each Production Line belongs to one Area.

A Production Line may contain multiple Machines.

Production Lines are optional in the hierarchy because not every industrial machine belongs to a production line.

---

### Machine

The existing FactoryPulse Machine entity will become part of the broader industrial hierarchy.

A Machine will belong to an Area.

A Machine may optionally belong to a Production Line.

This allows FactoryPulse to represent both:

Production assets:

Area → Production Line → Machine

and utility or infrastructure assets:

Area → Machine

The existing Machine → Sensor relationship remains unchanged.

---

## Initial Relationship Model

Organization

↓

Site

↓

Area

├── Production Line

│   └── Machine

│       └── Sensor

│           └── SensorReading

│               └── Prediction

│                   └── Alert

└── Machine

    └── Sensor

This hierarchy extends the existing FactoryPulse operational intelligence pipeline without replacing it.

---

## Architectural Principle

Industrial modules should attach to the most appropriate level of the hierarchy.

Examples:

Organization level:

- Cross-site reports
- Corporate KPIs
- User administration

Site level:

- Factory production totals
- Site energy consumption
- Site-level dashboards

Area level:

- Department performance
- Utility consumption
- Area-specific alerts

Production Line level:

- Production rate
- Downtime
- OEE
- Line efficiency

Machine level:

- Condition monitoring
- Predictive maintenance
- Sensor telemetry

This prevents FactoryPulse from using Machine as the parent of every industrial concept.

---

## Future Expansion

The hierarchy is intentionally designed so FactoryPulse can later introduce additional entities such as:

- Asset
- Equipment groups
- Energy meters
- Work centers
- Warehouses
- Quality stations
- Utility systems
- Storage systems
- Production orders

without redesigning the entire backend.

---

## Related Documentation

- [[Backend_Implementation]]
- [[Backend_Roadmap]]
- [[Architecture_Overview]]
- [[Database_Schema]]
- [[Entity_Relationship_Diagram]]
- [[Data_Dictionary]]
- [[Authentication_and_RBAC]]

---

## Implementation Order

The initial hierarchy will be implemented in this order:

1. Organization
2. Site
3. Area
4. Production Line
5. Integrate Machine into the hierarchy
6. Add API services and routes
7. Apply RBAC
8. Test hierarchy relationships
9. Update database and architecture documentation



---

## Industrial Hierarchy ORM Implementation

The first FactoryPulse industrial hierarchy has been implemented in the SQLAlchemy ORM layer.

New models:

- `Organization`
- `Site`
- `Area`
- `ProductionLine`

The existing `Machine` model was integrated into the hierarchy.

The resulting structure is:

Organization

↓

Site

↓

Area

├── ProductionLine

│   └── Machine

└── Machine

The existing Machine-to-Sensor relationship remains unchanged.

This allows FactoryPulse to represent both production assets and standalone utility or infrastructure assets.

---

## Organization Model

Implemented in:

`backend/app/models/organization.py`

Table:

`organizations`

Fields:

- `id`
- `name`
- `code`
- `description`
- `created_at`

The `code` field is unique.

Relationship:

`Organization → Sites`

---

## Site Model

Implemented in:

`backend/app/models/site.py`

Table:

`sites`

Fields:

- `id`
- `organization_id`
- `name`
- `code`
- `location`
- `description`
- `created_at`

Relationship:

`sites.organization_id → organizations.id`

Each Site belongs to one Organization.

A Site may contain multiple Areas.

---

## Area Model

Implemented in:

`backend/app/models/area.py`

Table:

`areas`

Fields:

- `id`
- `site_id`
- `name`
- `code`
- `description`
- `created_at`

Relationship:

`areas.site_id → sites.id`

An Area may contain:

- Production Lines
- Machines directly

This is important because not every industrial asset belongs to a production line.

---

## ProductionLine Model

Implemented in:

`backend/app/models/production_line.py`

Table:

`production_lines`

Fields:

- `id`
- `area_id`
- `name`
- `code`
- `description`
- `created_at`

Relationship:

`production_lines.area_id → areas.id`

A Production Line may contain multiple Machines.

---

## Machine Hierarchy Integration

The existing Machine model was extended with:

`area_id`

and:

`production_line_id`

The final architectural rule is:

`area_id = required`

`production_line_id = optional`

This supports:

`Area → ProductionLine → Machine`

and:

`Area → Machine`

The Machine ORM relationships are:

`machine.area`

and:

`machine.production_line`

Reverse relationships include:

`area.machines`

and:

`production_line.machines`

---

## Industrial Hierarchy Migration

The first hierarchy migration was generated using:

`alembic revision --autogenerate -m "add industrial hierarchy"`

Migration revision:

`60a98459d249`

Previous revision:

`9e42d11f73be`

The migration created:

- `organizations`
- `sites`
- `areas`
- `production_lines`

It also added:

- `machines.area_id`
- `machines.production_line_id`

The Machine foreign-key constraints were explicitly named:

`fk_machines_area_id`

and:

`fk_machines_production_line_id`

The initial migration temporarily allowed:

`machines.area_id = NULL`

because Machine records already existed before the hierarchy was introduced.

This allowed the database schema to evolve without destroying or invalidating existing machine data.

---

## Development Hierarchy Seed

A reproducible hierarchy seed script was implemented in:

`backend/app/scripts/seed_industrial_hierarchy.py`

The development hierarchy is:

FactoryPulse Demo Industries

↓

Tangier Factory

↓

Production Area

↓

Production Line 1

↓

Industrial Motor 01

The hierarchy was verified directly through PostgreSQL using joins across:

- organizations
- sites
- areas
- production_lines
- machines

The existing Machine record was successfully preserved and attached to the new hierarchy.

---

## Required Machine Area Migration

After all existing machines were assigned to valid Areas, the database was checked for machines where:

`area_id IS NULL`

Result:

`0 rows`

The Machine ORM model was then updated so:

`area_id`

became required.

A second migration was generated:

`alembic revision --autogenerate -m "require machine area"`

Migration revision:

`85c9a83351b5`

Previous revision:

`60a98459d249`

The migration changed only:

`machines.area_id`

from nullable to:

`NOT NULL`

The migration was applied successfully.

PostgreSQL verification confirmed:

`area_id → NOT NULL`

while:

`production_line_id → nullable`

The final enforced database model is therefore:

Every Machine MUST belong to an Area.

A Machine MAY belong to a Production Line.

Foreign-key constraints verified:

`machines.area_id → areas.id`

`machines.production_line_id → production_lines.id`

The first persistent FactoryPulse industrial hierarchy is now operational.

---

## Current Phase 3 State

Implemented:

- Organization ORM
- Site ORM
- Area ORM
- ProductionLine ORM
- Machine hierarchy integration
- Database migrations
- Existing machine data migration
- Development hierarchy seed
- Required Machine-to-Area relationship

Next milestone:

**Implement Pydantic schemas, services, REST APIs, and RBAC for Organization, Site, Area, and ProductionLine.**

