// Component views. A component view holds only its own container's components; other containers appear whole.

component platform.controlPlane "components-control-plane" "The control-plane server's components, grouped by bounded context, with the clients, agents, external systems and database they connect to." {
    include "*"
    autoLayout lr
}

component platform.database "components-database" "The database's schemas: one per bounded context, grouped like the components that own them, and one shared by no context; no context reaches another's schema (D47)." {
    include *
    autoLayout lr
}
