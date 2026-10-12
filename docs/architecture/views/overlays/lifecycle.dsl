// Overlay: lifecycle
// Purpose: styles elements tagged "Later" (model/overlays/lifecycle.dsl) and adds a container view without them.
// Remove when: no element is tagged "Later"; delete this file, model/overlays/lifecycle.dsl and both !include lines in workspace.dsl.

container platform "containers-first-slice" "The containers of the first development slice (D29), leaving out what is not yet built." {
    include "element.parent==platform"
    exclude "element.tag==Later"
    autoLayout lr
}

styles {
    element "Later" {
        border dashed
        opacity 60
    }
}
