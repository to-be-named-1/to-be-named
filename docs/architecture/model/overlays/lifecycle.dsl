// Overlay: lifecycle
// Purpose: tags elements that are designed but not yet built with "Later", using !element blocks.
// Remove when: no element is tagged "Later"; delete this file, views/overlays/lifecycle.dsl and both !include lines in workspace.dsl.

// Containers outside the first development slice (D29).
!element platform.cli {
    tags "Later"
}
!element platform.sessionUnit {
    tags "Later"
}
!element platform.commandUnit {
    tags "Later"
}
!element platform.publicationUnit {
    tags "Later"
}

// External systems the first development slice does not use (D29).
!element hpcScheduler {
    tags "Later"
}
!element cloudBatch {
    tags "Later"
}
!element warehouses {
    tags "Later"
}
!element lakehouseCatalog {
    tags "Later"
}
!element notificationChannels {
    tags "Later"
}
!element ciSystem {
    tags "Later"
}
