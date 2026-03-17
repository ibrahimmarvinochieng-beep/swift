// Swift Dependency Graph - Neo4j Schema
// Run manually: neo4j-admin or Neo4j Browser
// Constraints and indexes for production deployment

// ============ CONSTRAINTS (Unique IDs per node type) ============
CREATE CONSTRAINT loc_id IF NOT EXISTS FOR (n:Location) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT infra_id IF NOT EXISTS FOR (n:Infrastructure) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT ind_id IF NOT EXISTS FOR (n:Industry) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT org_id IF NOT EXISTS FOR (n:Organization) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT sc_id IF NOT EXISTS FOR (n:SupplyChain) REQUIRE n.id IS UNIQUE;

// ============ INDEXES (Name + Type for traversal) ============
CREATE INDEX location_name IF NOT EXISTS FOR (n:Location) ON (n.name);
CREATE INDEX location_type IF NOT EXISTS FOR (n:Location) ON (n.type);
CREATE INDEX infrastructure_name IF NOT EXISTS FOR (n:Infrastructure) ON (n.name);
CREATE INDEX infrastructure_type IF NOT EXISTS FOR (n:Infrastructure) ON (n.type);
CREATE INDEX industry_name IF NOT EXISTS FOR (n:Industry) ON (n.name);
CREATE INDEX industry_type IF NOT EXISTS FOR (n:Industry) ON (n.type);
CREATE INDEX organization_name IF NOT EXISTS FOR (n:Organization) ON (n.name);
CREATE INDEX organization_type IF NOT EXISTS FOR (n:Organization) ON (n.type);
CREATE INDEX supplychain_name IF NOT EXISTS FOR (n:SupplyChain) ON (n.name);
CREATE INDEX supplychain_type IF NOT EXISTS FOR (n:SupplyChain) ON (n.type);
